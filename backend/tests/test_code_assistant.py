"""
Tests for the Code Assistant service: language detection, code extraction,
and system prompt building.
"""
import pytest

from app.services.code_assistant import (
    CodeAssistantService,
    detect_language_from_content,
    detect_language_from_filename,
    extract_code_and_text,
)


# ---------------------------------------------------------------------------
# detect_language_from_filename
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename,expected", [
    ("script.py", "python"),
    ("main.cpp", "cpp"),
    ("index.js", "javascript"),
    ("Component.tsx", "typescript"),
    ("App.ts", "typescript"),
    ("Main.java", "java"),
    ("styles.css", "css"),
    ("page.html", "html"),
    ("query.sql", "sql"),
    ("header.h", "c"),
    ("util.c", "c"),
    ("unknown.xyz", None),
])
def test_detect_language_from_filename(filename, expected):
    assert detect_language_from_filename(filename) == expected


# ---------------------------------------------------------------------------
# detect_language_from_content
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("code,expected", [
    ("def hello():\n    print('world')\n", "python"),
    ("from flask import Flask\nimport os\n", "python"),
    ("#include <iostream>\nusing namespace std;\nint main() { cout << 1; }\n", "cpp"),
    ("public class Main { public static void main(String[] args) {} }\n", "java"),
    ("SELECT name FROM users WHERE id = 1;\n", "sql"),
    ("<html><body><div class='x'>hello</div></body></html>\n", "html"),
    ("const foo = () => console.log('bar');\n", "javascript"),
    ("interface Foo { name: string; age: number; }\n", "typescript"),
])
def test_detect_language_from_content(code, expected):
    result = detect_language_from_content(code)
    assert result == expected


# ---------------------------------------------------------------------------
# extract_code_and_text
# ---------------------------------------------------------------------------

def test_extract_fenced_code_block():
    msg = "Can you explain this code?\n```python\ndef add(a, b):\n    return a + b\n```"
    query, code, lang = extract_code_and_text(msg)
    assert code is not None
    assert "def add" in code
    assert lang == "python"
    assert "explain" in query.lower()


def test_extract_no_code_returns_original():
    msg = "What is the capital of France?"
    query, code, lang = extract_code_and_text(msg)
    assert code is None
    assert lang is None
    assert query == msg


def test_extract_fenced_block_without_lang_tag():
    msg = "Review this:\n```\nSELECT * FROM users;\n```"
    query, code, lang = extract_code_and_text(msg)
    assert code is not None
    assert "SELECT" in code


def test_extract_implicit_code_from_lines():
    code_block = (
        "def foo(x):\n"
        "    for i in range(x):\n"
        "        if i % 2 == 0:\n"
        "            return i\n"
        "    return None\n"
    )
    query, code, lang = extract_code_and_text(code_block)
    assert code is not None
    assert lang == "python"


def test_extract_query_preserved_when_code_present():
    msg = "Debug this:\n```cpp\nint main() {\n    cout << \"Hello\" << endl;\n    return 0;\n}\n```"
    query, code, lang = extract_code_and_text(msg)
    assert "Debug" in query
    assert code is not None
    assert lang == "cpp"


# ---------------------------------------------------------------------------
# CodeAssistantService — system prompt
# ---------------------------------------------------------------------------

def test_code_assistant_builds_system_prompt_with_language():
    svc = CodeAssistantService()
    prompt = svc.build_system_prompt("python")
    assert "Python" in prompt
    assert "NEVER execute" in prompt or "NEVER claim" in prompt or "NEVER" in prompt


def test_code_assistant_builds_system_prompt_without_language():
    svc = CodeAssistantService()
    prompt = svc.build_system_prompt()
    assert len(prompt) > 100  # non-trivial prompt
    assert "ChautiBot" in prompt


def test_code_assistant_prompt_contains_key_directives():
    svc = CodeAssistantService()
    prompt = svc.build_system_prompt("javascript")
    prompt_lower = prompt.lower()
    assert "execute" in prompt_lower
    assert "complexity" in prompt_lower or "big-o" in prompt_lower.replace("–", "-")

