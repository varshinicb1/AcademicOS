/**
 * Chapter-isolated retrieval over the 572-chapter NCERT corpus.
 *
 * The corpus arrives as one gzipped JSONL object in R2 and is split three ways:
 * D1 holds the text and an FTS5 index for lexical recall, one Vectorize index
 * holds 1024-dim bge-m3 vectors under one namespace per chapter, and the
 * question generator consumes the passages this Worker returns.
 *
 * Three decisions are worth stating up front.
 *
 * One namespace per chapter. A question about acids in Class 7 must not be
 * answered out of Class 10, and namespace isolation is the only mechanism here
 * that makes that true by construction rather than by hoping the ranking
 * cooperates. 572 namespaces fits inside the 1,000 the free plan allows.
 *
 * Hybrid, not dense-only. bge-m3 blurs exactly the things a school textbook
 * leans on: a proper noun, a chemical formula, a number in a worked sum. BM25
 * over FTS5 is blunt about those, and the two failure modes are different
 * enough that fusing them beats either alone. RRF fuses them because BM25 scores
 * and cosine scores are not on a comparable scale, and normalising two arbitrary
 * score distributions is a worse idea than ranking-based fusion.
 *
 * The indexer is resumable and bounded per call. Embedding 12,570 chunks does
 * not fit in one request, and the previous seeding attempt died mid-flight and
 * left no way to tell how far it had got. Progress lives in D1, not in the
 * caller's memory, so `/status` is truthful after a crash and every call reports
 * what it actually did.
 *
 * The tokenizer in migrations/0001_init.sql is the load-bearing part of the
 * lexical half. FTS5's default unicode61 splits Devanagari matras off their base
 * letters, indexing "दादाजी" as द / ज, which makes BM25 on Hindi noise. That is a
 * measured result on this corpus, not a guess, and the migration comment records
 * it so nobody "simplifies" the tokenizer back.
 */

export interface Env {
	AI: Ai;
	VECTORIZE: Vectorize;
	CORPUS: D1Database;
	PACKS: R2Bucket;
}

const EMBED_MODEL = "@cf/baai/bge-m3";
const RERANK_MODEL = "@cf/baai/bge-reranker-base";
const PACK_KEY = "corpus/chunks.v1.jsonl.gz";

/** RRF damping. 60 is the value from the original Cormack paper. */
const RRF_K = 60;

/** Vectorize returns at most 50 matches when metadata comes back. */
const MAX_VECTOR_K = 20;
// Only used when a class/subject filter forces post-filtering of the dense side.
const FILTERED_VECTOR_K = 64;

/** Reranker input is 512 tokens for query+passage combined, so passages are cut
 *  before they are sent. Enough to judge relevance, not enough to overflow. */
const RERANK_MAX_CHARS = 600;
const RERANK_POOL = 12;

const DEFAULT_EMBED_BATCH = 50;
const D1_BATCH = 100;

const JSON_HEADERS = { "Content-Type": "application/json" };

function json(data: unknown, status = 200): Response {
	return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}

function error(message: string, status = 400): Response {
	return json({ ok: false, error: message }, status);
}

/** SQL string literal. The query text that reaches FTS MATCH is user input, so
 *  escaping is not optional. */
function lit(value: unknown): string {
	if (value === null || value === undefined) return "NULL";
	if (typeof value === "number") return Number.isFinite(value) ? String(value) : "NULL";
	return `'${String(value).replace(/'/g, "''")}'`;
}

// --------------------------------------------------------------------------- //
// Chunk shape, as written by scripts/corpus/chunk_corpus.py
// --------------------------------------------------------------------------- //

interface ChunkRow {
	id: string;
	chapter_id: string;
	heading_path: string;
	text: string;
	embed_text: string;
	book_code: string;
	// The chunk pack names this field `class`; `class_no` is the D1 column and
	// the name used in search filters. Accept either so a pack rename cannot
	// silently blank the column again.
	class?: number;
	class_no?: number | null;
	subject: string;
	language: string;
	chapter_no: number | null;
	text_quality: string;
	quote_exact: number;
	n_chars: number;
	est_tokens: number;
	text_sha: string;
}

// `class` is a reserved word in SQL, so the pack cannot name its column that way
// in every consumer; normalise both spellings to the stored integer here.
function toClassNo(row: ChunkRow): number | null {
	const raw = row.class ?? row.class_no;
	if (raw === null || raw === undefined) return null;
	const n = Number(raw);
	return Number.isFinite(n) ? n : null;
}

