"""
bio_serialize — safe (de)serialization for Biopython objects carried between
ComfyUI nodes as STRING payloads.

Background
----------
Nodes serialize rich Biopython objects (SeqRecord, Alignment, Blast records,
PDB structures, ...) into a STRING socket value and reconstruct them downstream.
The historical pattern was::

    base64.b64encode(pickle.dumps(obj)).decode()      # produce
    pickle.loads(base64.b64decode(s))                 # consume

``pickle.loads`` executes arbitrary code embedded in the payload during
reconstruction. Because a ComfyUI workflow (with its node-input strings) is
commonly shared as a ``.json`` file, an attacker could ship a malicious payload
that runs code on whoever loads the workflow — a classic deserialization RCE.

This module keeps the **same wire format** (base64 of a pickle stream) so
existing in-memory flows and previously saved values keep working, but routes
loading through a *restricted unpickler* that only reconstructs a whitelist of
safe classes (Biopython, numpy, and a small set of stdlib containers). Any
reference to a non-whitelisted global (``os.system``, ``builtins.eval``,
``subprocess.*``, ...) raises :class:`UnsafeDeserializationError`.
"""
from __future__ import annotations

import base64
import io
import pickle
from typing import Any

__all__ = ["serialize", "deserialize", "UnsafeDeserializationError"]


class UnsafeDeserializationError(Exception):
    """Raised when a payload references a global that is not on the safelist."""


# Module prefixes whose classes are safe to reconstruct. A name is allowed when
# its module equals one of these or starts with the entry followed by a dot.
_ALLOWED_MODULE_PREFIXES = (
    "Bio",        # Biopython: Seq, SeqRecord, Align, Blast, PDB, Phylo, ...
    "numpy",      # alignment matrices / structure coordinates
    "collections",
    "datetime",
    "decimal",
)

# Specific builtins that legitimately appear in pickle streams of safe objects.
# Intentionally excludes eval/exec/getattr/__import__/open/compile/etc.
_ALLOWED_BUILTINS = frozenset({
    "set", "frozenset", "complex", "bytearray", "slice",
    "list", "dict", "tuple", "str", "bytes", "int", "float", "bool",
})


def _module_allowed(module: str) -> bool:
    for prefix in _ALLOWED_MODULE_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return True
    return False


class _RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:
        if module in ("builtins", "__builtin__"):
            if name in _ALLOWED_BUILTINS:
                return super().find_class(module, name)
            raise UnsafeDeserializationError(
                f"refused to load disallowed builtin: {module}.{name}"
            )
        if _module_allowed(module):
            return super().find_class(module, name)
        raise UnsafeDeserializationError(
            f"refused to load disallowed global: {module}.{name}"
        )


def serialize(obj: Any) -> str:
    """Serialize *obj* to a base64 STRING (pickle wire format)."""
    return base64.b64encode(pickle.dumps(obj)).decode()


def deserialize(payload: str) -> Any:
    """Reconstruct an object from a base64 STRING produced by :func:`serialize`
    (or the legacy inline ``base64.b64encode(pickle.dumps(...))`` pattern).

    Raises :class:`UnsafeDeserializationError` if the payload references a
    global outside the safelist.
    """
    raw = base64.b64decode(payload)
    try:
        return _RestrictedUnpickler(io.BytesIO(raw)).load()
    except UnsafeDeserializationError:
        raise
    except pickle.UnpicklingError as exc:
        # A blocked global surfaces here on some Python builds; normalize it.
        raise UnsafeDeserializationError(str(exc)) from exc
