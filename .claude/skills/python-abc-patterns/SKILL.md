---
name: python-abc-patterns
description: Use when designing class hierarchies, defining contracts between components, the user asks "abstract class", "base class", "ABC", "inherit from", "subclass", "template method", "override", or when a design calls for a shared interface with enforced implementation.
---
# Skill: python-abc-patterns

## Team Preference

This team prefers **ABCs and class hierarchies** over Protocols and structural subtyping. ABCs make contracts explicit, are enforced at instantiation time (not just by a type checker), and make `isinstance` checks reliable. Use this skill for any interface or shared-behaviour design.

Protocols are only appropriate when: (a) you cannot modify the implementing class (third-party code), or (b) you need to match an existing duck-typed interface. In all other cases, use an ABC.

---

## When ABCs Are Worth It vs Not

**Use an ABC when:**
- Two or more concrete implementations exist (or are planned)
- The interface has more than one method
- You want `isinstance` checks to be meaningful
- Subclasses share some default behaviour (Template Method)
- You want instantiation of the base class to be impossible

**Do NOT use an ABC when:**
- Only one concrete implementation exists and none is planned — just write the class
- The "contract" is a single callable — use a `Callable` type hint instead
- The class has no `@abstractmethod` decorators — it's just a regular base class

---

## Core ABC Pattern

```python
from abc import ABC, abstractmethod
import polars as pl


class TrajectoryRepository(ABC):
    """Abstract base for trajectory data storage backends.

    Subclass this to implement a new storage backend (S3, local disk, database).
    All methods decorated with @abstractmethod must be overridden.

    Example:
        class S3TrajectoryRepository(TrajectoryRepository):
            def load(self, split: str) -> pl.DataFrame:
                return pl.scan_parquet(f"s3://bucket/{split}/").collect()
    """

    @abstractmethod
    def load(self, split: str) -> pl.DataFrame:
        """Load a dataset split as a DataFrame.

        Args:
            split: One of "train", "val", "test".

        Returns:
            DataFrame containing the split data.

        Raises:
            KeyError: If the split does not exist in this backend.
        """

    @abstractmethod
    def save(self, df: pl.DataFrame, name: str) -> None:
        """Persist a DataFrame under a given name.

        Args:
            df: DataFrame to persist.
            name: Logical key for the stored dataset.
        """

    def exists(self, name: str) -> bool:
        """Check whether a named dataset exists in this backend.

        Provides a default implementation using load(); override for efficiency.

        Args:
            name: Dataset name to check.

        Returns:
            True if the dataset exists, False otherwise.
        """
        try:
            self.load(name)
            return True
        except KeyError:
            return False
```

Rules:
- Every `@abstractmethod` must have a complete docstring — it IS the contract.
- Concrete methods on the ABC (like `exists` above) provide sensible defaults subclasses can override.
- The ABC's `__init__` should only hold state genuinely shared by all subclasses.

---

## Template Method Pattern

Use when subclasses share a fixed algorithm structure but differ in specific steps.
The base class defines the skeleton; subclasses fill in the blanks.

```python
from abc import ABC, abstractmethod
import pytorch_lightning as ptl
import torch


class BaseMotionModel(ABC, ptl.LightningModule):
    """Abstract base for motion synthesis models.

    Defines the training loop structure. Subclasses implement the forward
    pass and loss computation; logging and optimiser logic is shared here.

    Attributes:
        cfg: Model configuration dictionary.
    """

    def __init__(self, cfg: dict) -> None:
        super().__init__()
        self.save_hyperparameters(cfg)
        self.cfg = cfg

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run the model forward pass.

        Args:
            x: Input tensor of shape (B, T, J*3).

        Returns:
            Predicted output tensor.
        """

    @abstractmethod
    def compute_loss(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """Compute the training loss.

        Args:
            predictions: Model output tensor.
            targets: Ground-truth tensor of the same shape.

        Returns:
            Scalar loss tensor.
        """

    # Template method — not abstract, not meant to be overridden
    def _shared_step(self, batch: dict, stage: str) -> torch.Tensor:
        """Run one forward + loss step and log the result.

        Args:
            batch: Dict with keys "sequence" and "target".
            stage: One of "train", "val", "test" — used as the log prefix.

        Returns:
            Loss tensor.
        """
        preds = self(batch["sequence"])
        loss = self.compute_loss(preds, batch["target"])
        self.log(f"{stage}/loss", loss, prog_bar=True, on_epoch=True, sync_dist=True)
        return loss

    def training_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "train")

    def validation_step(self, batch: dict, batch_idx: int) -> None:
        self._shared_step(batch, "val")

    def configure_optimizers(self) -> dict:
        opt = torch.optim.AdamW(self.parameters(), lr=self.cfg["learning_rate"])
        return {"optimizer": opt}


# Concrete subclass — only implements what's abstract
class TransformerMotionModel(BaseMotionModel):
    """Transformer-based motion synthesis model.

    Attributes:
        encoder: Transformer encoder stack.
        head: Linear output projection.
    """

    def __init__(self, cfg: dict) -> None:
        super().__init__(cfg)
        self.encoder = torch.nn.TransformerEncoder(
            torch.nn.TransformerEncoderLayer(d_model=cfg["hidden_dim"], nhead=8, batch_first=True),
            num_layers=cfg["num_layers"],
        )
        self.head = torch.nn.Linear(cfg["hidden_dim"], cfg["output_dim"])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x)[:, -1, :])

    def compute_loss(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.mse_loss(predictions, targets)
```

