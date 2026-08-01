---
name: python-patterns
description: Use when applying a design pattern, refactoring toward a pattern, or the user asks "how should I structure this", "what pattern fits here", "factory", "strategy", "observer", "builder", "repository", "decorator".
---
# Skill: python-patterns

## Your Job

Apply the right design pattern for the problem — no more, no less. Python is not Java. Most Gang of Four patterns have simpler Pythonic equivalents. Prefer functions, dataclasses, and protocols over class hierarchies.

---

## Decision Tree: Which Pattern?

Before writing anything, map the problem to the right bucket:

| Problem | Reach for |
|---|---|
| Need to create objects without specifying concrete class | Factory Function or `__init_subclass__` registry |
| Same algorithm, swappable implementations | Strategy (callable or Protocol) |
| React to events across decoupled components | Observer / event bus |
| Build complex objects step by step | Builder (dataclass + fluent methods) |
| Wrap behaviour without changing interface | Decorator (`functools.wraps`) |
| One instance only | Module-level singleton (not a Singleton class) |
| Uniform interface over a subsystem | Facade function |
| Data access abstraction | Repository Protocol |
| Cache expensive calls | `functools.lru_cache` / `functools.cache` |
| Retry / circuit breaker | Decorator with backoff |

---

## Patterns

### Factory Function (not Factory Class)

Use when: you need to create objects of different types based on a parameter.

```python
# Bad — Java-style AbstractFactory
class ShapeFactory:
    def create(self, kind: str): ...

# Good — just a function
def create_optimizer(kind: str, lr: float) -> torch.optim.Optimizer:
    """Create an optimizer by name.

    Args:
        kind: One of "adam", "sgd", "adamw".
        lr: Learning rate.

    Returns:
        Configured optimizer instance.

    Raises:
        ValueError: If kind is not recognised.
    """
    optimizers = {
        "adam": torch.optim.Adam,
        "sgd": torch.optim.SGD,
        "adamw": torch.optim.AdamW,
    }
    if kind not in optimizers:
        raise ValueError(f"Unknown optimizer: {kind!r}. Choose from {list(optimizers)}")
    return optimizers[kind](lr=lr)
```

For **self-registering subclasses** (plugins, model registry):

```python
_REGISTRY: dict[str, type] = {}

def register(name: str):
    """Class decorator that registers a model by name."""
    def decorator(cls):
        _REGISTRY[name] = cls
        return cls
    return decorator

def build(name: str, **kwargs):
    if name not in _REGISTRY:
        raise ValueError(f"Unknown model: {name!r}")
    return _REGISTRY[name](**kwargs)

# Usage
@register("transformer")
class TransformerModel(BaseModel): ...

model = build("transformer", hidden_dim=256)
```

---

### Strategy — Use Callables, Not Classes

Use when: you want swappable algorithms.

```python
# Bad — class hierarchy for each strategy
class MeanAggregator: ...
class MaxAggregator: ...

# Good — callable Protocol
from typing import Protocol
import torch

class AggregationFn(Protocol):
    def __call__(self, x: torch.Tensor, dim: int) -> torch.Tensor: ...

def pool_sequence(
    x: torch.Tensor,
    aggregate: AggregationFn = torch.mean,
) -> torch.Tensor:
    """Pool a sequence tensor along the time dimension.

    Args:
        x: Input tensor of shape (B, T, D).
        aggregate: Function to reduce along dim=1. Defaults to mean pooling.

    Returns:
        Pooled tensor of shape (B, D).
    """
    return aggregate(x, dim=1)

# Usage — strategy is just a callable
pool_sequence(x, aggregate=torch.max)
pool_sequence(x, aggregate=lambda t, dim: t[:, -1, :])  # last frame
```

---

### Observer — Event Bus

Use when: decoupled components need to react to events.

```python
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """Simple synchronous event bus for decoupled component communication."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        """Register a handler for an event type.

        Args:
            event: Event name string.
            handler: Callable invoked with the event payload.
        """
        self._handlers[event].append(handler)

    def publish(self, event: str, payload: Any = None) -> None:
        """Publish an event to all registered handlers.

        Args:
            event: Event name string.
            payload: Data passed to each handler.
        """
        for handler in self._handlers[event]:
            handler(payload)


# Usage
bus = EventBus()
bus.subscribe("epoch_end", lambda payload: print(f"Epoch {payload['epoch']} done"))
bus.publish("epoch_end", {"epoch": 5, "val_loss": 0.23})
```

