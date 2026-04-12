---
name: cli-api-recon
version: 1.0.0
description: >-
  Map an API surface — endpoints, schemas, rate limits, pagination patterns.
  Use when exploring an API, reverse-engineering endpoints, parsing OpenAPI specs,
  mapping a GraphQL schema, discovering gRPC methods, or preparing API data for CLI generation.
metadata:
  requires:
    skills: []
---

# CLI API Recon

Map an API surface completely before generating a CLI. Produces an `endpoints.json` that the CLI
generator and cli-architect skill consume.

---

## When to Use

**Trigger phrases:** "map the API", "what endpoints does X have", "discover endpoints", "reverse engineer API",
"parse OpenAPI spec", "explore API surface", "what methods does this service have", "API recon",
"scan endpoints", "find API methods", "what can this API do"

**Scenarios:**
- About to generate a CLI and need the full endpoint inventory
- Exploring an unfamiliar API or service
- Validating that a generated CLI covers the full API surface
- Building an agent workflow and need to know what operations are available

---

## Strategy by Input Type

| Input | Strategy |
|-------|----------|
| **Docs available** (OpenAPI, GraphQL schema, .proto, API reference URL) | Parse docs first. Build `endpoints.json` from spec. Skip probing unless coverage is incomplete. |
| **Docs + running service** | Parse docs for the baseline. Probe the running service to discover undocumented endpoints, validate response schemas, and capture pagination/rate-limit behavior. |
| **Running service only** (no docs) | Reverse-engineer: crawl the base URL, probe common path patterns, capture network traffic via CDP if the service has a web UI. |
| **Raw endpoint list** | Treat the list as a partial spec. Validate each endpoint, probe for parameters and response schema, then enrich to full `endpoints.json` format. |

---

## Endpoint Discovery Methods

### OpenAPI / Swagger

1. Fetch the spec: try `/openapi.json`, `/swagger.json`, `/api-docs`, `/v1/openapi.yaml`
2. Parse `paths` — extract method, path, summary, parameters, requestBody, responses
3. Parse `components.schemas` — extract all referenced models
4. Parse `components.securitySchemes` — hand off to `cli-auth-recon`
5. Capture `info.x-rateLimit` or any vendor extension for rate limits
6. Note pagination hints: `x-pagination`, cursor fields in response schemas, Link headers

### GraphQL

1. Run introspection query:
   ```graphql
   { __schema { queryType { fields { name description args { name type { name kind } } } }
               mutationType { fields { name description args { name type { name kind } } } }
               subscriptionType { fields { name description } } } }
   ```
2. Extract queries, mutations, and subscriptions with argument types
3. Note any custom directives that affect rate limiting or auth (`@auth`, `@rateLimit`)
4. Map to `endpoints.json` using `method: "QUERY"`, `"MUTATION"`, or `"SUBSCRIPTION"`

### gRPC / Protobuf

1. Locate `.proto` files in the repo, or fetch via gRPC server reflection: `grpc_cli ls <host>`
2. Parse each `.proto` — extract services, RPCs, request/response message types
3. Note streaming patterns: `stream` keyword on request or response
4. Map to `endpoints.json` using `method: "RPC"`, with `proto_service` and `proto_method` fields

### Web URL (no docs)

1. `GET <base_url>/` — parse links, forms, script sources for API path hints
2. Probe common prefixes: `/api/`, `/v1/`, `/v2/`, `/graphql`, `/rest/`, `/services/`
3. If the service has a browser UI, use CDP to capture network traffic:
   - Attach to Edge browser profile
   - Navigate through the UI while recording XHR/fetch calls
   - Capture method, URL, request headers, response status and body shape
4. Try `GET <base_url>/.well-known/openapi` and `/.well-known/api-catalog`
5. Check response headers for `Link: <url>; rel="describedby"` (RFC 8631)

### SDK / Client Library

1. Locate public method declarations in the SDK source or type definitions
2. Extract method names, parameter types, return types from TypeScript `.d.ts`, Python stubs, or Java interfaces
3. Map each public method to a likely HTTP endpoint using naming conventions
4. Use the SDK's own docs or source comments for descriptions

