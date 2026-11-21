"""Bounded, source-bound static Source appearance; no Blender import or writes."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FORMAT = "studio_source_appearance_request_1"
MAX_REQUEST = 64 * 1024
MAX_GROUPS = 256
MAX_CHOICES = 256
MAX_SKINS = 256
MAX_REFERENCES = 2048


def _index(value, limit, label):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError(f"Invalid {label}; choose a native integer index below {limit}")
    return value


def _sha(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Invalid appearance " + label)
    return value


def validate(value):
    fields = {"format", "source_sha256", "native_mdl_sha256", "skin", "bodygroups"}
    if not isinstance(value, dict) or set(value) != fields or value.get("format") != FORMAT:
        raise ValueError("Invalid appearance request fields or format")
    _sha(value["source_sha256"], "original-source checksum")
    _sha(value["native_mdl_sha256"], "native-model checksum")
    _index(value["skin"], MAX_SKINS, "skin")
    groups = value["bodygroups"]
    if not isinstance(groups, dict) or len(groups) > MAX_GROUPS:
        raise ValueError("Invalid or excessive appearance bodygroups")
    for key, choice in groups.items():
        if not isinstance(key, str) or not re.fullmatch(r"0|[1-9][0-9]{0,2}", key):
            raise ValueError("Appearance bodygroups use canonical native numeric indices")
        _index(int(key), MAX_GROUPS, "bodygroup")
        _index(choice, MAX_CHOICES, "bodygroup choice")
    # Detach caller-owned data and preserve every reviewed index.
    return {**value, "bodygroups": dict(groups)}


def load(path: Path, original_sha256: str):
    if path.stat().st_size > MAX_REQUEST:
        raise ValueError("Appearance request exceeds64KiB")
    with path.open("rb") as stream:
        raw = stream.read(MAX_REQUEST + 1)
    if len(raw) > MAX_REQUEST:
        raise ValueError("Appearance request exceeds64KiB")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate appearance request key: " + key)
            result[key] = value
        return result

    value = validate(json.loads(raw, object_pairs_hook=unique))
    if value["source_sha256"] != original_sha256:
        raise ValueError("Appearance request does not match the original input checksum")
    return value


def bind(value, original_sha256: str, native_path: Path):
    value = validate(value)
    if native_path.suffix.lower() != ".mdl":
        raise ValueError("Appearance choices apply only to one MDL model, not a BSP map")
    with native_path.open("rb") as stream:
        native_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if value["source_sha256"] != original_sha256 or value["native_mdl_sha256"] != native_sha:
        raise ValueError("Appearance request no longer matches the selected native model")
    return value


def catalogue(container):
    mdl = getattr(container, "mdl", None)
    if mdl is None or not hasattr(mdl, "body_parts") or not hasattr(mdl, "skin_groups"):
        raise ValueError("Native appearance metadata is unavailable for this model")
    parts = mdl.body_parts
    if len(parts) > MAX_GROUPS or not isinstance(container.bodygroups, dict):
        raise ValueError("Excessive or unavailable native bodygroups")
    skins = [[material.name for material in family] for family in mdl.skin_groups]
    if not 1 <= len(skins) <= MAX_SKINS or not skins[0] or len(skins[0]) > MAX_REFERENCES:
        raise ValueError("Appearance review needs a bounded native skin table")
    if any(len(row) != len(skins[0]) for row in skins):
        raise ValueError("Native skin families have mismatched material slots")
    if any(not isinstance(name, str) or not name or len(name) > 2048 for row in skins for name in row):
        raise ValueError("Invalid or excessive native skin material names")
    groups = []
    names = set()
    objects = set()
    total_choices = 0
    for index, part in enumerate(parts):
        name = part.name
        if not isinstance(name, str) or len(name) > 1024 or name in names:
            raise ValueError("Ambiguous native bodygroup names cannot be selected safely")
        names.add(name)
        variants = container.bodygroups.get(name)
        if variants is None or not 1 <= len(part.models) <= MAX_CHOICES or len(variants) != len(part.models):
            raise ValueError("Converted bodygroup choices do not match the native model")
        total_choices += len(part.models)
        if total_choices > 4096:
            raise ValueError("Native appearance exceeds4096bodygroup choices")
        choices = []
        for choice, model in enumerate(part.models):
            blank = model.vertex_count == 0
            obj = variants[choice]
            if type(model.vertex_count) is not int or model.vertex_count < 0 or (obj is None) != blank:
                raise ValueError("Converted bodygroup blank does not match native zero geometry")
            if obj is not None:
                if obj not in container.objects or obj in objects or obj.type != "MESH":
                    raise ValueError("Ambiguous converted bodygroup object ownership")
                objects.add(obj)
            choices.append({"index": choice, "name": model.name, "vertices": model.vertex_count, "blank": blank})
        groups.append({"index": index, "name": name, "choices": choices})
    if set(container.bodygroups) != names:
        raise ValueError("Converted bodygroup names do not match native metadata")
    materials = getattr(mdl, "materials", [])
    default_identity = len(materials) >= len(mdl.skin_groups[0]) and all(material is materials[i] for i, material in enumerate(mdl.skin_groups[0]))
    return {"skin_groups": skins, "bodygroups": groups, "default_skin_has_native_slot_identity": default_identity}


def choose(container, value):
    value = validate(value)
    native = catalogue(container)
    skin = _index(value["skin"], len(native["skin_groups"]), "native skin")
    # The pinned importer identifies initial Blender slots by material identity.
    # Repeated default materials can lose their original native table column.
    # Never guess when the requested family would split that ambiguous column.
    if skin:
        initial = native["skin_groups"][0]
        target = native["skin_groups"][skin]
        for material in set(initial):
            if len({target[i] for i, old in enumerate(initial) if old == material}) > 1:
                raise ValueError("Ambiguous native skin columns need explicit mesh-slot mapping before this skin can be selected")
        if not native["default_skin_has_native_slot_identity"]:
            raise ValueError("Nonidentity default skin tables need explicit native mesh-slot mapping before another skin can be selected")
    groups = native["bodygroups"]
    for key in value["bodygroups"]:
        _index(int(key), len(groups), "native bodygroup")
    active = set()
    selected = {}
    selected_numeric = {}
    for group in groups:
        index = group["index"]
        choice = _index(value["bodygroups"].get(str(index), 0), len(group["choices"]), "native bodygroup choice")
        selected[group["name"]] = choice
        selected_numeric[str(index)] = choice
        obj = container.bodygroups[group["name"]][choice]
        if obj is not None:
            active.add(obj)
    if not any(len(obj.data.polygons) for obj in active):
        raise ValueError("Selected bodygroups contain no renderable geometry; keep at least one visible part")
    return {"selected_skin": skin, "selected_bodygroup_indices": selected,
            "selected_native_bodygroup_indices": selected_numeric,
            "native_appearance_choices": native, "active": active}


def apply(container, value, set_model_skin):
    # Plan every choice before mutating even the disposable Blender model.
    plan = choose(container, value)
    set_model_skin(container, plan["selected_skin"])
    for obj in container.objects:
        if container.bodygroups and obj not in plan["active"]:
            obj.hide_render = True
            obj.hide_set(True)
        elif obj in plan["active"]:
            obj.hide_render = False
            obj.hide_set(False)
    return {key: item for key, item in plan.items() if key != "active"}
