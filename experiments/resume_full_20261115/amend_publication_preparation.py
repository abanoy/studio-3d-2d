"""Apply root's pre-execution review; metadata/source only, no recipe execution."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OLD = ROOT / "experiments/owner_pause_20261114/prepared-unrun/windows-canonical-bone-binding-retry-publication-prep-20261114"
BACKUP = BASE / "amendment-history/pre-root-review"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def main():
    if BACKUP.exists():
        raise RuntimeError("Preserve prior amendment history")
    names = ("INDEX.json", "publication/INDEX.json", "publication/build_consolidated_packet.py", "SOURCE_REVIEW.json", "COMMANDS.md", "README.md", "diffs/publication__build_consolidated_packet.py.diff")
    preserved = {}
    for name in names:
        raw = (BASE / name).read_bytes()
        destination = BACKUP / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(raw)
        preserved[name] = {"bytes": len(raw), "sha256": sha(raw)}

    script = BASE / "publication/build_consolidated_packet.py"
    raw = script.read_bytes()
    old = b"assert python['command']==CONTEXT['suite_python_command']"
    new = b"assert python['command_line']==CONTEXT['suite_python_command']"
    if raw.count(old) != 1:
        raise RuntimeError("Unexpected command-field assertion; source review required")
    script.write_bytes(raw.replace(old, new))
    ast.parse(script.read_text(encoding="utf-8"))
    previous = (OLD / script.name).read_text(encoding="utf-8").splitlines(keepends=True)
    current = script.read_text(encoding="utf-8").splitlines(keepends=True)
    (BASE / "diffs/publication__build_consolidated_packet.py.diff").write_text("".join(difflib.unified_diff(previous, current, fromfile=str(OLD / script.name), tofile="publication/" + script.name)), encoding="utf-8", newline="\n")

    review = json.loads((BASE / "SOURCE_REVIEW.json").read_bytes())
    for row in review["comparisons"]:
        if row["path"] == "publication/build_consolidated_packet.py":
            changed = script.read_bytes()
            row.update({"successor_bytes": len(changed), "successor_sha256": sha(changed), "byte_identical": False})
    review["root_pre_execution_amendment"] = {
        "status": "SOURCE_ONLY_UNRUN", "reason": "Root caught a second live command-field read and an output-only metadata acquisition boundary.",
        "consolidation_fix": "Use the actual root raw proof's command_line field; all PID/birth/raw-hash/state checks stay intact.",
        "execution_location": "Root must copy the exact indexed public publication recipe into a fresh ROOT/output folder after actual full PASS/closure, then execute the copy. summarize.acquire remains restricted to ROOT/output.",
        "original_preparation": preserved, "recipe_execution": False, "new_full_PASS_claimed": False,
    }
    (BASE / "SOURCE_REVIEW.json").write_bytes(encode(review))
    readme = (BASE / "README.md").read_text(encoding="utf-8")
    readme = readme.replace("Five publication modules are byte-identical; only the live-proof field admission changes in publication_gates.py.", "Four publication modules remain byte-identical; publication_gates.py and the consolidation assertion use the actual root raw proof's command_line field.")
    readme += "\nRoot pre-execution review caught the remaining consolidation field read and the summary recipe's output-only acquisition boundary. The narrow amendment preserves prior bytes under amendment-history/pre-root-review. Publication must execute from the fresh byte-verified ROOT/output copy described in COMMANDS.md; do not run it directly from this experiments folder. summarize.acquire's boundary is unchanged. No recipe was imported/executed to discover or correct these issues.\n"
    (BASE / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    public = BASE / "publication"
    rows = [{"path": p.name, "bytes": len(p.read_bytes()), "sha256": sha(p.read_bytes())} for p in sorted(public.iterdir()) if p.is_file() and p.name != "INDEX.json"]
    index = {"format": "has_prepared_successor_index_1", "source_commit": review["source_commit"], "status": "PREPARED_UNRUN", "files": rows, "file_count": len(rows), "bytes": sum(row["bytes"] for row in rows)}
    (public / "INDEX.json").write_bytes(encode(index))
    public_index_sha = sha((public / "INDEX.json").read_bytes())
    commands = (BASE / "COMMANDS.md").read_text(encoding="utf-8")
    commands = commands.replace("$resumeRecipe = 'C:\\a\\Programming\\cloudflare\\has-acceptance-session-20261111\\experiments\\resume_full_20261115\\publication'", "$resumeSourceRecipe = 'C:\\a\\Programming\\cloudflare\\has-acceptance-session-20261111\\experiments\\resume_full_20261115\\publication'\n$resumeRecipe = 'C:\\a\\Programming\\cloudflare\\has-acceptance-session-20261111\\output\\resume-full-publication-f0dd57a-20261115'")
    marker = "$resumeHostSha = (Get-FileHash"
    if commands.count(marker) != 1:
        raise RuntimeError("Unexpected command instructions; preserve history and review")
    copy_block = """# Execute only from a byte-verified fresh output copy: summary acquisition remains output-only.