---

## Output Schema

Write to `endpoints.json` in the working directory.

```json
{
  "service": "example-api",
  "base_url": "https://api.example.com/v1",
  "spec_source": "openapi",
  "spec_url": "https://api.example.com/v1/openapi.json",
  "endpoints": [
    {
      "method": "GET",
      "path": "/users",
      "operation_id": "listUsers",
      "description": "List all users with optional filtering.",
      "params": {
        "query": [
          { "name": "limit", "type": "integer", "required": false, "default": 20 },
          { "name": "cursor", "type": "string", "required": false }
        ],
        "path": [],
        "header": []
      },
      "request_body": null,
      "response_schema": {
        "type": "object",
        "properties": {
          "users": { "type": "array", "items": { "$ref": "#/models/User" } },
          "next_cursor": { "type": "string" }
        }
      },
      "pagination": {
        "type": "cursor",
        "cursor_field": "next_cursor",
        "param_name": "cursor"
      },
      "auth_required": true,
      "rate_limit": { "requests_per_minute": 60, "header": "X-RateLimit-Remaining" },
      "tags": ["users"]
    }
  ],
  "models": {
    "User": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "email": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" }
      }
    }
  },
  "rate_limits": {
    "global": { "requests_per_minute": 600 },
    "per_endpoint": {}
  },
  "coverage": {
    "total_endpoints": 12,
    "documented": 12,
    "probed": 8,
    "undocumented_discovered": 1
  }
}
```

**Endpoint field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `method` | Yes | HTTP verb, or `QUERY`/`MUTATION`/`SUBSCRIPTION`/`RPC` for non-REST |
| `path` | Yes | URL path template (`:id` or `{id}` notation) |
| `operation_id` | No | Unique operation name — used as CLI command name if available |
| `description` | No | Human-readable summary |
| `params.query` | No | Query string parameters with types and defaults |
| `params.path` | No | Path parameters |
| `params.header` | No | Required request headers (non-auth) |
| `request_body` | No | JSON schema for request body |
| `response_schema` | No | JSON schema for successful response |
| `pagination` | No | Pagination type and field names (see Enrichment section) |
| `auth_required` | Yes | Whether this endpoint requires authentication |
| `rate_limit` | No | Per-endpoint rate limit if different from global |
| `tags` | No | Grouping tags — used to cluster endpoints into CLI resources |

---

## Enrichment

After initial discovery, probe live endpoints to fill gaps. Do this only when a running service is available.

### What to Capture

| Signal | How to Get It | Why It Matters |
|--------|--------------|----------------|
| **Actual response schema** | `GET /endpoint` with valid auth, inspect body | Docs are often stale or incomplete |
| **Pagination pattern** | Make paginated request, inspect response for cursor/token/link | CLI needs to auto-paginate correctly |
| **Rate limit headers** | Inspect `X-RateLimit-*`, `RateLimit-*`, `Retry-After` headers | CLI retry/throttle logic |
| **Error response format** | Trigger a 400/404, inspect error body shape | CLI error handler needs to parse this |
| **Response time baseline** | Time 3-5 requests to each endpoint | Helps set timeout defaults |
| **Undocumented fields** | Compare live response to documented schema | May expose useful data the docs omit |

### Pagination Pattern Classification

| Type | Signals | `endpoints.json` value |
|------|---------|------------------------|
| Cursor | `next_cursor`, `cursor`, `after` in response body | `"type": "cursor"` |
| Offset | `offset` + `limit` params, `total` in response | `"type": "offset"` |
| Page token | `pageToken`, `nextPageToken` (Google-style) | `"type": "page_token"` |
| Link header | `Link: <url>; rel="next"` response header | `"type": "link_header"` |
| None | Single response, no continuation mechanism | `null` |

### Enrichment Output

Add probed data alongside documented data. Use separate fields to distinguish source:

```json
{
  "response_schema": { ... },
  "response_schema_probed": { ... },
  "response_schema_diff": ["field 'undocumented_flag' present in live, missing from spec"]
}
```

This lets the CLI generator flag spec drift without discarding the official schema.
