"""test_check_no_network.py - Unit tests for enhanced static network audit tool."""
import ast
from pathlib import Path

from tools.check_no_network import EnhancedNetworkVisitor


def _check_code(code_str: str, allowlist=None):
    tree = ast.parse(code_str)
    fake_path = Path("typing_buddy/test_sample.py")
    root_dir = Path(".")
    visitor = EnhancedNetworkVisitor(fake_path, root_dir, allowlist or set())
    visitor.visit(tree)
    return visitor.violations


def test_clean_code_passes():
    code = """
import os
import json
import math

def calculate(x):
    return math.sqrt(x)
"""
    violations = _check_code(code)
    assert violations == [], f"Expected clean code to have zero violations, got: {violations}"


def test_prohibited_imports_detected():
    banned_imports = [
        "import socket",
        "import requests",
        "import urllib.request",
        "import httpx",
        "import ssl",
        "import webbrowser",
        "from ftplib import FTP",
        "from os import system",
        "from os import popen",
        "from asyncio import open_connection",
    ]
    for statement in banned_imports:
        violations = _check_code(statement)
        assert len(violations) > 0, f"Expected violation for: {statement}"


def test_dynamic_imports_detected():
    dynamic_cases = [
        "__import__('requests')",
        "__import__('urllib.parse')",
        "import importlib\nimportlib.import_module('socket')",
    ]
    for code in dynamic_cases:
        violations = _check_code(code)
        assert len(violations) > 0, f"Expected violation for dynamic import: {code}"


def test_process_execution_calls_detected():
    cases = [
        "os.system('dir')",
        "os.popen('whoami')",
    ]
    for code in cases:
        violations = _check_code(code)
        assert len(violations) > 0, f"Expected violation for shell execution: {code}"


def test_banned_networking_dll_strings_detected():
    dll_cases = [
        "lib = 'wininet.dll'",
        "target = 'winhttp'",
        "sock_lib = 'ws2_32.dll'",
        "url_mon = 'urlmon.dll'",
    ]
    for code in dll_cases:
        violations = _check_code(code)
        assert len(violations) > 0, f"Expected violation for banned network DLL string: {code}"


def test_startfile_with_url_detected():
    bad_code = "os.startfile('https://github.com')"
    violations = _check_code(bad_code)
    assert len(violations) > 0, "Expected violation for os.startfile with web URL"

    good_code = "os.startfile('C:\\\\local\\\\file.txt')"
    violations = _check_code(good_code)
    assert violations == [], "Local file path in os.startfile should not be flagged"


def test_allowlist_permits_justified_exception():
    code = "import subprocess"
    # Without allowlist -> fails
    assert len(_check_code(code)) > 0

    # With allowlist matching file:lineno
    allowlist = {"typing_buddy/test_sample.py:1: Allowed for test"}
    violations = _check_code(code, allowlist=allowlist)
    assert violations == []
