# FintechForge

An educational project for onboarding aspiring professionals into the financial technology ("fintech") domain, with a focus on trading operations, processes, controls, and supporting technology.

## Structure

- `docs/`: Conceptual documentation and trading domain guides
  - `domain/`: Core domain knowledge (order lifecycle, market microstructure, etc.)
- `src/fintechforge/`: Python package with examples and reference implementations
  - `data_models/`: Pydantic models for common trading data schemas
  - `trading_ops/`: Utilities and examples for trade lifecycle, allocations, reconciliations
- `examples/python/`: Small runnable scripts for teaching
- `tests/`: Unit tests

## Getting started

Prereqs: Python 3.12.x and Poetry.

```bash
# Use local venv inside project
poetry config virtualenvs.in-project true

# Create project environment with Python 3.12
poetry env use python3.12

# Install dependencies
poetry install

# Activate shell
poetry shell

# Run tests
pytest -q
```
