$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$fastmcp = Join-Path $root ".venv\Scripts\fastmcp.exe"
& $fastmcp dev inspector mcp_server.py --server-port 6277 --ui-port 6274 --no-reload