interface StoredHit {
	id: string;
	chapter_id: string;
	heading_path: string;
	text: string;
	text_quality: string;
	quote_exact: number;
	// Only selected where the dense branch needs narrowing; see the fetch in
	// `search`. Optional so the narrower lexical query stays unchanged.
	class_no?: number | null;
	subject?: string;
}

/** Idempotent upsert that only invalidates the vector when the embedded text
 *  actually changed. Re-ingesting an unchanged pack must not force 12,570
 *  re-embeds, but a corrected chunk must not keep a vector for text it no longer has. */
const UPSERT_CHUNK = `INSERT INTO chunks
  (id, chapter_id, heading_path, text, embed_text, book_code, class_no, subject,
   language, chapter_no, text_quality, quote_exact, n_chars, est_tokens, text_sha, vectorized)
 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
 ON CONFLICT(id) DO UPDATE SET
   chapter_id = excluded.chapter_id,
   heading_path = excluded.heading_path,
   text = excluded.text,
   embed_text = excluded.embed_text,
   book_code = excluded.book_code,
   class_no = excluded.class_no,
   subject = excluded.subject,
   language = excluded.language,
   chapter_no = excluded.chapter_no,
   text_quality = excluded.text_quality,
   quote_exact = excluded.quote_exact,
   n_chars = excluded.n_chars,
   est_tokens = excluded.est_tokens,
   text_sha = excluded.text_sha,
   vectorized = CASE WHEN chunks.embed_text = excluded.embed_text THEN chunks.vectorized ELSE 0 END`;

// --------------------------------------------------------------------------- //
// Models
// --------------------------------------------------------------------------- //

interface EmbeddingResponse {
	shape: number[];
	data: number[][];
}

async function embed(env: Env, texts: string[]): Promise<number[][]> {
	const response = (await env.AI.run(EMBED_MODEL, { text: texts })) as EmbeddingResponse;
	if (!response || !Array.isArray(response.data)) {
		throw new Error(`embed: unexpected model response`);
	}
	if (response.data.length !== texts.length) {
		throw new Error(`embed: asked for ${texts.length}, got ${response.data.length}`);
	}
	const width = response.data[0]?.length ?? 0;
	if (width !== 1024) {
		// The index was created at 1024 dims; a silent width change would make
		// every upsert fail deep inside Vectorize instead of here.
		throw new Error(`embed: expected 1024 dimensions, got ${width}`);
	}
	return response.data;
}

interface RerankScore {
	id?: number;
	score?: number;
}

/** Shape the API actually requires for `@cf/baai/bge-reranker-base`.
 *
 *  The generated `Ai_Cf_Baai_Bge_Reranker_Base_Input` in @cloudflare/workers-types
 *  is missing `query` -- its own "A query you wish to perform against the provided
 *  contexts" doc comment is orphaned above `top_k`, which is the generator losing
 *  the field. The published model schema and the HTTP API both require `query`, and
 *  a reranker with no query is not a reranker, so the runtime contract wins and the
 *  cast is deliberate. Dropping `query` to satisfy the .d.ts would compile and then
 *  return meaningless scores. */
interface RerankInput {
	query: string;
	top_k?: number;
	contexts: { text: string }[];
}

async function rerank(env: Env, query: string, passages: string[]): Promise<number[]> {
	if (passages.length === 0) return [];
	const input: RerankInput = {
		query,
		contexts: passages.map((text) => ({ text })),
	};
	const response = (await env.AI.run(
		RERANK_MODEL,
		input as unknown as Ai_Cf_Baai_Bge_Reranker_Base_Input,
	)) as { response?: RerankScore[] };
	const scores = new Array<number>(passages.length).fill(0);
	for (const row of response?.response ?? []) {
		if (typeof row.id === "number" && typeof row.score === "number" && row.id >= 0 && row.id < passages.length) {
			scores[row.id] = row.score;
		}
	}
	return scores;
}

// --------------------------------------------------------------------------- //
// Ingest: R2 pack -> D1
// --------------------------------------------------------------------------- //

/**
 * Streams the packed object and upserts rows in D1 batches, resuming from a
 * stored record offset. Re-reading a 5 MB object per call is cheaper than
 * holding 12,570 parsed chunks in a Worker, which is what the earlier per-file
 * upload loop effectively tried to do.
 */
