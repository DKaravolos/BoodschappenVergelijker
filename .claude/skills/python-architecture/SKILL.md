---
name: python-architecture
description: Use when designing a new module or service, restructuring existing code, the user asks "how should I organise this", "what architecture", "where does this code belong", "dependency injection", "clean architecture", "hexagonal", "layered".
---
# Skill: python-architecture

## Your Job

Design a Python codebase structure that is easy to test, easy to change, and has clear ownership. Propose the simplest architecture that fits the problem — not the most sophisticated.

---

## Architecture Selection

### When to use each approach

**Layered (most projects — use this by default)**
- Clear separation: presentation → application → domain → infrastructure
- Works well for pipelines, training scripts, Dash apps, CLI tools
- Simple to understand; straightforward to test

**Hexagonal / Ports & Adapters**
- Use when the same core logic must plug into multiple I/O backends (local disk, S3, database)
- Repositories and protocols define the ports; concrete implementations are adapters
- Recommended for data pipelines and model serving where backends vary

**Clean Architecture**
- Full inversion of dependencies; domain has zero imports from infrastructure
- Only worth it for large, long-lived services with many engineers
- Overkill for ML scripts, pipelines, or internal tools

**Rule:** Start with layered. Introduce ports when you have two or more backends to swap. Only go full clean architecture if explicitly needed.

---

## Layered Architecture

```
src/
├── presentation/     ← CLI, Dash app, API handlers (thin — no logic)
├── application/      ← use cases, orchestration (calls domain + infra)
├── domain/           ← pure business logic, no I/O, no framework imports
└── infrastructure/   ← S3, filesystem, databases, HTTP clients
```

**Dependency direction:** `presentation → application → domain`. Infrastructure is called by application, but domain never imports infrastructure.

```python
# domain/trajectory.py — pure logic, zero imports from outside domain
from dataclasses import dataclass
import torch


@dataclass
class Trajectory:
    """A sequence of 3D joint positions over time.

    Attributes:
        sequence_id: Unique identifier for this sequence.
        joints: Tensor of shape (T, J, 3) — T frames, J joints, 3D coords.
        label: Action category label.
    """

    sequence_id: str
    joints: torch.Tensor
    label: str

    def duration_frames(self) -> int:
        """Return the number of frames in the trajectory.

        Returns:
            Frame count as an integer.
        """
        return self.joints.shape[0]

    def slice(self, start: int, end: int) -> "Trajectory":
        """Return a sub-trajectory from start to end frame.

        Args:
            start: Start frame index (inclusive).
            end: End frame index (exclusive).

        Returns:
            New Trajectory with sliced joints.
        """
        return Trajectory(
            sequence_id=self.sequence_id,
            joints=self.joints[start:end],
            label=self.label,
        )
```

```python
# application/predict.py — orchestrates domain + infra, no I/O logic itself
from src.domain.trajectory import Trajectory
from src.infrastructure.repository import TrajectoryRepository
from src.domain.model import MotionModel


class PredictionService:
    """Application service that coordinates trajectory prediction.

    Attributes:
        repo: Repository for loading trajectory data.
        model: Trained model for prediction.
    """

    def __init__(self, repo: TrajectoryRepository, model: MotionModel) -> None:
        self._repo = repo
        self._model = model

    def predict(self, sequence_id: str, horizon: int) -> Trajectory:
        """Load a trajectory and predict its future motion.

        Args:
            sequence_id: ID of the trajectory to load.
            horizon: Number of frames to predict.

        Returns:
            Predicted future trajectory.
        """
        trajectory = self._repo.load_by_id(sequence_id)
        return self._model.predict(trajectory, horizon=horizon)
```

---

## Hexagonal Architecture (Ports & Adapters)

Define the port as a Protocol in the domain or application layer. Place all concrete implementations in infrastructure.

```
src/
├── domain/
│   ├── trajectory.py
│   └── ports.py          ← Protocol interfaces (the "ports")
├── application/
│   └── predict.py
└── infrastructure/
    ├── s3_repository.py  ← adapter 1
    └── local_repository.py  ← adapter 2
```

