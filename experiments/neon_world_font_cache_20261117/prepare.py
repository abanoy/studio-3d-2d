"""Source-only single-function font lifetime successor; does not edit REVIEW."""
from pathlib import Path
import hashlib
import json
import re
import difflib

HERE=Path(__file__).resolve().parent
REVIEW=HERE.parents[1].parent/'has-neon-review-20261116-c2d52ff'
BEFORE='fb2cfa70ab94dbf4d9a57c3f041cb10916aed7e828c94af14feee6ade0b790de'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    raw=(REVIEW/'src/world_selection.gd').read_bytes();assert sha(raw)==BEFORE
    newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode().replace('\r\n','\n')
    match=re.search(r'^func tree_font\(\) -> Font:\n.*?(?=^func )',text,re.M|re.S);assert match
    original=match[0]
    expected='''func tree_font() -> Font:
\t# Neon: the interface font, with Yu Gothic UI kept as the fallback for Japanese object names.
\tvar japanese := SystemFont.new(); japanese.font_names = PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"])
\tif not StudioTheme.is_neon(): return japanese
\tvar font := SystemFont.new(); font.font_names = PackedStringArray(StudioTheme.UI_FONTS); font.font_weight = 500
\tfont.fallbacks = [japanese]
\treturn font

'''
    assert original==expected
    replacement='''func tree_font() -> Font:
\t# Neon: the interface font, with Yu Gothic UI kept as the fallback for Japanese object names.
\t# Retain both original profiles so docking reuses the same Font resources.
\tvar neon := StudioTheme.is_neon()
\tvar key := "world_tree_neon" if neon else "world_tree_classic"
\tif StudioTheme.fonts.has(key): return StudioTheme.fonts[key]
\tvar japanese := SystemFont.new(); japanese.font_names = PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"])
\tif not neon:
\t\tStudioTheme.fonts[key] = japanese
\t\treturn japanese
\tvar font := SystemFont.new(); font.font_names = PackedStringArray(StudioTheme.UI_FONTS); font.font_weight = 500
\tfont.fallbacks = [japanese]
\tStudioTheme.fonts[key] = font
\treturn font

'''
    proposed=text[:match.start()]+replacement+text[match.end():]
    assert proposed.replace(replacement,original,1).replace('\n',newline).encode()==raw
    output=proposed.replace('\n',newline).encode()
    assert output.count(b'\r')==output.count(b'\n')==output.count(b'\r\n') and b'\r\r\n' not in output
    (HERE/'world_selection.gd.proposed').write_bytes(output)
    (HERE/'tree_font_only.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),output.decode().splitlines(True),fromfile='a/src/world_selection.gd',tofile='b/src/world_selection.gd')),encoding='utf-8',newline='')
    proof={'format':'has_neon_world_font_cache_source_proof_1','status':'SOURCE_ONLY_UNPARSED_UNRUN','before_sha256':BEFORE,'proposed_sha256':sha(output),'before_bytes':len(raw),'proposed_bytes':len(output),'only_changed_function':'tree_font','exact_inverse':True,'CRLF_preserved':True,'font_family_weight_and_fallback_values_unchanged':True,'cache_owner':'existing StudioTheme.fonts static dictionary','new_cache_keys':['world_tree_classic','world_tree_neon'],'cache_stores_Font_resources_only':True,'prior_lifecycle_guards_preserved':True,'REVIEW_edited':False,'engines_CIM_Git_executed':False}
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof))


if __name__=='__main__':main()
