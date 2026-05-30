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

Write code like Robert C. Martin.

Things NOT to do:
- don't use Any. Instead: set of concrete types
- don't return multiple values. Instead: use a new type
- don't use callbacks. Instead: direct flow with async, await, yield

No `# type: ignore` without a comment explaining why.

Check `docs/status.md` before starting work on a new component — it tracks what is scaffolded versus what still needs to be built.
