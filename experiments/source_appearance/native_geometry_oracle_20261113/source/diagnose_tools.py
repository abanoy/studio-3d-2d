"""Metadata-only relation diagnostics; no tolerance, transform or identity fitting."""
import json
from pathlib import Path
import time
import compare_cases as R
import compare_mesh as C
import native_reader as N
import glb_reference as G
import inspect_cases as I


def main():
    receipt=json.loads(I.RECEIPT.read_bytes())
    files={extension:Path(next(r['path'] for r in receipt['staged'] if r['case']=='keiki_tools_chisels' and r['member'].lower().endswith(extension))) for extension in ['.mdl','.vvd','.dx90.vtx']}
    glb_path=I.PRIOR/'conversion-run-1794546473806155800/04-keiki_tools_chisels-groups-000/bundle/scene.glb'
    protected=[I.stamp(p) for p in [*files.values(),glb_path]]
    m=N.mdl(files['.mdl'].read_bytes());v=N.vvd(files['.vvd'].read_bytes(),m['checksum'],len(m['bones']))
    group=m['groups'][0];model=group['models'][0];mesh=model['meshes'][0]
    native=R.native_mesh_records(m,v,group,model,mesh)
    primitive=next(p for p in R.derived_meshes(G.GLB(glb_path.read_bytes())) if p['source_name']=='tools.dmx')
    ambiguous=[];covered=set();without=0
    for index,row in primitive['vertices'].items():
        candidates=[]
        for ni,n in native.items():
            if C.distance(n['position'],row['position'])<=C.POSITION_TOLERANCE and max(abs(a-b) for a,b in zip(n['uv'],row['uv']))<=C.UV_TOLERANCE and C.weights_error(n['weights'],row['weights'])<=C.WEIGHT_TOLERANCE:candidates.append(ni)
        covered.update(candidates);without+=int(not candidates)
        keys={C.signature(native[i]) for i in candidates}
        if len(keys)>1:
            pairs=[]
            for ai,first in enumerate(candidates):
                for second in candidates[ai+1:]:
                    a,b=native[first],native[second]
                    pairs.append({'native_lod0_rows':[first,second],'native_position_separation_m':C.distance(a['position'],b['position']),
                                  'native_uv_max_difference':max(abs(x-y) for x,y in zip(a['uv'],b['uv'])),
                                  'native_named_weight_max_difference':C.weights_error(a['weights'],b['weights']),
                                  'native_raw_normal_difference':C.distance(a['normal'],b['normal'])})
            ambiguous.append({'derived_used_vertex_index':index,'native_lod0_candidates':candidates,
                              'candidate_position_errors_m':[C.distance(native[i]['position'],row['position']) for i in candidates],
                              'candidate_raw_normal_errors':[C.distance(native[i]['normal'],row['normal']) for i in candidates],
                              'pairs':pairs})
    result={'format':'has_native_tools_correspondence_diagnostic_1','scope':'Only source IDs and scalar separations; no decoded geometry arrays persisted',
            'tolerances_unchanged':True,'nearest_choice_or_transform_fit_performed':False,'native_rows':len(native),'derived_used_rows':len(primitive['vertices']),
            'derived_rows_without_any_native_attribute_candidate':without,'native_rows_not_in_any_derived_candidate_set':len(set(native)-covered),
            'distinct_near_native_class_ambiguities':ambiguous,'protected_before':protected,'protected_after':[I.stamp(p['path']) for p in protected]}
    result['protected_unchanged']=result['protected_before']==result['protected_after']
    folder=I.TASK/'diagnostics'/str(time.time_ns());I.write(folder/'tools-correspondence.json',result)
    print(json.dumps({'folder':str(folder),'derived_without_candidate':without,'native_uncovered':result['native_rows_not_in_any_derived_candidate_set'],'ambiguities':ambiguous,'preserved':result['protected_unchanged']}))


if __name__=='__main__':main()
