"""check_no_network.py - Verify that the application package contains ZERO network code."""
import ast
import sys
from pathlib import Path

FORBIDDEN_MODULES = {
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
    "asyncio.streams",
}


class NetworkImportVisitor(ast.NodeVisitor):
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in FORBIDDEN_MODULES or alias.name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"{self.filepath}:{node.lineno}: Prohibited network import 'import {alias.name}'"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in FORBIDDEN_MODULES or node.module in FORBIDDEN_MODULES:
                self.violations.append(
                    f"{self.filepath}:{node.lineno}: Prohibited network import 'from {node.module} import ...'"
                )
        self.generic_visit(node)


def check_package(package_dir: Path) -> list[str]:
    violations = []
    for py_file in package_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            visitor = NetworkImportVisitor(py_file)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except Exception as e:
            violations.append(f"Failed to parse {py_file}: {e}")
    return violations


def main():
    root = Path(__file__).resolve().parent.parent
    pkg_dir = root / "typing_buddy"

    if not pkg_dir.exists():
        print(f"FAIL: Package directory {pkg_dir} does not exist.")
        sys.exit(1)

    violations = check_package(pkg_dir)

    # Also check app.py at root if it exists
    root_app = root / "app.py"
    if root_app.exists():
        violations.extend(check_package(root / "app.py").copy() if root_app.is_dir() else [])
        try:
            tree = ast.parse(root_app.read_text(encoding="utf-8"), filename=str(root_app))
            visitor = NetworkImportVisitor(root_app)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except Exception as e:
            violations.append(f"Failed to parse {root_app}: {e}")

    if violations:
        print("FAIL: Prohibited network modules detected in application package:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)

    print("PASS: Application package contains zero network code. Privacy promise verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