```python
# domain/ports.py — the port; infrastructure must implement this
from typing import Protocol
from src.domain.trajectory import Trajectory


class TrajectoryRepository(Protocol):
    """Port: abstract storage for trajectories."""

    def load_by_id(self, sequence_id: str) -> Trajectory:
        """Load a single trajectory by its ID.

        Args:
            sequence_id: Unique trajectory identifier.

        Returns:
            The loaded Trajectory.

        Raises:
            KeyError: If the sequence_id does not exist.
        """
        ...

    def save(self, trajectory: Trajectory) -> None:
        """Persist a trajectory.

        Args:
            trajectory: Trajectory to save.
        """
        ...
```

```python
# infrastructure/s3_repository.py — adapter
import polars as pl
from src.domain.ports import TrajectoryRepository
from src.domain.trajectory import Trajectory


class S3TrajectoryRepository:
    """TrajectoryRepository backed by Parquet files on S3.

    Attributes:
        bucket: S3 bucket name.
        prefix: Key prefix for all trajectory files.
    """

    def __init__(self, bucket: str, prefix: str) -> None:
        self._base = f"s3://{bucket}/{prefix}"

    def load_by_id(self, sequence_id: str) -> Trajectory:
        df = pl.scan_parquet(f"{self._base}/{sequence_id}.parquet").collect()
        return _row_to_trajectory(df)

    def save(self, trajectory: Trajectory) -> None:
        _trajectory_to_df(trajectory).write_parquet(
            f"{self._base}/{trajectory.sequence_id}.parquet",
            compression="zstd",
        )
```

---

## Dependency Injection Without a Framework

Never use a DI framework (injector, dependency-injector, etc.) unless the project is genuinely large. Constructor injection is sufficient.

```python
# composition_root.py — one place where everything is wired together
import boto3
from src.infrastructure.s3_repository import S3TrajectoryRepository
from src.infrastructure.local_repository import LocalTrajectoryRepository
from src.application.predict import PredictionService
from src.domain.model import MotionModel


def build_production() -> PredictionService:
    """Construct the production dependency graph.

    Returns:
        Fully wired PredictionService using S3 backend.
    """
    repo = S3TrajectoryRepository(bucket="ml-data", prefix="trajectories/")
    model = MotionModel.load_from_checkpoint("s3://ml-models/motion/latest.ckpt")
    return PredictionService(repo=repo, model=model)


def build_test(tmp_path: str) -> PredictionService:
    """Construct a test dependency graph using local filesystem.

    Args:
        tmp_path: Temporary directory for test fixtures.

    Returns:
        Fully wired PredictionService using local backend.
    """
    repo = LocalTrajectoryRepository(root=tmp_path)
    model = MotionModel.load_from_checkpoint("tests/fixtures/tiny_model.ckpt")
    return PredictionService(repo=repo, model=model)
```

Rules:
- Only one composition root per application entry point.
- Never call `build_production()` inside library code — only in `main()` or `app.py`.
- Test code only ever calls `build_test(...)`.

---

## Module Boundaries

**Rule: import direction must match dependency direction.** If a lower layer needs to import from a higher layer, the design is wrong.

```
✅  application imports from domain
✅  infrastructure imports from domain (to implement its protocols)
✅  presentation imports from application
❌  domain imports from application
❌  domain imports from infrastructure
❌  infrastructure imports from application
```

Enforce with `ruff` import rules (`TID252`) or by code review.

**Circular imports** are always a design smell. If two modules need each other, extract the shared concept into a third module that both can import from.

---

## When to Use a Class vs a Function

| Situation | Use |
|---|---|
| Stateless transformation | Function |
| Multiple related stateless functions | Module (group functions, no class) |
| Has state that persists between calls | Class |
| Implements a Protocol / port | Class |
| Has `__enter__`/`__exit__` lifecycle | Class (context manager) |
| Single callable with config | `functools.partial` or a closure |
| Configuration bag | `dataclass` |

---

## Red Flags — Flag These Before Proceeding

- `from src.infrastructure import X` inside `src/domain/` — dependency inversion violation.
- A module with more than ~300 lines — propose splitting.
- `__init__.py` containing more than re-exports — move logic to named modules.
- Passing more than 3 positional arguments to a function — propose a dataclass parameter object.
- Two modules importing from each other — circular dependency, needs refactoring first.
- A class with only one method (and it's not a Protocol implementation) — make it a function.
