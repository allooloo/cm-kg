# HARNESS — the COMPOUND hunt harness (ORDER-C02, cut 2026-09-29)

One hunt codebase, estate as a parameter. PADEL's harness is the pattern: one codebase, keys read from the estate's own vault at launch, never copied, never printed.

```
hunt.py --estate <name> --week 2026-Wnn --scope <scope-id> [--stage width0|width1|fill|gate|land|check|all] [--dry-run] [--live] [--out <folder>]
install.ps1 --estate <name>        copy into <estate root>\HARNESS\ beside the existing rail, never over it; one line in the root's CLAUDE.md
core\program.py    PROGRAM\<estate>.md reader: sections, tables, scope block (id, go), engine roles, published totals, extras
core\vault.py      vault and login-directory pointers per estate (STARTHERE rows); key(lab, estate); nothing written
core\engines.py    the laboratory clients (Sonar = Perplexity Agent API, Grok, OpenAI, Gemini, Mistral, Tavily), metered; refuse to call unless --live; exhausted → skipped
core\gate.py       the tailings-pond check: two agreeing reads → verified; one → listed; disputes → Review tab; Mistral-only → flag; readers never sources
core\pond.py       dated immutable drops; scratch copies for dry runs under HARNESS\dryrun\
core\land.py       the landing lock, byte compare, the dated lock entry, the landing event data; published totals never touched
core\check.py      PADEL as a library call (live: PADEL's own sweep.py/report.py/pack.py through its venv; dry: the newest sealed pack)
core\weekfolder.py the week-folder contract writer (LEDGER-SCHEMA § 5) and the ledger event writer (signed with the rail's kid, else unsigned)
adapters\<estate>\adapter.py   only where the estate's sources need it: agent-bev, allooloo, gsc, a2a-cosmetics, a2a-peptides, office
```

Three constants on every estate, every week: width0 (new participants), fill + gate (missing pages and fields on records held), check (PADEL and the edge instrument). The flavour lives in PROGRAM\<estate>.md and nowhere else.

Rules bound here: no lab call in a dry run; no pause prompt; a lab out of credit is marked exhausted and skipped; non-interactive everywhere (CI=1, no wrangler prompts, each root's own AZURE_CONFIG_DIR and GH_CONFIG_DIR); never delete; the existing rail stays the rail of record until the CEO switches on the equivalence report; a landing that would change a published total writes a QUESTION line and stops that surface's update.

Dry-run outputs land in HARNESS\dryrun\<week>\<estate>\ (the week-folder contract) and are closed out with `closeout.py --estate <name> --week <week> --folder <that folder> --dry-run`.