async function ingest(
	env: Env,
	maxRecords: number,
	offsetOverride?: number,
): Promise<Record<string, unknown>> {
	const object = await env.PACKS.get(PACK_KEY);
	if (!object) return { ok: false, error: `missing pack ${PACK_KEY}` };

	// Ingest keeps its own run row: it streams a pack and needs a cursor into that
	// stream, which has nothing to do with how many chunks the embedder has done.
	// Sharing the 'index' row silently restarted ingest at zero on every call.
	const run = await currentRun(env, "ingest");
	// An explicit offset wins, so a corrupted cursor can be replayed from the top
	// without hand-written SQL. The upsert is idempotent, so replaying is safe.
	const startOffset = Number.isFinite(offsetOverride)
		? Math.max(Number(offsetOverride), 0)
		: Number(run?.ingest_offset ?? 0);

	const decoded = object.body
		.pipeThrough(new DecompressionStream("gzip"))
		.pipeThrough(new TextDecoderStream());
	const reader = decoded.getReader();

	const insert = env.CORPUS.prepare(UPSERT_CHUNK);
	let statements: D1PreparedStatement[] = [];

	const flush = async () => {
		if (statements.length === 0) return;
		await env.CORPUS.batch(statements);
		statements = [];
	};

	let recordNo = 0;
	let processed = 0;
	let malformed = 0;
	let firstMalformedAt = 0;
	let firstMalformedSample = "";
	let malformedDetail: Record<string, unknown> | null = null;
	const failures: string[] = [];

	// A ReadableStream hands back arbitrary byte boundaries, not lines. Parsing
	// each read as if it were a record marks every partial line as malformed, so
	// the buffer has to carry the tail of one read into the next. `whole` is the
	// safety net for a final line with no trailing newline.
	let buffer = "";
	const handleLine = async (line: string): Promise<void> => {
		if (!line) return;
		recordNo += 1;
		if (recordNo <= startOffset) return;

		let row: ChunkRow;
		try {
			row = JSON.parse(line) as ChunkRow;
		} catch (err) {
			malformed += 1;
			if (firstMalformedAt === 0) {
				firstMalformedAt = recordNo;
				// V8's message carries the offset that failed to parse, which is
				// what identifies the offending byte in an otherwise valid record.
				const reason = String(err).slice(0, 120);
				const at = /position (\d+)/.exec(reason);
				const pos = at ? Number(at[1]) : -1;
				firstMalformedSample = line;
				malformedDetail = {
					reason,
					pos,
					context: pos >= 0 ? line.slice(Math.max(0, pos - 40), pos + 40) : line.slice(0, 80),
					codepoints: line.slice(Math.max(0, pos - 4), pos + 4)
						.split("")
						.map((ch) => `${ch}[U+${ch.codePointAt(0)!.toString(16)}]`)
						.join(""),
					length: line.length,
				};
			}
			return;
		}
		statements.push(
			insert.bind(
				row.id, row.chapter_id, row.heading_path ?? "", row.text, row.embed_text,
				row.book_code ?? "", toClassNo(row), row.subject ?? "",
				row.language ?? "", row.chapter_no ?? null,
				row.text_quality ?? "native-text-layer", row.quote_exact ? 1 : 0,
				row.n_chars ?? row.text.length, row.est_tokens ?? 0, row.text_sha ?? "",
			),
		);
		processed += 1;
		if (statements.length >= D1_BATCH) await flush();
	};

	// Whether the pack was read to the end, as opposed to being cut short by
	// `maxRecords`. Only the former means the buffer holds a single trailing
	// line; after an early exit it holds the whole unread remainder of the
	// object, and passing that to `handleLine` parses several thousand records as
	// one bad one.
	let drained = false;
	outer: for (;;) {
		const { value, done: finished } = await reader.read();
		if (finished) {
			drained = true;
			break;
		}
		buffer += value;
		let newline = buffer.indexOf("\n");
		while (newline >= 0) {
			await handleLine(buffer.slice(0, newline).trim());
			buffer = buffer.slice(newline + 1);
			if (processed >= maxRecords) break outer;
			newline = buffer.indexOf("\n");
		}
	}
	// A final line with no trailing newline is only a single line if we actually
	// reached the end of the object.
	if (drained) await handleLine(buffer.trim());
	await flush();
	// Draining keeps the connection reusable and surfaces a truncated pack here
	// rather than as a confusing offset on the next call.
	await reader.cancel().catch(() => undefined);

	const totals = await corpusCounts(env);
	await env.CORPUS.prepare(
		`INSERT INTO index_runs
		   (run_id, status, started_at, updated_at, failed_chunks, embed_batch_size, model, last_error, ingest_offset)
		 VALUES ('ingest','running',?,?,?,?,?,?,?)
		 ON CONFLICT(run_id) DO UPDATE SET
		   status='running', updated_at=excluded.updated_at,
		   failed_chunks=excluded.failed_chunks, last_error=excluded.last_error,
		   ingest_offset=excluded.ingest_offset`,
	)
		.bind(
			new Date().toISOString(), new Date().toISOString(), malformed,
			DEFAULT_EMBED_BATCH, EMBED_MODEL,
			malformed > 0
				? `${malformed} unparseable records, first at #${firstMalformedAt}: ${firstMalformedSample}`
				: null,
			recordNo,
		)
		.run();

	return {
		ok: malformed === 0,
		processed_this_call: processed,
		resumed_from: startOffset,
		offset: recordNo,
		// True only when the object was read to its end, so a caller looping on
		// this knows the pack is finished rather than just that the batch filled.
		reached_end: drained,
		drained,
		malformed,
		// Surfaced in the response as well as the run row: a bad record that only
		// shows up in D1 is one whole loop away from being mistaken for progress.
		malformed_sample:
			malformed > 0
				? `record #${firstMalformedAt} len=${firstMalformedSample.length} ${JSON.stringify(firstMalformedSample.slice(0, 160))}`
				: null,
		// The byte position and neighbouring codepoints, so a parse failure can be
		// diagnosed from the log alone instead of by re-running the ingest.
		malformed_detail: malformed > 0 ? malformedDetail : null,
		failures: failures.slice(0, 5),
		...totals,
	};
}

