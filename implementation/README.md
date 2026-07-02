# SQLite FastMCP Lab Implementation

This implementation exposes a seeded SQLite database through a FastMCP server with three tools:

- `search`
- `insert`
- `aggregate`

It also exposes schema resources:

- `schema://database`
- `schema://table/{table_name}`

## Setup

```powershell
cd implementation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python init_db.py
```

No API key is required for the local stdio MCP server.

## Run the Server

```powershell
python mcp_server.py
```

MCP clients normally start this command for you over stdio.

## Verify Without a Client

```powershell
python verify_server.py
pytest
```

The verification script demonstrates:

- database initialization
- full schema output
- valid `search`
- valid `insert`
- valid `aggregate`
- one invalid request with a clear error

## Inspector

```powershell
.\start_inspector.ps1
```

In Inspector, verify that:

- tools `search`, `insert`, and `aggregate` are discoverable
- resource `schema://database` is readable
- resource template `schema://table/{table_name}` works with `students`
- invalid calls, such as `search` on `missing_table`, return clear errors

## Example Tool Calls

Search all students in cohort `A1`:

```json
{
  "table": "students",
  "filters": {"cohort": "A1"},
  "order_by": "score",
  "descending": true
}
```

Insert a student:

```json
{
  "table": "students",
  "values": {
    "name": "Minh Do",
    "cohort": "A2",
    "email": "minh.do@example.edu",
    "score": 86.0
  }
}
```

Average score by cohort:

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## Gemini CLI Client Example

Replace the paths with absolute paths on your machine:

```powershell
gemini mcp add sqlite-lab C:\Path\To\implementation\.venv\Scripts\python.exe C:\Path\To\implementation\mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use sqlite-lab to show the top 2 students by score."
```

## Claude Code Client Example

`.mcp.json`:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "C:\\Path\\To\\implementation\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Path\\To\\implementation\\mcp_server.py"],
      "env": {}
    }
  }
}
```

## Codex Client Example

`~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "C:\\Path\\To\\implementation\\.venv\\Scripts\\python.exe"
args = ["C:\\Path\\To\\implementation\\mcp_server.py"]
```
