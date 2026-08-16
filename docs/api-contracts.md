# API Contracts (v1)

Base: `/v1`. All request/response bodies JSON. Errors: `{"detail": str}`.

## Search
`POST /v1/search`
```json
{ "query": "photosynthesis light reaction", "limit": 10 }
```
```json
{ "query": "...",
  "hits": [ { "document_id", "page", "heading", "score", "text", "sources" } ] }
```

## Registry
`GET /v1/registry/stats` → `{"count": N}`

## Agents
`POST /v1/agent/doubt` `{ "doubt" }` → answer + citations + evidence
`POST /v1/agent/score` `{ "question", "student_answer", "marks_available" }`
`POST /v1/agent/analyze` `{ "paper_id" }`

## Graph
`POST /v1/graph/neighbors` `{ "node_id", "max_depth" }` → nodes+edges per depth
`POST /v1/graph/paths` `{ "source", "target", "max_depth" }` → edge-type paths

## Health
`GET /health`

## Planned (Phase 4+)
- `GET /v1/documents/{id}` — canonical JSON of a registered document
- `POST /v1/questions/{id}/scheme` — linked answer scheme
- `POST /v1/retrieve/evidence` — evidence bundle for a claim
- `POST /v1/graph/snapshot` / `POST /v1/graph/restore` — versioning
