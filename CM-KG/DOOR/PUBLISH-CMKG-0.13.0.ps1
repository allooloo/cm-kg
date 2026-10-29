# LIST-02 (2026-10-26): publish io.github.allooloo/cm-kg 0.13.0 (server.json re-cut from the live roster: 34 markets; validated against the registry).
# The registry needs a GitHub device login for the io.github.allooloo namespace (the stored token expired). Run in PowerShell:
#   1. the login prints a code: open https://github.com/login/device, sign in as allooloo, enter the code, authorise
#   2. the publish runs straight after
Set-Location C:\ALLOOLOO\CM-KG\DOOR
.\.tools\mcp-publisher.exe login github
if ($LASTEXITCODE -eq 0) { .\.tools\mcp-publisher.exe publish }
