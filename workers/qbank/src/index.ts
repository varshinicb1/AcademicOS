/**
 * A question bank that answers a request instead of filling a quota.
 *
 * The batch pipeline this replaces generated every chapter in advance, which meant
 * rationing a daily neuron allowance and shipping a bank full of questions nobody
 * had asked for. Here nothing is generated until a teacher asks: they pick a book,
 * a chapter, then the topics -- and the topics are read out of the chapter on the
 * spot -- and only that paper costs anything.
 *
 * Three rules shaped it.
 *
 * The format is data, not prose. `blueprint.json` in the bucket is exported from
 * `cbse_blueprint.py`, so the sections, marks and answer lengths the Worker enforces
 * are the same numbers the Python tests assert. The Worker cannot drift from the
 * format, because it does not hold a copy of it.
 *
 * Nothing generated here is trusted. Every question comes back through the same
 * checks the offline validator applies -- marks match the section, options are
 * answerable, distractors are not an arithmetic ladder, the stem is a question and
 * does not name its own source, and a "show that" stem whose answer denies the
 * claim is refused. Those refusals are returned to the caller with a reason, not
 * silently dropped, because a teacher who is told "that chapter will not support a
 * case study" can act on it and a teacher who silently gets fewer questions cannot.
 *
 * The existing bank is consulted before anything is written, so a generated
 * question is never one the school already has.
 */

