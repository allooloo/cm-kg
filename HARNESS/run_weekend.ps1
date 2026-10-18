# run_weekend.ps1 -estate <name> -step hunt|closeout — the action behind the Windows tasks "COMPOUND weekend hunt <estate>" (Friday 22:00 local)
# and "COMPOUND weekend closeout <estate>" (Sunday 18:00 local), installed DISABLED by ORDER-C04 Part B. Arm/disarm: C:\COMPOUND\schedule.ps1.
# Non-interactive; the estate root's own AZURE_CONFIG_DIR and GH_CONFIG_DIR are set by the harness (core\vault.py); logs to the week folder.
# The week is the ISO week of the run; the scope id comes from PROGRAM\<estate>.md § Standing scope; no go in the scope block → hunt.py writes
# a "no go" note and exits 0; closeout still runs and signs a statement with a zero-spend books section and the checks.
param([Parameter(Mandatory=$true)][string]$estate, [Parameter(Mandatory=$true)][ValidateSet('hunt','closeout')][string]$step)
$ErrorActionPreference = 'Continue'
$py = 'C:\Users\matth\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$compound = 'C:\COMPOUND'
$env:CI = '1'; $env:WRANGLER_SEND_METRICS = 'false'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$d = Get-Date
$cal = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$dow = [int]$d.DayOfWeek; if ($dow -eq 0) { $dow = 7 }
$thursday = $d.AddDays(4 - $dow)
$week = '{0}-W{1:D2}' -f $thursday.Year, $cal.GetWeekOfYear($thursday, [System.Globalization.CalendarWeekRule]::FirstFourDayWeek, [System.DayOfWeek]::Monday)
$wf = Join-Path $compound "$week\$estate"; New-Item -ItemType Directory -Force (Join-Path $wf 'evidence') | Out-Null
$log = Join-Path $wf ("evidence\weekend-$step-" + $d.ToString('yyyy-MM-dd') + '.log')
"weekend $step $estate $week start $($d.ToString('yyyy-MM-dd'))" | Tee-Object -FilePath $log -Append
if ($step -eq 'hunt') {
  $scope = (Select-String -Path (Join-Path $compound "PROGRAM\$estate.md") -Pattern '^\s*-?\s*id:\s*(.+)$' | Select-Object -First 1).Matches[0].Groups[1].Value.Trim()
  & $py (Join-Path $PSScriptRoot 'hunt.py') --estate $estate --week $week --scope $scope --stage all --live 2>&1 | Tee-Object -FilePath $log -Append
} else {
  & $py (Join-Path $compound 'closeout.py') --estate $estate --week $week 2>&1 | Tee-Object -FilePath $log -Append
}
"weekend $step $estate $week done $((Get-Date).ToString('yyyy-MM-dd'))" | Tee-Object -FilePath $log -Append
