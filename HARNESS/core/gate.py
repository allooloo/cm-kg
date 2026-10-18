"""gate.py — the tailings-pond check, one implementation for every estate (Book § 3, ORDER-C02 stage 4).
A field is {value, source_url, read_by, state}. Readers are never sources; the source page settles conflicts.
  two agreeing reads (same value, a source_url on the record) -> verified
  one read with a source_url                                   -> listed
  reads that disagree                                          -> review flag (the Review tab), the field stays as the lead read left it
  a Mistral-only finding                                       -> review flag, never the record
  no source_url                                                -> pond (the record does not enter the store)
Local names kept per estate in the PROGRAM file: agent-bev 'fences' and 'refusals'; Allooloo 'Confirm' (State sourced · filled · confirmed · conflict);
A2A Cosmetics 'labpass' (confirmed · changed · pond); A2A Peptides 'validated'."""
import re

REVIEW_ONLY = {"mistral"}


def norm(v):
    if v is None: return None
    if isinstance(v, (dict, list)): return str(v)
    return re.sub(r"\s+", " ", str(v)).strip().lower()


def gate_field(reads, review_only=REVIEW_ONLY):
    """reads: list of {value, source_url, read_by}. Returns (value, state, flags)."""
    reads = [r for r in reads if r and r.get("value") not in (None, "")]
    if not reads: return None, "absent", []
    sourced = [r for r in reads if r.get("source_url")]
    flags = []
    scoring = [r for r in sourced if (r.get("read_by") or "").split(" ")[0].lower() not in review_only]
    ro = [r for r in sourced if (r.get("read_by") or "").split(" ")[0].lower() in review_only]
    if not scoring:
        if ro: flags.append({"flag": "review-only finding (never the record)", "reads": ro})
        return None, "pond", flags
    values = {}
    for r in scoring: values.setdefault(norm(r["value"]), []).append(r)
    best = max(values.values(), key=len)
    if len(values) > 1: flags.append({"flag": "readers disagree", "values": {k: [x.get("read_by") for x in v] for k, v in values.items()}})
    if ro and norm(ro[0]["value"]) not in values: flags.append({"flag": "review-only reader dissents", "reads": ro})
    state = "verified" if len({(x.get("read_by") or "") for x in best}) >= 2 else "listed"
    return best[0]["value"], state, flags


def gate_record(record, required, review_only=REVIEW_ONLY):
    """record: {field: [reads]} or {field: {value, source_url, read_by, state}}. Returns (out_record, verdict, flags).
    verdict: 'verified' when every required field is verified, 'listed' when every required field is at least listed, 'pond' otherwise."""
    out, flags, states = {}, [], []
    for f, v in record.items():
        reads = v if isinstance(v, list) else [v]
        val, st, fl = gate_field(reads, review_only)
        src = next((r.get("source_url") for r in reads if r and r.get("source_url") and norm(r.get("value")) == norm(val)), None)
        out[f] = {"value": val, "source_url": src, "read_by": sorted({(r.get("read_by") or "") for r in reads if r and norm(r.get("value")) == norm(val)}), "state": st}
        for x in fl: flags.append(dict(x, field=f))
        if f in required: states.append(st)
    if any(s in ("pond", "absent") for s in states): verdict = "pond"
    elif all(s == "verified" for s in states): verdict = "verified"
    else: verdict = "listed"
    return out, verdict, flags


def gate_store(records, required, review_only=REVIEW_ONLY):
    """records: iterable of (record_id, record). Returns counts and the Review tab rows."""
    counts = {"verified": 0, "listed": 0, "pond": 0, "flags": 0}
    review = []
    kept = {}
    for rid, rec in records:
        out, verdict, flags = gate_record(rec, required, review_only)
        counts[verdict] += 1; counts["flags"] += len(flags)
        for fl in flags: review.append(dict(fl, record_id=rid))
        if verdict != "pond": kept[rid] = out
    return counts, review, kept