export interface Env {
	AI: Ai;
	BANK: R2Bucket;
	STATE: KVNamespace;
	/** A Google AI Studio key. Present means Gemini is used; absent falls back to
	 *  the free Workers AI binding, so the Worker still answers with no key. */
	GEMINI_API_KEY?: string;
	/** Bearer token for the model routes and /api/papers (`wrangler secret put
	 *  QBANK_TOKEN`). Unset means those routes refuse. */
	QBANK_TOKEN?: string;
	/** Hard daily ceiling on paid (Gemini) spend, in US dollars. Default 2. */
	DAILY_USD_CAP?: string;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

/** Daily ceiling. Over this, requests are refused with a reason rather than billed. */
const NEURON_BUDGET = 9000;

/** The most questions one request may ask for: one request is one bounded spend. */
const MAX_COUNT = 20;

/** The paid path's daily stop when DAILY_USD_CAP is not set. */
const DEFAULT_USD_CAP = 2;

function usdCap(env: Env): number {
	const cap = Number(env.DAILY_USD_CAP);
	return Number.isFinite(cap) && cap > 0 ? cap : DEFAULT_USD_CAP;
}

/** Over today's allowance: the free one without a key, the dollar cap with one. */
async function overBudget(env: Env): Promise<Response | null> {
	if (env.GEMINI_API_KEY) {
		const usd = await spentUsd(env);
		if (usd >= usdCap(env)) {
			return Response.json({
				error: `today's spending cap of $${usdCap(env)} is reached; it resets at 00:00 UTC`,
				spentUsd: usd, capUsd: usdCap(env),
			}, { status: 429, ...JSON_HEADERS });
		}
		return null;
	}
	const already = await spent(env);
	if (already >= NEURON_BUDGET) {
		return Response.json({
			error: "today's free allowance is spent; it resets at 00:00 UTC",
			spent: already, budget: NEURON_BUDGET,
		}, { status: 429, ...JSON_HEADERS });
	}
	return null;
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

const STOPWORDS = new Set([
	"the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was", "were",
	"be", "been", "for", "with", "from", "by", "on", "at", "as", "that", "this",
	"these", "those", "it", "its", "his", "her", "their", "our", "your", "what",
	"which", "who", "find", "state", "write", "show", "prove", "given", "also",
	"into", "than", "then", "when", "where", "how", "why",
]);

interface Section {
	key: string; name: string; qtype: string; count: number; marks: number;
	answerWords: number | null; internalChoice: number; carriesSource: boolean;
}
interface Blueprint {
	subject: string; gradeBand: string; theoryMarks: number;
	durationMinutes: number; notes: string; sections: Section[];
}
interface BookMeta {
	code: string;
	book: { code: string; class: number; subject: string; title: string; language: string };
	chapters: string[];
}

// --------------------------------------------------------------------------- //
// R2 / KV helpers
// --------------------------------------------------------------------------- //

async function getJson<T>(bucket: R2Bucket, key: string): Promise<T | null> {
	const object = await bucket.get(key);
	if (!object) return null;
	try {
		return (await object.json()) as T;
	} catch {
		return null;
	}
}

async function putJson(bucket: R2Bucket, key: string, value: unknown): Promise<void> {
	await bucket.put(key, JSON.stringify(value), {
		httpMetadata: { contentType: "application/json" },
	});
}

function tokens(text: string): Set<string> {
	const cleaned = (text || "")
		.toLowerCase()
		.replace(/[^\p{L}\p{N}\s]/gu, " ")
		.split(/\s+/);
	const out = new Set<string>();
	for (let word of cleaned) {
		if (word.length <= 2 || STOPWORDS.has(word)) continue;
		// Crude singularisation, so "primes" and "prime" are the same word. A
		// restatement check that misses on a plural is not a restatement check.
		if (word.length > 4 && word.endsWith("s") && !word.endsWith("ss")) {
			word = word.slice(0, -1);
		}
		out.add(word);
	}
	return out;
}

function jaccard(a: Set<string>, b: Set<string>): number {
	if (!a.size || !b.size) return 0;
	let shared = 0;
	const [small, large] = a.size <= b.size ? [a, b] : [b, a];
	for (const word of small) if (large.has(word)) shared += 1;
	const union = a.size + b.size - shared;
	return union ? shared / union : 0;
}

async function spent(env: Env): Promise<number> {
	const day = new Date().toISOString().slice(0, 10);
	if ((await env.STATE.get("day")) !== day) return 0;
	return amount(await env.STATE.get("neurons"));
}

/** A ledger value, or 0 for one that is missing or not a number. generate() once
 *  recorded `undefined` dollars, which made the day's total NaN; a NaN total
 *  compares false against any cap, so the cap never fired. */
function amount(value: unknown): number {
	const n = Number(value);
	return Number.isFinite(n) ? n : 0;
}

async function addSpent(env: Env, neurons: number, usd: number): Promise<void> {
	neurons = amount(neurons);
	usd = amount(usd);
	const day = new Date().toISOString().slice(0, 10);
	if ((await env.STATE.get("day")) !== day) {
		await env.STATE.put("day", day);
		await env.STATE.put("neurons", String(neurons));
		await env.STATE.put("usd", String(usd));
		return;
	}
	// Two ledgers, because the two providers charge in different units and adding a
	// neuron to a dollar would be a number that means nothing.
	await env.STATE.put("neurons",
		String(amount(await env.STATE.get("neurons")) + neurons));
	await env.STATE.put("usd",
		String(amount(await env.STATE.get("usd")) + usd));
}

async function spentUsd(env: Env): Promise<number> {
	if ((await env.STATE.get("day")) !== new Date().toISOString().slice(0, 10)) return 0;
	return amount(await env.STATE.get("usd"));
}

// --------------------------------------------------------------------------- //
// text
// --------------------------------------------------------------------------- //

/**
 * The chapter as the book printed it, one line per entry with its page.
 *
 * The page markers matter: a generated question records the page it came from, and
 * a teacher checking it opens the book at that page. Without them every question
 * would say "from the chapter", which is worth nothing when someone is deciding
 * whether to trust it.
 */
function chapterLines(text: string): Array<[number, string]> {
	const out: Array<[number, string]> = [];
	let page = 1;
	for (const raw of (text || "").split(/\r?\n/)) {
		const line = raw.trim();
		if (!line) continue;
		const marker = /^\[page (\d+)\]$/.exec(line);
		if (marker) {
			page = Number(marker[1]);
			continue;
		}
		out.push([page, line]);
	}
	return out;
}

/** The window of the chapter around a topic's heading, for a question about it. */
function topicWindow(lines: Array<[number, string]>, topics: string[], index: number,
	window = 110): string {
	if (!topics.length) return lines.slice(0, window).map(([, l]) => l).join("\n");
	const needle = (topics[index] || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").trim();
	let start = -1;
	if (needle) {
		for (let i = 0; i < lines.length; i += 1) {
			const hay = lines[i][1].toLowerCase();
			if (hay.includes(needle)) { start = i; break; }
		}
	}
	if (start < 0) start = 0;
	// Up to the next heading, so a question is set from its own material.
	let end = lines.length;
	for (let j = index + 1; j < topics.length; j += 1) {
		const next = (topics[j] || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").trim();
		for (let i = start + 1; i < lines.length; i += 1) {
			if (next && lines[i][1].toLowerCase().includes(next)) { end = i; break; }
		}
		if (end < lines.length) break;
	}
	const slice = lines.slice(start, Math.min(end, start + window));
	return (slice.length >= 25 ? slice : lines.slice(0, window)).map(([, l]) => l).join("\n");
}

// --------------------------------------------------------------------------- //
// the model
// --------------------------------------------------------------------------- //

const MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";

/**
 * Paid models, and which section each is for.
 *
 * The free tier is genuinely free and genuinely good at one thing: long answers.
 * Asked to prove sqrt(5) irrational it returned a correct proof by contradiction.
 * Asked to factorise 32760 it returned "expression as a product of primes" as the
 * model answer -- the question, rephrased -- and the run ended up refusing half
 * its own output.
 *
 * So the paid model takes the whole job, and the split inside it is by measured
 * quality, not by price. `flash` proved it can set a case-based passage the free
 * model never once managed in four attempts, so the written and case sections are
 * not negotiable. The objective run is where the cheap model is tried first and
 * the answer is checked; if `flash-lite` cannot hold the format or the quality, the
 * route does not use it.
 *
 * Published rates, USD per million tokens: flash 0.30 in / 2.50 out, lite
 * 0.10 / 0.40. Cached input is 0.03.
 */
const GEMINI_FLASH = "gemini-2.5-flash";
const GEMINI_LITE = "gemini-2.5-flash-lite";

/** Sections whose whole output is four options and a letter. */
const OBJECTIVE_TYPES = new Set(["mcq", "assertion_reason", "map_based"]);

/**
 * Which model sets a section.
 *
 * `lite` is off by default and has to be asked for. It is 6x cheaper on output,
 * which sounds attractive, but "cheap" is worth nothing if the questions need
 * regenerating, and no benchmark has yet shown it holding the CBSE format as
 * reliably as `flash` on the objective run.
 */
function paidModelFor(section: Section, useLite: boolean): string {
	if (useLite && OBJECTIVE_TYPES.has(section.qtype)) return GEMINI_LITE;
	return GEMINI_FLASH;
}

interface AiRun { response?: unknown; usage?: { neurons?: number };
	choices?: { finish_reason?: string }[] }

/**
 * One generation call, on whichever provider the request asked for.
 *
 * The two speak different dialects. Workers AI takes the schema under
 * `response_format` and hands the object back already parsed. Gemini takes it under
 * `generationConfig.responseSchema` and hands back a JSON *string* in
 * `candidates[0].content.parts[0].text` that has to be parsed here. It also
 * rejects `const`, rejects an `enum` on a number, and rejects `minItems` -- which is
 * why `_schema` in the Python side uses string enums and no length keywords. That
 * intersection is the price of being able to switch providers at all, and it is
 * worth paying: a language model asked to follow a format in prose will report that
 * it did whether or not it did, so the schema is the only part of this that is not
 * negotiable.
 *
 * Cost is recorded per provider and in the unit that provider charges, because
 * "today's spend" means neurons on one and dollars on the other and adding them
 * would be meaningless.
 */
async function ask(env: Env, system: string, user: string, schema: unknown,
	section: Section | null, opts: { maxTokens?: number; lite?: boolean } = {}):
	Promise<{ data: unknown; neurons: number; usd: number; model: string; error?: string; fellBack?: boolean }> {
	if (env.GEMINI_API_KEY) {
		const paid = await askGemini(env, system, user, schema,
			section ? paidModelFor(section, Boolean(opts.lite)) : GEMINI_FLASH,
			opts.maxTokens ?? 2000);
		if (!paid.error) return paid;
		// Fall back rather than fail. A key on Gemini's free tier carries a quota
		// that runs out, and a key with billing off returns 429 for every call --
		// so a Worker that hard-depends on it returns nothing at all once that
		// happens, which is the opposite of what a request path should do. The
		// free binding always works, so the question still gets set, and the
		// response says which model answered so the quality difference is visible
		// rather than silent.
		if (/429|quota|RESOURCE_EXHAUSTED/i.test(paid.error)) {
			const free = await askWorkers(env, system, user, schema,
				opts.maxTokens ?? 2000);
			return { ...free, model: `${MODEL} (fallback: ${paid.model} ${paid.error.slice(0, 60)})`,
				fellBack: true };
		}
		return paid;
	}
	const free = await askWorkers(env, system, user, schema, opts.maxTokens ?? 2000);
	return { ...free, model: MODEL };
}

async function askWorkers(env: Env, system: string, user: string, schema: unknown,
	maxTokens: number):
	Promise<{ data: unknown; neurons: number; usd: number; model: string; error?: string }> {
	try {
		const result = (await env.AI.run(MODEL as never, {
			messages: [
				{ role: "system", content: system },
				{ role: "user", content: user },
			],
			response_format: { type: "json_schema", json_schema: schema as never },
			temperature: 0.35,
			max_tokens: maxTokens,
		} as never)) as unknown as AiRun;
		const response = result.response;
		if (response && typeof response === "object" && "error" in (response as object)) {
			return { data: null, neurons: result.usage?.neurons ?? 0, usd: 0, model: MODEL,
				error: String((response as Record<string, unknown>).error) };
		}
		return { data: response, neurons: result.usage?.neurons ?? 0, usd: 0, model: MODEL };
	} catch (error) {
		return { data: null, neurons: 0, usd: 0, model: MODEL,
			error: String(error).slice(0, 200) };
	}
}

const GEMINI_RATE: Record<string, { in: number; out: number; cached: number }> = {
	[GEMINI_FLASH]: { in: 0.30, out: 2.50, cached: 0.03 },
	[GEMINI_LITE]: { in: 0.10, out: 0.40, cached: 0.03 },
};
const _RETRY_IN = /retry in\s+([0-9.]+)\s*s/i;

async function askGemini(env: Env, system: string, user: string, schema: unknown,
	model: string, maxTokens: number):
	Promise<{ data: unknown; neurons: number; usd: number; model: string; error?: string }> {
	const rate = GEMINI_RATE[model] || GEMINI_RATE[GEMINI_FLASH];
	const body = {
		// The chapter text is the stable prefix, so it is sent first and cached
		// across the sections of one chapter. Cached input is a tenth of fresh.
		contents: [
			{ parts: [{ text: user }] },
			{ parts: [{ text: system }] },
		],
		generationConfig: {
			temperature: 0.35,
			maxOutputTokens: maxTokens,
			responseMimeType: "application/json",
			responseSchema: schema,
		},
	};
	const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}`
		+ `:generateContent?key=${env.GEMINI_API_KEY}`;

	let last = "unknown";
	for (let attempt = 0; attempt < 2; attempt += 1) {
		try {
			const response = await fetch(url, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(body),
			});
			if (!response.ok) {
				const text = await response.text();
				last = `HTTP ${response.status}: ${text.slice(0, 240)}`;
				// Gemini says how long to wait in the body. Guessing shorter spends
				// the rest of the request-per-minute window and gets another 429.
				// A *quota* message is different: no wait clears it, so stop
				// immediately and let the caller fall back rather than sit here
				// holding a request open for two minutes.
				if (/quota|RESOURCE_EXHAUSTED/i.test(text) && !_RETRY_IN.test(text)) {
					return { data: null, neurons: 0, usd: 0, model, error: last };
				}
				const hinted = _RETRY_IN.exec(text);
				await sleep(hinted ? Number(hinted[1]) + 1
					: response.status === 429 ? 20 * (attempt + 1) : 2 ** attempt * 2);
				continue;
			}
			const payload = await response.json() as {
				candidates?: { content?: { parts?: { text?: string }[] } }[];
				usageMetadata?: { promptTokenCount?: number; candidatesTokenCount?: number;
					cachedContentTokenCount?: number };
			};
			const meta = payload.usageMetadata || {};
			const prompt = meta.promptTokenCount || 0;
			const cached = meta.cachedContentTokenCount || 0;
			const completion = meta.candidatesTokenCount || 0;
			const usd = ((prompt - cached) / 1e6) * rate.in
				+ (cached / 1e6) * rate.cached
				+ (completion / 1e6) * rate.out;
			return {
				data: (payload.candidates?.[0]?.content?.parts?.[0]?.text) || null,
				neurons: 0, usd, model,
			};
		} catch (error) {
			last = `network: ${String(error).slice(0, 160)}`;
			await sleep(2 ** attempt * 2);
		}
	}
	return { data: null, neurons: 0, usd: 0, model, error: last };
}

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * The same response, always as an object.
 *
 * Workers AI returns `response` already parsed when a schema is honoured, and as
 * a JSON *string* when it is not -- and it says which in the body rather than by
 * failing. Passing the string on to the caller as if it were an object is how a
 * topic list comes back empty while the call reports success and 74 neurons spent.
 */
function asObject(data: unknown): unknown {
	if (typeof data !== "string") return data;
	try {
		return JSON.parse(data);
	} catch {
		return null;
	}
}

const TOPIC_SCHEMA = {
	type: "object",
	properties: {
		topics: {
			type: "array",
			items: {
				type: "object",
				properties: {
					title: { type: "string" },
					page: { type: "string" },
				},
				required: ["title"],
			},
		},
	},
	required: ["topics"],
};

async function extractTopics(env: Env, code: string, chapter: string,
	title: string, language: string): Promise<{ topics: string[]; cached: boolean; neurons: number; usd: number }> {
	const key = `topics/${code}-${chapter}.json`;
	const stored = await getJson<{ topics: string[] }>(env.BANK, key);
	if (stored?.topics?.length) {
		return { topics: stored.topics, cached: true, neurons: 0 };
	}
	const text = await getJson<Record<string, string>>(env.BANK, `text/${code}.json`);
	if (!text) return { topics: [], cached: false, neurons: 0, usd: 0 };
	const body = topicWindow(chapterLines(text[chapter] || ""), [], 0, 200);
	const languageName = language === "hi" ? "Hindi" : "English";
	const system = `You are reading one chapter of a CBSE ${languageName} textbook and listing the topics it is divided into. List only the headings the book itself prints, in the order it prints them. Do not invent a topic. Do not list exercises, answers, review questions, "Project Work", page furniture or the running head.`;
	const user = `Chapter: ${title}\n\n--- chapter ---\n${body}\n--- end ---\n\nList this chapter's topics.`;
	const { data, neurons, usd, error } = await ask(env, system, user, TOPIC_SCHEMA, null, { maxTokens: 1200 });
	if (error) {
		// Surfaced, not swallowed: a caller that gets an empty topic list and no
		// reason cannot tell "this chapter has no headings" from "the call failed",
		// and those need different responses from whoever is asking.
		return { topics: [], cached: false, neurons, usd, error };
	}
	const payload = asObject(data) as { topics?: { title?: string }[] } | null;
	const topics = (payload?.topics || [])
		.map((t) => (t?.title || "").trim())
		.filter(Boolean);
	if (!topics.length && data !== null && data !== undefined) {
		return { topics: [], cached: false, neurons, usd,
			error: "model returned no topics", raw: asObject(data) };
	}
	if (topics.length) await putJson(env.BANK, key, { topics, at: Date.now() });
	return { topics, cached: false, neurons, usd };
}

function questionSchema(section: Section) {
	const item: Record<string, unknown> = {
		type: "object",
		properties: {
			// String enums on purpose: Workers AI and Gemini accept only this form of
			// a single-value constraint, and a wrong mark value must fail to parse
			// rather than be produced and caught.
			qtype: { type: "string", enum: [section.qtype] },
			marks: { type: "string", enum: [String(section.marks)] },
			bloomLevel: {
				type: "string",
				enum: ["remember", "understand", "apply", "analyze", "evaluate", "create"],
			},
			stem: { type: "string" },
		},
		required: ["qtype", "marks", "bloomLevel", "stem"],
	};
	if (["mcq", "assertion_reason"].includes(section.qtype)) {
		item.properties = {
			...item.properties,
			options: {
				type: "object",
				properties: Object.fromEntries(
					["A", "B", "C", "D"].map((k) => [k, { type: "string" }])),
				required: ["A", "B", "C", "D"],
			},
			correctOption: { type: "string", enum: ["A", "B", "C", "D"] },
		};
		item.required = [...(item.required as string[]), "options", "correctOption"];
	}
	if (["very_short_answer", "short_answer", "long_answer"].includes(section.qtype)) {
		item.properties = {
			...item.properties,
			modelAnswer: { type: "string" },
			markingPoints: { type: "array", items: { type: "string" } },
		};
		item.required = [...(item.required as string[]), "modelAnswer", "markingPoints"];
	}
	if (section.qtype === "case_study") {
		item.properties = { ...item.properties, passage: { type: "string" },
			modelAnswer: { type: "string" } };
		item.required = [...(item.required as string[]), "passage", "modelAnswer"];
	}
	return {
		type: "object",
		properties: { questions: { type: "array", items: item } },
		required: ["questions"],
	};
}

// --------------------------------------------------------------------------- //
// validation
// --------------------------------------------------------------------------- //

const BANNED_IN_STEM = [
	"as an ai", "language model", "i cannot", "in the chapter", "in this chapter",
	"according to the text", "based on the text", "the text mentions",
	"the passage above", "as per the", "note that", "in conclusion",
	"it is important to note", "furthermore,", "overall,",
];
const LEADING_NUMBER = /^\s*(?:q(?:uestion)?\.?\s*)?\(?(?:\d{1,2}|[ivxlc]{1,4}|[a-d])\)?\s*[.)\-:]\s+/i;

function numbersIn(text: string): number[] {
	return (text.match(/\d+/g) || []).map(Number);
}

/** Whether the wrong options are the right one walked up and down a number. */
function isLadder(options: Record<string, string>, correct: string): boolean {
	const right = numbersIn(options[correct] || "");
	if (!right.length) return false;
	const deltas = new Set<number>();
	for (const key of ["A", "B", "C", "D"]) {
		if (key === correct) continue;
		const nums = numbersIn(options[key] || "");
		if (nums.length !== right.length) return false;
		if (nums.every((n, i) => n === right[i])) { deltas.add(0); continue; }
		const moved = nums.map((n, i) => Math.abs(n - right[i])).filter((d) => d > 0);
		if (moved.length !== 1) return false;
		deltas.add(moved[0]);
	}
	return deltas.size > 0 && Math.max(...deltas) <= 3;
}

/**
 * Whether an answer says the same thing as the question, rather than answering it.
 *
 * Measured as containment, not symmetric overlap: how much of the *answer* is
 * already in the question. "Express 32760 as a product of its prime factors" came
 * back with the answer "product of primes" -- a subset of the question's own words.
 * Jaccard misses that, because two words out of five is a weak match, and it misses
 * it harder when the model pluralises: "primes" is not "prime". So words are
 * singularised, and the test is what fraction of the answer's own words the question
 * already contains.
 *
 * A real answer does reuse the question's nouns -- a proof repeats the proposition
 * it is proving -- so the bar is not absolute. At 0.65 the measured free-tier case
 * is caught ("expression as a product of primes" shares two of its three words with
 * "Express 32760 as a product of its prime factors") while "unique factorisation"
 * against a stem about factorisation is let through at one of two. Erring toward
 * letting a thin answer through is the safer side: a teacher sees a weak answer and
 * replaces it, whereas a question silently dropped is a paper that is short a
 * question for reasons nobody can see.
 */
function restates(stem: string, candidate: string, threshold = 0.65): boolean {
	const asked = tokens(stem);
	const answer = tokens(candidate);
	if (asked.size < 4 || answer.size < 2) return false;
	let shared = 0;
	for (const word of answer) if (asked.has(word)) shared += 1;
	return shared / answer.size >= threshold;
}

interface Item { qtype: string; marks: unknown; bloomLevel: string; stem: string;
	options?: Record<string, string>; correctOption?: string; modelAnswer?: string;
	markingPoints?: string[]; passage?: string }

/** Why a question does not belong in this section, or null if it does. */
function validate(item: Item, section: Section): string | null {
	const stem = (item.stem || "").trim();
	if (!stem) return "empty-stem";
	if (stem.length < 12) return "stem-too-short";
	const low = stem.toLowerCase();
	if (BANNED_IN_STEM.some((tell) => low.includes(tell))) return "stem-names-the-text";
	// A leading enumerator is *not* a refusal. The paper supplies the number, and
	// `toRecord` strips one, so refusing here would throw away a sound question
	// over its own numbering -- which is what a model does when asked for two
	// questions in one call. The offline validator in `cbse_generate.py` strips
	// rather than refuses for the same reason; this copy had drifted and refused.
	if (/\s(?:I{1,3}V?|IV|V|\(?[a-e]\))\s*[.)\-]\s+/.test(stem)) {
		return "stem-is-several-questions";
	}
	if (item.qtype !== section.qtype) return "wrong-type";
	const marks = Number(String(item.marks).trim());
	if (!Number.isFinite(marks) || marks !== section.marks) return "wrong-marks";
	if (!["remember", "understand", "apply", "analyze", "evaluate", "create"]
		.includes(item.bloomLevel)) return "bad-bloom";

	if (["mcq", "assertion_reason"].includes(section.qtype)) {
		const options = item.options || {};
		if (JSON.stringify(Object.keys(options).sort()) !==
			JSON.stringify(["A", "B", "C", "D"])) return "options-not-abcd";
		const texts = Object.values(options).map((v) => (v || "").trim());
		if (texts.some((t) => t.length < 1)) return "option-empty";
		const normalised = texts.map((t) => t.toLowerCase().replace(/[^\p{L}\p{N}]/gu, ""));
		if (new Set(normalised).size !== normalised.length) return "options-not-answerable";
		const key = item.correctOption;
		if (!key || !["A", "B", "C", "D"].includes(key)) return "no-correct-option";
		if (!(options[key] || "").trim()) return "no-correct-option";
		if (isLadder(options, key)) return "distractor-ladder";
	}

	if (["very_short_answer", "short_answer", "long_answer"].includes(section.qtype)) {
		if (!(item.modelAnswer || "").trim()) return "no-model-answer";
		const points = (item.markingPoints || []).filter((p) => (p || "").trim());
		if (!points.length) return "no-marking-points";
		// A scheme is worth the section's marks; how many steps express that is the
		// board's business. A 5-mark answer scored in three steps is normal CBSE.
		if (points.length > section.marks) return "too-many-marking-points";
		// An answer that says the same thing as the question is not an answer. A
		// free-tier run asked to factorise 32760 came back with the model answer
		// "expression as a product of primes" -- the question, rephrased -- and a
		// marking point reading the same thing again. A marker cannot award marks
		// against that, and it is invisible to any check that only looks at shape.
		if (restates(stem, item.modelAnswer || "")) return "answer-restates-question";
		for (const point of points) {
			if (restates(stem, point)) return "marking-point-restates-question";
		}
		// A stem that tells the student to prove something, and an answer that
		// denies it, cannot both go on a paper.
		if (/\b(show|prove|verify|establish|demonstrate)\b.{0,40}\b(that|whether)\b/s
			.test(low)) {
			const answer = (item.modelAnswer || "").toLowerCase();
			if (/(is not|are not|does not|do not|cannot|≠|not equal|is false|incorrect)/.test(answer)
				&& !/(therefore|hence|thus|so,|which proves|as required)/.test(answer)) {
				return "premise-not-supported";
			}
		}
	}

	if (section.qtype === "case_study") {
		if (((item.passage || "").trim().split(/\s+/).filter(Boolean)).length < 60) {
			return "case-passage-too-short";
		}
	}
	return null;
}

/** Marks shared across the steps so the stored scheme is worth the section's marks. */
function markingPoints(texts: string[], total: number) {
	const kept = texts.map((t) => (t || "").trim()).filter(Boolean).slice(0, total);
	if (!kept.length) return [];
	const base = Math.floor(total / kept.length);
	const extra = total % kept.length;
	return kept.map((text, i) => ({
		description: text, marks: base + (i < extra ? 1 : 0),
		keyword: "", isRequired: true, synonyms: [],
	}));
}

/**
 * Build the system prompt for one section.
 *
 * The section''s numbers come from the blueprint, not from here: a sentence asking
 * for one mark is a request, while marks: {enum: ["1"]} in the schema is a
 * constraint the model cannot talk its way past. Both are sent, because the schema
 * holds the line and the words get it to try.
 */
function systemFor(section: Section, blueprint: Blueprint, language: string,
	topic: string, count: number): string {
	const languageName = language === "hi" ? "Hindi" : "English";
	const script = language === "hi"
		? "Write in natural, exam-standard Hindi, not translated English. Use the book's own Devanagari punctuation and numerals."
		: "Write in English. Use Latin numerals (1, 2, 3), as the book does.";
	const words = section.answerWords || Math.max(1, section.marks * 2);
	const shape: Record<string, string> = {
		mcq: "- One sentence of stem, then four options labelled A, B, C, D. Exactly four.\n"
			+ "- Every option is the same kind of thing: all words, or all numbers, or all dates.\n"
			+ "- Exactly one option is correct. Vary which letter is correct; do not favour A.\n",
		assertion_reason:
			"- Two numbered statements, an option, and the reason.\n"
			+ "- The four options are the standard pairs: both true and the reason explains; both true but it does not; assertion true, reason false; both false.\n",
		very_short_answer:
			"- The student answers in one line. No part (a)/(b), no sub-questions.\n"
			+ "- The answer is a single word, number, or short phrase. Not a sentence.\n",
		short_answer: `- The student answers in about ${words} words.\n`
			+ "- At most two parts, and only if the marks allow it.\n"
			+ `- Keep the model answer to about ${words} words. It is a mark scheme, not an essay.\n`,
		long_answer: `- The student answers in about ${words} words, in steps.\n`
			+ "- Show the working the student would write, not a paragraph of prose.\n"
			+ `- Keep the model answer to about ${words} words. It is a mark scheme, not an essay.\n`,
		case_study: `- Open with a short real-life passage of 80-120 words that the student reads.\n`
			+ `- Then ask ${Math.max(2, Math.min(count, 4))} short questions on it, the last one higher-order.\n`
			+ "- The passage is part of the question, not a separate item.\n"
			+ "- Keep the model answer to about 60 words in total.\n",
		map_based: "- Name the map or diagram the question needs and where it is in the chapter.\n"
			+ "- The question is unanswerable without it, so say so in one clause.\n",
	};
	return `You are a CBSE question paper maker. You set papers for ${blueprint.subject}, in ${languageName}.

The paper is ${blueprint.theoryMarks} marks in ${blueprint.durationMinutes} minutes. You are writing Section ${section.key}, "${section.name}".

Rules, all of which the board enforces:
- Every question in this section is worth exactly ${section.marks} mark(s).
- The question type is ${section.qtype}. Write it in the form the board uses for that type.
${shape[section.qtype] || ""}- Set the question in a real situation a student meets, not a definition to memorise. The board calls this competency-based, and it is the reason the paper exists.
- Use only what the chapter text below says. If the text does not settle it, write a different question; never write one the text cannot answer.
- Never mention the chapter, the text, the passage or yourself in the question. A student must not be able to tell it was written by reading the question.
- ${script}
- Distractors, where the type has them, must be plausible to a student who has read the chapter and wrong for a reason. No joke options, no "all of the above", no "none of these".
- Write ${count} question(s), each asking about something different.
${topic ? `- This question is about "${topic}".` : ""}
Return only the questions, as JSON matching the schema.`;
}

interface Generated { question: Record<string, unknown>; section: string; topic: string }

/**
 * Generate, validate, and either return the questions or say why there are none.
 *
 * `count` is spread over the sections asked for, because a teacher picking four
 * topics wants four questions spread across them rather than four on the first.
 * `refusals` is returned rather than swallowed: a teacher told "this chapter will
 * not support a case study" can choose a different section, and a teacher silently
 * handed four questions out of twelve asked for cannot.
 */
async function generate(env: Env, request: Request): Promise<Response> {
	const body = await readBody(request);
	const code = String(body.code || "");
	const chapter = String(body.chapter || "");
	const topics = Array.isArray(body.topics) ? (body.topics as string[]) : [];
	const asked = Math.floor(Number(body.count)) || topics.length || 5;
	const wanted = Math.min(Math.max(1, asked), MAX_COUNT);

	const meta = await getJson<BookMeta>(env.BANK, `meta/${code}.json`);
	if (!meta) return Response.json({ error: "unknown book" },
		{ status: 404, ...JSON_HEADERS });
	const formats = (await getJson<Record<string, Blueprint>>(
		env.BANK, "blueprint.json")) || {};
	const grade = Number(meta.book.class) || 10;
	const band = grade <= 5 ? "primary" : grade <= 8 ? "middle" : "board";
	const blueprint = formats[`${meta.book.subject}|${band}`]
		|| formats[`${meta.book.subject}|board`];
	if (!blueprint) {
		return Response.json(
			{ error: `no CBSE format for ${meta.book.subject} in the ${band} band` },
			{ status: 404, ...JSON_HEADERS });
	}

	// Both paths stop hard: the free one at its neuron allowance, the paid one at
	// DAILY_USD_CAP. A cap that is only reported is no cap on a public URL.
	const over = await overBudget(env);
	if (over) return over;

	const corpus = await getJson<Record<string, string>>(env.BANK, `text/${code}.json`);
	const chapterText = corpus?.[chapter];
	if (!chapterText) return Response.json({ error: "chapter not in the corpus" },
		{ status: 404, ...JSON_HEADERS });

	const lines = chapterLines(chapterText);
	const chapterName = await chapterTitle(env, code, chapter);
	const sections = body.section
		? blueprint.sections.filter((s) => s.key === String(body.section))
		: blueprint.sections;
	if (!sections.length) {
		return Response.json({ error: `no section ${String(body.section)} in this paper` },
			{ status: 400, ...JSON_HEADERS });
	}
	const perSection = Math.max(1, Math.round(wanted / sections.length));

	const kept: Generated[] = [];
	const refusals: Array<{ section: string; reason: string; stem?: string; raw?: unknown; rawType?: string }> = [];
	const known = await loadBankStems(env, meta.book.subject, grade);
	const useLite = body.lite === true;
	const models = new Set<string>();
	let fellBack = false;
	let neurons = 0;
	let usd = 0;

	for (const [index, section] of sections.entries()) {
		const topic = topics.length ? topics[(index * perSection) % topics.length] : "";
		const context = topicWindow(lines, topics,
			topics.indexOf(topic) >= 0 ? topics.indexOf(topic) : 0);
		const system = systemFor(section, blueprint, meta.book.language || "en",
			topic, perSection);
		const user = `Chapter ${chapter}: ${chapterName} (${code})\n\n--- chapter ---\n${context}\n--- end ---`;
		const { data, neurons: used, usd: cost, model, error, fellBack: fellBackTo } = await ask(env, system,
			user, questionSchema(section), section,
			{ maxTokens: section.qtype === "case_study" ? 2500 : 1800,
			  lite: useLite });
		neurons += used;
		usd += cost;
		models.add(model);
		if (fellBackTo) fellBack = true;
		if (error) {
			refusals.push({ section: section.key, reason: `model: ${error}` });
			continue;
		}
		const items = (asObject(data) as { questions?: Item[] } | null)?.questions || [];
		if (!items.length) {
			// The raw body is returned, not just a reason. "Model returned nothing"
			// on its own cannot be acted on: an empty finishReason, a safety block
			// and a schema the model quietly ignored all look identical from here,
			// and they need three different fixes.
			refusals.push({ section: section.key, reason: "model returned nothing",
				raw: typeof data === "string" ? data.slice(0, 400) : data,
				rawType: typeof data });
			continue;
		}
		for (const item of items) {
			const reason = validate(item, section);
			if (reason) {
				refusals.push({ section: section.key, reason,
					stem: (item.stem || "").slice(0, 140) });
				continue;
			}
			const words = tokens(item.stem || "");
			if (isRepeat(words, known)) {
				refusals.push({ section: section.key, reason: "already-in-bank",
					stem: (item.stem || "").slice(0, 140) });
				continue;
			}
			known.push(words);
			kept.push({ section: section.key, topic,
				question: toRecord(item, section, meta, code, chapter, chapterName) });
		}
	}

	await addSpent(env, neurons, usd);
	const paperId = `${code}-${chapter}-${Date.now()}`;
	await putJson(env.BANK, `papers/${paperId}.json`, {
		id: paperId, code, chapter, chapterName, subject: meta.book.subject, grade,
		topics, questions: kept, refusals, neurons, usd,
		models: [...models], fellBack, createdAt: new Date().toISOString(),
	});

	return Response.json({
		paperId, code, chapter, chapterName, subject: meta.book.subject, grade,
		blueprint: { theoryMarks: blueprint.theoryMarks, band: blueprint.gradeBand },
		requested: wanted, generated: kept.length, refusals, questions: kept,
		neurons, usd, models: [...models], fellBack,
		spend: { neuronsToday: already + neurons, usdToday: (await spentUsd(env)),
			budget: NEURON_BUDGET },
	}, JSON_HEADERS);
}

function toRecord(item: Item, section: Section, meta: BookMeta, code: string,
	chapter: string, chapterName: string): Record<string, unknown> {
	const marks = Number(String(item.marks).trim()) || section.marks;
	const objective = ["mcq", "assertion_reason"].includes(section.qtype);
	const written = ["very_short_answer", "short_answer", "long_answer"].includes(section.qtype);
	const scheme: Record<string, unknown> = {
		totalMarks: marks,
		markingPoints: written ? markingPoints(item.markingPoints || [], marks) : [],
		rubricLevels: [], commonErrors: [], alternativeAnswers: [],
		modelAnswer: item.modelAnswer || "",
		modelAnswerLatex: "", hasPartialCredit: marks >= 3,
		metadata: { answerSource: "generated", evidence: [], objective },
	};
	if (objective) {
		scheme.metadata = { ...(scheme.metadata as object),
			options: item.options || {}, correctOption: item.correctOption || "" };
		scheme.modelAnswer = (item.options || {})[item.correctOption || ""] || "";
	}
	if (section.qtype === "case_study") {
		scheme.metadata = { ...(scheme.metadata as object),
			passage: item.passage || "" };
	}
	return {
		id: `ai:cbse:${code}:${chapter}:${section.key}`,
		questionBankId: `ai-cbse:${code}`,
		subject: meta.book.subject,
		grade: Number(meta.book.class),
		chapterIds: [], chapterName,
		type: section.qtype, marks, bloomLevel: item.bloomLevel,
		// The paper supplies the number; the stem must not carry one.
		stem: (item.stem || "").replace(LEADING_NUMBER, "").trim(),
		stemLatex: "", parts: [], answerScheme: scheme,
		estimatedTimeMinutes: Math.max(1, marks),
		source: "ai_generated", language: meta.book.language,
		provenance: {
			method: "cbse-blueprint-on-demand",
			model: MODEL,
			section: `${section.key} ${section.name}`,
			chapter: `${code} ch${chapter}`,
			chapterName,
		},
	};
}

/**
 * The questions this subject and grade already hold, as word sets.
 *
 * Cached per subject and grade, because a request would otherwise re-parse nine
 * thousand stems on every click, and read only when a question is actually on the
 * point of being accepted.
 */
async function loadBankStems(env: Env, subject: string, grade: number): Promise<Set<string>[]> {
	const key = `stemcache/${subject.replace(/\W+/g, "_")}-${grade}.json`;
	const cached = await getJson<{ stems: string[][] }>(env.BANK, key);
	if (cached?.stems) return cached.stems.map((s) => new Set(s));
	const bank = await getJson<{ rows: string[][] }>(env.BANK, "bank/existing.json");
	const stems: string[][] = [];
	for (const row of bank?.rows || []) {
		if (row[0] && row[0] !== subject) continue;
		const words = [...tokens(row[2] || "")];
		if (words.length >= 3) stems.push(words);
	}
	await putJson(env.BANK, key, { stems });
	return stems.map((s) => new Set(s));
}

function isRepeat(words: Set<string>, known: Set<string>[], threshold = 0.72): boolean {
	if (words.size < 3) return false;
	for (const other of known) {
		if (Math.abs(other.size - words.size) > words.size * (1 - threshold) / threshold) {
			continue;
		}
		if (jaccard(words, other) >= threshold) return true;
	}
	return false;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const route = url.pathname;

		try {
			// -- what the school already has, so nothing is generated twice ------
			if (route === "/api/corpus") {
				const codes = await listBookCodes(env);
				const books = [];
				for (const code of codes) {
					const meta = await getJson<BookMeta>(env.BANK, `meta/${code}.json`);
					if (meta?.book) books.push(meta);
				}
				books.sort((a, b) => (a.book.class - b.book.class)
					|| a.book.subject.localeCompare(b.book.subject));
				return Response.json({ books }, JSON_HEADERS);
			}

			if (route === "/api/blueprint") {
				const subject = url.searchParams.get("subject") || "Mathematics";
				const grade = Number(url.searchParams.get("grade") || 10);
				const all = (await getJson<Record<string, Blueprint>>(
					env.BANK, "blueprint.json")) || {};
				const band = grade <= 5 ? "primary" : grade <= 8 ? "middle" : "board";
				const blueprint = all[`${subject}|${band}`];
				if (!blueprint) {
					return Response.json(
						{ error: `no CBSE format registered for ${subject} in the ${band} band` },
						{ status: 404, ...JSON_HEADERS });
				}
				return Response.json({ blueprint }, JSON_HEADERS);
			}

			// -- topics, read out of the chapter on request ----------------------
			if (route === "/api/topics" && request.method === "POST") {
				const refused = refuseUnlessAuthorised(request, env.QBANK_TOKEN)
					|| await overBudget(env);
				if (refused) return refused;
				const body = await readBody(request);
				if (!body.code || !body.chapter) {
					return Response.json({ error: "code and chapter are required" },
						{ status: 400, ...JSON_HEADERS });
				}
				const meta = await getJson<BookMeta>(env.BANK, `meta/${body.code}.json`);
				if (!meta) return Response.json({ error: "unknown book" },
						{ status: 404, ...JSON_HEADERS });
				const title = await chapterTitle(env, body.code, body.chapter);
				const result = await extractTopics(env, body.code, String(body.chapter),
					title, meta.book.language || "en");
				await addSpent(env, result.neurons, result.usd || 0);
				return Response.json(result, JSON_HEADERS);
			}

			// -- the paper, generated because somebody asked for it --------------
			if (route === "/api/generate" && request.method === "POST") {
				const refused = refuseUnlessAuthorised(request, env.QBANK_TOKEN);
				if (refused) return refused;
				return await generate(env, request);
			}

			// -- what has been generated, so a finaliser can collect it ----------
			if (route === "/api/papers") {
				const refused = refuseUnlessAuthorised(request, env.QBANK_TOKEN);
				if (refused) return refused;
				// `wrangler r2 object list` does not exist, so an offline finaliser
				// cannot enumerate the bucket itself. It could also fetch each key
				// with `wrangler r2 object get`, which is one subprocess per paper
				// and mostly failed. Returning the papers themselves is one request
				// and no subprocess at all; the payload is small because a paper is
				// a dozen questions.
				const listed = await env.BANK.list({ prefix: "papers/", limit: 1000 });
				const papers = [];
				for (const object of listed.objects) {
					const stored = await getJson<Record<string, unknown>>(
						env.BANK, object.key);
					if (stored) papers.push(stored);
				}
				return Response.json({ count: papers.length, papers },
					JSON_HEADERS);
			}

			if (route === "/api/health") {
				return Response.json({ ok: true,
					provider: env.GEMINI_API_KEY ? "gemini" : "workers-ai",
					neuronsToday: await spent(env), usdToday: await spentUsd(env),
					freeBudget: NEURON_BUDGET, capUsd: usdCap(env),
					day: new Date().toISOString().slice(0, 10) }, JSON_HEADERS);
			}
		} catch (error) {
			return Response.json({ error: String(error).slice(0, 300) },
				{ status: 500, ...JSON_HEADERS });
		}
		return new Response("qbank", { status: 404 });
	},
};

async function listBookCodes(env: Env): Promise<string[]> {
	const listed = await env.BANK.list({ prefix: "meta/", limit: 1000 });
	return listed.objects.map((o) => o.key.slice("meta/".length).replace(/\.json$/, ""));
}

async function readBody(request: Request): Promise<Record<string, unknown>> {
	try {
		return (await request.json()) as Record<string, unknown>;
	} catch {
		return {};
	}
}

async function chapterTitle(env: Env, code: string, chapter: string): Promise<string> {
	const text = await getJson<Record<string, string>>(env.BANK, `text/${code}.json`);
	const body = text?.[chapter] || "";
	const lines = chapterLines(body);
	for (const [, line] of lines.slice(0, 12)) {
		if (line.length > 3 && line.length < 70 && !/^\d+$/.test(line)) return line;
	}
	return `Chapter ${chapter}`;
}