// --------------------------------------------------------------------------- //
// Reset: forget a set of chapters entirely, in D1 and in Vectorize
// --------------------------------------------------------------------------- //

/**
 * Drop every row and vector belonging to the named chapters.
 *
 * The upsert is deliberately non-destructive so a re-ingested pack does not
 * re-embed 12,570 chunks. That is exactly wrong for the OCR rebuild, though.
 * Shortening a chapter's text shortens its chunk list, so ids like
 * `jhks1-ch03:022` stop appearing in the new pack. Nothing deletes them: the
 * rows stay in D1 and the vectors stay in Vectorize, so a search can still
 * return the pre-correction text for a chapter that has since been rewritten.
 * Re-ingesting alone can never fix that, only hide it behind fresh chunks.
 *
 * So the chapters being rebuilt are removed first. They come back from the pack
 * with `vectorized = 0` and get re-embedded, which is bounded by the size of
 * the rebuild rather than the size of the corpus.
 */
async function resetChapters(env: Env, chapters: string[]): Promise<Record<string, unknown>> {
	const unique = [...new Set(chapters)].sort();
	const placeholders = unique.map(() => "?").join(",");

	const rows = await env.CORPUS.prepare(
		`SELECT id FROM chunks WHERE chapter_id IN (${placeholders})`,
	)
		.bind(...unique)
		.all<{ id: string }>();
	const ids = (rows.results ?? []).map((r) => r.id);

	// D1 first: the delete trigger keeps FTS5 in step, so no row survives in
	// the lexical index either. An id deleted here but not from Vectorize would
	// return dense hits that hydrate to nothing.
	const deleted = await env.CORPUS.prepare(
		`DELETE FROM chunks WHERE chapter_id IN (${placeholders})`,
	)
		.bind(...unique)
		.run();

	let vectorsDeleted = 0;
	const vectorErrors: string[] = [];
	// Vectorize caps ids per call, so delete in small groups and keep going on
	// failure. A partial vector delete is recoverable by re-running the route,
	// whereas an aborted run leaves the two stores disagreeing.
	for (let i = 0; i < ids.length; i += 100) {
		const batch = ids.slice(i, i + 100);
		try {
			await env.VECTORIZE.deleteByIds(batch);
			vectorsDeleted += batch.length;
		} catch (err) {
			vectorErrors.push(String(err).slice(0, 200));
		}
	}

	const after = await env.CORPUS.prepare(
		`SELECT COUNT(*) AS n FROM chunks WHERE chapter_id IN (${placeholders})`,
	)
		.bind(...unique)
		.first<{ n: number }>();

	return {
		ok: vectorErrors.length === 0,
		chapters: unique.length,
		// From the SELECT, not from the driver's `changes`. `chunks_fts_ad` fires
		// on every row and writes to the FTS5 shadow tables, and D1 counts those
		// trigger writes too: deleting 7 chunks reports 21. The row count has to
		// come from the select to be comparable with vectors_deleted.
		rows_removed: ids.length,
		vectors_deleted: vectorsDeleted,
		driver_changes: deleted.meta?.changes ?? null,
		rows_remaining: after?.n ?? null,
		vector_errors: vectorErrors,
		note:
			"Re-ingest the pack, then POST /index. Only these chapters are re-embedded.",
	};
}

