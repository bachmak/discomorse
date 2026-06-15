# Claude Code — Project Guide

Aggressively and proactively follow and enforce these guidelines when writing code:
- DRY and SOLID
- stick to OOP in general
- prefer class-based polymorphism instead of if-else-chains and enumerators
- proactively look for ways to use design patterns
- small functions and classes with clear names
- if a function/method is more than 15 lines, refactor
- if a class is more than 100 lines, refactor
- if a file is more than 300 lines, refactor
- no comments unless they explain non-obvious logic

Write code like Robert C. Martin.

Things NOT to do:
- don't use Any. Instead: set of concrete types
- don't return multiple values. Instead: use a new type
- don't use callbacks. Instead: direct flow with async, await, yield

How to write tests:
- write table-driven tests with @pytest.mark.parametrize instead of many isolated test functions with duplicated code.
Example:
```python
@pytest.mark.parametrize("a, b, want", [
    pytest.param(2,  3, 5, id="positive"),
    pytest.param(0,  0, 0, id="zero"),
    pytest.param(-1, 1, 0, id="negative"),
])
def test_add(a, b, want):
    assert add(a, b) == want
```

No `# type: ignore` without a comment explaining why.

Check `docs/status.md` before starting work on a new component — it tracks what is scaffolded versus what still needs to be built.
