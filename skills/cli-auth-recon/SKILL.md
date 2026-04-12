---
name: cli-auth-recon
version: 1.0.0
description: >-
  Discover authentication mechanism for an API. Use when figuring out how an API authenticates,
  what auth type a service uses, discovering OAuth2 endpoints, checking for API keys,
  or preparing to wrap an authenticated API in a CLI.
metadata:
  requires:
    skills: []
---

# CLI Auth Recon

Autonomously discover how an API authenticates before generating a CLI. Produces an `auth-profile.json`
that the CLI generator consumes — never storing actual secrets.

---

## When to Use

**Trigger phrases:** "figure out auth", "how does this API authenticate", "discover auth", "what auth does X use",
"OAuth endpoints for X", "find API key", "prepare auth for CLI", "auth recon", "check auth mechanism"

**Scenarios:**
- About to wrap an API in a CLI and don't know the auth type
- Reverse-engineering a service's authentication from browser sessions or docs
- Generating the `auth` command tree for a new CLI
- Validating whether an existing credential will work

---

## Resolution Order

Run these steps in order. Stop at the first successful discovery.

| Step | Method | What You're Looking For |
|------|--------|------------------------|
| 1 | Edge browser profile cookies (CDP) | Active session cookies, Bearer tokens in XHR requests |
| 2 | Env vars, config files, keyrings | `*_TOKEN`, `*_KEY`, `*_SECRET`, `~/.config/<service>`, OS keyring entries |
| 3 | OpenAPI `securitySchemes` | Auth type declared in spec: `bearerAuth`, `apiKey`, `oauth2`, `http/basic` |
| 4 | Cloud provider configs | `~/.aws/credentials`, `~/.azure/`, `~/.kube/config`, `gcloud auth list` |
| 5 | Unauthenticated probe | `GET /` or `GET /health` — check `WWW-Authenticate` header on 401 response |

If all 5 steps fail to determine auth, write `auth-blocked.json` (see Fallback section).

---

## Supported Auth Types

