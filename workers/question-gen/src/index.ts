/**
 * Generate CBSE-format questions for NCERT chapters, on the free tier, nightly.
 *
 * The worker is deliberately dumb. It reads a job -- a system prompt, a user
 * prompt, a JSON schema -- sends it to Workers AI, and stores the raw completion.
 * It does not know what a section is, what the board's marks are, or which subject
 * a chapter belongs to. All of that is decided in Python, in
 * `scripts/gen_cbse_batch.py` and `cbse_blueprint`, where it is tested.
 *
 * Two reasons it is built this way:
 *
 *  - The CBSE format is the part with 31 tests against it. Re-implementing it in
 *    TypeScript would leave the worker running on an untested copy, and the two
 *    copies would drift.
 *  - A prompt built in Python is the same prompt the local runs and the tests
 *    used, so what the worker sends is what was verified.
 *
 * Validation is not here either. The worker stores what came back; the Python
 * side judges it, because the validator is where the interesting failures live --
 * the false premise, the distractor ladder, the stem that names its own source.
 * A worker that quietly dropped those would be a worker that looked productive.
 *
 * The budget is the real constraint, and it is enforced here rather than hoped
 * for: the free tier is 10,000 neurons a day, and the run stops at
 * `NEURON_BUDGET` rather than overrunning into a paid tier.
 */

export interface Env {
	AI: Ai;
	BANK: R2Bucket;
	STATE: KVNamespace;
	/** Bearer token for /run and /probe (`wrangler secret put RUN_TOKEN`).
	 *  Unset means those routes refuse; the 02:17 cron needs no token. */
	RUN_TOKEN?: string;
}

/**
 * Every route that calls a model, or hands out what was generated, needs
 * `Authorization: Bearer <token>`, the token being a `wrangler secret`. The
 * Worker sits on a public workers.dev hostname, so without this anyone who
 * found the URL could spend the account's model budget. No token configured
 * means those routes are off (503), never open.
 */
function sameToken(given: string, expected: string): boolean {
	// Constant time: the comparison must not say how many leading bytes matched.
	const a = new TextEncoder().encode(given);
	const b = new TextEncoder().encode(expected);
	let diff = a.length ^ b.length;
	for (let i = 0; i < Math.max(a.length, b.length); i++) diff |= (a[i] ?? 0) ^ (b[i] ?? 0);
	return diff === 0;
}

function refuseUnlessAuthorised(request: Request, expected: string | undefined): Response | null {
	if (!expected) {
		return Response.json({ error: "this route is off until its token secret is set" },
			{ status: 503 });
	}
	const header = request.headers.get("Authorization") || "";
	const given = header.startsWith("Bearer ") ? header.slice("Bearer ".length).trim() : "";
	if (!given || !sameToken(given, expected)) {
		return Response.json({ error: "unauthorised" }, { status: 401 });
	}
	return null;
}

/** Under the 10,000/day free allowance, with headroom for a second call. */
const NEURON_BUDGET = 9000;
const KEY_DAY = "neurons:day";
const KEY_DAY_STAMP = "day";

interface Job {
	key: string;
	raw: string;
	code: string;
	chapter: number;
	sectionKey: string;
	qtype: string;
	marks: number;
}

interface Manifest {
	model: string;
	markBudget: number;
	entries: Job[];
	chapters: unknown[];
}

interface RawResult {
	code: string;
	chapter: number;
	index: number;
	sectionKey: string;
	qtype: string;
	marks: number;
	model: string;
	neurons: number;
	ok: boolean;
	finish?: string;
	raw?: unknown;
	schemaError?: string;
	at: string;
}

function today(): string {
	return new Date().toISOString().slice(0, 10);
}

async function spent(env: Env): Promise<number> {
	const stamp = await env.STATE.get(KEY_DAY_STAMP);
	if (stamp !== today()) return 0;
	return Number((await env.STATE.get(KEY_DAY)) || 0);
}

async function addSpent(env: Env, neurons: number): Promise<void> {
	const stamp = await env.STATE.get(KEY_DAY_STAMP);
	if (stamp !== today()) {
		await env.STATE.put(KEY_DAY_STAMP, today());
		await env.STATE.put(KEY_DAY, String(neurons));
		return;
	}
	const now = Number((await env.STATE.get(KEY_DAY)) || 0);
	await env.STATE.put(KEY_DAY, String(now + neurons));
}

