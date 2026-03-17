"""
Singleton PyMemuc instance and protected VM registry.

On first import, snapshots existing VMs into protected_vms.json so that
destructive operations (delete, stop_all) never touch pre-existing instances.
"""

import json
import logging
import os
import sys

from pymemuc import PyMemuc, PyMemucError

# ── Logging (stderr only — stdout is the MCP JSON-RPC channel) ──────────
logger = logging.getLogger("mcp-memu")
logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(_handler)

# ── PyMemuc singleton ───────────────────────────────────────────────────
_memuc_path = os.environ.get("MEMUC_PATH")
memuc = PyMemuc(memuc_path=_memuc_path) if _memuc_path else PyMemuc()

# ── Protected VM registry ───────────────────────────────────────────────
# Store protected_vms.json in the project root (2 levels up from this file in src layout)
_PROTECTED_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "protected_vms.json"
)


def _snapshot_existing_vms() -> list[dict]:
    """Capture current VM list and persist to protected_vms.json."""
    try:
        vms = memuc.list_vm_info()
        # vms is list[VMInfo] — each has index, title, running, pid, etc.
        protected = [{"index": vm["index"], "title": vm["title"]} for vm in vms]
        with open(_PROTECTED_FILE, "w", encoding="utf-8") as f:
            json.dump(protected, f, indent=2)
        logger.info("Protected VMs snapshot saved: %s", protected)
        return protected
    except (PyMemucError, FileNotFoundError, OSError) as e:
        logger.warning("Could not snapshot VMs (will protect nothing): %s", e)
        return []


def get_protected_vms() -> list[dict]:
    """Return the list of protected VMs (index + title)."""
    if os.path.exists(_PROTECTED_FILE):
        with open(_PROTECTED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return _snapshot_existing_vms()


def is_protected(vm_index: int) -> bool:
    """Check if a VM index belongs to a protected (pre-existing) instance."""
    return any(vm["index"] == vm_index for vm in get_protected_vms())


def is_protected_by_name(vm_name: str) -> bool:
    """Check if a VM name belongs to a protected (pre-existing) instance."""
    return any(vm["title"] == vm_name for vm in get_protected_vms())


def assert_not_protected(vm_index: int, operation: str = "operation") -> None:
    """Raise an error if the VM is protected."""
    if is_protected(vm_index):
        pvm = next(vm for vm in get_protected_vms() if vm["index"] == vm_index)
        raise RuntimeError(
            f"BLOCKED: '{operation}' on protected VM index={vm_index} "
            f"name='{pvm['title']}'. This VM existed before the MCP server "
            f"started. Only VMs created during this session can be modified "
            f"destructively."
        )


def refresh_protected_vms() -> list[dict]:
    """Re-snapshot current VMs (call after server restart if needed)."""
    return _snapshot_existing_vms()


# Snapshot on first import (only if file doesn't already exist)
if not os.path.exists(_PROTECTED_FILE):
    try:
        _snapshot_existing_vms()
    except OSError as e:
        logger.warning("Cannot snapshot VMs yet (needs admin): %s", e)
