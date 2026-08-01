---
name: python-quality
description: Use when writing new Python code, reviewing existing code, setting up linting/typing, or the user asks "add type hints", "set up ruff", "improve code quality", "write docstrings", "mypy", "logging", "error handling".
---
# Skill: python-quality

## Your Job

Write Python code that is typed, documented, linted, and structured according to the Google Python Style Guide with a 120-character line length. Generate the tooling config when setting up a project.

---

## Tooling Config

When setting up a new project or asked to configure linting/formatting, generate this `pyproject.toml` section:

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "D",    # pydocstyle (Google style)
    "TID",  # flake8-tidy-imports (enforce import direction)
    "ANN",  # flake8-annotations (type hints)
    "RUF",  # ruff-specific rules
    "W505", # doc-line-too-long — enforces max-doc-length below (docstrings wrap at 120, not 80)
]
ignore = [
    "ANN101",  # missing type annotation for self
    "ANN102",  # missing type annotation for cls
    "D105",    # missing docstring in magic method
    "D107",    # missing docstring in __init__ (document on class instead)
]

[tool.ruff.lint.pycodestyle]
max-doc-length = 120   # docstrings and comments wrap at 120 — the team deviation from Google's 80

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
line-length = 120
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["slow: marks tests as slow (deselect with -m 'not slow')"]
```

Also add a `.editorconfig` at the project root:

```ini
root = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 120
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```

---

## Google Style Guide Rules (applied when writing code)

### Docstrings — always, everywhere

All public modules, classes, functions, and methods get a docstring. Format: Google style, 120-char wrap.
Wrap docstring prose at 120 characters — do not break lines at 80, and do not exceed 120. This is
enforced by ruff rule W505 (`max-doc-length = 120`) and the PostToolUse hook.

**Function/method docstring:**
```python
def compute_trajectory_velocity(
    joints: torch.Tensor,
    fps: float = 30.0,
) -> torch.Tensor:
    """Compute per-frame velocity from joint position sequences.

    Finite differences are computed along the time axis. The first frame velocity is
    set to zero to maintain the original sequence length.

    Args:
        joints: Joint positions of shape (T, J, 3), where T is frames, J is joints.
        fps: Frames per second used to convert to units/second. Defaults to 30.0.

    Returns:
        Velocity tensor of shape (T, J, 3) in the same units/second as joints.

    Raises:
        ValueError: If joints has fewer than 2 frames.
    """
    if joints.shape[0] < 2:
        raise ValueError(f"Need at least 2 frames to compute velocity, got {joints.shape[0]}")
    velocity = torch.zeros_like(joints)
    velocity[1:] = (joints[1:] - joints[:-1]) * fps
    return velocity
```

**Class docstring (on the class, not `__init__`):**
```python
class MotionEncoder(nn.Module):
    """Transformer encoder for motion sequence representation learning.

    Encodes a sequence of joint positions into a fixed-size latent vector
    suitable for downstream prediction or classification tasks.

    Attributes:
        hidden_dim: Size of the internal representation dimension.
        num_layers: Number of transformer encoder layers.
    """

    def __init__(self, hidden_dim: int, num_layers: int) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        ...
