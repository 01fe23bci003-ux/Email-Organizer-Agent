# Assignment 5 — MCP-Style Connector: Mini Integration Layer

Run with `python solution.py`. `list_files` is advertised in the server's
capability registry and selected by the client through discovery. `read_file`
normalizes and restricts paths to `/safe/`. The adversarial `/etc/secret.txt`
request returns a structured error.

## Console output

```text
discovered resources: ['list_files']
list_files('/safe'): ['notes.txt']
adversarial read: {'error': {'code': 'PATH_NOT_ALLOWED', 'message': 'read_file only permits paths under /safe/'}}
```
