"""Source-only transaction proposal. Writes this packet, never the review."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[2] / 'has-neon-review-20261116-c2d52ff'
PINS = {'world_selection.gd': 'f5b877745a63cb4d1aa2ff8d40a05f456c4979664efc70d275599410dab07637',
        'workspace_layout.gd': '7da378b1147266fbecdabf63422e19b1ee06024c40083d6fcf4ed8e93540bcfd'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def function(raw, name):
    pattern = rb'(?m)^func ' + name.encode() + rb'\([^\r\n]*\r\n'
    match = re.search(pattern, raw)
    assert match, name
    following = re.search(rb'(?m)^func ', raw[match.end():])
    end = match.end() + following.start() if following else len(raw)
    return raw[match.start():end]


def replace_once(raw, before, after):
    assert raw.count(before) == 1, before
    return raw.replace(before, after, 1)


def main():
    assert not (HERE / 'INDEX.json').exists()
    source = {}
    for name, digest in PINS.items():
        raw = (REVIEW / 'src' / name).read_bytes()
        assert sha(raw) == digest
        assert raw.count(b'\r\r\n') == 0
        source[name] = raw
    old = source['world_selection.gd']
    original_setter = function(old, 'set_rail')
    setter = replace_once(original_setter,
                          b'func set_rail(on: bool, force := false) -> void:',
                          b'func set_rail(on: bool, force := false) -> bool:')
    assert setter.count(b': return\r\n') == 4
    setter = setter.replace(b': return\r\n', b': return false\r\n')
    setter = replace_once(setter,
                          b'if on == rail_mode and not force: return false',
                          b'if on == rail_mode and not force: return true')
    setter = setter.rstrip(b'\r\n') + b'\r\n\treturn true\r\n\r\n'
    selection = replace_once(old, original_setter, setter)
    # Invert every changed token and require exact original bytes, including fonts.
    inverse_setter = setter.removesuffix(b'\treturn true\r\n\r\n') + b'\r\n'
    inverse_setter = inverse_setter.replace(b'-> bool:', b'-> void:', 1)
    inverse_setter = inverse_setter.replace(b': return false\r\n', b': return\r\n')
    inverse_setter = inverse_setter.replace(b': return true\r\n', b': return\r\n')
    assert inverse_setter == original_setter
    assert selection.replace(setter, original_setter, 1) == old

    old_layout = source['workspace_layout.gd']
    refresh = function(old_layout, 'refresh_world_mode')
    new_refresh = replace_once(refresh,
        b'if rail==world_rail and not force:',
        b'if rail==world_rail and app.world_selection.rail_mode==rail and not force:')
    new_refresh = replace_once(new_refresh,
        b'\tworld_rail=rail\r\n\tapp.world_selection.set_rail(rail,force)\r\n',
        b'\tif not app.world_selection.set_rail(rail,force):return\r\n\tworld_rail=rail\r\n')
    floating = function(old_layout, 'float_panel')
    new_floating = replace_once(floating,
        b'\trefresh_slots();save_later()\r\n',
        b'\trefresh_slots();save_later()\r\n\tif id=="world":call_deferred("refresh_world_mode",true)\r\n')
    layout = replace_once(old_layout, refresh, new_refresh)
    layout = replace_once(layout, floating, new_floating)
    assert layout.replace(new_refresh, refresh, 1).replace(new_floating, floating, 1) == old_layout
    proposed = {'world_selection.gd': selection, 'workspace_layout.gd': layout}
    proof = {'status': 'SOURCE_ONLY_NOT_RUNTIME_QUALIFIED', 'files': {},
             'no_engines_cim_native_git': True, 'review_modified': False,
             'new_tests_run': False, 'runtime_tests_required': ['rail45', 'lifecycle29', 'controls48', 'standard12504'],
             'changed_functions': {'world_selection.gd': ['set_rail'],
                                   'workspace_layout.gd': ['refresh_world_mode', 'float_panel']}}
    for name, raw in proposed.items():
        target = HERE / (name + '.proposed')
        assert not target.exists()
        target.write_bytes(raw)
        names = re.findall(rb'(?m)^func (\w+)\(', source[name])
        for fn in names:
            if fn.decode() not in proof['changed_functions'][name]:
                assert function(source[name], fn.decode()) == function(raw, fn.decode()), fn
        proof['files'][name] = {'before_sha256': PINS[name], 'after_sha256': sha(raw),
                                'bytes': len(raw), 'exact_inverse': True,
                                'all_other_functions_byte_exact': True,
                                'CRLF': raw.count(b'\r\n'), 'CRCRLF': raw.count(b'\r\r\n')}
    for name in PINS:
        assert sha((REVIEW / 'src' / name).read_bytes()) == PINS[name]
    (HERE / 'SOURCE_PROOF.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
