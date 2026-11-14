"""Create a separate minimal adapter; preserve the historical sidecar draft."""
import ast
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).absolute().parent
OLD = TASK / "source"
TARGET = TASK / "minimal-source"

def main():
    TARGET.mkdir(exist_ok=False)
    reader = (OLD / "source_jiggle_values.py").read_bytes()
    assert hashlib.sha256(reader).hexdigest() == "3a6f690ad94498ae88803a6665c686cceb6d8f97c5f50b4d22a3ade65c69983e"
    (TARGET / "source_jiggle_values.py").write_bytes(reader)
    text = (OLD / "source_jiggle_metadata.py").read_text(encoding="utf-8")
    module = ast.parse(text)
    selected = {node.name: ast.get_source_segment(text, node) for node in module.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    header = '''"""Draft inline-or-omitted inert jiggle metadata, no runtime imports/solver."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
import struct
import source_jiggle_values as Raw

FORMAT = "studio_source_jiggle_metadata_1"
LAYOUT = "sourceio_flags_plus_29_float_prefix_120"
READER_SHA256 = "3a6f690ad94498ae88803a6665c686cceb6d8f97c5f50b4d22a3ade65c69983e"
SOURCEIO_REVISION = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
METADATA_LIMIT = 128 * 1024
REPORT_LIMIT = 256 * 1024
STATUS_LIMIT = 4096
KEY = "source_jiggle"
REASONS = {"layout_unsupported": "Optional native jiggle layout could not be retained.",
    "native_inventory_mismatch": "Native bone identities differ from the imported native inventory.",
    "metadata_value_budget": "Native jiggle values exceed the optional metadata admission bound.",
    "metadata_budget": "Complete jiggle metadata exceeds128KiB; no partial rules are retained.",
    "report_budget": "Complete jiggle metadata does not fit the256KiB parameter report.",
    "baseline_report_over_budget": "The original parameter report already exceeds256KiB.",
    "baseline_unserializable": "The original report cannot be encoded as finite JSON."}
'''
    inspect = selected["inspect"]
    inspect = inspect.replace('if not any(struct.unpack_from("<I", raw, start + i * Raw.BONE_BYTES + 164)[0] == 5 for i in range(count)):', 'declared = sum(struct.unpack_from("<I", raw, start + i * Raw.BONE_BYTES + 164)[0] == 5 for i in range(count))\n        context.update(native_bone_count=count, declared_jiggle_rule_count=declared)\n        if not declared:')
    inspect = inspect.replace('if len(_compact(metadata)) > METADATA_LIMIT:\n        return {"state": "unavailable", "status": _status("metadata_budget", context)}\n    return {"state": "retained", "metadata": metadata}', 'candidate = candidate_fingerprint(metadata)\n    if candidate["metadata_candidate_bytes"] > METADATA_LIMIT:\n        return {"state": "unavailable", "status": _status("metadata_budget", {**context, **candidate})}\n    return {"state": "retained", "metadata": metadata}')
    assert 'candidate = candidate_fingerprint(metadata)' in inspect and 'declared = sum(' in inspect
    names = ("SourceIdentityError", "_sha", "_compact", "report_bytes", "_status")
    result = header + "\n\n" + "\n\n".join(selected[name] for name in names) + "\n\n" + inspect + "\n\n" + selected["_inert"] + "\n\n" + (TASK / "minimal_report_functions.txt").read_text(encoding="utf-8")
    (TARGET / "source_jiggle_metadata.py").write_text(result, encoding="utf-8")
    fixture_text = (OLD / "test_source_jiggle_metadata.py").read_text(encoding="utf-8")
    fixture_ast = ast.parse(fixture_text)
    functions = {node.name: ast.get_source_segment(fixture_text, node) for node in fixture_ast.body if isinstance(node, ast.FunctionDef)}
    fixtures = 'import copy\nimport hashlib\nimport io\nimport json\nimport struct\nimport source_jiggle_metadata as M\nORIGINAL = hashlib.sha256(b"authored original archive identity").hexdigest()\n\n' + "\n\n".join(functions[name] for name in ("authored", "legacy_bytes", "base_report", "padded")) + "\n"
    fixtures = fixtures.replace('"source_file": "authored.mdl",', '"source_file": "authored.mdl", "scale": 0.01905,')
    (TARGET / "authored_fixture.py").write_text(fixtures, encoding="utf-8")
    (TASK / "MINIMAL_REBASE.json").write_text(json.dumps({"format": "has_minimal_inert_jiggle_rebase_1", "historical_sidecar_adapter_sha256": hashlib.sha256((OLD / "source_jiggle_metadata.py").read_bytes()).hexdigest(),
        "verified_raw_reader_sha256": hashlib.sha256(reader).hexdigest(), "changes": ["Keep raw decoder/inert identity checks", "Remove every external sidecar/confirmation API", "Retained source identity checked BEFORE all budget fallback", "Inline exactmetadata or explicitwhole-branch omission with candidate digest/counts", "Log-only bounded status if no report headroom; sourceMDL/bundle remains truth"],
        "production_changed": False, "native_conversion_fit_tested": False}, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
