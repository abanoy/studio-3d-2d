"""Prove the failed projection and independent audio reference without an app."""
from copy import deepcopy
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CASE = ROOT / 'output/sfm-joints-final-validation-f0dd57a-20261115/01-keiki_tools_chisels-groups-000'
sys.path.insert(0, str(HERE / 'replay'))
from audio_contract import audio_expectations, audio_rows


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_cache(clip, expected, cache, actual_file_sha, pcm):
    source = clip.get('source', {})
    expected_path = (cache / expected['path']).resolve()
    actual_path = Path(source.get('path', '')).resolve()
    return (set(source) == {'channels', 'frames', 'name', 'path', 'pcm', 'rate', 'sha256'} and
            actual_path == expected_path and actual_path.is_relative_to(cache.resolve()) and
            clip['id'] == expected['id'] and clip['path'] == expected['path'] and
            clip['sha256'] == source['sha256'] == actual_file_sha == expected['sha256'] and
            source['name'] == expected['source_name'] and
            source['channels'] == expected['channels'] and source['rate'] == expected['rate'] and
            source['frames'] == expected['frames'] and len(pcm) == expected['pcm_bytes'] and
            sha(pcm) == expected['pcm_sha256'])


def main():
    spec = importlib.util.spec_from_file_location('portable_review_comparison', ROOT / 'tools/verify_owner_review.py')
    pure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pure)
    request = json.loads((CASE / 'request.json').read_bytes())
    package = Path(request['package'])
    before_package = package.read_bytes()
    expected = pure.metadata(package)
    references = audio_expectations(package, expected['audio'])
    assert len(references) == 1
    observed_inputs = {}
    phases = []
    for phase in ['before', 'after', 'extra']:
        path = CASE / ('observed-' + phase + '.json')
        raw = path.read_bytes()
        observed_inputs[path.name] = {'bytes': len(raw), 'sha256': sha(raw)}
        observed = json.loads(raw)
        differences = pure.compare(expected, observed)
        assert differences == [{'at': '$.audio', 'reason': 'dictionary keys', 'missing': [], 'added': ['source']}]
        clip = audio_rows(observed['audio'])[0]
        source = clip['source']
        # The failed JSON observer stringified PackedByteArray. Decode only
        # this own retained bounded decimal list; no payload is written/printed.
        values = json.loads(source['pcm'])
        assert len(values) <= 64 * 1024 * 1024 and all(type(value) is int and 0 <= value <= 255 for value in values)
        pcm = bytes(values)
        source_path = Path(source['path'])
        cache = Path(json.loads((CASE / 'result.json').read_bytes())['project_folder'])
        file_sha = sha(source_path.read_bytes())
        assert valid_cache(clip, references[0], cache, file_sha, pcm)
        portable = deepcopy(observed)
        for item in audio_rows(portable['audio']):
            item.pop('source')
        assert pure.compare(expected, portable) == []
        negative = []
        for key, value in [('sha256', '0'*64), ('channels', 2), ('rate', 44100), ('frames', 24001),
                           ('name', 'wrong.wav'), ('path', str(ROOT / 'outside-cache.wav'))]:
            broken = deepcopy(clip)
            broken['source'][key] = value
            assert not valid_cache(broken, references[0], cache, file_sha, pcm)
            negative.append(key)
        broken = deepcopy(clip); broken['source']['unexpected'] = True
        assert not valid_cache(broken, references[0], cache, file_sha, pcm)
        assert not valid_cache(clip, references[0], cache, '0'*64, pcm)
        bad_pcm = bytearray(pcm); bad_pcm[0] ^= 1
        assert not valid_cache(clip, references[0], cache, file_sha, bad_pcm)
        for field, replacement in [('start_frame', 25), ('gain_db', -1), ('muted', True)]:
            changed = deepcopy(portable)
            audio_rows(changed['audio'])[0][field] = replacement
            assert pure.compare(expected, changed)
        phases.append({'phase': phase, 'original_difference_exact': True, 'portable_projection_equal': True,
                       'independent_WAV_and_PCM_binding': True, 'negative_cache_controls': negative + ['unknown_field', 'file_sha', 'PCM_bit_flip'],
                       'authored_change_refusals': ['start_frame', 'gain_db', 'muted']})
    assert package.read_bytes() == before_package
    result = {'format': 'has_audio_replay_projection_cpu_audit_1', 'passed': True,
              'package_sha256': sha(before_package), 'observed_private_inputs': observed_inputs,
              'independent_audio_references': references, 'phases': phases,
              'runtime_payloads_published': False, 'apps_or_engine_parser_run': False,
              'comparison_tolerance': 'Existing1e-12absolute; unchanged dictionaries/strings/order/booleans',
              'GDScript_status': 'UNPARSED_UNRUN', 'old_observed_states_modified': False}
    with (HERE / 'CPU_AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': True, 'phases': len(phases), 'cache_negative_controls': 27,
                      'authored_change_negative_controls': 9, 'media_bytes_written': 0}))


if __name__ == '__main__':
    main()
