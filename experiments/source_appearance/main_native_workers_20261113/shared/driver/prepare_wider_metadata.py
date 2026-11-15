"""Bind actual staged native tables, sidecars and material references; no convert."""
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
sys.path.insert(0, str(TASK / "source"))
import archive_safety as S
import vmt_reference as V
sys.path.insert(0, str(ROOT / "tools"))
from source_mdl_choices import catalogue

RECEIPT = TASK / "runs/wider-execute-1794612147814048100/verification.json"

def cstring(raw, at):
    S.require(0 <= at < len(raw), "String offset outside native model")
    end = raw.find(b"\0", at, min(at + 2049, len(raw)))
    S.require(end >= at, "Unterminated/excessive native string")
    return raw[at:end].decode("latin-1")

def materials_paths(raw):
    count, offset = struct.unpack_from("<2i", raw, 212)
    S.require(0 <= count <= 2048 and 0 <= offset <= len(raw) - 4 * count, "Native CDtexture table exceeds bounds")
    values = [cstring(raw, struct.unpack_from("<i", raw, offset + i * 4)[0]).replace("\\", "/") for i in range(count)]
    for value in values:
        if value: S.safe_name(value.rstrip("/"))
    return values

def sidecars(source, checksum):
    rows = {}
    for suffix in (".vvd", ".dx90.vtx"):
        path = source.with_suffix(suffix)
        with path.open("rb") as stream: raw = stream.read(64)
        if suffix == ".vvd":
            S.require(raw[:4] == b"IDSV" and struct.unpack_from("<I", raw, 4)[0] == 4 and struct.unpack_from("<I", raw, 8)[0] == checksum, "Native VVD version/checksum mismatch")
        else:
            S.require(struct.unpack_from("<I", raw, 0)[0] == 7 and struct.unpack_from("<I", raw, 16)[0] == checksum, "Native DX90 VTX version/checksum mismatch")
        rows[suffix] = {"path": str(path), **S.identity(path)}
    return rows

