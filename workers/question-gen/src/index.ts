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
	/** Sarvam subscription key. Absent means the worker stays on Workers AI. */
	SARVAM_API_KEY?: string;
}

/** Under the 10,000/day free allowance, with headroom for a second call. */
const NEURON_BUDGET = 9000;
const KEY_DAY = "neurons:day";
const KEY_DAY_STAMP = "day";

/**
 * Sarvam spend, in rupees, tracked separately from the neuron ledger.
 *
 * The two cannot share a counter: neurons are a Cloudflare free-tier unit, and
 * Sarvam bills real money per token. A run has to be able to stop on whichever
 * limit it is closer to without confusing the two.
 */
const SARVAM_ENDPOINT = "https://api.sarvam.ai/v1/chat/completions";
/** Published 105B rates, rupees per million tokens. */
const SARVAM_IN_RUPEES_PER_M = 29.28;
const SARVAM_OUT_RUPEES_PER_M = 73.2;
const SARVAM_RUPEE_BUDGET = 50;
const KEY_SARVAM_STAMP = "sarvam:day";
const KEY_SARVAM_SPEND = "sarvam:rupees";
const KEY_FAIL = "fail:count";
const KEY_FAIL_STAMP = "fail:day";

/**
 * 105B is a reasoning model: it emits `reasoning_content` first and the answer
 * afterwards, and both come out of `max_tokens`. Measured on this prompt shape,
 * 120 tokens returned an empty `content` -- the budget was entirely consumed by
 * reasoning. 1500 worked. This leaves room for a reasoning pass on a real
 * section and a schema-sized answer after it.
 */
const SARVAM_MAX_TOKENS = 6000;

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
	model?: string;
	/** Which generator to use. Defaults to Sarvam when its key is present. */
	provider?: "sarvam" | "workersai";
	markBudget: number;
	entries: Job[];
	chapters: unknown[];
}

const SARVAM_DEFAULT_MODEL = "sarvam-105b";
const WORKERSAI_DEFAULT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";

/**
 * Resolve the model name for one provider, ignoring a name meant for the other.
 *
 * `manifest.model` is a single field but the two providers are separate services
 * with separate catalogues, and every Workers AI model is namespaced `@cf/...`.
 * Passing a manifest that names `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
 * straight through to Sarvam's endpoint yields a 404 for an unknown model, so the
 * name is accepted only when it actually belongs to the provider being called.
 */
