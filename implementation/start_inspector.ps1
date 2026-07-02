$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $root "mcp_server.py"
$python = Join-Path $root ".venv\Scripts\python.exe"
$env:MCP_SERVER_REQUEST_TIMEOUT = "300000"
$env:MCP_REQUEST_TIMEOUT = "300000"
npx.cmd -y @modelcontextprotocol/inspector $python $server