/** R2 has no `get(key, "json")` shorthand -- that is KV's. Parse it. */
async function getJson<T>(bucket: R2Bucket, key: string): Promise<T | null> {
	const object = await bucket.get(key);
	if (!object) return null;
	try {
		return (await object.json()) as T;
	} catch {
		return null;
	}
}

/** What is already generated, so a run resumes rather than restarting. */
async function doneKeys(env: Env): Promise<Set<string>> {
	const done = new Set<string>();
	let cursor: string | undefined;
	do {
		const listed = await env.BANK.list({ prefix: "raw/", cursor, limit: 1000 });
		for (const object of listed.objects) {
			done.add(object.key.slice("raw/".length));
		}
		cursor = listed.truncated ? listed.cursor : undefined;
	} while (cursor);
	return done;
}

/**
 * One generation call.
 *
 * The response is stored as it arrived. Workers AI will not always honour the
 * schema; when it does not it says so with an `error` body rather than an HTTP
 * failure, and that has to survive the round trip so the local validator can see
 * it -- an error turned into an empty object here would look like a chapter that
 * generated nothing.
 */
async function generate(env: Env, model: string, job: Job): Promise<RawResult> {
	const base: RawResult = {
		code: job.code,
		chapter: job.chapter,
		index: Number(job.key.match(/-(\d+)\.json$/)?.[1] ?? 0),
		sectionKey: job.sectionKey,
		qtype: job.qtype,
		marks: job.marks,
		model,
		neurons: 0,
		ok: false,
		at: new Date().toISOString(),
	};

	const stored = await getJson<typeof payload>(env.BANK, job.key);
	if (!stored) {
		base.schemaError = "prompt object missing from R2";
		return base;
	}

	let payload: {
		system?: string;
		user?: string;
		schema?: unknown;
	};
	try {
		payload = stored as typeof payload;
	} catch {
		base.schemaError = "prompt object unreadable";
		return base;
	}
	if (!payload.system || !payload.user) {
		base.schemaError = "prompt object has no system/user";
		return base;
	}

	try {
		const response = await env.AI.run(model as never, {
			messages: [
				{ role: "system", content: payload.system },
				{ role: "user", content: payload.user },
			],
			// The blueprint's own schema: a one-mark question cannot come back as
			// three marks, and the section's type cannot come back as something
			// else. This is why the format lives in code.
			response_format: { type: "json_schema", json_schema: payload.schema as never },
			temperature: 0.4,
			max_tokens: 2500,
		} as never);

		const parsed = response as unknown as {
			response?: unknown;
			usage?: { neurons?: number };
			choices?: { finish_reason?: string }[];
		};
		base.neurons = parsed.usage?.neurons ?? 0;
		base.finish = parsed.choices?.[0]?.finish_reason;
		base.raw = parsed.response;
		if (parsed.response && typeof parsed.response === "object" &&
			"error" in (parsed.response as Record<string, unknown>)) {
			base.schemaError = String(
				(parsed.response as Record<string, unknown>).error);
		} else {
			base.ok = true;
		}
	} catch (error) {
		base.schemaError = `call failed: ${String(error).slice(0, 200)}`;
	}
	return base;
}

async function runBatch(env: Env): Promise<{
	attempted: number;
	written: number;
	neurons: number;
	stopped: string;
}> {
	const manifestObject = await getJson<Manifest>(env.BANK, "manifest.json");
	if (!manifestObject) {
		return { attempted: 0, written: 0, neurons: 0,
			stopped: "no manifest.json in R2; run gen_cbse_batch.py and upload it" };
	}
	const manifest = manifestObject as unknown as Manifest;
	if (!Array.isArray(manifest.entries) || manifest.entries.length === 0) {
		return { attempted: 0, written: 0, neurons: 0, stopped: "manifest has no entries" };
	}

	const done = await doneKeys(env);
	const pending = manifest.entries.filter((e) => !done.has(e.raw.slice(4)));
	if (pending.length === 0) {
		return { attempted: 0, written: 0, neurons: 0, stopped: "everything already generated" };
	}

	let neurons = await spent(env);
	let written = 0;
	let attempted = 0;
	let stopped = "queue exhausted";

	for (const job of pending) {
		if (neurons >= NEURON_BUDGET) {
			// Stopping here is the whole reason this constant exists. The free
			// allowance is 10,000 a day; going past it is a charge.
			stopped = `daily budget reached (${neurons.toFixed(0)}/${NEURON_BUDGET} neurons)`;
			break;
		}
		attempted += 1;
		const result = await generate(env, manifest.model || "@cf/meta/llama-3.3-70b-instruct-fp8-fast", job);
		await env.BANK.put(job.raw, JSON.stringify(result), {
			httpMetadata: { contentType: "application/json" },
		});
		written += 1;
		neurons += result.neurons;
		await addSpent(env, result.neurons);
	}

	return { attempted, written, neurons, stopped };
}

