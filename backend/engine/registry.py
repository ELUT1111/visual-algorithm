"""Algorithm plugin registry with auto-discovery."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol


class AlgorithmRegistry:
    def __init__(self) -> None:
        self._algorithms: dict[str, type[AlgorithmProtocol]] = {}
        self._meta_cache: dict[str, AlgorithmMeta] = {}

    def register(self, cls: type[AlgorithmProtocol]) -> type[AlgorithmProtocol]:
        instance = cls()
        meta = instance.get_meta()
        key = f"{meta.category}/{meta.name}"
        self._algorithms[key] = cls
        self._meta_cache[key] = meta
        return cls

    def get(self, key: str) -> AlgorithmProtocol:
        if key not in self._algorithms:
            raise KeyError(f"Algorithm not found: {key}")
        return self._algorithms[key]()

    def list_all(self, category: str | None = None) -> list[AlgorithmMeta]:
        result = []
        for key, meta in self._meta_cache.items():
            if category is None or meta.category == category:
                result.append(meta)
        return result

    def list_keys(self) -> list[str]:
        return list(self._algorithms.keys())

    def discover(self, package: str = "backend.algorithms") -> None:
        package_path = Path(__file__).parent.parent / "algorithms"
        self._discover_recursive(package_path, package)

    def _discover_recursive(self, path: Path, prefix: str) -> None:
        for finder, name, ispkg in pkgutil.iter_modules([str(path)]):
            full_name = f"{prefix}.{name}"
            if ispkg:
                sub_path = path / name
                self._discover_recursive(sub_path, full_name)
            else:
                try:
                    importlib.import_module(full_name)
                except Exception as e:
                    print(f"Warning: Failed to import {full_name}: {e}")


registry = AlgorithmRegistry()
