"""Root-only stdlib boundary comparison; publish aggregates, never vectors."""
from pathlib import Path
from collections import defaultdict
from itertools import product
import argparse
import ast
import contextlib
import io
import json
import math
import sys
sys.dont_write_bytecode=True
from probe_support import ROOT,check_lease,safe_path,sha,require
from normal_metrics import EPS,length,distance,unit,pair,stats,summarize,candidate_bounds

HERE=Path(__file__).resolve().parent
MATCHER=ROOT/'experiments/source_appearance/native_coordinates_20261114/prove_coordinates_stdlib.py'
MATCHER_SHA='f9afff684c82d601029f3a6a32d187a7df476d94b96bc39eff3abe2814c2723f'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lease',type=Path,required=True);parser.add_argument('--private',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();require(Path.cwd().resolve()==ROOT,'Root cwd required')
    lease_json=json.loads(args.lease.read_bytes());lease,files=check_lease(args.lease,lease_json['files']['probe']['path'])
    private_path=safe_path(args.private);output=safe_path(args.output)
    require(private_path.is_relative_to(ROOT/'output') and output.is_relative_to(ROOT/'output') and not output.exists(),'Retained private input/new owned output required')
    private_bytes=private_path.read_bytes();public_path=private_path.with_name('PUBLIC_CAPTURE.json');public_bytes=public_path.read_bytes()
    capture=json.loads(private_bytes);public=json.loads(public_bytes)
    require(capture['format']=='has_private_blender_normal_intermediates_2' and public['format']=='has_blender_normal_capture_2' and public['private_sha256']==sha(private_bytes),'Capture identity mismatch')
    require(public['lease_sha256']==sha(args.lease.read_bytes()) and public['input_hashes']=={name:row['sha256'] for name,row in lease['files'].items()},'Lease/capture locks differ')
    original=MATCHER.read_bytes();require(sha(original)==MATCHER_SHA,'Frozen matcher changed')
    text=original.decode('utf-8-sig').split('# Source SDK forward',1)[0]
    initializer='consumed=set();geometry_errors=';anchor='   actual=[0.,0.,0.];native_result=[0.,0.,0.]'
    require(text.count(initializer)==text.count(anchor)==1,'Matcher instrumentation anchors changed')
    text=text.replace(initializer,'diagnostic_export_rows=[]\n'+initializer,1)
    text=text.replace(anchor,"   require(abs(dist(normal,source_vertices[vi][1])-ne)<1e-12,'selected native normal/error join differs')\n   diagnostic_export_rows.append((tuple(pos),tuple(normal),tuple(uv),dict(wm),vi,ne))\n"+anchor,1)
    ast.parse(text);namespace={};private_log=io.StringIO()
    try:
        with contextlib.redirect_stdout(private_log),contextlib.redirect_stderr(private_log):exec(compile(text,str(MATCHER),'exec'),namespace)
    except Exception:
        # Failure diagnostics may contain native coordinates; keep them private.
        with (private_path.parent/'PRIVATE_MATCHER_REFUSAL.log').open('x',encoding='utf-8') as handle:handle.write(private_log.getvalue())
        raise ValueError('Frozen matcher refused; private diagnostic retained, no boundary conclusion') from None
    for role,key in [('mdl','raw'),('vvd','vvd'),('glb','glb'),('parameters','params_raw')]:require(sha(namespace[key])==lease['files'][role]['sha256'],'Qualified input differs: '+role)
    require(namespace['native_path'].resolve()==files['mdl'] and namespace['native_path'].with_suffix('.vvd').resolve()==files['vvd'],'Native path alias differs')
    require(len(namespace['primitive_rows'])==4 and len(namespace['diagnostic_export_rows'])==9661 and len(capture['objects'])==2,'Exact2mesh/4primitive/9661 profile required')
    mv=namespace['mv'];native_names={row['name']:index for index,row in enumerate(namespace['native'])};require(len(native_names)==69,'Unique native group names required')
    buckets=defaultdict(list);corner_count=0;step=1e-5;corner_lengths=[];transport_lengths=[]
    for object_index,obj in enumerate(capture['objects']):
        transform=[v for row in obj['object_matrix_world'] for v in row];require(obj['corner_uv_active'] is not None,'UV0 required')
        groups=obj['vertex_groups']
        for corner,vertex in enumerate(obj['corner_vertex_indices']):
            point=mv(namespace['C'],mv(transform,obj['vertices'][vertex]));weights=defaultdict(float)
            for group,weight in obj['vertex_weights'][vertex]:
                if weight:require(groups[group] in native_names,'Unknown weighted group');weights[native_names[groups[group]]]+=weight
            uv=obj['corner_uv_active'][corner];uv=(uv[0],1.-uv[1])
            raw_corner=obj['corner_normals_stored_snapshot'][corner];transport=obj['stored_normal_transport_Y_up_raw'][corner];predicted=obj['predicted_exporter_Y_up'][corner]
            require(all(math.isfinite(v) for row in (point,uv,raw_corner,transport,predicted) for v in row),'Nonfinite captured corner')
            corner_lengths.append(abs(length(raw_corner)-1));transport_lengths.append(abs(length(transport)-1))
            buckets[tuple(round(v/step) for v in point)].append((point,dict(weights),uv,tuple(transport),tuple(predicted),object_index,corner))
            corner_count+=1
    pairs={key:[] for key in ('native_raw_to_glb_raw','native_raw_to_blender_transported_raw','native_raw_to_blender_transport_unit','blender_transported_raw_to_glb_raw','blender_transport_unit_to_glb_raw','predicted_exporter_to_glb_raw')}
    errors=[];ambiguities=normal_ambiguities=unmatched=0;candidate_count=0;bounds={key:[] for key in ('raw_best','raw_worst','unit_best','unit_worst')}
    for point,normal,uv,weights,native_vertex,raw_error in namespace['diagnostic_export_rows']:
        native=namespace['source_vertices'][native_vertex][1];pairs['native_raw_to_glb_raw'].append(pair(native,normal))
        center=tuple(round(v/step) for v in point);candidates=[]
        for delta in product((-1,0,1),repeat=3):
            for p,w,u,transport,predicted,obj,corner in buckets.get(tuple(v+d for v,d in zip(center,delta)),()):
                if distance(point,p)>=2e-6 or math.dist(uv,u)>=2e-6:continue
                if max(abs(weights.get(k,0.)-w.get(k,0.)) for k in set(weights)|set(w))>=2e-6:continue
                candidates.append((distance(normal,predicted),obj,corner,transport,predicted))
        if not candidates:unmatched+=1;continue
        candidate_count+=len(candidates);ambiguities+=len(candidates)>1
        normal_ambiguities+=len({(entry[3],entry[4]) for entry in candidates})>1
        candidates.sort();error,_,_,transport,predicted=candidates[0];errors.append(error)
        pairs['native_raw_to_blender_transported_raw'].append(pair(native,transport))
        pairs['blender_transported_raw_to_glb_raw'].append(pair(transport,normal))
        transported_unit=unit(transport)
        if transported_unit is not None:
            pairs['native_raw_to_blender_transport_unit'].append(pair(native,transported_unit));pairs['blender_transport_unit_to_glb_raw'].append(pair(transported_unit,normal))
        pairs['predicted_exporter_to_glb_raw'].append(pair(predicted,normal))
        row_bounds=candidate_bounds(native,[entry[3] for entry in candidates])
        for key,value in row_bounds.items():bounds[key].append(value)
    raw_stats=summarize(pairs['native_raw_to_glb_raw']);raw=raw_stats['raw_distance']
    reproduced=raw['count']==9661 and raw['diagnostic_above_2e_5']==8364 and abs(raw['max']-.00121654672362075)<1e-12
    coherent=unmatched==0 and len(errors)==9661 and max(errors)<2e-6 and reproduced
    require(private_path.read_bytes()==private_bytes and public_path.read_bytes()==public_bytes and MATCHER.read_bytes()==original,'Capture/matcher changed during analysis')
    for name,path in files.items():require(sha(path.read_bytes())==lease['files'][name]['sha256'],'Locked file changed during analysis')
    result={'format':'has_blender_normal_boundary_comparison_2','status':('COHERENT_BOUNDARY_MEASUREMENT' if coherent else 'BOUNDARY_PREDICTION_OR_MATCH_FAILED') if reproduced else 'ORIGINAL_RAW_GATE_REPRODUCTION_FAILED',
            'normal_fidelity':'FAILED_UNQUALIFIED; original raw2e-5 gate preserved','private_capture_sha256':sha(private_bytes),'public_capture_sha256':sha(public_bytes),'matcher_sha256':MATCHER_SHA,
            'captured_meshes':len(capture['objects']),'original_primitives':4,'captured_corners':corner_count,'exported_vertices':9661,'matched_exported_vertices':len(errors),'unmatched_exported_vertices':unmatched,
            'original_raw_gate':{'threshold':EPS,'historical_failure_reproduced':reproduced,'raw_metrics':raw},
            'metrics':{name:summarize(rows) for name,rows in pairs.items()},
            'blender_corner_local_length_deviation':stats(corner_lengths),'blender_transported_raw_length_deviation':stats(transport_lengths),'exporter_prediction_error':stats(errors),
            'original_native_match_ambiguities':namespace['equivalent_ambiguities'],'all_compatible_corner_candidates':candidate_count,'multiple_corner_candidates':ambiguities,'multiple_exact_normal_classes':normal_ambiguities,
            'native_to_blender_all_candidate_bounds':{key:stats(values) for key,values in bounds.items()},
            'normalized_direction_metrics':'Supplemental only; neither unit normalization nor a coherent exporter prediction changes the original raw failure.',
            'identity_limit':'Original compatible native multiset with normal tie-break; nearest prediction corner witness is not unique attribution. All-candidate raw bounds/exact normal-class counts retained.',
            'causal_limit':'Saved mesh corner-normal read localizes a boundary, not the original SourceIO setter call or a proved custom-normal encoder cause.',
            'private_arrays_published':False,'native_runtime_launched_by_analysis':False}
    with output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps({'output':str(output),'status':result['status'],'matched':len(errors),'unmatched':unmatched,'original_raw_failure_reproduced':reproduced}))


if __name__=='__main__':main()
