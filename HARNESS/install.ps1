# install.ps1 --estate <name> — copy the COMPOUND harness into <estate root>\HARNESS\ beside the existing rail, never over it (ORDER-C02 § Install).
# Writes one line to the estate root's CLAUDE.md (or START_ME_UP\CLAUDE.md where the root keeps its boot file there):
#   "COMPOUND harness installed <date>; the existing rail stays the rail of record until the CEO switches."
# Never deletes. An existing <root>\HARNESS\ is refreshed file by file (new output beside old: a changed file is written, an old file is never removed).
param([Parameter(Mandatory=$true)][string]$estate)
$ErrorActionPreference = 'Stop'
$roots = @{ 'agent-bev' = 'C:\AGENTBEV'; 'allooloo' = 'C:\ALLOOLOO'; 'gsc' = 'C:\GREENCORE'; 'a2a-cosmetics' = 'C:\A2ACOSMETICS'; 'a2a-peptides' = 'C:\A2APEPTIDES'; 'office' = 'C:\MATTHEWKEDDY' }
if (-not $roots.ContainsKey($estate)) { throw "unknown estate $estate" }
$root = $roots[$estate]; $src = $PSScriptRoot; $dst = Join-Path $root 'HARNESS'
$date = Get-Date -Format 'yyyy-MM-dd'
New-Item -ItemType Directory -Force $dst | Out-Null
$copied = 0
Get-ChildItem -Path $src -Recurse -File | Where-Object { $_.FullName -notmatch '\\dryrun\\|\\__pycache__\\|\.pyc$' } | ForEach-Object {
  $rel = $_.FullName.Substring($src.Length).TrimStart('\')
  $to = Join-Path $dst $rel
  New-Item -ItemType Directory -Force (Split-Path $to) | Out-Null
  Copy-Item $_.FullName $to -Force
  $copied++
}
# the installed copy points its ledger and program reads at C:\COMPOUND (the source of record); a marker records the install
"installed $date from $src into $dst; program files and the ledger stay in C:\COMPOUND; the existing rail stays the rail of record" | Out-File -Encoding utf8 (Join-Path $dst 'INSTALLED.txt')
$claude = Join-Path $root 'CLAUDE.md'
if (-not (Test-Path $claude)) { $claude = Join-Path $root 'START_ME_UP\CLAUDE.md' }
$line = "COMPOUND harness installed $date; the existing rail stays the rail of record until the CEO switches. (C:\COMPOUND\HARNESS -> $dst; hunt.py --estate $estate)"
$have = if (Test-Path $claude) { Get-Content $claude -Raw } else { '' }
if ($have -notmatch [regex]::Escape("COMPOUND harness installed $date")) { Add-Content -Path $claude -Value "`n$line" -Encoding utf8 }
Write-Output ("installed {0}: {1} files into {2}; line in {3}" -f $estate, $copied, $dst, $claude)
