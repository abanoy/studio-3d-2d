"""Attribute/corner comparison. Keeps seams, source IDs and duplicate counts visible."""
from collections import Counter, defaultdict
import math

POSITION_TOLERANCE=0.000002
UV_TOLERANCE=0.000002
WEIGHT_TOLERANCE=0.000002


def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def cyclic(triangle):
    a,b,c=triangle
    return min((a,b,c),(b,c,a),(c,a,b))


def weights_error(a,b):return max([abs(a.get(j,0)-b.get(j,0)) for j in a.keys()|b.keys()] or [0.])


def signature(row):return (tuple(row['position']),tuple(row['uv']),tuple(sorted(row['weights'].items())))


def compare(native,triangles,derived,derived_triangles):
    """No transform fitting, nearest-surface interpolation or seam deduplication.

    Native rows with exactly equal position/UV/named-weight attributes form an
    explicitly reported equivalence class. Normal equivalence is separate.
    Distinct native classes merely within tolerance are ambiguous, not guessed.
    Oriented triangle multiplicities are compared after the declared adapter
    winding reversal, preserving UV/weight seams and coincident triangles.
    """
    def cell(p):return tuple(math.floor(x/POSITION_TOLERANCE) for x in p)
    grid=defaultdict(list);classes={};native_classes={}
    for index,row in native.items():
        grid[cell(row['position'])].append(index)
        key=signature(row)
        if key not in classes:classes[key]=len(classes)
        native_classes[index]=classes[key]
    mapping={};missing=[];near_ambiguous=[];candidate_max=0
    maximum={'position':0.,'uv':0.,'weight':0.,'nearest_possible_raw_normal':0.}
    ambiguous_normal=0
    for index,row in derived.items():
        center=cell(row['position']);candidates=[]
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                for z in [-1,0,1]:
                    for ni in grid.get((center[0]+x,center[1]+y,center[2]+z),[]):
                        n=native[ni]
                        if distance(n['position'],row['position'])<=POSITION_TOLERANCE and max(abs(a-b) for a,b in zip(n['uv'],row['uv']))<=UV_TOLERANCE and weights_error(n['weights'],row['weights'])<=WEIGHT_TOLERANCE:candidates.append(ni)
        if not candidates:missing.append(index);continue
        candidate_max=max(candidate_max,len(candidates));possible={native_classes[i] for i in candidates}
        if len(possible)!=1:near_ambiguous.append(index);continue
        mapping[index]=possible.pop()
        maximum['position']=max(maximum['position'],min(distance(native[i]['position'],row['position']) for i in candidates))
        maximum['uv']=max(maximum['uv'],min(max(abs(a-b) for a,b in zip(native[i]['uv'],row['uv'])) for i in candidates))
        maximum['weight']=max(maximum['weight'],min(weights_error(native[i]['weights'],row['weights']) for i in candidates))
        normals={tuple(native[i]['normal']) for i in candidates}
        ambiguous_normal+=int(len(normals)>1)
        maximum['nearest_possible_raw_normal']=max(maximum['nearest_possible_raw_normal'],min(distance(n,row['normal']) for n in normals))
    referenced=set(i for t in triangles for i in t) if triangles is not None else set(native)
    unseen={native_classes[i] for i in referenced}-set(mapping.values())
    point_match=not missing and not near_ambiguous and not unseen
    native_counts=Counter(native_classes[i] for i in referenced)
    derived_counts=Counter(mapping.values())
    result={'position_tolerance_m':POSITION_TOLERANCE,'uv_tolerance':UV_TOLERANCE,'weight_tolerance':WEIGHT_TOLERANCE,
            'native_base_rows':len(native),'native_referenced_rows':len(referenced),'derived_used_vertex_records':len(derived),
            'native_position_uv_weight_equivalence_classes':len(classes),'maximum_exact_native_row_candidates':candidate_max,
            'derived_rows_without_native_match':len(missing),'derived_rows_with_distinct_near_native_classes':len(near_ambiguous),
            'native_reference_classes_without_derived_match':len(unseen),'maximum_errors':maximum,
            'position_uv_vvd_named_weights_match':point_match,'raw_normal_candidates_ambiguous':ambiguous_normal,
            'vertex_record_multiplicity_equal':native_counts==derived_counts,
            'vertex_identity_limit':'Exact-equal native position/UV/weight rows remain an explicit candidate set; no unique native-ID correspondence or normal-seam identity is inferred.',
            'triangles':'UNRUN_NO_SUPPORTED_NATIVE_VTX' if triangles is None else 'NOT_COMPARED_UNMATCHED_VERTICES'}
    if triangles is not None and point_match:
        expected=Counter(cyclic(tuple(native_classes[i] for i in reversed(t))) for t in triangles)
        actual=Counter(cyclic(tuple(mapping[i] for i in t)) for t in derived_triangles)
        result.update({'triangles':'ATTRIBUTED_ORIENTED_MULTIPLICITY_MATCH' if expected==actual else 'MISMATCH',
                       'native_triangles':len(triangles),'derived_triangles':len(derived_triangles),
                       'missing_native_triangle_multiplicity':sum((expected-actual).values()),
                       'unexpected_derived_triangle_multiplicity':sum((actual-expected).values()),
                       'triangle_scope':'Oriented position/UV/named-VVD-weight corners and duplicate multiplicity; normal seams, flex and hardware palette state are separate.'})
    return result