| Auth Type | Discovery Strategy | Automated? |
|-----------|-------------------|------------|
| **Bearer token** | Check env vars (`*_TOKEN`, `*_ACCESS_TOKEN`), CDP network tab for `Authorization: Bearer` headers | Yes |
| **API key** | Check env vars (`*_API_KEY`, `*_KEY`), OpenAPI `apiKey` securityScheme, request headers/query params | Yes |
| **Cookie** | CDP network tab for `Cookie` headers, Edge profile cookies for target domain | Yes |
| **HTTP Basic** | OpenAPI `http/basic` securityScheme, `WWW-Authenticate: Basic` on 401 probe | Yes |
| **OAuth2 manual flow** | OpenAPI `oauth2` securityScheme, `.well-known/openid-configuration` endpoint | Partial — requires user browser action for consent |
| **AWS SigV4** | `~/.aws/credentials`, env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) | Yes |
| **Azure AD** | `~/.azure/` (az CLI profile), env vars (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`) | Yes |
| **mTLS** | Check for `.pem`/`.pfx`/`.crt` files, env vars (`*_CERT_PATH`, `*_KEY_PATH`), service configuration | Yes (cert detection); No (cert provisioning) |
| **Custom headers** | CDP network tab — capture non-standard headers on authenticated requests (e.g., `X-Api-Key`, `X-Auth-Token`) | Yes |
| **SAML** | Browser redirect to IdP SSO URL, presence of `SAMLResponse` in POST bodies via CDP | No — document redirect URL only |
| **No auth** | Unauthenticated probe returns 200; no `WWW-Authenticate` header on any endpoint | Yes |

---

## OAuth2 Manual Flow

Use this pattern (inspired by gogcli) when the API uses OAuth2 and no cached tokens exist.

### Steps

1. **Discover OAuth2 endpoints**
   - Parse OpenAPI `securitySchemes` for `authorizationUrl` and `tokenUrl`
   - Try `GET <base_url>/.well-known/openid-configuration`
   - Extract: `authorization_endpoint`, `token_endpoint`, `scopes_supported`

2. **Determine required scopes**
   - From OpenAPI `security` blocks on relevant endpoints
   - From API docs if available
   - Default to the minimum scope set that covers the CLI's command surface

3. **Generate the auth URL**
   ```
   https://<authorization_endpoint>
     ?response_type=code
     &client_id=<client_id>
     &redirect_uri=<redirect_uri>
     &scope=<space-separated scopes>
     &state=<random 32-char hex>
     &code_challenge=<S256 PKCE challenge>
     &code_challenge_method=S256
   ```

4. **Present URL to user**
   - Print to stderr: `Open this URL in any browser to authenticate:`
   - Print the full URL
   - Do NOT attempt to open the browser programmatically (corp device restrictions)

5. **User pastes redirect URL back**
   - Prompt: `Paste the redirect URL after authentication:`
   - Parse `code` and `state` parameters from the pasted URL
   - Validate `state` matches what was generated

6. **Exchange code for tokens**
   - `POST <token_endpoint>` with `grant_type=authorization_code`, `code`, `redirect_uri`, PKCE verifier
   - Extract `access_token`, `refresh_token`, `expires_in`

7. **Store credential reference (never the token itself)**
   - Write `refresh_token` to OS keyring: `keyring set <service-name> refresh_token`
   - Record the keyring reference in `auth-profile.json`
   - Never write the raw token to disk

8. **Document auto-refresh in auth-profile.json**
   - Record `token_endpoint`, `expires_in`, credential source reference
   - The generated CLI's auth module reads this profile to implement token refresh

---

## Auth Profile Output

Write to `auth-profile.json` in the working directory. This file is consumed by the CLI generator.

**Schema:**

```json
{
  "auth_type": "bearer_token",
  "credential_source": {
    "type": "env_var",
    "var_name": "EXAMPLE_API_TOKEN",
    "fallback": "keyring:example-api"
  },
  "header": "Authorization",
  "prefix": "Bearer",
  "refresh": {
    "type": "oauth2_refresh",
    "endpoint": "/oauth/token",
    "expires_in": 3600
  },
  "discovery_method": "edge_profile_cookies",
  "notes": "Auth discovered via Edge browser profile."
}
```

**Field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `auth_type` | Yes | One of: `bearer_token`, `api_key`, `cookie`, `basic`, `oauth2`, `aws_sigv4`, `azure_ad`, `mtls`, `custom_header`, `saml`, `none` |
| `credential_source.type` | Yes | Where the credential lives: `env_var`, `keyring`, `config_file`, `cloud_provider_cli`, `none` |
| `credential_source.var_name` | Conditional | Env var name (when `type = env_var`) |
| `credential_source.fallback` | No | Secondary source if primary is missing |
| `header` | Conditional | HTTP header name (for `bearer_token`, `api_key`, `custom_header`) |
| `prefix` | Conditional | Value prefix, e.g. `"Bearer"`, `"Token"` |
| `query_param` | Conditional | Query parameter name (when API key goes in URL, not header) |
| `refresh` | No | Token refresh configuration |
| `refresh.type` | Conditional | `oauth2_refresh`, `none` |
| `refresh.endpoint` | Conditional | Full URL or path for token refresh |
| `refresh.expires_in` | Conditional | Token TTL in seconds |
| `discovery_method` | Yes | Which of the 5 resolution steps succeeded |
| `notes` | No | Free-form notes for the CLI generator or human reviewer |

**Security rules:**
- NEVER write actual tokens, secrets, or passwords to `auth-profile.json`
- NEVER log credential values to stdout or stderr
- Keyring references use the format `keyring:<service-name>` — not the credential value

---

## Fallback

When all 5 resolution steps fail, write `auth-blocked.json`:

```json
{
  "status": "blocked",
  "reason": "Could not determine auth mechanism autonomously.",
  "tried": [
    "edge_profile_cookies",
    "env_vars_config_files",
    "openapi_security_schemes",
    "cloud_provider_configs",
    "unauthenticated_probe"
  ],
  "needs": {
    "auth_type": "unknown — please specify: bearer_token | api_key | oauth2 | basic | aws_sigv4 | azure_ad | mtls | custom_header | none",
    "credential_source": "unknown — where should the CLI read credentials from?",
    "oauth2_client_id": "required if auth_type=oauth2",
    "oauth2_scopes": "required if auth_type=oauth2"
  },
  "next_step": "Provide the missing fields above. The orchestrator will re-run auth-recon with this input."
}
```

Write `auth-blocked.json` with the details above. If you have the `AskUserQuestion` tool available (e.g., when dispatched as a subagent), prompt the user directly for the missing fields. Otherwise, surface the file to the orchestrator and let it handle the user interaction.
