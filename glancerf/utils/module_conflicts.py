"""Detect and resolve conflicts when duplicate modules have different settings.

Used by layout and map-modules config pages. When the same module appears in multiple
places (layout cells and/or map overlay) with different non-boolean settings (e.g. APRS
dots vs icons), we detect conflicts and let the user pick one value to apply to all.
"""

from __future__ import annotations

from typing import Any


def _get_conflict_prone_types() -> set[str]:
    """Setting types that can have conflicting values across instances."""
    return {"select"}


def _is_boolean_like(schema: dict[str, Any]) -> bool:
    """True if setting is effectively on/off (checkbox or select with yes/no)."""
    if schema.get("type") == "checkbox":
        return True
    if schema.get("type") == "select":
        opts = schema.get("options") or []
        if len(opts) <= 2:
            vals = {str(o.get("value")) for o in opts if o.get("value") is not None}
            if vals <= {"0", "1", "true", "false", "yes", "no", ""}:
                return True
    return False


def detect_module_conflicts(
    layout: list[list[str]],
    map_overlay_layout: list[str],
    module_settings: dict[str, dict[str, Any]],
    modules_settings_schema: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Detect conflicts for modules that appear in multiple places.

    Returns list of conflicts. Each conflict:
    {
        "module_id": str,
        "module_name": str,
        "setting_id": str,
        "setting_label": str,
        "options": [{"value": v, "label": l}, ...],
        "instances": [{"cell_key": str, "value": str, "label": str}, ...],
    }
    """
    conflicts: list[dict[str, Any]] = []
    layout = layout or []
    map_overlay_layout = map_overlay_layout or []
    module_settings = module_settings or {}
    modules_settings_schema = modules_settings_schema or {}

    # Collect all (cell_key, module_id, settings) for each module instance
    instances_by_module: dict[str, list[tuple[str, dict[str, Any]]]] = {}

    for r, row in enumerate(layout):
        if not isinstance(row, (list, tuple)):
            continue
        for c, cell_value in enumerate(row):
            mid = (cell_value or "").strip()
            if not mid:
                continue
            key = f"{r}_{c}"
            settings = module_settings.get(key)
            settings = settings if isinstance(settings, dict) else {}
            if mid not in instances_by_module:
                instances_by_module[mid] = []
            instances_by_module[mid].append((key, settings))

    for i, mid in enumerate(map_overlay_layout or []):
        mid = (mid or "").strip()
        if not mid:
            continue
        key = f"map_overlay_{i}"
        settings = module_settings.get(key)
        settings = settings if isinstance(settings, dict) else {}
        if mid not in instances_by_module:
            instances_by_module[mid] = []
        instances_by_module[mid].append((key, settings))

    # For each module with 2+ instances, check for conflicts
    for module_id, instances in instances_by_module.items():
        if len(instances) < 2:
            continue
        schema_list = modules_settings_schema.get(module_id) or []
        for s in schema_list:
            if not isinstance(s, dict):
                continue
            setting_id = s.get("id")
            if not setting_id:
                continue
            stype = s.get("type") or ""
            if stype not in _get_conflict_prone_types():
                continue
            if _is_boolean_like(s):
                continue
            opts = s.get("options") or []
            if not opts:
                continue
            value_to_label = {str(o.get("value")): str(o.get("label", o.get("value", ""))) for o in opts}
            values_seen: dict[str, list[tuple[str, str]]] = {}
            for cell_key, settings in instances:
                raw = settings.get(setting_id)
                val = str(raw).strip() if raw is not None and raw != "" else ""
                label = value_to_label.get(val, val or "(default)")
                if val not in values_seen:
                    values_seen[val] = []
                values_seen[val].append((cell_key, label))
            if len(values_seen) <= 1:
                continue
            instance_list = []
            for val, pairs in values_seen.items():
                for cell_key, label in pairs:
                    instance_list.append({"cell_key": cell_key, "value": val, "label": label})
            conflicts.append({
                "module_id": module_id,
                "module_name": "",  # Filled by caller if needed
                "setting_id": setting_id,
                "setting_label": str(s.get("label", setting_id)),
                "options": [{"value": str(o.get("value")), "label": str(o.get("label", o.get("value", "")))} for o in opts],
                "instances": instance_list,
            })
    return conflicts


def get_cell_keys_for_module(
    module_id: str,
    layout: list[list[str]],
    map_overlay_layout: list[str],
) -> list[str]:
    """Return all cell keys where this module appears."""
    keys: list[str] = []
    layout = layout or []
    map_overlay_layout = map_overlay_layout or []
    for r, row in enumerate(layout):
        if not isinstance(row, (list, tuple)):
            continue
        for c, cell_value in enumerate(row):
            if (cell_value or "").strip() == module_id:
                keys.append(f"{r}_{c}")
    for i, mid in enumerate(map_overlay_layout or []):
        if (mid or "").strip() == module_id:
            keys.append(f"map_overlay_{i}")
    return keys