def main():
    plan = json.loads((TASK / "RESOURCE_PLAN.json").read_bytes())
    staged = json.loads(RECEIPT.read_bytes())
    S.require(staged["passed"] and staged["staged_files"] == 265, "Staging receipt not accepted")
    native_inventory_path = ROOT / "output/sfm-extra-native-inventory/portable-root-639301165838922272/metadata.json"
    historical = json.loads(native_inventory_path.read_bytes())
    models = historical["models"]
    protected = {row["path"]: {k: row[k] for k in ("sha256", "bytes", "mtime_ns")} for row in staged["rows"]}
    protected.update(plan["original_archives"])
    protected[str(RECEIPT)] = S.identity(RECEIPT)
    protected[str(native_inventory_path)] = S.identity(native_inventory_path)
    protected[str(ROOT / "tools/source_mdl_choices.py")] = S.identity(ROOT / "tools/source_mdl_choices.py")
    S.require(all(S.identity(Path(p)) == row for p, row in protected.items()), "Native metadata input changed")
    families = {}; selected_models = {}
    for family in plan["cases"]:
        family_root = TASK / "stage" / family["family"]
        resources = [r for r in staged["rows"] if r["family"] == family["family"]]
        family_models = {}
        for selected in family["selected_models"]:
            source = family_root / selected["native_member"]
            resource_root = family_root / selected["content_prefix"]
            raw = source.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
            S.require(sha == selected["native_mdl_sha256"], "Fresh native model differs")
            cat = catalogue(raw, sha, source.name)
            dirs = materials_paths(raw)
            indexed = {}
            for resource in resources:
                path = Path(resource["path"])
                if path.is_relative_to(resource_root):
                    member = "owned/" + path.relative_to(resource_root).as_posix()
                    indexed[member.casefold()] = {**resource, "member": member}
            resolutions = []; roots = []
            for material in cat["materials"]:
                # Match pinned SourceIO's declared policy, without basename guesses:
                # bare name, then each relative nonempty CDtexture directory.
                names = [material["name"]] + [directory.rstrip("/") + "/" + material["name"] for directory in dirs if directory]
                candidates = []; seen = set(); hit = None
                for name in names:
                    member = "owned/materials/" + S.safe_name(name.replace("\\", "/") + ".vmt")
                    if member.casefold() in seen: continue
                    seen.add(member.casefold()); row = indexed.get(member.casefold())
                    candidates.append({"member": member, "exists": row is not None})
                    if row is not None and hit is None: hit = row["member"]
                resolutions.append({"material_index": material["index"], "material_name": material["name"], "candidates": candidates, "resolved": hit})
                if hit and hit not in roots: roots.append(hit)
            closure = V.collect(roots, indexed) if roots else None
            matches = [row for row in models if row["sha256"] == sha and row["archive"] == Path(family["archive"]).name]
            S.require(len(matches) == 1, "Historical native metadata SHA/member join ambiguous")
            model = {"family": family["family"], "source": str(source), "member": source.name, "archive_member": selected["native_member"],
                "source_identity": S.identity(source), "resource_root": str(resource_root), "native_catalogue": cat,
                "sidecar_headers": sidecars(source, cat["native_checksum"]), "native_material_search_paths": dirs,
                "native_material_resolution": resolutions, "missing_native_materials": [r for r in resolutions if not r["resolved"]],
                "vmt_closure": closure, "historical_full_native_metadata": matches[0],
                "historical_join": "Exact freshly read selectedMDL SHA+archive name; expected metadata only, not runtime/fidelity acceptance"}
            family_models[selected["case"]] = model; selected_models[selected["case"]] = model
        families[family["family"]] = {"archive": family["archive"], "archive_identity": family["archive_identity"], "resources": resources,
            "resource_count": len(resources), "resource_bytes": sum(r["bytes"] for r in resources), "models": family_models}
    S.save(TASK / "WIDER_FAMILIES.json", {"format": "has_source_appearance_wider_families_1", "families": families,
        "metadata_provenance": {"path": str(native_inventory_path), **S.identity(native_inventory_path)},
        "native_convert_app_render_fidelity": "UNRUN"})
    specifications = [
        ("junko_main", "default-no-appearance", 0, {}, False, False),
        ("junko_main", "skin-15", 15, {}, True, False),
        ("junko_main", "skin-15-belt-off", 15, {"1": 1}, True, False),
        ("junko_hair", "default-no-appearance", 0, {}, False, False),
        ("junko_hair", "hat-off", 0, {"1": 1}, True, False),
        ("mima_body", "default-no-appearance", 0, {}, False, False),
        ("mima_body", "skin-3", 3, {}, True, False),
        ("mima_body", "skin-3-socks-off", 3, {"2": 1}, True, False),
        ("kanako_props", "default-no-appearance", 0, {}, False, False),
        ("kanako_props", "bat-left-off", 0, {"0": 1}, True, False),
        ("kanako_props", "all-blank-refusal", 0, {str(i): 1 for i in range(4)}, True, True),
    ]
    request_root = TASK / "wider-requests"; request_root.mkdir(exist_ok=False)
    cases = []; commands = []
    for model_name, variant, skin, overrides, use, blank in specifications:
        model = selected_models[model_name]; cat = model["native_catalogue"]
        groups = {str(group["index"]): overrides.get(str(group["index"]), 0) for group in cat["bodygroups"]}
        S.require(0 <= skin < len(cat["skins"]), "Variant skin out of range")
        actual_blank = all(cat["bodygroups"][int(key)]["choices"][value]["true_blank"] for key, value in groups.items())
        S.require(actual_blank is blank, "Proposed trueblank outcome differs from actual native tables")
        name = model_name + "-" + variant
        request_path = request_root / (name + ".json") if use else None
        if request_path:
            S.save(request_path, {"format": "studio_source_appearance_request_1", "source_sha256": model["source_identity"]["sha256"],
                "native_mdl_sha256": model["source_identity"]["sha256"], "skin": skin, "bodygroups": groups})
        row = {"name": name, "family": model["family"], "model": model_name, "variant": variant,
            "source": model["source"], "source_sha256": model["source_identity"]["sha256"], "member": model["member"],
            "resource_root": model["resource_root"], "skin": skin, "bodygroups": groups, "use_override": use, "expect_all_blank": blank,
            "resource_manifest": "WIDER_FAMILIES.json", "appearance_request": str(request_path) if request_path else None}
        cases.append(row)
        command = [r"C:\Program Files\Python313\python.exe", "-B", "-u", str(ROOT / "tools/prepare_source.py"), model["source"],
            "--output", str(TASK / "wider-conversions" / name), "--sourceio", plan["sourceio"],
            "--blender", r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe", "--mount-plan", str(TASK / "empty-mount-plan.json")]
        if request_path: command += ["--appearance", str(request_path)]
        commands.append({"name": name, "command": command, "expect_success": not blank})
    S.save(TASK / "native-wider-cases.json", {"format": "has_source_appearance_native_cases_1", "cases": cases,
        "metadata_only_models": ["mima_head"], "case_count": len(cases), "native_conversion_app_render_fidelity": "UNRUN",
        "limits": ["No assembly/jiggle/native shaders or procedural evaluation claim.", "Mima head existing native control/descriptors/rules inventoried only; body/dress/head are distinct rigs.", "Material closure may retain missing native/bridge resources, not substituted through installed content."]})
    S.save(TASK / "WIDER_COMMANDS.json", {"format": "has_source_appearance_wider_cli_proposal_1", "commands": commands,
        "execution": "UNRUN; future separate root-reviewed lock and dual-attested serial lease required"})
    S.require(all(S.identity(Path(p)) == row for p, row in protected.items()), "Protected resource changed during metadata read")
    S.save(TASK / "WIDER_METADATA_RECEIPT.json", {"format": "has_wider_metadata_preservation_1", "passed": True, "inputs_before_after": protected,
        "models": {name: {"source": m["source"], "skins": len(m["native_catalogue"]["skins"]), "groups": len(m["native_catalogue"]["bodygroups"]),
            "missing_native_materials": len(m["missing_native_materials"]), "missing_vmt_texture_references": len(m["vmt_closure"]["missing_native_references"]) if m["vmt_closure"] else None,
            "bridge_base_inputs_complete": bool(m["vmt_closure"] and m["vmt_closure"]["supported_bridge_base_inputs_complete"]) and not m["missing_native_materials"]} for name, m in selected_models.items()},
        "native_conversion_app_render_fidelity": "UNRUN"})
    print(json.dumps({"models": len(selected_models), "cases": len(cases), "expected_allblank_refusals": 1, "inputs_preserved": True, "converter_launched": False}))

if __name__ == "__main__": main()
