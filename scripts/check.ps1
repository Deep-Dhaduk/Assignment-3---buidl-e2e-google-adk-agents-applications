$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& ./.venv/Scripts/python.exe -m ruff check assignment agents tests scripts
if ($LASTEXITCODE -ne 0) { throw "Lint failed" }
& ./.venv/Scripts/python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