export default {
	/** The nightly cron. */
	async scheduled(_event: ScheduledController, env: Env, ctx: ExecutionContext) {
		ctx.waitUntil(
			(async () => {
				const result = await runBatch(env);
				console.log(
					`qgen: ${result.written}/${result.attempted} written, ` +
					`${result.neurons.toFixed(0)} neurons, ${result.stopped}`);
			})(),
		);
	},

	/** A person, or a script, starting a run without waiting for 02:17. */
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		if (url.pathname === "/health") {
			return Response.json({
				ok: true,
				spent: await spent(env),
				budget: NEURON_BUDGET,
				day: today(),
			});
		}
		if (url.pathname === "/status") {
			const done = await doneKeys(env);
			const manifest = await getJson<Manifest>(env.BANK, "manifest.json");
			return Response.json({
				done: done.size,
				total: manifest?.entries?.length ?? 0,
				spent: await spent(env),
				budget: NEURON_BUDGET,
			});
		}
		if (url.pathname === "/run" && request.method === "POST") {
			const refused = refuseUnlessAuthorised(request, env.RUN_TOKEN);
			if (refused) return refused;
			const result = await runBatch(env);
			return Response.json(result);
		}

		/**
		 * One call, any model, result returned raw.
		 *
		 * This exists because of a measurement problem, not for convenience. An
		 * API token pulled out of ~/.wrangler works for about an hour and then
		 * 401s, and a token typed into an env var has to be pasted around and
		 * expires anyway. The binding does not expire, so a probe through it is
		 * the only way to keep comparing models without asking anyone to keep
		 * minting credentials. It is also how the JSON-mode model list gets
		 * checked: Workers AI lists nine models as supporting `response_format`,
		 * and whether a given one honours a schema is worth measuring rather than
		 * reading off a doc page.
		 */
		if (url.pathname === "/probe" && request.method === "POST") {
			const refused = refuseUnlessAuthorised(request, env.RUN_TOKEN);
			if (refused) return refused;
			if (await spent(env) >= NEURON_BUDGET) {
				return Response.json({ error: "today's budget is spent; it resets at 00:00 UTC" },
					{ status: 429 });
			}
			let body: {
				model?: string;
				system?: string;
				user?: string;
				schema?: unknown;
			};
			try {
				body = (await request.json()) as typeof body;
			} catch {
				return Response.json({ error: "body is not JSON" }, { status: 400 });
			}
			if (!body?.model || !body?.user) {
				return Response.json(
					{ error: "model and user are required" }, { status: 400 });
			}
			const started = Date.now();
			try {
				const response = (await env.AI.run(body.model as never, {
					messages: [
						{ role: "system", content: body.system ?? "" },
						{ role: "user", content: body.user },
					],
					response_format: body.schema
						? ({ type: "json_schema", json_schema: body.schema } as never)
						: undefined,
					temperature: 0.4,
					max_tokens: 2500,
				} as never)) as unknown as {
					response?: unknown;
					usage?: { neurons?: number; prompt_tokens?: number;
						completion_tokens?: number };
					choices?: { finish_reason?: string }[];
				};
				return Response.json({
					ok: true,
					model: body.model,
					routed: (response as unknown as { model?: string }).model,
					neurons: response.usage?.neurons,
					prompt_tokens: response.usage?.prompt_tokens,
					completion_tokens: response.usage?.completion_tokens,
					finish: response.choices?.[0]?.finish_reason,
					ms: Date.now() - started,
					response: response.response,
				});
			} catch (error) {
				// A model that cannot be loaded, or does not accept
				// `response_format`, throws here. That answer is the point of the
				// probe, so it is reported rather than swallowed.
				return Response.json({
					ok: false,
					model: body.model,
					error: String(error).slice(0, 400),
					ms: Date.now() - started,
				}, { status: 200 });
			}
		}

		return new Response("academicos-qgen: /health /status /run (POST) /probe (POST)",
			{ status: 404 });
	},
};