---

## Mixin Pattern

Use mixins to share concrete behaviour across unrelated class hierarchies.
Keep each mixin to one responsibility.

```python
import logging


class LoggingMixin:
    """Adds a pre-configured logger named after the class.

    Mix into any class to get self.logger without boilerplate.

    Example:
        class MyService(LoggingMixin, SomeBase):
            def do_work(self) -> None:
                self.logger.info("Working...")
    """

    @property
    def logger(self) -> logging.Logger:
        """Return a logger named after this class.

        Returns:
            Logger instance scoped to the class's qualified name.
        """
        return logging.getLogger(type(self).__qualname__)


class CheckpointMixin(ABC):
    """Adds save/load checkpoint capability to a model class.

    Requires the subclass to implement state_dict and load_state_dict.
    """

    @abstractmethod
    def state_dict(self) -> dict:
        """Return the model's state as a serialisable dict.

        Returns:
            State dictionary.
        """

    @abstractmethod
    def load_state_dict(self, state: dict) -> None:
        """Restore model state from a dictionary.

        Args:
            state: State dictionary as returned by state_dict().
        """

    def save_checkpoint(self, path: str) -> None:
        """Serialise the model state to disk.

        Args:
            path: Filesystem path for the checkpoint file.
        """
        import torch
        torch.save(self.state_dict(), path)

    def load_checkpoint(self, path: str) -> None:
        """Load model state from a checkpoint file.

        Args:
            path: Filesystem path of the checkpoint to load.
        """
        import torch
        self.load_state_dict(torch.load(path, weights_only=True))
```

Mixin rules:
- Mixins go **left** in the MRO, before the main base class: `class Foo(MixinA, MixinB, BaseClass)`.
- Maximum **two mixins** per class. More is a design smell — consider composition.
- Mixins must not call `super().__init__()` with positional arguments.
- Never inherit from two non-mixin base classes (diamond problem).

---

## Self-Registering Subclass Registry

Use when you need to select a concrete subclass by name from config.

```python
from abc import ABC, abstractmethod
import torch


class BaseModel(ABC):
    """Abstract base for all motion models with automatic name-based registry.

    Subclasses register themselves by passing name= in the class definition.
    Use BaseModel.build(name, **kwargs) to instantiate by config.

    Example:
        model = BaseModel.build("transformer", hidden_dim=256, output_dim=69)
    """

    _registry: dict[str, type["BaseModel"]] = {}

    def __init_subclass__(cls, name: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if name is not None:
            BaseModel._registry[name] = cls

    @classmethod
    def build(cls, name: str, **kwargs) -> "BaseModel":
        """Instantiate a registered model subclass by name.

        Args:
            name: Registry name declared in the subclass definition.
            **kwargs: Passed directly to the subclass constructor.

        Returns:
            Instantiated model.

        Raises:
            ValueError: If name is not in the registry.
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown model: {name!r}. Registered: {list(cls._registry)}")
        return cls._registry[name](**kwargs)

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run the model forward pass.

        Args:
            x: Input tensor.

        Returns:
            Model output tensor.
        """


# Registration is declared at class definition — no separate decorator needed
class TransformerModel(BaseModel, name="transformer"):
    """Transformer model, registered under the name 'transformer'."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        ...


class DiffusionModel(BaseModel, name="diffusion"):
    """Diffusion model, registered under the name 'diffusion'."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        ...


# Config-driven instantiation — no if/elif chains
model = BaseModel.build(cfg["model"]["name"], **cfg["model"]["params"])
```

---

## ABC vs Protocol — Team Position

| Concern | ABC (team default) | Protocol (exception only) |
|---|---|---|
| Contract enforced at instantiation | Yes | No — only mypy |
| `isinstance` checks reliable | Yes | Only with `@runtime_checkable` |
| Shared default behaviour | Yes | No |
| Third-party / unmodifiable classes | No | Yes — use Protocol here |
| Explicit inheritance required | Yes | No |

**Default: ABC. Exception: Protocol when the implementing class can't be modified.**

---

## Red Flags — Flag These Before Proceeding

- ABC with only one concrete subclass and no second planned — remove the ABC.
- ABC with zero `@abstractmethod` methods — it's not an ABC, remove the `ABC` base.
- More than two mixins on one class — propose composition instead.
- Diamond inheritance (two non-mixin bases) — redesign before proceeding.
- `@abstractmethod` with no docstring — the contract is undefined; write the docstring first.
- Subclass overriding a non-abstract method without calling `super()` — flag it; almost always a bug.
- Protocol used where ABC would work — raise it with the team; ABCs are the preference.
