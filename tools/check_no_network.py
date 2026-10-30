"""check_no_network.py - Statically verify application package contains ZERO network code.

Inspects Python Abstract Syntax Trees (AST) across the typing_buddy package to detect:
1. Imports of standard or third-party networking modules (socket, urllib, requests, httpx, ssl, etc.).
2. Process/execution escapes: subprocess, os.system, os.popen, webbrowser.
3. Dynamic import invocations: __import__ and importlib.import_module with banned targets.
4. Native Windows networking DLL strings: wininet, winhttp, ws2_32, urlmon.
5. Invocation of os.startfile with web URLs (http://, https://, ftp://).
6. Asyncio networking helpers (open_connection, start_server, streams).

Allows justified exceptions via tools/network_allowlist.txt (kept empty by default).
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Set

BANNED_MODULES = {
    "socket",
    "urllib",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "nntplib",
    "telnetlib",
    "xmlrpc",
    "websocket",
    "websockets",
    "ssl",
    "webbrowser",
    "subprocess",
}

BANNED_STRINGS = {
    "wininet",
    "winhttp",
    "ws2_32",
    "urlmon",
}

URL_PATTERN = re.compile(r"^(?:https?|ftp)://", re.IGNORECASE)


def load_allowlist(allowlist_path: Path) -> Set[str]:
    """Load allowed exception patterns from allowlist file."""
    allowed = set()
    if allowlist_path.exists():
        for line in allowlist_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Take key part before colon if formatted as file:line:reason
                allowed.add(line)
    return allowed


class EnhancedNetworkVisitor(ast.NodeVisitor):
    def __init__(self, filepath: Path, root_dir: Path, allowlist: Set[str]):
        self.filepath = filepath
        self.root_dir = root_dir
        self.rel_path = filepath.relative_to(root_dir).as_posix()
        self.allowlist = allowlist
        self.violations: List[str] = []

    def _is_allowed(self, lineno: int, rule: str) -> bool:
        # Check matching file:lineno or exact rule pattern
        for entry in self.allowlist:
            if entry.startswith(f"{self.rel_path}:{lineno}:") or entry == rule:
                return True
        return False

    def _add_violation(self, node: ast.AST, msg: str):
        lineno = getattr(node, "lineno", 0)
        rule_desc = f"{self.rel_path}:{lineno}: {msg}"
        if not self._is_allowed(lineno, rule_desc):
            self.violations.append(rule_desc)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split(".")[0].lower()
            if base_mod in BANNED_MODULES or alias.name.lower() in BANNED_MODULES:
                self._add_violation(node, f"Prohibited network import 'import {alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0].lower()
            full_mod = node.module.lower()
            if base_mod in BANNED_MODULES or full_mod in BANNED_MODULES:
                self._add_violation(node, f"Prohibited network import 'from {node.module} import ...'")
            elif full_mod == "os":
                for alias in node.names:
                    if alias.name in ("system", "popen"):
                        self._add_violation(node, f"Prohibited process execution import 'from os import {alias.name}'")
            elif full_mod == "asyncio":
                for alias in node.names:
                    if alias.name in ("open_connection", "start_server", "streams"):
                        self._add_violation(node, f"Prohibited asyncio network helper 'from asyncio import {alias.name}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # 1. Dynamic imports: __import__('requests') or importlib.import_module('requests')
        fn_name = ""
        if isinstance(node.func, ast.Name):
            fn_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                fn_name = f"{node.func.value.id}.{node.func.attr}"
            else:
                fn_name = node.func.attr

        if fn_name == "__import__" and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                base_target = first_arg.value.split(".")[0].lower()
                if base_target in BANNED_MODULES:
                    self._add_violation(node, f"Prohibited dynamic import '__import__({first_arg.value!r})'")

        if fn_name in ("importlib.import_module", "import_module") and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                base_target = first_arg.value.split(".")[0].lower()
                if base_target in BANNED_MODULES:
                    self._add_violation(node, f"Prohibited dynamic import '{fn_name}({first_arg.value!r})'")

        # 2. Process execution calls: os.system(...), os.popen(...)
        if fn_name in ("os.system", "system"):
            self._add_violation(node, "Prohibited shell execution 'os.system(...)'")
        if fn_name in ("os.popen", "popen"):
            self._add_violation(node, "Prohibited pipe execution 'os.popen(...)'")

        # 3. os.startfile with URLs
        if fn_name in ("os.startfile", "startfile") and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                if URL_PATTERN.match(first_arg.value.strip()):
                    self._add_violation(node, f"Prohibited os.startfile with network URL: {first_arg.value!r}")

        # 4. Asyncio network calls: asyncio.open_connection, asyncio.start_server
        if fn_name in ("asyncio.open_connection", "asyncio.start_server"):
            self._add_violation(node, f"Prohibited network call '{fn_name}(...)'")

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        # Scan string literals for banned low-level networking DLLs
        if isinstance(node.value, str):
            val_lower = node.value.lower()
            for banned in BANNED_STRINGS:
                # Flag if it references the DLL/library, e.g. "wininet.dll", "wininet", "ws2_32"
                pattern = rf"\b{re.escape(banned)}(?:\.dll)?\b"
                if re.search(pattern, val_lower):
                    self._add_violation(node, f"Prohibited reference to networking library/API '{banned}' in string")
        self.generic_visit(node)


def check_source_tree(package_dir: Path, root_dir: Path, allowlist: Set[str]) -> List[str]:
    violations = []
    for py_file in package_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            visitor = EnhancedNetworkVisitor(py_file, root_dir, allowlist)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except Exception as e:
            violations.append(f"Failed to parse {py_file}: {e}")
    return violations


def main():
    root = Path(__file__).resolve().parent.parent
    pkg_dir = root / "typing_buddy"
    allowlist_file = root / "tools" / "network_allowlist.txt"

    if not pkg_dir.exists():
        print(f"FAIL: Package directory {pkg_dir} does not exist.")
        sys.exit(1)

    allowlist = load_allowlist(allowlist_file)
    violations = check_source_tree(pkg_dir, root, allowlist)

    if violations:
        print("FAIL: Prohibited network, execution, or dynamic import code detected in typing_buddy package:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)

    print("PASS: Application package contains zero network code. Privacy promise verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
