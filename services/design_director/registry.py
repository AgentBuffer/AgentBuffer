"""Specialist agent registry — maps agent names to callable classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from services.shared.models import PlanStep, SpecialistResult


class BaseSpecialist(Protocol):
    """Interface every specialist must satisfy."""

    def execute(self, step: PlanStep, task_id: str) -> SpecialistResult: ...


_REGISTRY: dict[str, type[BaseSpecialist]] = {}


def register(name: str, cls: type[BaseSpecialist]) -> None:
    """Register a specialist class under *name*."""
    _REGISTRY[name] = cls


def get_specialist(name: str) -> BaseSpecialist:
    """Instantiate and return the specialist registered under *name*."""
    if name not in _REGISTRY:
        raise KeyError(f"No specialist registered for {name!r}")
    return _REGISTRY[name]()


def registered_names() -> list[str]:
    return list(_REGISTRY.keys())
