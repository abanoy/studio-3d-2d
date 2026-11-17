"""CPU-only construction of a diagnostic derivative; does not launch Godot."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'neon_waveform_palette_successor_20261117' / 'waveform_levels_smoke.proposed.gd'
EXPECTED = '9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE / 'INDEX.json').exists(), 'Sealed packet must not be regenerated'
    original = BASE.read_bytes()
    assert digest(original) == EXPECTED
    text = original.decode('utf-8')
    newline = '\r\n' if b'\r\n' in original else '\n'
    additions = []

    def before(anchor, addition):
        nonlocal text
        addition = addition.replace('\n', newline)
        assert text.count(anchor) == 1, anchor
        text = text.replace(anchor, addition + anchor, 1)
        additions.append(addition)

    before('\tfor i in range(fine.size()):', '''\tvar diagnostic_clip_rect: Rect2=view.audio_rect(0)
\tprint("WAVEFORM_PALETTE_CONTEXT ",JSON.stringify({"format":"has_waveform_palette_context_1","neon":neon_style,"selected_audio":view.audio_selected,"focus_lane":view.focus_lane,"fill_source_rgba":[0.239,0.863,0.592,0.12],"wave_source_rgba":[0.239,0.863,0.592,0.85],"body_expected_rgb":[neon_body.r,neon_body.g,neon_body.b],"border_expected_rgb":[neon_border.r,neon_border.g,neon_border.b],"view_global":[view.global_position.x,view.global_position.y],"view_size":[view.size.x,view.size.y],"clip_rect":[diagnostic_clip_rect.position.x,diagnostic_clip_rect.position.y,diagnostic_clip_rect.size.x,diagnostic_clip_rect.size.y],"audio_y":view.audio_y(),"tracks_scroll_vertical":tracks_scroll.scroll_vertical,"dock_scroll_vertical":dock_scroll.scroll_vertical,"image_size":[screen.get_width(),screen.get_height()],"audio_muted":view.audio_clips[0].get("muted",false),"text_drawn_after_waveform":true}))
''')
    before('\t\t# Check all nine pixels before reading any, and prove they belong to the visible tracks.', '''\t\tvar diagnostic_raw_x: float=view.x(float(i)/fine.size()*view.duration)
\t\tvar diagnostic_right_x: float=view.x(float(i+1)/fine.size()*view.duration)
\t\tvar diagnostic_border: bool=view.audio_selected==0 and diagnostic_raw_x<=diagnostic_clip_rect.position.x
\t\tvar diagnostic: Dictionary={"format":"has_waveform_transient_sample_1","index":i,"value":fine[i],"raw_x":diagnostic_raw_x,"renderer_right_x":diagnostic_right_x,"renderer_culled_by_clip":diagnostic_right_x<=diagnostic_clip_rect.position.x or diagnostic_raw_x>=diagnostic_clip_rect.end.x,"amplitude":fine[i]*11,"clip_rect":[diagnostic_clip_rect.position.x,diagnostic_clip_rect.position.y,diagnostic_clip_rect.size.x,diagnostic_clip_rect.size.y],"global_point":[point.x,point.y],"integer_point":[Vector2i(point).x,Vector2i(point).y],"selected_left_border":diagnostic_border,"neon":neon_style,"selected_audio":view.audio_selected}
''')
    before('\t\t\tcontinue'+newline+'\t\tif neon_style:', '''\t\t\tdiagnostic["sample_bounds_valid"]=false
\t\t\tdiagnostic["expected_rgb"]=[neon_border.r,neon_border.g,neon_border.b] if neon_style and diagnostic_border else [neon_body.r,neon_body.g,neon_body.b] if neon_style else [green.r,green.g,green.b]
\t\t\tdiagnostic["found"]=false;diagnostic["samples"]=[]
\t\t\tprint("WAVEFORM_TRANSIENT_DIAGNOSTIC ",JSON.stringify(diagnostic))
''')
    before('\t\tfor dx in range(-1,2):', '''\t\tvar diagnostic_pixels: Array=[]
''')
    before('\t\t\t\tif absf(pixel.r-green.r)<.02 and absf(pixel.g-green.g)<.02 and absf(pixel.b-green.b)<.02:found=true', '''\t\t\t\tdiagnostic_pixels.append({"offset":[dx,dy],"rgb":[pixel.r,pixel.g,pixel.b],"alpha":pixel.a})
''')
    before('\t\tif found:bars+=1', '''\t\tdiagnostic["sample_bounds_valid"]=true;diagnostic["expected_rgb"]=[green.r,green.g,green.b];diagnostic["found"]=found;diagnostic["samples"]=diagnostic_pixels
\t\tprint("WAVEFORM_TRANSIENT_DIAGNOSTIC ",JSON.stringify(diagnostic))
''')
    inverse = text
    for addition in reversed(additions):
        assert inverse.count(addition) == 1
        inverse = inverse.replace(addition, '', 1)
    assert inverse.encode('utf-8') == original
    old_checks = [line for line in original.decode().splitlines() if 'check(' in line]
    new_checks = [line for line in text.splitlines() if 'check(' in line]
    assert old_checks == new_checks and text.count('check(') == 14
    predicate = 'if absf(pixel.r-green.r)<.02 and absf(pixel.g-green.g)<.02 and absf(pixel.b-green.b)<.02:found=true'
    assert predicate in text and text.count(predicate) == 1
    assert 'check(bars==4,"actual zoomed viewport displays all four independent transient bars")' in text
    proposed = text.encode('utf-8')
    (HERE / 'waveform_levels_smoke.diagnostic.gd').write_bytes(proposed)
    proof = {'format':'has_waveform_diagnostic_source_proof_1','status':'SOURCE_ONLY_UNPARSED_UNRUN',
             'base_path':str(BASE),'base_sha256':digest(original),'diagnostic_sha256':digest(proposed),
             'base_bytes':len(original),'diagnostic_bytes':len(proposed),'insertion_blocks':len(additions),
             'inverse_removes_only_diagnostic_insertions':True,'all_14_check_source_lines_byte_exact':True,
             'RGB_tolerance_predicate_byte_exact':True,'four_transient_predicate_byte_exact':True,
             'line_endings_preserved':True,'expectation_palette_or_product_changes':False,
             'native_or_engine_calls':False,'pixel_samples_per_valid_positive_bucket':9}
    (HERE / 'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