```

**Module docstring — first line of every `.py` file:**
```python
"""Trajectory velocity and acceleration feature extractors.

Functions in this module operate on Polars DataFrames containing joint position
sequences and return derived kinematic features for model input.
"""
```

---

### Type Hints — always, no exceptions

```python
# Every function parameter and return type must be annotated
def split_sequence(
    joints: torch.Tensor,
    context_len: int,
    horizon_len: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    ...

# Use | for union types (Python 3.10+)
def load_config(path: str | None = None) -> dict[str, Any]:
    ...

# Use dataclasses for structured data — not dicts, not tuples
from dataclasses import dataclass, field

@dataclass
class ExperimentConfig:
    """Configuration for a single training experiment.

    Attributes:
        name: Unique experiment name used for logging and checkpointing.
        seed: Random seed for reproducibility.
        lr: Learning rate for the optimiser.
        tags: Optional metadata tags for experiment tracking.
    """

    name: str
    seed: int = 42
    lr: float = 1e-4
    tags: list[str] = field(default_factory=list)
```

Rules:
- No `Any` unless truly unavoidable — if you use it, add a `# noqa: ANN401` comment explaining why.
- No untyped `dict` or `list` — always parameterise: `dict[str, float]`, `list[str]`.
- Return type `None` must be explicit: `def foo() -> None:`.
- The team prefers ABCs over `typing.Protocol` (see `python-abc-patterns`). Use `Protocol` only for legacy or utility code.

---

### Error Handling

Build a lightweight exception hierarchy per domain, not a flat pile of `ValueError`s.

```python
# src/domain/exceptions.py
class MLProjectError(Exception):
    """Base exception for all project errors."""


class DataError(MLProjectError):
    """Raised when input data is invalid or missing."""


class ModelError(MLProjectError):
    """Raised when a model operation fails."""


class ConfigError(MLProjectError):
    """Raised when configuration is missing or invalid."""
```

Usage rules:
- Raise the most specific exception.
- Always include the bad value in the message: `raise DataError(f"Sequence too short: {n} frames (min 30)")`
- Never catch `Exception` at the call site unless you're at a boundary (API handler, CLI entrypoint).
- Never silence exceptions with `except Exception: pass`.
- Use `raise ... from original_exc` to preserve the chain.

```python
def load_parquet(path: str) -> pl.DataFrame:
    """Load a Parquet file, raising DataError on failure.

    Args:
        path: Filesystem or S3 path to the Parquet file.

    Returns:
        Loaded DataFrame.

    Raises:
        DataError: If the file cannot be read or parsed.
    """
    try:
        return pl.scan_parquet(path).collect()
    except Exception as exc:
        raise DataError(f"Failed to load Parquet from {path!r}") from exc
```

---

### Structured Logging

Never use `print()` in non-script code. Use `logging` with structured context.

```python
import logging

# Always get a logger named after the module — never use the root logger
logger = logging.getLogger(__name__)


def train_epoch(model, dataloader, epoch: int) -> float:
    """Run one training epoch and return mean loss."""
    logger.info("Starting epoch %d", epoch)
    total_loss = 0.0

    for batch_idx, batch in enumerate(dataloader):
        loss = model.training_step(batch, batch_idx)
        total_loss += loss.item()

        if batch_idx % 100 == 0:
            logger.debug("Epoch %d batch %d/%d loss=%.4f", epoch, batch_idx, len(dataloader), loss.item())

    mean_loss = total_loss / len(dataloader)
    logger.info("Epoch %d complete. mean_loss=%.4f", epoch, mean_loss)
    return mean_loss
```

Logging setup (in `main()` or `app.py` only — never in library code):

```python
import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger for the application.

    Args:
        level: Logging level string. One of DEBUG, INFO, WARNING, ERROR.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )
```

Rules:
- `logger = logging.getLogger(__name__)` — one per module, at module level.
- Use `%s` formatting in log calls — never f-strings (avoids work when level is filtered).
- `logger.exception(...)` inside `except` blocks — it captures the traceback automatically.
- Never call `logging.basicConfig()` inside a library module.

---

### Naming (Google Style)

| Thing | Convention | Example |
|---|---|---|
| Module | `snake_case` | `trajectory_encoder.py` |
| Package | `snake_case` | `motion_synthesis/` |
| Class | `PascalCase` | `MotionEncoder` |
| Function / method | `snake_case` | `compute_velocity()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_SEQUENCE_LEN = 512` |
| Private | `_single_leading_underscore` | `_internal_cache` |
| Type variable | `T`, `KT`, `VT` or descriptive | `T = TypeVar("T")` |

- Avoid single-letter names except for loop indices (`i`, `j`) and well-known maths (`x`, `y`, `t`).
- Be descriptive: `num_frames` not `n`, `learning_rate` not `lr` in config keys.

---

### Imports (Google Style)

Order (enforced by ruff `I` rules):
1. Standard library
2. Third-party
3. First-party (`src/`)

One import per line. No wildcard imports (`from module import *`). No implicit relative imports.

```python
# Good
import os
import sys
from pathlib import Path
from typing import Any

import polars as pl
import torch
import torch.nn as nn

from src.domain.trajectory import Trajectory
from src.domain.ports import TrajectoryRepository
```

---

### What to Flag When Reviewing Existing Code

- Missing type annotations on any public function → add them.
- Missing or incomplete docstring (no Args/Returns/Raises) → fill it in.
- `print()` outside of a script's `__main__` block → replace with `logger`.
- Bare `except:` or `except Exception: pass` → fix error handling.
- `from module import *` → replace with explicit imports.
- Lines over 120 characters → wrap them.
- `dict` or `list` as parameter type without parameterisation → add type params.
- Mutable default arguments (`def foo(items=[])`) → use `None` + `if items is None: items = []`.
