# STANDING RULE — build machine, Azure CLI: one root at a time (CEO, Sept 13 2026)

1. **One root at a time on the Azure CLI.** The machine's `az` default context belongs to one estate at a time: Allooloo (`C:\ALLOOLOO`) or GreenCore (`C:\GREENCORE`).
2. **Before any Azure write, every rail on either root confirms tenant, subscription and signed-in user match its own estate, and stops if not.** No write on a mismatch, no "set it and continue" inside a rail.
3. **When switching roots, the thread that takes over sets the CLI context first and reports it** (tenant, subscription, user) in its own report before its first Azure call.
4. Logged in both roots' start-me-up folders: this file, and `C:\GREENCORE\START_ME_UP\AZURE-CLI-ONE-ROOT-RULE.md` (same text).

## Allooloo estate of record

- Tenant `04a24e43-dc13-4578-950a-910db076a799` · subscription `038b49c0-5a0c-46f7-bd34-41ee6d087b41` ("Azure subscription 1") · user `mkeddy@mkeddyallooloo296.onmicrosoft.com`.
- Guard for rails: `C:\ALLOOLOO\AZURE\az_guard.py` — `from az_guard import require_allooloo; require_allooloo()` at the top of every rail that writes; it reads `az account show`, compares tenant, subscription and user, prints the three on match and raises `SystemExit` on any mismatch. Existing rails (`apic_listings.py`, `apic_descriptions.py`, `provision_region.py` family) carry the same check inline.
- Taking the CLI back for Allooloo without a browser: `az account set --subscription 038b49c0-5a0c-46f7-bd34-41ee6d087b41` then `az account show` (the Allooloo token stays cached after the first `az login --tenant 04a24e43…`).

## Why (the incident)

On Sept 13 2026 the CLI context was found switched to the GreenCore tenant (a `mk@gsc-em.com` login from another window) two hours after a clean Allooloo run. The Allooloo rail's tenant assert stopped before any write; the context was set back and reported, then the writes ran. Nothing landed in the wrong estate.