// --------------------------------------------------------------------------- //
// Index: D1 rows -> Vectorize
// --------------------------------------------------------------------------- //

async function indexPending(
	env: Env,
	maxChunks: number,
	batchSize: number,
): Promise<Record<string, unknown>> {
	const run = await currentRun(env);
	const startedAt = run?.started_at ?? new Date().toISOString();
	// Entry of *this* call, kept apart from the run's own start time below.
	const callStartedAt = Date.now();

	const pending = await env.CORPUS.prepare(
		`SELECT * FROM chunks WHERE vectorized = 0 ORDER BY id LIMIT ?`,
	).bind(maxChunks).all<ChunkRow>();

	const rows = pending.results ?? [];
	if (rows.length === 0) {
		await env.CORPUS.prepare(
			`UPDATE index_runs SET status='done', updated_at=? WHERE run_id='index'`,
		).bind(new Date().toISOString()).run();
		return { ok: true, indexed_this_call: 0, message: "nothing pending" };
	}

	let indexed = 0;
	let failed = 0;
	let lastError = "";
	const failures: string[] = [];

	for (let i = 0; i < rows.length; i += batchSize) {
		const slice = rows.slice(i, i + batchSize);
		try {
			const vectors = await embed(env, slice.map((r) => r.embed_text));
			await env.VECTORIZE.upsert(
				slice.map((r, n) => ({
					id: r.id,
					namespace: r.chapter_id,
					values: vectors[n],
					metadata: {
						chapter_id: r.chapter_id,
						heading_path: (r.heading_path ?? "").slice(0, 200),
						language: r.language ?? "",
						class_no: r.class_no ?? 0,
						quote_exact: r.quote_exact ? 1 : 0,
						text_quality: r.text_quality ?? "",
					},
				})),
			);
			await env.CORPUS.prepare(
				`UPDATE chunks SET vectorized = 1 WHERE id IN (${slice.map((r) => lit(r.id)).join(",")})`,
			).run();
			indexed += slice.length;
		} catch (err) {
			failed += slice.length;
			lastError = String(err).slice(0, 300);
			if (failures.length < 5) {
				failures.push(`${slice[0]?.id}: ${lastError}`);
			}
		}
	}

	const totals = await corpusCounts(env);
	// Two different clocks, because they answer different questions.
	// `startedAt` is the run row's own start, which for a resumed index is hours
	// in the past -- reporting that as this call's duration makes a 6-second
	// re-embed of 7 chunks look like a 99-minute job.
	const runElapsedMs = Date.now() - new Date(startedAt).getTime();
	const callElapsedMs = Date.now() - callStartedAt;
	await env.CORPUS.prepare(
		`INSERT INTO index_runs
		   (run_id, status, started_at, updated_at, total_chunks, indexed_chunks,
		    failed_chunks, embed_batch_size, model, last_error)
		 VALUES ('index',?,?,?,?,?,?,?,?,?)
		 ON CONFLICT(run_id) DO UPDATE SET
		   status=excluded.status, updated_at=excluded.updated_at,
		   total_chunks=excluded.total_chunks, indexed_chunks=excluded.indexed_chunks,
		   failed_chunks=excluded.failed_chunks, embed_batch_size=excluded.embed_batch_size,
		   model=excluded.model, last_error=excluded.last_error`,
	)
		.bind(
			failed > 0 || totals.pending > 0 ? "running" : "done",
			startedAt, new Date().toISOString(), totals.total, totals.vectorized,
			totals.pending, batchSize, EMBED_MODEL, lastError || null,
		)
		.run();

	return {
		ok: failed === 0,
		indexed_this_call: indexed,
		failed_this_call: failed,
		// How long this call took, and separately how long the whole run has been
		// going. They diverge sharply on a resumed index.
		call_elapsed_ms: callElapsedMs,
		run_elapsed_ms: runElapsedMs,
		chunk_rate_per_s:
			callElapsedMs > 0 ? Number(((indexed / callElapsedMs) * 1000).toFixed(3)) : null,
		failures,
		...totals,
		pct: totals.total ? Math.round((totals.vectorized / totals.total) * 1000) / 10 : 0,
	};
}

// --------------------------------------------------------------------------- //
// Search: dense + BM25 -> RRF -> rerank
// --------------------------------------------------------------------------- //

interface Hit {
	id: string;
	chapter_id: string;
	heading_path: string;
	text: string;
	score: number;
	dense_rank: number | null;
	bm25_rank: number | null;
	rerank_score: number | null;
	quote_exact: boolean;
	text_quality: string;
}

