# SITE-Tidings (tidings.family)

## 🔴 Memory store — read this before writing any memory

This project's durable memory lives in **`MEM-AnimumRege`**.

- The live store is `~/.claude/projects/<this-project-slug>/memory/`. Write there; it is mirrored
  to `MEM-AnimumRege` by `VNTR-Perpetua/company/ops/memory/mem-sync.sh --apply`.
- **Write only into THIS project's store.** A session here does not write into another project's
  memory, even when it learns something about that project.
- **A fact goes where it will be NEEDED, not where it was learned.** If you learn something here
  that belongs to another venture, tell that project — do not file it here "for now".
- **One destination per fact.** The same fact in two stores is a defect: they drift, and the next
  reader cannot tell which is current.
- Never hand-edit a `MEM-*` repo. The next sync overwrites it.
- 🔴 Nothing from `MEM-ReevesFamily` may ever be promoted or copied into a business store, in
  either direction.

Record format, size bounds, staleness and archiving: `VNTR-Perpetua/company/ops/memory/README.md`.

Product context: `README.md` here; the app it markets: `APP-Tidings/CLAUDE.md`.
