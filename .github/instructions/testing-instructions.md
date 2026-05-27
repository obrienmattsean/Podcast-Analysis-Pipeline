---
description: "Unit and integration testing best practices with pytest"
applyTo: "**/*test*.py"
---

# Unit and Integration Tests Instructions

## Overview

This instruction file defines testing standards using pytest for Python projects.

## Unit Tests

Test individual components in isolation without external dependencies.

## Fixtures

Use pytest fixtures and factory patterns for test data.

## Mocking

Use pytest-mock or unittest.mock for external dependencies.


## Parametrized Tests

Test multiple scenarios efficiently using `@pytest.mark.parametrize`.

## Test Naming Convention

Follow this pattern: `test_<unit>_<scenario>_<expected_result>`

Examples:

- `test_order_confirm_with_items_succeeds`
- `test_order_confirm_when_empty_raises_error`
- `test_repository_save_order_persists_to_database`


## Coverage

Aim for high coverage but focus on meaningful tests:

```bash
# Run tests from the pipeline service
cd services/pipeline && uv run pytest
```

## Best Practices

1. **AAA Pattern**: Arrange, Act, Assert
2. **One assertion per test** (when possible)
3. **Test behavior, not implementation**
4. **Use descriptive test names**
5. **Keep tests independent**
6. **Fast unit tests** (<100ms each)
7. **Mock external services**
8. **Use factories for complex objects**

## Validation Checklist

- [ ] Tests follow AAA pattern
- [ ] Unit tests have no external dependencies
- [ ] Integration tests use test database
- [ ] Fixtures are reusable
- [ ] Test names are descriptive
- [ ] Coverage is above 80%
- [ ] All tests pass before committing
