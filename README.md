# mcmesh-docs

Official specifications, API schemas, and developer documentation for [mcmesh](https://github.com/mcmeshsolutions) — serverless shared Minecraft worlds with automatic host failover and content-addressed storage.

---

## Contents

| File | Description |
|---|---|
| [`openapi.json`](./openapi.json) | Complete **OpenAPI 3.0.3** specification for `gatewayd` HTTP REST & SSE endpoints (tested in CI against the live Axum router) |
| [`mod-api.md`](./mod-api.md) | Developer documentation for `dev.mcmesh.api` (`MeshApi`, `MeshWorld`, `MeshEvent`, `MeshRole`, `MeshState`) |
| [`mcmesh_compat.schema.json`](./mcmesh_compat.schema.json) | JSON Schema for `META-INF/mcmesh_compat.json` declarative mod state synchronization rules |
| [`marketing.html`](./marketing.html) | Self-contained product overview, architecture breakdown, and community reference page |
| [`marketing-strategy.html`](./marketing-strategy.html) | Go-to-market and community rollout plan |

---

## Architecture Overview

1. **`gatewayd` ([mcmeshsolutions/gatewayd](https://github.com/mcmeshsolutions/gatewayd)):**
   - Stores world revisions as content-addressed SHA-256 blobs (`cas/`) with Ed25519 host signatures and tamper-evident hash chains.
   - Coordinates host leases (`epoch`-fenced), failover elections, and multi-tenant world quotas.
   - Relays guest connections (`:25565` TCP) and Simple Voice Chat (`:24454` UDP) when direct P2P hole-punching is unavailable.
   - Replicates hot SQLite WAL snapshots and CAS blobs asynchronously to S3 / Cloudflare R2 / MinIO.
2. **`mod` ([mcmeshsolutions/mod](https://github.com/mcmeshsolutions/mod)):**
   - Syncs changed chunks and auxiliary mod files before hosting.
   - Streams delta WAL frames during gameplay and executes zero-disconnect handovers when the host exits.

---

## Using the OpenAPI Spec

You can inspect or generate typed clients from `openapi.json` using Swagger UI, Redoc, or OpenAPI Generator:

```bash
# Preview locally with npx @redocly/cli
npx @redocly/cli preview-docs openapi.json
```

All endpoints in `openapi.json` are continuously verified against the `gatewayd` router to guarantee zero drift between documentation and implementation.
