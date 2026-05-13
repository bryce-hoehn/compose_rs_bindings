from .compose_spec import (  # type: ignore[attr-defined, no-redef]  # pylint: disable=E0611
    PyCompose as _PyCompose,
    PyOptions as _PyOptions,
    format_duration,
    parse_duration,
)
from .models import (
    ComposeSpecification,
    Config,
    Include,
    Model,
    Network,
    Secret,
    Service,
    Volume,
)

from typing import Any


class PyCompose:
    """High-level wrapper that works with Pydantic models.

    Delegates all serialization to the native Rust-backed ``_PyCompose`` while
    exposing a Pythonic API that accepts and returns Pydantic model instances.
    """

    def __init__(self, _inner: _PyCompose) -> None:
        self._inner = _inner

    # ── Constructors ──────────────────────────────

    @staticmethod
    def from_yaml(yaml: str) -> "PyCompose":
        return PyCompose(_PyCompose.from_yaml(yaml))

    @staticmethod
    def from_json(json: str) -> "PyCompose":
        return PyCompose(_PyCompose.from_json(json))

    @staticmethod
    def from_dict(spec: ComposeSpecification) -> "PyCompose":
        return PyCompose(_PyCompose.from_dict(spec.model_dump(mode="json", exclude_none=True)))

    # ── Serialization ─────────────────────────────

    def to_yaml(self) -> str:
        return self._inner.to_yaml()

    def to_json(self) -> str:
        return self._inner.to_json()

    def to_dict(self) -> dict[str, Any]:
        return self._inner.to_dict()

    def to_spec(self) -> ComposeSpecification:
        """Return the spec as a validated ComposeSpecification model.

        Unlike to_dict(), this validates the data against the full
        ComposeSpecification schema and returns a Pydantic model.
        """
        return ComposeSpecification.model_validate(self._inner.to_dict())

    # ── Field getters ─────────────────────────────

    @property
    def version(self) -> str | None:
        return self._inner.version

    @property
    def name(self) -> str | None:
        return self._inner.name

    @property
    def services(self) -> dict[str, Service] | None:
        raw = self._inner.services
        return _map_values(raw, Service)

    @property
    def networks(self) -> dict[str, Network | None] | None:
        raw = self._inner.networks
        return _map_values_nullable(raw, Network)

    @property
    def volumes(self) -> dict[str, Volume | None] | None:
        raw = self._inner.volumes
        return _map_values_nullable(raw, Volume)

    @property
    def configs(self) -> dict[str, Config] | None:
        raw = self._inner.configs
        return _map_values(raw, Config)

    @property
    def secrets(self) -> dict[str, Secret] | None:
        raw = self._inner.secrets
        return _map_values(raw, Secret)

    @property
    def include(self) -> list[Include] | None:
        raw = self._inner.include
        if raw is None:
            return None
        return [Include.model_validate(item) for item in raw]

    @property
    def extensions(self) -> dict[str, Any]:
        return self._inner.extensions

    # ── Field setters ─────────────────────────────

    @version.setter
    def version(self, value: str | None) -> None:
        self._inner.version = value

    @name.setter
    def name(self, value: str | None) -> None:
        self._inner.name = value

    @services.setter
    def services(self, value: dict[str, Service] | None) -> None:
        self._inner.services = _dump_map(value)

    @networks.setter
    def networks(self, value: dict[str, Network | None] | None) -> None:
        self._inner.networks = _dump_map_nullable(value)

    @volumes.setter
    def volumes(self, value: dict[str, Volume | None] | None) -> None:
        self._inner.volumes = _dump_map_nullable(value)

    @configs.setter
    def configs(self, value: dict[str, Config] | None) -> None:
        self._inner.configs = _dump_map(value)

    @secrets.setter
    def secrets(self, value: dict[str, Secret] | None) -> None:
        self._inner.secrets = _dump_map(value)

    @include.setter
    def include(self, value: list[Include] | None) -> None:
        if value is None:
            self._inner.include = None
        else:
            self._inner.include = [v.model_dump(mode="json", exclude_none=True) for v in value]

    @extensions.setter
    def extensions(self, value: dict[str, Any]) -> None:
        self._inner.extensions = value

    # ── Validation ────────────────────────────────

    def validate(self) -> None:
        self._inner.validate()

    def validate_networks(self) -> None:
        self._inner.validate_networks()

    def validate_volumes(self) -> None:
        self._inner.validate_volumes()

    def validate_configs(self) -> None:
        self._inner.validate_configs()

    def validate_secrets(self) -> None:
        self._inner.validate_secrets()

    # ── Service convenience ───────────────────────

    def service_names(self) -> list[str]:
        return self._inner.service_names()

    def get_service(self, name: str) -> Service | None:
        raw = self._inner.get_service(name)
        if raw is None:
            return None
        return Service.model_validate(raw)

    def set_service(self, name: str, service: Service) -> None:
        self._inner.set_service(name, service.model_dump(mode="json", exclude_none=True))

    def remove_service(self, name: str) -> Service | None:
        raw = self._inner.remove_service(name)
        if raw is None:
            return None
        return Service.model_validate(raw)

    # ── Dunder methods ────────────────────────────

    def __repr__(self) -> str:
        return repr(self._inner)

    def __len__(self) -> int:
        return len(self._inner)

    def __contains__(self, name: str) -> bool:
        return name in self._inner

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PyCompose):
            return self._inner == other._inner
        return NotImplemented


# ── Helpers ────────────────────────────────────────


def _map_values(raw: dict[str, Any] | None, model_cls: type) -> dict[str, Any] | None:
    if raw is None:
        return None
    return {k: model_cls.model_validate(v) for k, v in raw.items()}


def _map_values_nullable(raw: dict[str, Any] | None, model_cls: type) -> dict[str, Any | None] | None:
    if raw is None:
        return None
    return {k: (model_cls.model_validate(v) if v is not None else None) for k, v in raw.items()}


def _dump_map(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {k: v.model_dump(mode="json", exclude_none=True) for k, v in value.items()}


def _dump_map_nullable(value: dict[str, Any] | None) -> dict[str, Any | None] | None:
    if value is None:
        return None
    return {k: (v.model_dump(mode="json", exclude_none=True) if v is not None else None) for k, v in value.items()}


class PyOptions:
    """Wrapper around the native PyOptions that returns PyCompose instances."""

    def __init__(self, *, apply_merge: bool = False) -> None:
        self._inner = _PyOptions(apply_merge=apply_merge)

    @property
    def apply_merge(self) -> bool:
        return self._inner.apply_merge

    @apply_merge.setter
    def apply_merge(self, value: bool) -> None:
        self._inner.apply_merge = value

    def from_yaml(self, yaml: str) -> PyCompose:
        return PyCompose(self._inner.from_yaml(yaml))


__all__ = [
    "PyCompose",
    "PyOptions",
    "format_duration",
    "parse_duration",
    "ComposeSpecification",
    "Config",
    "Include",
    "Model",
    "Network",
    "Secret",
    "Service",
    "Volume",
]