if (Test-Path -LiteralPath $resumeRecipe) { throw 'Preserve existing execution folder' }
$resumeSourceIndexSha = (Get-FileHash -LiteralPath "$resumeSourceRecipe\\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($resumeSourceIndexSha -ne 'INDEX_SHA_TO_INSERT') { throw 'Reviewed public recipe INDEX changed' }
$resumeSourceIndex = Get-Content -LiteralPath "$resumeSourceRecipe\\INDEX.json" -Raw | ConvertFrom-Json
foreach ($resumeRow in $resumeSourceIndex.files) {
    if ($resumeRow.path -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Recipe member path refused' }
    $resumeSourceFile = Join-Path $resumeSourceRecipe $resumeRow.path
    if ((Get-Item -LiteralPath $resumeSourceFile).Length -ne $resumeRow.bytes -or (Get-FileHash -LiteralPath $resumeSourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256) { throw 'Source recipe bytes changed' }
}
New-Item -ItemType Directory -Path $resumeRecipe -ErrorAction Stop | Out-Null
$resumeCopyRows = foreach ($resumeRow in $resumeSourceIndex.files) {
    $resumeSourceFile = Join-Path $resumeSourceRecipe $resumeRow.path
    $resumeCopiedFile = Join-Path $resumeRecipe $resumeRow.path
    Copy-Item -LiteralPath $resumeSourceFile -Destination $resumeCopiedFile -ErrorAction Stop
    if ((Get-Item -LiteralPath $resumeCopiedFile).Length -ne $resumeRow.bytes -or (Get-FileHash -LiteralPath $resumeCopiedFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256 -or (Get-FileHash -LiteralPath $resumeSourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256) { throw 'Copied recipe or source changed' }
    [ordered]@{source=$resumeSourceFile;copied=$resumeCopiedFile;bytes=$resumeRow.bytes;sha256=$resumeRow.sha256;byte_identical=$true}
}
Copy-Item -LiteralPath "$resumeSourceRecipe\\INDEX.json" -Destination "$resumeRecipe\\SOURCE-RECIPE-INDEX.json" -ErrorAction Stop
if ((Get-FileHash -LiteralPath "$resumeRecipe\\SOURCE-RECIPE-INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeSourceIndexSha -or (Get-FileHash -LiteralPath "$resumeSourceRecipe\\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeSourceIndexSha) { throw 'Recipe index changed during copy' }
$resumeCopyProof = [ordered]@{format='has_publication_recipe_execution_copy_1';source_commit=$resumeState.source_commit;canonical_run=$resumeRun;source_recipe=$resumeSourceRecipe;execution_recipe=$resumeRecipe;source_index_sha256=$resumeSourceIndexSha;copied_files=$resumeCopyRows;recipes_executed=$false}
[System.IO.File]::WriteAllText((Join-Path $resumeRecipe 'COPY-PROVENANCE.json'),($resumeCopyProof|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
""".replace("INDEX_SHA_TO_INSERT", public_index_sha)
    commands = commands.replace(marker, copy_block + marker)
    (BASE / "COMMANDS.md").write_text(commands, encoding="utf-8", newline="\n")
    (BASE / "EXECUTION_COPY_REVIEW.json").write_bytes(encode({
        "format": "has_publication_recipe_relocation_source_review_1", "status": "SOURCE_ONLY_UNRUN", "reviewed_recipe_INDEX_sha256": public_index_sha,
        "execution_target": str(ROOT / "output/resume-full-publication-f0dd57a-20261115"),
        "module_roots": "All six publication modules derive final ROOT from RUN_EXPECTATIONS.workspace_root; TASK/BASE derives from the copied __file__.",
        "local_import": "publication_gates imports from the same copied directory; registry/context are local copies with exact pinned bytes.",
        "output_boundaries": "Default receipt-audit, actual-summary and review-ready remain direct children of copied TASK/BASE under ROOT/output; acquire remains unchanged and accepts source recipe metadata there.",
        "other_paths": "All actual run/scoped-native/reviewed-test-delta paths come from locked context. No publication module references the experiments folder as an execution location.",
        "schema": "Both live-proof consumers now use command_line. Runner state command and launch arguments retain their own unchanged schema.",
        "mutation": "Preparation only; no output execution copy, recipe import, final-report read, lease release or runtime occurred.",
    }))
    rows = []
    for p in sorted(BASE.rglob("*")):
        if p.is_file() and p != BASE / "INDEX.json":
            raw = p.read_bytes()
            rows.append({"path": p.relative_to(BASE).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    (BASE / "INDEX.json").write_bytes(encode({"format": "has_resumed_full_preparation_index_1", "status": "PREPARED_UNRUN_ROOT_REVIEW_AMENDMENT", "source_commit": review["source_commit"], "file_count": len(rows), "bytes": sum(row["bytes"] for row in rows), "files": rows}))
    print(json.dumps({"narrow_command_fix": True, "recipe_execution_copy_UNRUN": True, "source_recipe_INDEX_sha256": public_index_sha, "preparation_INDEX_sha256": sha((BASE / "INDEX.json").read_bytes()), "indexed_files": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