interface SearchRequest {
	q: string;
	chapter_id?: string;
	class_no?: number;
	subject?: string;
	top_k?: number;
	rerank?: boolean;
	require_quote_exact?: boolean;
}

/**
 * FTS5 MATCH syntax. Terms are extracted rather than passed through, because a
 * raw user query full of quotes, hyphens and colons is a syntax error waiting to
 * happen. The character class must include \p{M}: Devanagari vowel signs are
 * combining marks, so a letters-only class would strip the matras back off and
 * hand the index a mangled query.
 */
function ftsQuery(raw: string): string {
	const terms = raw.toLowerCase().match(/[\p{L}\p{M}\p{N}]+/gu) ?? [];
	const unique = [...new Set(terms)].filter((t) => t.length > 1).slice(0, 12);
	if (unique.length === 0) return "";
	return unique.map((t) => `"${t.replace(/"/g, '""')}"`).join(" OR ");
}

async function search(env: Env, body: SearchRequest): Promise<Response> {
	const query = (body.q ?? "").trim();
	if (!query) return error("q is required");
	const topK = Math.min(Math.max(body.top_k ?? 8, 1), 25);
	const useRerank = body.rerank !== false;

	// --- dense -------------------------------------------------------------- //
	// When class or subject is given, the dense candidates are filtered against
	// D1 below rather than inside Vectorize, so most of them are discarded. A
	// narrow filter (Class 1 is 195 of 12,570 chunks) would otherwise return an
	// almost empty result, so ask for a wider pool to filter down from.
	const filtered = typeof body.class_no === "number" || !!body.subject;
	const denseK = filtered
		? Math.min(FILTERED_VECTOR_K, Math.max(topK * 4, 32))
		: Math.min(MAX_VECTOR_K, Math.max(topK, 10));
	const [queryVector] = await embed(env, [query]);
	const dense = await env.VECTORIZE.query(queryVector, {
		topK: denseK,
		...(body.chapter_id ? { namespace: body.chapter_id } : {}),
		returnMetadata: true,
	});

	// --- lexical ------------------------------------------------------------ //
	const match = ftsQuery(query);
	const filters: string[] = [];
	const binds: unknown[] = [];
	if (body.chapter_id) {
		filters.push("c.chapter_id = ?");
		binds.push(body.chapter_id);
	}
	if (typeof body.class_no === "number") {
		filters.push("c.class_no = ?");
		binds.push(body.class_no);
	}
	if (body.subject) {
		filters.push("c.subject = ?");
		binds.push(body.subject);
	}

	let lexical: StoredHit[] = [];
	if (match) {
		const where = ["chunks_fts MATCH ?", ...filters].join(" AND ");
		const found = await env.CORPUS.prepare(
			`SELECT c.id, c.chapter_id, c.heading_path, c.text, c.text_quality, c.quote_exact
			 FROM chunks_fts
			 JOIN chunks c ON c.rowid = chunks_fts.rowid
			 WHERE ${where}
			 ORDER BY bm25(chunks_fts)
			 LIMIT ?`,
		).bind(match, ...binds, MAX_VECTOR_K).all<StoredHit>();
		lexical = found.results ?? [];
	}

	// --- RRF ---------------------------------------------------------------- //
	// Rank-based, so the BM25 and cosine scales never have to be reconciled.
	const fused = new Map<string, Hit>();
	const touch = (id: string): Hit => {
		let hit = fused.get(id);
		if (!hit) {
			hit = {
				id, chapter_id: "", heading_path: "", text: "", score: 0,
				dense_rank: null, bm25_rank: null, rerank_score: null,
				quote_exact: true, text_quality: "native-text-layer",
			};
			fused.set(id, hit);
		}
		return hit;
	};

	(dense.matches ?? []).forEach((m, i) => {
		const hit = touch(String(m.id));
		hit.dense_rank = i + 1;
		hit.score += 1 / (RRF_K + i + 1);
		hit.chapter_id = String(m.namespace ?? hit.chapter_id);
		const meta = (m.metadata ?? {}) as Record<string, unknown>;
		if (typeof meta.heading_path === "string") hit.heading_path = meta.heading_path;
		if (typeof meta.quote_exact === "number") hit.quote_exact = meta.quote_exact === 1;
		if (typeof meta.text_quality === "string") hit.text_quality = meta.text_quality;
	});

	lexical.forEach((row, i) => {
		const hit = touch(row.id);
		hit.bm25_rank = i + 1;
		hit.score += 1 / (RRF_K + i + 1);
		hit.chapter_id ||= row.chapter_id;
		hit.heading_path ||= row.heading_path;
		hit.text = row.text;
		hit.quote_exact = hit.quote_exact && row.quote_exact === 1;
		hit.text_quality =
			hit.text_quality === "native-text-layer" ? row.text_quality : hit.text_quality;
	});

	// Chunks only the dense side found have no text yet; fetch them in one query
	// rather than letting the reranker score an empty passage.
	//
	// Vectorize cannot filter on class or subject here: its metadata carries only
	// heading_path, quote_exact and text_quality, and adding fields would mean
	// re-upserting all 12,570 vectors, which needs an embedding pass we currently
	// have no neuron budget for. So the dense side is narrowed against D1 instead.
	// `class_no` and `subject` are fetched for that reason and for no other.
	const missing = [...fused.values()].filter((h) => !h.text).map((h) => h.id);
	if (missing.length > 0) {
		const fetched = await env.CORPUS.prepare(
			`SELECT id, chapter_id, heading_path, text, text_quality, quote_exact,
			        class_no, subject
			 FROM chunks WHERE id IN (${missing.map(lit).join(",")})`,
		).all<StoredHit>();
		for (const row of fetched.results ?? []) {
			const hit = fused.get(row.id);
			if (hit) {
				hit.text = row.text;
				hit.chapter_id = row.chapter_id;
				hit.heading_path = row.heading_path;
				hit.text_quality = row.text_quality;
				hit.quote_exact = hit.quote_exact && row.quote_exact === 1;
				// Drop dense-only candidates the caller filtered out, so a
				// `class_no=1` search cannot answer with Class 6 passages.
				if (typeof body.class_no === "number" && row.class_no !== body.class_no) {
					fused.delete(row.id);
					continue;
				}
				if (body.subject && row.subject !== body.subject) {
					fused.delete(row.id);
				}
			}
		}
	}

	let ranked = [...fused.values()].filter((h) => h.text).sort((a, b) => b.score - a.score);

	// Callers that intend to quote the text back to a student cannot use the
	// legacy-decoded chapters, because their glyphs came out of a broken font map.
	// Filtering here, before the reranker, keeps those chunks out of the pool
	// entirely instead of merely demoting them and reporting the count after the
	// fact. Over-fetching the branches first is what keeps the result full when
	// some candidates are unsafe.
	if (body.require_quote_exact) {
		const safe = ranked.filter((h) => h.quote_exact);
		if (safe.length > 0) ranked = safe;
		else ranked = [];
	}

	// --- rerank ------------------------------------------------------------- //
	if (useRerank && ranked.length > 1) {
		const pool = ranked.slice(0, RERANK_POOL);
		try {
			const scores = await rerank(
				env,
				query,
				pool.map((h) => `${h.heading_path}\n${h.text}`.slice(0, RERANK_MAX_CHARS)),
			);
			pool.forEach((h, i) => {
				h.rerank_score = scores[i];
			});
			pool.sort((a, b) => (b.rerank_score ?? -1) - (a.rerank_score ?? -1));
			ranked = [...pool, ...ranked.slice(RERANK_POOL)];
		} catch {
			// A reranker failure degrades to the fused order rather than failing
			// the search: the RRF ranking is already usable on its own.
		}
	}

	const hits = ranked.slice(0, topK);
	const decoded = hits.filter((h) => !h.quote_exact).length;

	return json({
		ok: true,
		query,
		models: { embed: EMBED_MODEL, rerank: useRerank ? RERANK_MODEL : null },
		scope: {
			chapter_id: body.chapter_id ?? null,
			class_no: body.class_no ?? null,
			subject: body.subject ?? null,
		},
		counts: { returned: hits.length, dense: dense.matches?.length ?? 0, lexical: lexical.length },
		// Legacy-decoded chunks come back labelled, never silently mixed in.
		quote_safety: {
			decoded_chunks_in_results: decoded,
			all_quote_exact: decoded === 0,
			required: body.require_quote_exact === true,
		},
		hits,
	});
}

