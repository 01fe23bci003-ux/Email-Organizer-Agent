from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


class MiniServer:
    CAPABILITIES = [
        {"name": "read_file", "kind": "tool"},
        {"name": "list_files", "kind": "resource"},
    ]
    FILES = {"/safe/notes.txt": "project notes", "/etc/secret.txt": "secret"}

    def call(self, name: str, **arguments: str) -> dict[str, Any] | list[str] | str:
        if name == "list_files":
            directory = arguments.get("path", "/safe")
            return [
                path.rsplit("/", 1)[-1]
                for path in self.FILES
                if path.startswith(directory.rstrip("/") + "/")
            ]
        if name == "read_file":
            requested = arguments.get("path", "")
            normalized = str(PurePosixPath(requested))
            if (
                not normalized.startswith("/safe/")
                or ".." in PurePosixPath(requested).parts
            ):
                return {
                    "error": {
                        "code": "PATH_NOT_ALLOWED",
                        "message": "read_file only permits paths under /safe/",
                    }
                }
            if normalized not in self.FILES:
                return {"error": {"code": "NOT_FOUND", "message": "File not found"}}
            return self.FILES[normalized]
        return {"error": {"code": "UNKNOWN_CAPABILITY", "message": name}}


class MCPClient:
    def __init__(self, server: MiniServer) -> None:
        self.server = server

    def discover(self, kind: str) -> list[str]:
        return [
            capability["name"]
            for capability in self.server.CAPABILITIES
            if capability["kind"] == kind
        ]

    def list_files(self, path: str) -> list[str]:
        resource_name = self.discover("resource")[0]
        result = self.server.call(resource_name, path=path)
        if not isinstance(result, list):
            raise RuntimeError(f"Unexpected resource response: {result}")
        return result

    def read_file(self, path: str) -> dict[str, Any] | str:
        return self.server.call("read_file", path=path)


def main() -> None:
    client = MCPClient(MiniServer())
    resources = client.discover("resource")
    listed = client.list_files("/safe")
    adversarial = client.read_file("/etc/secret.txt")
    assert resources == ["list_files"]
    assert isinstance(adversarial, dict) and "error" in adversarial
    print(f"discovered resources: {resources}")
    print(f"list_files('/safe'): {listed}")
    print(f"adversarial read: {adversarial}")


if __name__ == "__main__":
    main()
