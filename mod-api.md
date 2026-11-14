# mcmesh mod API, v0

Module `mod/api` (package `dev.mcmesh.api`, Java 21, no dependencies). A mod depends on it at compile time and bundles it (NeoForge `jarJar`). `MeshApi.current()` never returns null and never throws: when the mcmesh mod is not installed every call is a harmless no-op, so using the API does not make your mod depend on mcmesh.

```java
MeshApi api = MeshApi.current();
api.mode();                       // STANDALONE_LOCAL, MESH_HOST (MESH_GUEST and GHOST_READONLY are reserved)
api.worldId();                    // null when not in a mesh world
api.peers();                      // members with role and CPU benchmark score; blocks on the network, cached 30 s
api.addListener(new MeshListener() {
    public void preMigrate(String target) { }   // the gateway asked this host to give the world away
    public void postPromote(String worldId) { } // this machine just became the host
    public void roleChanged(SessionMode from, SessionMode to) { }
});
```

## Storage that travels with the world
`api.aux()` is a key-value store (scopes WORLD_GLOBAL, TEAM, PLAYER_PRIVATE; namespace and key are 1 to 64 characters of `a-z 0-9 . _ -`). Values are files under `<world>/mesh/aux/<scope>/<namespace>/<key>`, so they reach the gateway with every save and every later host has them.

`api.state().register(id, snapshot, restore)` is for in-memory state that must survive a handover. The mesh calls `snapshot` before every autosave and before the final save and writes the bytes to `<world>/mesh/state/<id>.bin`; the next host calls `restore` with them after the world has loaded. A failing mod never blocks a save.

`api.revisions()` reads history from the gateway without booting a world (`revisionIds(limit)`, `readAux(revisionId, path)`); these block, never call them on the server thread.

## v1 pieces that exist
`api.locks()` gives named locks kept by the gateway and fenced by the host epoch: `tryLock(owner, name, ttl)` returns a `Held` with a fence token or nothing (somebody else holds it, this machine is not the host, the gateway is unreachable); calling it again as the same owner renews and keeps the token; `unlock(owner, name)` frees it. A lock taken under an older epoch is void, so a new host never waits for a lock that a dead host held, and the token grows every time a lock changes hands: a service fed by two hosts should refuse the smaller token. Names and owners are 1 to 64 characters of `a-z 0-9 . _ -` (use your mod id as the owner). Calls block on the network: not on the server thread. Over HTTP: `POST /v1/leases/:id/lock` and `/unlock` (lease holder only), `GET /v1/worlds/:id/locks` (members).

`api.scheduler().submit(runnable)` runs work on the server thread, in order, under a per-tick budget: 2 ms when the host is healthy, 0.5 ms when it has started shedding load, nothing while it sheds heavily. At least one task runs per tick when there is budget. A task that throws is logged and skipped.

## Not built
`requestTakeover()` always returns false: asking a stronger machine to take hosting needs a server that can start on the asking machine, which today only the Synced Worlds screen and the anchor service do. Pub/sub, RPC, synced variables and the tunnel API are not built: with one host at a time there is no remote peer for a mod to call, and the game's own networking already covers host and players. They come back when multi-host sharding is proven. The SPIs (`MeshAuthProvider`, `MeshElectionPolicy`, `MeshQuarantineHandler`, `MeshTransportProvider`) are not built either, because they would let a mod change who may host or who may log in, which needs a security review first. Island message bus, compute pool and the other multi-host sharding pieces are gated on the sharding research.
## Compatibility manifest
Besides the API, a mod can ship `data/<modid>/mcmesh_compat.json` (schema in `docs/mcmesh_compat.schema.json`). Applied today: `quarantine_rules.max_tick_micros` and `dimension_policies` `EPHEMERAL_NO_CAS`. A pack author can supply the same file for any mod as `config/mcmesh-compat/<modid>.json`.
