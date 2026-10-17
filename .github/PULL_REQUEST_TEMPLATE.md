## Summary

<!-- Briefly describe what changed and why. -->

## Verification

- [ ] `uv run pytest` passes (including `tests/test_golden.py` and headless GUI tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy rcg` passes
- [ ] `uv run python -m sphinx -W --keep-going -E -b html docs/source docs/_build/html` builds without warnings
- [ ] Documentation (`README.md`, `docs/source/`, NumPy-style docstrings) updated if behavior or public API changed
