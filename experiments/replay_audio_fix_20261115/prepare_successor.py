"""Prepare source-only retry; never launches an app, parser, process or Git."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / 'experiments/resume_full_20261115'
FAILED = ROOT / 'output/sfm-joints-final-validation-f0dd57a-20261115'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, raw):
    assert path.resolve().is_relative_to(HERE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)


def save(path, value):
    put(path, (json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def edit(original, replacements):
    text = original.decode('utf-8-sig').replace('\r\n', '\n')
    for before, after in replacements:
        assert text.count(before) == 1, before[:120]
        text = text.replace(before, after, 1)
    return text.encode()


AUDIO_FUNCTIONS = '''func audio_rows(audio: Dictionary) -> Array:
	if audio.is_empty():return []
	return audio.clips if audio.has("clips") and audio.clips is Array else [audio]

func portable_audio() -> Dictionary:
	# Authored clip fields remain exact; decoded bytes/paths are runtime-only.
	var audio: Dictionary=app.audio_document().duplicate(true)
	for clip in audio_rows(audio):clip.erase("source")
	return audio

func check_audio_cache(phase: String) -> void:
	var audio: Dictionary=app.audio_document()
	var clips: Array=audio_rows(audio)
	var expected: Array=request.audio_sources
	var valid: bool=clips.size()==expected.size()
	var rows: Array=[]
	for index in range(clips.size()):
		if index>=expected.size():valid=false;continue
		var clip: Dictionary=clips[index]
		var reference: Dictionary=expected[index]
		var source=clip.get("source")
		if not source is Dictionary:
			valid=false;rows.append({"id":clip.get("id",""),"passed":false,"reason":"Missing decoded source"});continue
		var keys: Array=source.keys();keys.sort()
		var fields_ok: bool=keys==["channels","frames","name","path","pcm","rate","sha256"]
		var path: String=str(source.get("path",""))
		var expected_path: String=app.project_folder.path_join(str(reference.path))
		var confined: bool=normalized_path(path)==normalized_path(expected_path) and normalized_path(path).begins_with(normalized_path(app.project_folder)+"/")
		var file_sha: String=FileAccess.get_sha256(path) if confined else ""
		var pcm_ok: bool=source.get("pcm") is PackedByteArray
		var pcm_sha: String=RasterReader.digest_bytes(source.pcm) if pcm_ok else ""
		var pcm_bytes: int=source.pcm.size() if pcm_ok else -1
		var samples_ok: bool=source.get("channels") is int and source.get("rate") is int and source.get("frames") is int and source.channels==int(reference.channels) and source.rate==int(reference.rate) and source.frames==int(reference.frames)
		var passed: bool=fields_ok and confined and clip.get("id")==reference.id and clip.get("path")==reference.path and clip.get("sha256")==reference.sha256 and source.get("sha256")==reference.sha256 and source.get("name")==reference.source_name and file_sha==reference.sha256 and samples_ok and pcm_bytes==int(reference.pcm_bytes) and pcm_sha==reference.pcm_sha256
		valid=valid and passed
		rows.append({"id":clip.get("id",""),"passed":passed,"source_fields_exact":fields_ok,"cache_confined":confined,"file_sha256":file_sha,"pcm_sha256":pcm_sha,"pcm_bytes":pcm_bytes,"channels":source.get("channels",-1),"rate":source.get("rate",-1),"frames":source.get("frames",-1)})
	if not report.has("audio_cache_proofs"):report["audio_cache_proofs"]={}
	report.audio_cache_proofs[phase]={"passed":valid,"clips":rows,"expected_clips":expected.size()}
	check(valid,"audio.cache."+phase)

'''


def main():
    origins = []
    for folder, names in [('builder', ['input-lock.json', 'README.template.md']),
                          ('replay', ['reference-lock.json', 'release-context.json'])]:
        for name in names:
            source = PREVIOUS / folder / name
            raw = source.read_bytes()
            put(HERE / folder / name, raw)
            origins.append({'path': str(source), 'bytes': len(raw), 'sha256': sha(raw), 'copied_byte_exact': True})
    for folder, name in [('builder', 'build_after_full.py'), ('replay', 'validate_after_full.py'), ('replay', 'replay.gd')]:
        source = PREVIOUS / folder / name
        raw = source.read_bytes()
        put(HERE / 'origins' / name, raw)
        if name == 'build_after_full.py':
            changed = edit(raw, [('final.name == "HAS-Review-20261115-SFM-Joints-"+args.revision[:7]',
                                   'final.name == "HAS-Review-20261115-SFM-Joints-"+args.revision[:7]+"-replay2"')])
        elif name == 'replay.gd':
            changed = edit(raw, [('func state() -> Dictionary:', AUDIO_FUNCTIONS + 'func state() -> Dictionary:'),
                ('"audio":app.audio_document().duplicate(true)', '"audio":portable_audio()'),
                ('\tvar before:=state();var camera_before:=camera_state()', '\tcheck_audio_cache("before")\n\tvar before:=state();var camera_before:=camera_state()'),
                ('\tvar after:=state()\n', '\tcheck_audio_cache("after")\n\tvar after:=state()\n'),
                ('\twrite_json(request.folder.path_join("observed-extra.json"),state())', '\tcheck_audio_cache("extra")\n\twrite_json(request.folder.path_join("observed-extra.json"),state())')])
        else:
            changed = edit(raw, [('import sys\n', 'import sys\nfrom audio_contract import audio_expectations\n'),
                ('review.name == "HAS-Review-20261115-SFM-Joints-"+args.expected_revision[:7]',
                 'review.name == "HAS-Review-20261115-SFM-Joints-"+args.expected_revision[:7]+"-replay2"'),
                ('expected_checks = 20+len(expected["world"]["objects"])+cels+len(expected_extras)',
                 'expected_checks = 23+len(expected["world"]["objects"])+cels+len(expected_extras)'),
                ('    cache = Path(result.get("project_folder", "")).resolve()',
                 '    audio_proofs = result.get("audio_cache_proofs", {})\n    result_ok = result_ok and set(audio_proofs) == {"before", "after", "extra"} and all(\n        proof.get("passed") is True and proof.get("expected_clips") == len(request["audio_sources"]) and\n        len(proof.get("clips", [])) == len(request["audio_sources"]) and all(row.get("passed") is True for row in proof["clips"])\n        for proof in audio_proofs.values())\n    cache = Path(result.get("project_folder", "")).resolve()'),
                ('"reference-lock.json", BUILDER/"input-lock.json")}', '"reference-lock.json", HERE/"audio_contract.py", BUILDER/"input-lock.json")}'),
                ('"source_manifest_sha256": identity(output/"shipped-before.json")["sha256"], "native": details,',
                 '"source_manifest_sha256": identity(output/"shipped-before.json")["sha256"], "native": details,\n                       "audio_sources": audio_expectations(package, expected["audio"]),'),
                ('finite numbers1e-12 absolute, no relative tolerance", "differences": comparisons',
                 'finite numbers1e-12 absolute, no relative tolerance; decoded clip.source omitted only by explicit portable projection and separately file/PCM/sample-bound in all3phases", "differences": comparisons')])
        if name == 'validate_after_full.py':
            changed = edit(changed, [('    cache = Path(result.get("project_folder", "")).resolve()',
                '    result_ok = result_ok and all(\n'
                '        all(row.get("id") == reference["id"] and row.get("source_fields_exact") is True and\n'
                '            row.get("cache_confined") is True and row.get("file_sha256") == reference["sha256"] and\n'
                '            row.get("pcm_sha256") == reference["pcm_sha256"] and row.get("pcm_bytes") == reference["pcm_bytes"] and\n'
                '            all(row.get(key) == reference[key] for key in ("channels", "rate", "frames"))\n'
                '            for row, reference in zip(proof["clips"], request["audio_sources"]))\n'
                '        for proof in audio_proofs.values())\n'
                '    cache = Path(result.get("project_folder", "")).resolve()')])
        if name.endswith('.py'):
            ast.parse(changed.decode(), filename=name)
        put(HERE / folder / name, changed)
        diff = ''.join(difflib.unified_diff(raw.decode('utf-8-sig').replace('\r\n', '\n').splitlines(True), changed.decode().splitlines(True),
                                          fromfile=str(source.relative_to(ROOT)), tofile=folder + '/' + name))
        put(HERE / 'diffs' / (name + '.diff'), diff.encode())
        origins.append({'path': str(source), 'bytes': len(raw), 'sha256': sha(raw),
                        'successor': folder + '/' + name, 'successor_sha256': sha(changed)})
    # The independent reference helper is a new harness dependency.
    ast.parse((HERE / 'replay/audio_contract.py').read_text(encoding='utf-8'))
    for folder in ['builder', 'replay']:
        command = json.loads((PREVIOUS / folder / 'command.json').read_bytes())
        command['command'] = [value.replace(str(PREVIOUS), str(HERE)).replace(
            'HAS-Review-20261115-SFM-Joints-f0dd57a', 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2').replace(
            'sfm-joints-final-validation-f0dd57a-20261115', 'sfm-joints-final-validation-f0dd57a-replay2-20261115') for value in command['command']]
        command['status'] = 'UNRUN_REQUIRES_ROOT_SOURCE_REVIEW_AND_FRESH_PRIVATE_LEASE'
        save(HERE / folder / 'command.json', command)
    historical = ['verification.json']
    case = FAILED / '01-keiki_tools_chisels-groups-000'
    for name in ['engine.log', 'process-verification.json', 'private-receipt.json', 'state-comparison.json']:
        raw = (case / name).read_bytes()
        put(HERE / 'first-failure' / name, raw)
    put(HERE / 'first-failure/verification.json', (FAILED / 'verification.json').read_bytes())
    save(HERE / 'ORIGINS.json', {'format': 'has_audio_projection_successor_origins_1', 'sources': origins,
        'first_runtime_status': 'FAILED_STATE_PROJECTION_ENGINE41OF41_EXIT0_PRIVATE_CLOSED',
        'source_revision': 'f0dd57a2e568089d396fecba819ab987da658bf0',
        'private_observed_audio_payloads_copied': False, 'apps_or_parsers_run': False,
        'old_review_or_output_modified': False, 'GDScript_status': 'UNPARSED_UNRUN',
        'proposed_assertion_total': 180, 'original_proposed_assertion_total': 168,
        'delta': 'Three independent audio source cache checks per each of four examples'})
    print(json.dumps({'prepared': str(HERE), 'GDScript': 'UNPARSED_UNRUN', 'proposed_checks': 180}))


if __name__ == '__main__':
    main()
