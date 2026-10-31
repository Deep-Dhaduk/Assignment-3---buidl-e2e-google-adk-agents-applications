$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath .venv/Scripts/python.exe)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& ./.venv/Scripts/python.exe -m pip install --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw "Project installation failed" }
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw "Gemini CLI installation failed" }
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
& ./.venv/Scripts/python.exe -m assignment init
if ($LASTEXITCODE -ne 0) { throw "Database initialization failed" }
& ./.venv/Scripts/python.exe -m assignment doctor