// --------------------------------------------------------------------------- //
// Bookkeeping
// --------------------------------------------------------------------------- //

interface IndexRun {
	run_id: string;
	status: string;
	started_at: string;
	total_chunks: number | null;
	indexed_chunks: number | null;
	embed_batch_size: number | null;
	model: string | null;
	last_error: string | null;
	ingest_offset?: number;
}

async function currentRun(env: Env, runId: "index" | "ingest" = "index"): Promise<IndexRun | null> {
	const row = await env.CORPUS.prepare(`SELECT * FROM index_runs WHERE run_id = ?`)
		.bind(runId)
		.first<IndexRun>();
	return row ?? null;
}

async function corpusCounts(env: Env) {
	const row = await env.CORPUS.prepare(
		`SELECT COUNT(*) AS total,
		        COALESCE(SUM(vectorized), 0) AS vectorized,
		        COALESCE(SUM(CASE WHEN quote_exact = 0 THEN 1 ELSE 0 END), 0) AS decoded
		 FROM chunks`,
	).first<{ total: number; vectorized: number; decoded: number }>();
	const chapters = await env.CORPUS.prepare(
		`SELECT COUNT(DISTINCT chapter_id) AS n FROM chunks`,
	).first<{ n: number }>();
	const total = row?.total ?? 0;
	const vectorized = row?.vectorized ?? 0;
	return {
		total,
		vectorized,
		pending: total - vectorized,
		decoded_chunks: row?.decoded ?? 0,
		chapters: chapters?.n ?? 0,
	};
}

