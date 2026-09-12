# ORDER-018 ADDENDUM — TENANT OF RECORD (CEO, Sept 12 2026)
Recorded verbatim from the CEO's message. The ORDER-018 order file itself (pond to Azure) is not under START_ME_UP; this addendum is the only 018 text on file.

Target:
  Directory     Default Directory (allooloo.com)
  Directory ID  04a24e43-dc13-4578-950a-910db076a799
  Subscription  Azure subscription 1
  Subscription  038b49c0-5a0c-46f7-bd34-41ee6d087b41
  Sign-in       mkeddy@mkeddyallooloo296.onmicrosoft.com (MFA on)

Step 0, before any create: read-only inventory of the subscription — subscriptions visible, resource groups and their state, quotas for Container Apps and Storage in each of the eleven target regions. Report it as the first line of the 018 report.

Context: the subscription is being cleared by the CEO — ten legacy resource groups from the pre-Next-Gen proving ground are deleting now. Anything still showing as "Deleting" is not yours to touch or wait on. Create your own resource groups with your own names; the old ones are out of scope even if they're still on the list.

If az login to this directory needs an interactive MFA step, that is HITL line one: say so and continue with what doesn't need it.

## Standing rules applied
- Allooloo Azure tenant rule: `az login --tenant 04a24e43-dc13-4578-950a-910db076a799` then `az account show` before any Azure change; a tenant or subscription mismatch is a STOP.
- Never touch, wait on, or name-collide with the legacy resource groups; Allooloo resource groups carry their own names (`allooloo-cmkg-<region>` shape proposed at Step 1).
- Step 0 is read-only: `az account list`, `az group list` (with provisioning state), `az containerapp env list` / usage, `az storage account list`, and the Container Apps and Storage quotas per target region.