---

### Builder — Dataclass + Fluent Methods

Use when: constructing objects with many optional parameters. Avoids telescoping constructors.

```python
from dataclasses import dataclass, field


@dataclass
class TrainingConfig:
    """Configuration for a training run.

    Build incrementally using the fluent `with_*` methods, then call `build()` to validate.
    """

    lr: float = 1e-4
    max_epochs: int = 100
    batch_size: int = 32
    precision: str = "16-mixed"
    callbacks: list = field(default_factory=list)

    def with_lr(self, lr: float) -> "TrainingConfig":
        self.lr = lr
        return self

    def with_callbacks(self, *callbacks) -> "TrainingConfig":
        self.callbacks = list(callbacks)
        return self

    def build(self) -> "TrainingConfig":
        """Validate and return the finalised config.

        Returns:
            Self after validation.

        Raises:
            ValueError: If any field has an invalid value.
        """
        if self.lr <= 0:
            raise ValueError(f"lr must be positive, got {self.lr}")
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        return self


# Usage
config = TrainingConfig().with_lr(3e-4).with_callbacks(checkpoint, early_stop).build()
```

---

### Decorator — Behaviour Wrapping

Use when: adding cross-cutting concerns (retry, timing, logging) without changing the function signature.

```python
import functools
import time
import logging

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Retry a function on failure with fixed delay.

    Args:
        max_attempts: Maximum number of attempts before raising.
        delay: Seconds to wait between attempts.
        exceptions: Exception types to catch and retry.

    Returns:
        Decorator function.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.1fs.",
                        attempt, max_attempts, fn.__name__, exc, delay,
                    )
                    time.sleep(delay)
        return wrapper
    return decorator


@retry(max_attempts=3, delay=2.0, exceptions=(IOError, TimeoutError))
def upload_to_s3(path: str, bucket: str) -> None: ...
```

---

### Repository — Protocol for Data Access

Use when: you want to decouple business logic from storage (S3, local disk, database).

```python
from typing import Protocol
import polars as pl


class TrajectoryRepository(Protocol):
    """Abstract data access for trajectory datasets."""

    def load(self, split: str) -> pl.DataFrame:
        """Load a dataset split.

        Args:
            split: One of "train", "val", "test".

        Returns:
            DataFrame with the split's data.
        """
        ...

    def save(self, df: pl.DataFrame, name: str) -> None:
        """Persist a DataFrame.

        Args:
            df: DataFrame to persist.
            name: Logical name / key for the dataset.
        """
        ...


class S3TrajectoryRepository:
    """Trajectory repository backed by S3 Parquet files."""

    def __init__(self, bucket: str, prefix: str) -> None:
        self._base = f"s3://{bucket}/{prefix}"

    def load(self, split: str) -> pl.DataFrame:
        return pl.scan_parquet(f"{self._base}/{split}/*.parquet").collect()

    def save(self, df: pl.DataFrame, name: str) -> None:
        df.write_parquet(f"{self._base}/{name}.parquet", compression="zstd")


class LocalTrajectoryRepository:
    """Trajectory repository backed by local Parquet files (for testing)."""

    def __init__(self, root: str) -> None:
        self._root = root

    def load(self, split: str) -> pl.DataFrame:
        return pl.scan_parquet(f"{self._root}/{split}/*.parquet").collect()

    def save(self, df: pl.DataFrame, name: str) -> None:
        df.write_parquet(f"{self._root}/{name}.parquet", compression="zstd")
```

---

## Anti-Patterns to Flag and Refuse

- **Singleton class** — use a module-level instance instead.
- **Abstract base class with a single concrete subclass** — just write the concrete class.
- **Strategy class with a single method** — use a callable / Protocol instead.
- **Factory class that only calls `__init__`** — use a factory function.
- **Mixin chains deeper than 2 levels** — flag and propose composition instead.
- **`__init__` with more than 5 parameters that aren't config** — propose a dataclass config object.