// --------------------------------------------------------------------------- //
// Router
// --------------------------------------------------------------------------- //

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname.replace(/\/+$/, "") || "/";
		const int = (name: string, fallback: number, lo: number, hi: number) => {
			const raw = url.searchParams.get(name);
			const value = raw === null ? fallback : Number(raw);
			return Number.isFinite(value) ? Math.min(Math.max(value, lo), hi) : fallback;
		};

		if (request.method === "GET" && (path === "/" || path === "/health")) {
			// This runtime exposes Vectorize config via describe(), not
			// describeIndexStats(). The authoritative vector count is the D1
			// `vectorized` total: a chunk is only counted there after its upsert
			// returned, so the two numbers agreeing is a real consistency check
			// rather than two views of the same counter.
			let index: Record<string, unknown>;
			try {
				const stats = (await env.VECTORIZE.describe()) as unknown as Record<string, unknown>;
				index = {
					id: stats.id,
					name: stats.name,
					dimensions: stats.dimensions,
					metric: stats.metric,
					vector_count_reported: stats.vectorCount ?? null,
				};
			} catch (err) {
				index = { error: String(err).slice(0, 200) };
			}
			const corpus = await corpusCounts(env);
			return json({
				ok: true,
				models: { embed: EMBED_MODEL, rerank: RERANK_MODEL },
				pack: PACK_KEY,
				corpus,
				index,
				// If these disagree, Vectorize holds vectors D1 does not know about.
				vector_count_agrees:
					typeof index.vector_count_reported === "number"
						? index.vector_count_reported === corpus.vectorized
						: null,
				run: await currentRun(env),
			});
		}

		if (request.method === "POST" && path === "/ingest") {
			const rawOffset = url.searchParams.get("offset");
			return json(
				await ingest(
					env,
					int("max", 4000, 1, 6000),
					rawOffset === null ? undefined : Number(rawOffset),
				),
			);
		}

		if (request.method === "POST" && path === "/index") {
			return json(
				await indexPending(env, int("max", 2000, 1, 4000), int("batch", DEFAULT_EMBED_BATCH, 1, 100)),
			);
		}

		if (request.method === "POST" && path === "/reset-chapters") {
			let chapters: string[];
			try {
				const body = (await request.json()) as { chapters?: unknown };
				chapters = Array.isArray(body.chapters)
					? body.chapters.filter((c): c is string => typeof c === "string" && c.length > 0)
					: [];
			} catch {
				return error(`body must be {"chapters":["id",...]}`);
			}
			if (chapters.length === 0) return error("chapters must be a non-empty array");
			if (chapters.length > 200) return error("at most 200 chapters per call");
			return json(await resetChapters(env, chapters));
		}

		if (request.method === "GET" && path === "/status") {
			return json({ ok: true, corpus: await corpusCounts(env), run: await currentRun(env) });
		}

		if (request.method === "GET" && path === "/chapters") {
			const rows = await env.CORPUS.prepare(
				`SELECT chapter_id, MAX(class_no) AS class_no, MAX(subject) AS subject,
				        MAX(language) AS language, MAX(book_code) AS book_code,
				        MAX(chapter_no) AS chapter_no, COUNT(*) AS chunks,
				        SUM(quote_exact) AS quote_exact_chunks
				 FROM chunks GROUP BY chapter_id ORDER BY chapter_id LIMIT 1000`,
			).all();
			return json({ ok: true, chapters: rows.results ?? [] });
		}

		if (request.method === "POST" && path === "/search") {
			let body: SearchRequest;
			try {
				body = (await request.json()) as SearchRequest;
			} catch {
				return error("body must be JSON");
			}
			return search(env, body);
		}

		return error(`no route for ${request.method} ${path}`, 404);
	},
} satisfies ExportedHandler<Env>;