function modelFor(provider: "sarvam" | "workersai", manifest: Manifest): string {
	const named = manifest.model?.trim();
	if (!named) return provider === "sarvam" ? SARVAM_DEFAULT_MODEL : WORKERSAI_DEFAULT_MODEL;
	const isWorkersAi = named.startsWith("@cf/");
	if (provider === "workersai") return isWorkersAi ? named : WORKERSAI_DEFAULT_MODEL;
	return isWorkersAi ? SARVAM_DEFAULT_MODEL : named;
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
	/** Present only on the Sarvam path, so token cost survives to the ledger. */
	sarvam?: { prompt_tokens: number; completion_tokens: number; rupees: number };
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

/** Rupees already spent on Sarvam today. Zero across a day boundary. */
async function sarvamSpent(env: Env): Promise<number> {
	const stamp = await env.STATE.get(KEY_SARVAM_STAMP);
	if (stamp !== today()) return 0;
	return Number((await env.STATE.get(KEY_SARVAM_SPEND)) || 0);
}

async function addSarvamSpent(env: Env, rupees: number): Promise<void> {
	const stamp = await env.STATE.get(KEY_SARVAM_STAMP);
	if (stamp !== today()) {
		await env.STATE.put(KEY_SARVAM_STAMP, today());
		await env.STATE.put(KEY_SARVAM_SPEND, String(rupees));
		return;
	}
	const now = Number((await env.STATE.get(KEY_SARVAM_SPEND)) || 0);
	await env.STATE.put(KEY_SARVAM_SPEND, String(now + rupees));
}

/**
 * Failures counted at write time rather than derived from R2 on read.
 *
 * A status endpoint that fetched every stored result to recount failures would
 * cost one R2 GET per generated section on every call, which is the wrong trade
 * for a number that only ever moves when a run happens.
 */
async function failedCount(env: Env, provider: string): Promise<number> {
	const stamp = await env.STATE.get(`${KEY_FAIL_STAMP}:${provider}`);
	if (stamp !== today()) return 0;
	return Number((await env.STATE.get(`${KEY_FAIL}:${provider}`)) || 0);
}

async function addFailed(env: Env, provider: string): Promise<void> {
	const stampKey = `${KEY_FAIL_STAMP}:${provider}`;
	const stamp = await env.STATE.get(stampKey);
	if (stamp !== today()) {
		await env.STATE.put(stampKey, today());
		await env.STATE.put(`${KEY_FAIL}:${provider}`, "1");
		return;
	}
	const now = Number((await env.STATE.get(`${KEY_FAIL}:${provider}`)) || 0);
	await env.STATE.put(`${KEY_FAIL}:${provider}`, String(now + 1));
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
	const base = baseResult(job, model);
	const payload = await readPrompt(env, job, base);
	if (!payload) return base;

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

/**
 * Read a JSON object out of a chat completion.
 *
 * In `json_object` mode the answer is usually bare JSON, but a reasoning model
 * can still fence it. Tolerant of the three shapes that actually show up --
 * bare, ```json fenced, and a fenced block followed by prose -- because a
 * parse failure here would be indistinguishable from a bad question.
 */
function parseJsonContent(content: string): { ok: true; value: unknown } | { ok: false; error: string } {
	let text = content.trim();
	const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
	if (fence) text = fence[1].trim();
	const first = text.indexOf("{");
	const last = text.lastIndexOf("}");
	if (first === -1 || last <= first) {
		return { ok: false, error: `no JSON object in content: ${content.slice(0, 160)}` };
	}
	try {
		return { ok: true, value: JSON.parse(text.slice(first, last + 1)) };
	} catch (error) {
		return { ok: false, error: `content is not JSON: ${String(error).slice(0, 160)}` };
	}
}

/**
 * Check the answer against the blueprint's own schema.
 *
 * Workers AI enforces the schema server-side, so a one-mark question cannot come
 * back as three marks. Sarvam 105B rejects `json_schema` outright -- a request
 * carrying one returns 400, while `json_object` is accepted -- so with Sarvam
 * that guarantee has to be made here or not at all. The checks that matter are
 * the ones the format is built to catch: every required key present, and the
 * marks and question type agreeing with the section that was asked for.
 */
function validateAgainstSchema(
	value: unknown,
	schema: { required?: string[]; properties?: Record<string, { type?: string }> },
	job: Job,
): string | null {
	if (!value || typeof value !== "object" || Array.isArray(value)) {
		return "answer is not a JSON object";
	}
	const record = value as Record<string, unknown>;
	for (const key of schema.required ?? []) {
		if (!(key in record)) return `required key missing: ${key}`;
	}
	for (const [key, spec] of Object.entries(schema.properties ?? {})) {
		if (!(key in record) || spec.type === undefined) continue;
		const value = record[key];
		const actual = Array.isArray(value) ? "array" : typeof value;
		// JSON Schema distinguishes `integer` from `number`, but a JSON document
		// has only one numeric type: `marks: 1` arrives as a number and `typeof`
		// cannot tell it apart from 1.5. Requiring `"number" === "integer"` here
		// rejected every well-formed answer, so the integer check is done on the
		// value instead.
		if (spec.type === "integer") {
			if (typeof value !== "number" || !Number.isInteger(value)) {
				return `key "${key}" is ${actual}, schema wants integer`;
			}
			continue;
		}
		if (actual !== spec.type) {
			return `key "${key}" is ${actual}, schema wants ${spec.type}`;
		}
	}
	if ("marks" in record && record.marks !== job.marks) {
		return `marks is ${JSON.stringify(record.marks)}, section asked for ${job.marks}`;
	}
	if ("qtype" in record && typeof record.qtype === "string" && record.qtype !== job.qtype) {
		return `qtype is "${record.qtype}", section asked for "${job.qtype}"`;
	}
	return null;
}

function baseResult(job: Job, model: string): RawResult {
	return {
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
}

interface PromptPayload {
	system?: string;
	user?: string;
	schema?: unknown;
}

async function readPrompt(
	env: Env,
	job: Job,
	base: RawResult,
): Promise<PromptPayload | null> {
	const stored = await getJson<PromptPayload>(env.BANK, job.key);
	if (!stored) {
		base.schemaError = "prompt object missing from R2";
		return null;
	}
	if (!stored.system || !stored.user) {
		base.schemaError = "prompt object has no system/user";
		return null;
	}
	return stored;
}

/**
 * One generation call against Sarvam 105B.
 *
 * The schema is appended to the user turn as text rather than sent as
 * `json_schema`, because the API 400s on the latter. The result is stored the
 * same way the Workers AI path stores it -- raw, with any failure preserved --
 * so the Python validator downstream cannot tell the two providers apart, and
 * so a schema miss shows up as a described failure rather than a silent gap.
 */
async function generateSarvam(env: Env, job: Job, model: string): Promise<RawResult> {
	const base = baseResult(job, model);
	const payload = await readPrompt(env, job, base);
	if (!payload) return base;

	const schema = payload.schema as { required?: string[]; properties?: Record<string, { type?: string }> } | undefined;
	const schemaText = schema ? `\n\nReturn a single JSON object matching this schema exactly. No prose, no markdown fences.\n${JSON.stringify(schema)}` : "";
	const user = `${payload.user}${schemaText}`;

	try {
		const response = await fetch(SARVAM_ENDPOINT, {
			method: "POST",
			headers: {
				"api-subscription-key": env.SARVAM_API_KEY as string,
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				model,
				messages: [
					{ role: "system", content: payload.system },
					{ role: "user", content: user },
				],
				response_format: { type: "json_object" },
				temperature: 0.4,
				max_tokens: SARVAM_MAX_TOKENS,
			}),
		});

		if (!response.ok) {
			const detail = (await response.text()).slice(0, 200);
			base.schemaError = `sarvam HTTP ${response.status}: ${detail || "(empty body)"}`;
			return base;
		}

		const body = (await response.json()) as {
			choices?: {
				finish_reason?: string;
				message?: { content?: string; reasoning_content?: string };
			}[];
			usage?: { prompt_tokens?: number; completion_tokens?: number };
		};
		const choice = body.choices?.[0];
		base.finish = choice?.finish_reason;
		const promptTokens = body.usage?.prompt_tokens ?? 0;
		const completionTokens = body.usage?.completion_tokens ?? 0;
		const rupees =
			(promptTokens / 1e6) * SARVAM_IN_RUPEES_PER_M +
			(completionTokens / 1e6) * SARVAM_OUT_RUPEES_PER_M;
		base.sarvam = { prompt_tokens: promptTokens, completion_tokens: completionTokens, rupees };

		// An empty `content` with a `stop` finish is the reasoning model spending
		// the whole token budget before it starts answering. It is a real and
		// common failure, so it is named rather than stored as an empty answer.
		const content = (choice?.message?.content ?? "").trim();
		if (!content) {
			base.schemaError = choice?.message?.reasoning_content
				? "empty content: reasoning consumed max_tokens before answering"
				: "empty content from sarvam";
			return base;
		}

		const parsed = parseJsonContent(content);
		if (!parsed.ok) {
			base.schemaError = parsed.error;
			return base;
		}
		base.raw = parsed.value;
		if (schema) {
			const problem = validateAgainstSchema(parsed.value, schema, job);
			if (problem) {
				base.schemaError = `schema: ${problem}`;
				return base;
			}
		}
		base.ok = true;
	} catch (error) {
		base.schemaError = `sarvam call failed: ${String(error).slice(0, 200)}`;
	}
	return base;
}

async function runBatch(env: Env): Promise<{
	attempted: number;
	written: number;
	neurons: number;
	rupees: number;
	provider: string;
	model: string;
	stopped: string;
}> {
	const manifestObject = await getJson<Manifest>(env.BANK, "manifest.json");
	if (!manifestObject) {
		return { attempted: 0, written: 0, neurons: 0, rupees: 0, provider: "none",
			model: "-", stopped: "no manifest.json in R2; run gen_cbse_batch.py and upload it" };
	}
	const manifest = manifestObject as unknown as Manifest;
	if (!Array.isArray(manifest.entries) || manifest.entries.length === 0) {
		return { attempted: 0, written: 0, neurons: 0, rupees: 0, provider: "none",
			model: "-", stopped: "manifest has no entries" };
	}

	/**
	 * Sarvam is the default because the Gemini path is quota-blocked and 105B is
	 * the model that can actually read and write the Indic chapters. It still
	 * needs a subscription key, so an unset secret falls back to Workers AI
	 * rather than failing the whole run.
	 */
	const provider =
		manifest.provider === "workersai" || !env.SARVAM_API_KEY ? "workersai" : "sarvam";
	const model = modelFor(provider, manifest);

	const done = await doneKeys(env);
	const pending = manifest.entries.filter((e) => !done.has(e.raw.slice(4)));
	if (pending.length === 0) {
		return { attempted: 0, written: 0, neurons: 0, rupees: 0, provider, model,
			stopped: "everything already generated" };
	}

	let neurons = await spent(env);
	let rupees = await sarvamSpent(env);
	let written = 0;
	let attempted = 0;
	let stopped = "queue exhausted";

	for (const job of pending) {
		if (provider === "workersai" && neurons >= NEURON_BUDGET) {
			// Stopping here is the whole reason this constant exists. The free
			// allowance is 10,000 a day; going past it is a charge.
			stopped = `daily budget reached (${neurons.toFixed(0)}/${NEURON_BUDGET} neurons)`;
			break;
		}
		if (provider === "sarvam" && rupees >= SARVAM_RUPEE_BUDGET) {
			// Sarvam bills money, so it gets the same hard stop the neuron budget
			// exists to provide -- checked before the call, not after.
			stopped = `daily rupee budget reached (Rs ${rupees.toFixed(2)}/${SARVAM_RUPEE_BUDGET})`;
			break;
		}
		attempted += 1;
		if (provider === "sarvam") {
			const result = await generateSarvam(env, job, model);
			await env.BANK.put(job.raw, JSON.stringify(result), {
				httpMetadata: { contentType: "application/json" },
			});
			written += 1;
			if (result.sarvam) {
				rupees += result.sarvam.rupees;
				await addSarvamSpent(env, result.sarvam.rupees);
			}
			if (!result.ok) await addFailed(env, "sarvam");
		} else {
			const result = await generate(env, model, job);
			await env.BANK.put(job.raw, JSON.stringify(result), {
				httpMetadata: { contentType: "application/json" },
			});
			written += 1;
			neurons += result.neurons;
			await addSpent(env, result.neurons);
			if (!result.ok) await addFailed(env, "workersai");
		}
	}

	return { attempted, written, neurons, rupees, provider, model, stopped };
}

export default {
	/** The nightly cron. */
	async scheduled(_event: ScheduledController, env: Env, ctx: ExecutionContext) {
		ctx.waitUntil(
			(async () => {
				const result = await runBatch(env);
				console.log(
					`qgen[${result.provider}/${result.model}]: ` +
					`${result.written}/${result.attempted} written, ` +
					`${result.neurons.toFixed(0)} neurons, Rs ${result.rupees.toFixed(3)}, ` +
					`${result.stopped}`);
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
				rupees: await sarvamSpent(env),
				rupee_budget: SARVAM_RUPEE_BUDGET,
				sarvam_configured: Boolean(env.SARVAM_API_KEY),
				day: today(),
			});
		}
		if (url.pathname === "/status") {
			const done = await doneKeys(env);
			const manifest = await getJson<Manifest>(env.BANK, "manifest.json");
			// Resolve the provider the same way `runBatch` does, otherwise /status
			// can advertise Sarvam while the run silently uses Workers AI (or the
			// reverse), which is exactly the disagreement worth catching here.
			const activeProvider =
				manifest?.provider === "workersai" || !env.SARVAM_API_KEY
					? "workersai"
					: "sarvam";
			const failed = await failedCount(env, activeProvider);
			return Response.json({
				// Counted against the current manifest, not across all of `raw/`.
				// The bucket also holds objects from earlier batches, so a raw
				// object count can exceed the manifest and read as 266/192 --
				// progress that does not correspond to this run's work.
				done: manifest
					? manifest.entries.filter((e) => done.has(e.raw.slice(4))).length
					: 0,
				total: manifest?.entries?.length ?? 0,
				raw_objects: done.size,
				failed,
				provider: activeProvider,
				model: manifest ? modelFor(activeProvider, manifest) : "-",
				manifest_model: manifest?.model ?? null,
				spent: await spent(env),
				budget: NEURON_BUDGET,
				rupees: await sarvamSpent(env),
				rupee_budget: SARVAM_RUPEE_BUDGET,
			});
		}
		if (url.pathname === "/run" && request.method === "POST") {
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

		/**
		 * The Sarvam counterpart to /probe.
		 *
		 * `/probe` measures Workers AI models, but the question now is whether
		 * 105B, reached from the Worker, honours the pieces the run depends on:
		 * JSON mode, a parseable answer, and a schema it can be checked against.
		 * Each of those has already failed or behaved differently once, so the
		 * probe reports them separately instead of collapsing to ok/fail. With a
		 * `job` key it runs the real `generateSarvam` against a stored prompt;
		 * without one it uses a built-in prompt and the same code path minus R2.
		 */
		if (url.pathname === "/probe-sarvam" && request.method === "POST") {
			if (!env.SARVAM_API_KEY) {
				return Response.json({ ok: false, error: "SARVAM_API_KEY secret not set" },
					{ status: 400 });
			}
			let body: { model?: string; job?: string };
			try {
				body = (await request.json()) as typeof body;
			} catch {
				body = {};
			}
			const model = body.model || SARVAM_DEFAULT_MODEL;
			const started = Date.now();

			if (body.job) {
				const manifestObject = await getJson<Manifest>(env.BANK, "manifest.json");
				const job = manifestObject?.entries?.find((e) => e.key === body.job);
				if (!job) {
					return Response.json({ ok: false, error: `no manifest entry with key ${body.job}` },
						{ status: 404 });
				}
				const result = await generateSarvam(env, job, model);
				if (result.sarvam) await addSarvamSpent(env, result.sarvam.rupees);
				return Response.json({ ...result, ms: Date.now() - started });
			}

			const smokeSchema = {
				type: "object",
				properties: { question: { type: "string" }, marks: { type: "integer" } },
				required: ["question", "marks"],
			};
			const smokeJob: Job = {
				key: "smoke-1.json", raw: "raw/smoke-1.json", code: "smoke", chapter: 1,
				sectionKey: "smoke", qtype: "short", marks: 1,
			};
			try {
				const response = await fetch(SARVAM_ENDPOINT, {
					method: "POST",
					headers: {
						"api-subscription-key": env.SARVAM_API_KEY as string,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						model,
						messages: [
							{ role: "system", content: "You write CBSE exam questions. Answer in JSON only." },
							{
								role: "user",
								content:
									"Write one 1-mark question about photosynthesis. " +
									`Return a single JSON object matching this schema exactly. No prose, no markdown fences.\n${JSON.stringify(smokeSchema)}`,
							},
						],
						response_format: { type: "json_object" },
						temperature: 0.4,
						max_tokens: SARVAM_MAX_TOKENS,
					}),
				});
				if (!response.ok) {
					return Response.json({
						ok: false, model, status: response.status,
						error: (await response.text()).slice(0, 300), ms: Date.now() - started,
					}, { status: 200 });
				}
				const payloadJson = (await response.json()) as {
					choices?: { finish_reason?: string; message?: { content?: string; reasoning_content?: string } }[];
					usage?: { prompt_tokens?: number; completion_tokens?: number };
				};
				const content = (payloadJson.choices?.[0]?.message?.content ?? "").trim();
				const parsed = parseJsonContent(content);
				const promptTokens = payloadJson.usage?.prompt_tokens ?? 0;
				const completionTokens = payloadJson.usage?.completion_tokens ?? 0;
				return Response.json({
					ok: parsed.ok && !validateAgainstSchema(
						parsed.ok ? parsed.value : null, smokeSchema, smokeJob),
					model,
					finish: payloadJson.choices?.[0]?.finish_reason,
					parsed: parsed.ok,
					schema_problem: parsed.ok
						? validateAgainstSchema(parsed.value, smokeSchema, smokeJob)
						: parsed.error,
					answer: parsed.ok ? parsed.value : content.slice(0, 300),
					reasoning_chars: (payloadJson.choices?.[0]?.message?.reasoning_content ?? "").length,
					prompt_tokens: promptTokens,
					completion_tokens: completionTokens,
					rupees:
						(promptTokens / 1e6) * SARVAM_IN_RUPEES_PER_M +
						(completionTokens / 1e6) * SARVAM_OUT_RUPEES_PER_M,
					ms: Date.now() - started,
				});
			} catch (error) {
				return Response.json({ ok: false, model, error: String(error).slice(0, 400),
					ms: Date.now() - started }, { status: 200 });
			}
		}

		return new Response(
			"academicos-qgen: /health /status /run (POST) /probe (POST) /probe-sarvam (POST)",
			{ status: 404 });
	},
};
