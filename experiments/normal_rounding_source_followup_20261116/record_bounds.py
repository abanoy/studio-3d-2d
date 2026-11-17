"""Read pinned source and compute rounding bounds only; no native/app probe."""
from pathlib import Path
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
OLD=ROOT/'experiments/resume_coordinates_20261115/NORMAL_DIAGNOSIS.json'


def sha(body):return hashlib.sha256(body).hexdigest()


def main():
    assert sha(LOCK.read_bytes())==LOCK_SHA
    lock=json.loads(LOCK.read_bytes());exporter=Path(lock['exporter_root'])
    sourceio=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
    specs=[
        (exporter/'blender/exp/primitive_extract.py','exporter_noncache_sources','blender/exp/primitive_extract.py',[(1447,'np.round(self.normals, ROUNDING_DIGIT)')]),
        (exporter/'io/com/constants.py','exporter_noncache_sources','io/com/constants.py',[(159,'ROUNDING_DIGIT = 4')]),
        (sourceio/'blender_bindings/models/mdl49/import_mdl.py','sourceio_files','blender_bindings/models/mdl49/import_mdl.py',[(90,"normals_split_custom_set_from_vertices(vertices['normal'])")]),
    ]
    reads=[]
    for path,catalogue,relative,anchors in specs:
        body=path.read_bytes();lines=body.decode('utf-8').splitlines();expected=lock[catalogue][relative]
        assert sha(body)==expected['sha256'],relative
        for line,needle in anchors:assert needle in lines[line-1]
        reads.append({'path':str(path),'sha256':sha(body),'bytes':len(body),'approved_lock_hash_matches':True,'line_anchors':[line for line,_ in anchors]})
    old=json.loads(OLD.read_bytes())
    delta=math.sqrt(3)*0.5*10**-4
    # Stable expression for2sin(arcsin(delta)/2); requires a unit input and
    # component rounding error <=0.5e-4 before normalization, delta<1.
    tight=delta*math.sqrt(2/(1+math.sqrt(1-delta*delta)))
    simple=2*delta
    maximum=old['metrics']['raw_error']['max']
    native_radial=old['metrics']['native_length_error']['max']
    with_native_radius=delta+native_radial
    augmented=with_native_radius*math.sqrt(2/(1+math.sqrt(1-with_native_radius**2)))+native_radial
    assert maximum>simple and maximum>augmented
    result={'format':'has_normal_rounding_source_bounds_1','status':'SOURCE_ONLY_EXISTING_NORMAL_GATE_STILL_FAILED',
            'approved_shared_lock_sha256':LOCK_SHA,'source_reads':reads,
            'original_diagnosis_sha256':sha(OLD.read_bytes()),'original_gate':2e-5,'matched_vertices':old['vertices_matched'],
            'recorded_max_raw_error':maximum,'recorded_failures_above_gate':old['metrics']['raw_error']['above_2e_5'],
            'round4_component_max_error':0.5e-4,'round4_vector_error_delta':delta,
            'simple_normalized_distance_upper_bound':simple,'tight_unit_input_normalized_chord_bound':tight,
            'bound_including_recorded_native_radial_error_to_raw_reference':augmented,
            'observed_max_over_simple_bound':maximum/simple,
            'assumptions':['Unit or recorded-near-unit input.','Ideal component rounding then normalization; NumPy/exporter floating-point arithmetic is not executed or independently bounded here.','Excludes any extra matrix conditioning, Blender normal encoding/evaluation, rematching or other pipeline stage.','Axis-only orthogonal conversion preserves the bound.'],
            'conclusion':'Four-decimal rounding alone is insufficient for the recorded maximum. This does not identify the missing factor or reproduce any Blender/SourceIO cause.',
            'actual_Blender_Godot_converter_or_private_geometry_probe_run':False,
            'normal_fidelity':'FAILED_UNQUALIFIED;2e-5 unchanged',
            'next_probe_gate':'Fresh complete default full PASS plus authoritative root process/receipt closure, then separately approved exact probe/source/input pins and fresh private output. Existing prepared Blender/corner capture remains unrun.',
            'installed_sources_modified':False}
    (HERE/'BOUNDS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key not in ('source_reads','assumptions')},indent=2))


if __name__=='__main__':main()
