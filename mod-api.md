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

## Not in v0
`requestTakeover()` always returns false. The epoch-fenced lock, pub/sub, RPC, tick scheduler and the SPIs of the roadmap (8.3, v1) do not exist yet. Island message bus, compute pool and the other multi-host sharding pieces are gated on the sharding research.

## Compatibility manifest
Besides the API, a mod can ship `data/<modid>/mcmesh_compat.json` (schema in `docs/mcmesh_compat.schema.json`). Applied today: `quarantine_rules.max_tick_micros` and `dimension_policies` `EPHEMERAL_NO_CAS`. A pack author can supply the same file for any mod as `config/mcmesh-compat/<modid>.json`.
