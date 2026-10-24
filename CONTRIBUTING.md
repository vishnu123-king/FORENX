# Contributing to ForenX

Thank you for contributing to the ForenX academic digital forensics workbench.

## Guidelines
1. **Academic Rigor:** All browser parsers must be backed by synthetic test fixtures with documented schemas and expected ground-truth records.
2. **Never Modify Evidence:** Any contribution must preserve the separation between evidence vault originals and working copies.
3. **Safety First:** Never introduce dependencies or code that extracts browser credentials, cookies, or session secrets.
4. **Testing Requirement:** Run and pass the automated test suite before submitting pull requests:
   ```bash
   pytest -v
   ruff check src tests
   ```
5. **Code Style:** Use typed Python 3.10+ dataclasses, docstrings, and parameterized SQLite queries.
