"""Read-only, bounded VMT reference closure within verified owned staging.

This does not evaluate shaders/proxies, decode textures, import models or render.
Missing native-only resources are findings, not permission to substitute files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
import stage_resources as stage

MAX_VMT = 1024 * 1024
TEXTURES = {"$basetexture", "$basetexture2", "$bumpmap", "$bumpmap2", "$bumpmap3", "$normalmap",
            "$detail", "$detail2", "$envmap", "$envmapmask", "$envmapmask2", "$lightwarptexture",
            "$phongwarptexture", "$phongexponenttexture", "$selfillummask", "$selfillumtexture",
            "$blendmodulatetexture", "$iris", "$corneatexture", "$dudvmap", "$flowmap"}
BRIDGE = {"$basetexture", "$iris"}


def tokens(text):
    stage.require(len(text) <= MAX_VMT and "\x00" not in text, "VMT text exceeds budget or contains NUL")
    result, i = [], 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i + 2)
            i = len(text) if end < 0 else end + 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            stage.require(end >= 0, "Unclosed VMT block comment")
            i = end + 2
        elif c in "{}":
            result.append((c, False)); i += 1
        elif c == '"':
            value, i = [], i + 1
            while i < len(text) and text[i] != '"':
                if text[i] == "\\" and i + 1 < len(text) and text[i + 1] == '"':
                    value.append('"'); i += 2
                else:
                    value.append(text[i]); i += 1
            stage.require(i < len(text), "Unclosed VMT quoted string")
            result.append(("".join(value), True)); i += 1
        elif c == "[":
            end = text.find("]", i + 1)
            stage.require(end >= 0, "Unclosed VMT bracket value/condition")
            result.append((text[i:end + 1], False)); i = end + 1
        else:
            start = i
            while i < len(text) and not text[i].isspace() and text[i] not in '{}"[' and not text.startswith("//", i) and not text.startswith("/*", i):
                i += 1
            stage.require(i > start, "Unsupported VMT token")
            result.append((text[start:i], False))
        stage.require(len(result) <= 65536, "VMT token budget exceeded")
    return result


def parse(text):
    stream = tokens(text)
    position = 0
    def block(depth=0, nested=False):
        nonlocal position
        stage.require(depth <= 16, "VMT nesting budget exceeded")
        nodes = []
        while position < len(stream):
            key, quoted = stream[position]
            position += 1
            if key == "}" and not quoted:
                stage.require(nested, "Unexpected closing VMT brace")
                return nodes
            stage.require(key != "{" or quoted, "Missing VMT key")
            stage.require(position < len(stream), "Missing VMT value")
            value, value_quoted = stream[position]
            position += 1
            if value == "{" and not value_quoted:
                node = {"key": key, "children": block(depth + 1, True)}
            else:
                stage.require(value not in {"{", "}"} or value_quoted, "Missing VMT scalar value")
                node = {"key": key, "value": value}
            if position < len(stream):
                condition, condition_quoted = stream[position]
                if not condition_quoted and re.fullmatch(r"\[!?\$[A-Za-z0-9_]+\]", condition):
                    node["condition"] = condition
                    position += 1
            nodes.append(node)
        stage.require(not nested, "Unclosed VMT block")
        return nodes
    nodes = block()
    stage.require(len(nodes) == 1 and "children" in nodes[0], "Expected exactly one shader root block")
    return nodes[0]


def reference(value, suffix):
    stage.require(isinstance(value, str) and value.strip(), "Empty VMT resource reference")
    value = value.strip().replace("\\", "/")
    # These are runtime engine resources, not files. They cannot close a native
    # standalone material dependency graph and are reported explicitly.
    if value.casefold() == "env_cubemap" or value.casefold().startswith("_rt_"):
        return None
    value = stage.safe_name(value)
    if not value.casefold().startswith("materials/"):
        value = "materials/" + value
    if not value.casefold().endswith(suffix):
        stage.require(not Path(value).suffix, "Unexpected VMT resource extension")
        value += suffix
    return value


def collect(root_members, indexed):
    """Conservative union of observed file references; does not execute branches."""
    stage.require(root_members and len(root_members) <= 64, "Invalid root VMT count")
    package = root_members[0].split("/")[0]
    stage.require(all(name.split("/")[0] == package for name in root_members), "Mixed package roots")
    files, edges, diagnostics = {}, [], []
    stack = []
    def visit(member):
        key = member.casefold()
        stage.require(len(files) < 256 or key in files, "VMT closure file budget exceeded")
        if key in stack:
            diagnostics.append({"kind": "include_cycle", "member": member}); return
        if key in files:
            return
        item = indexed.get(key)
        stage.require(item is not None and item["member"].casefold() == key, "Root/include VMT absent from verified owned index")
        path = Path(item["path"])
        stage.no_reparse(path)
        stage.require(path.stat().st_size <= MAX_VMT, "VMT file exceeds1MiB")
        raw = path.read_bytes()
        stage.require(hashlib.sha256(raw).hexdigest() == item["sha256"], "VMT changed from staged checksum")
        tree = parse(raw.decode("utf-8-sig"))
        files[key] = {"member": item["member"], "path": str(path), "sha256": item["sha256"],
                      "bytes": len(raw), "shader": tree["key"], "parameter_keys": []}
        stack.append(key)
        def walk(nodes, ancestry=()):
            for node in nodes:
                parameter = node["key"].casefold()
                files[key]["parameter_keys"].append(node["key"])
                if node.get("condition"):
                    diagnostics.append({"kind": "conditional_reference_union", "member": member, "key": node["key"], "condition": node["condition"]})
                if "children" in node:
                    if parameter not in {"insert", "replace"}:
                        diagnostics.append({"kind": "unevaluated_block", "member": member, "key": node["key"]})
                    walk(node["children"], ancestry + (parameter,))
                    continue
                value = node["value"]
                include = parameter in {"include", "#include", "#base"}
                texture = parameter in TEXTURES
                if not (include or texture):
                    # Unknown path-like values must be investigated before a
                    # claim of complete native file-reference closure.
                    if ("/" in value or "\\" in value or value.casefold().endswith((".vtf", ".vmt"))) and not value.startswith("["):
                        diagnostics.append({"kind": "unclassified_path_value", "member": member, "key": node["key"], "value": value})
                    continue
                relative = reference(value, ".vmt" if include else ".vtf")
                target = package + "/" + relative if relative is not None else None
                resolved = indexed.get(target.casefold()) if target is not None else None
                edge = {"from": member, "key": node["key"], "value": value,
                        "kind": "include" if include else "texture", "reference": relative,
                        "owned_member": resolved["member"] if resolved else target,
                        "resolved": resolved is not None, "engine_generated": relative is None,
                        "supported_bridge_input": parameter in BRIDGE and not include}
                if resolved:
                    edge.update(path=resolved["path"], bytes=resolved["bytes"], sha256=resolved["sha256"])
                    stage.require(Path(resolved["path"]).suffix.casefold() == (".vmt" if include else ".vtf"), "Wrong dependency type")
                edges.append(edge)
                if include and resolved:
                    visit(resolved["member"])
        walk(tree["children"])
        stack.pop()
    for name in root_members:
        visit(name)
    missing = [edge for edge in edges if not edge["resolved"]]
    bridge_edges = [edge for edge in edges if edge["supported_bridge_input"]]
    return {"vmts": list(files.values()), "references": edges, "diagnostics": diagnostics,
            "native_observed_file_references_complete": not missing and not diagnostics,
            "supported_bridge_base_inputs_complete": bool(bridge_edges) and all(edge["resolved"] for edge in bridge_edges),
            "missing_native_references": missing,
            "reference_rule": "Conservative union of observed supported texture/include keys; unknown path-like values/blocks/conditions prevent a complete-native claim. No shader/proxy/patch evaluation."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--receipt-sha256", required=True)
    options = parser.parse_args(argv)
    receipt_path = options.staging_receipt.absolute()
    stage.no_reparse(receipt_path)
    stage.require(receipt_path.is_relative_to(stage.TASK / "runs"), "Staging receipt must be in this task's owned runs")
    stage.require(receipt_path.stat().st_size <= 2 * 1024 * 1024, "Staging receipt exceeds2MiB")
    raw = receipt_path.read_bytes()
    stage.require(hashlib.sha256(raw).hexdigest() == options.receipt_sha256, "Staging receipt byte hash differs")
    receipt = json.loads(raw, object_pairs_hook=stage.unique_object)
    stage.require(receipt["format"] == "has_sfm_resource_staging_1" and receipt["mode"] == "execute" and receipt["passed"]
                  and receipt["originals_unchanged"] and receipt["tool_plan_sources_unchanged"] and receipt["plan_sha256"] == stage.PLAN_SHA,
                  "Staging receipt is not a preserved successful execution")
    stage_root = Path(receipt["stage"]).absolute()
    stage.require(stage_root.parent == stage.TASK and re.fullmatch(r"stage(?:-[A-Za-z0-9_]+)?", stage_root.name), "Unowned stage root")
    cases = stage.load_plan(stage.TASK / "plan.json", stage.PLAN_SHA)
    plan = json.loads((stage.TASK / "plan.json").read_bytes())
    protected = {str(receipt_path): stage.identity(receipt_path), str(stage.TASK / "plan.json"): stage.identity(stage.TASK / "plan.json")}
    indexed = {}
    for row in receipt["staged"]:
        path = Path(row["path"]).absolute()
        stage.require(row["case"] in stage.CASE_COUNTS and path == stage_root / row["case"] / stage.safe_name(row["member"]), "Staged manifest path escaped its owned case")
        observed = stage.identity(path)
        stage.require(observed == {key: row[key] for key in ["sha256", "bytes", "mtime_ns"]}, "Staged input changed before closure read")
        protected[str(path)] = observed
        index = indexed.setdefault(row["case"], {})
        key = row["member"].casefold()
        stage.require(key not in index, "Duplicate staged member")
        index[key] = row
    stage.require(len(receipt["staged"]) == 296 and sum(row["bytes"] for row in receipt["staged"]) == 181460484, "Wrong staged count/bytes")
    for case in cases:
        stage.require(set(indexed[case["case"]]) == {row["member"].casefold() for row in case["entries"]}, "Staged member set differs from the reviewed plan")
    originals = receipt["original_after"]
    stage.require(all(stage.identity(Path(path)) == value for path, value in originals.items()), "Original archive changed before closure read")
    protected.update(originals)
    results = []
    for case in plan["cases"]:
        roots = [row["indexed_vmt_candidates"][0]["member"] for row in case["vmt_candidates"]]
        result = collect(roots, indexed[case["case"]])
        results.append({"case": case["case"], **result})
    after = {path: stage.identity(Path(path)) for path in protected}
    stage.require(after == protected, "Closure read changed original/staged/evidence inputs")
    evidence = stage.TASK / "runs" / ("vmt-closure-" + str(time.time_ns()))
    evidence.mkdir(exist_ok=False)
    report = {"format": "has_owned_vmt_closure_1", "analysis_completed": True, "cases": results,
              "all_native_observed_file_references_complete": all(case["native_observed_file_references_complete"] for case in results),
              "all_supported_bridge_base_inputs_complete": all(case["supported_bridge_base_inputs_complete"] for case in results),
              "inputs_before": protected, "inputs_after": after, "inputs_unchanged": True,
              "staging_receipt": str(receipt_path), "staging_receipt_sha256": options.receipt_sha256,
              "blender_gpu_network_or_installed_writes": False,
              "limits": ["Reference closure only; no texture decode, real material slot, shader or rendered fidelity proof.",
                         "No guessed/substituted resources or installed-content fallback.", "No model import/export, app adoption, Undo/HAS/movie acceptance."]}
    stage.save(evidence / "verification.json", report)
    print(json.dumps({"evidence": str(evidence), "cases": [{"case": item["case"], "vmts": len(item["vmts"]), "references": len(item["references"]), "missing": len(item["missing_native_references"]), "native_complete": item["native_observed_file_references_complete"], "bridge_base_complete": item["supported_bridge_base_inputs_complete"]} for item in results], "inputs_unchanged": True}), flush=True)


if __name__ == "__main__":
    main()
