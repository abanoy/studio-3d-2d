"""First refused bone only: private matrices, public scalar errors, no repair."""
from contextlib import contextmanager
from pathlib import Path
import json
import math
import sys

BODY_SHA = 'd916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7'
ERROR = 'native_Blender_rest_matrix_mismatch'


def maximum(a, b, indices=range(16)):
    return max(abs(a[i]-b[i]) for i in indices)


def normalized(a, b):
    return max(abs(x-y)/max(1.,abs(y)) for x,y in zip(a,b))


def emit(C, request, local):
    # Called only at the exact unchanged reference proof's failed require.
    row = local['row']; index = row['index']; scale = local['scale']
    if local['expected_native_mdl_sha256'] != BODY_SHA or request['sha256'] != BODY_SHA:
        raise ValueError('EXACT_BODY_DIAGNOSTIC_PROFILE_REQUIRED')
    actual = tuple(local['actual']); expected = tuple(local['expected'])
    if len(actual) != 16 or len(expected) != 16 or C.close(actual,expected):
        raise ValueError('ACTUAL_UNCHANGED_FAILED_REST_PREDICATE_REQUIRED')
    parent = row['parent']; db = local['db']; pb = local['pb']
    parent_actual = C.IDENTITY if parent < 0 else C.matrix(local['data'][parent].matrix_local)
    parent_expected = C.IDENTITY if parent < 0 else tuple(local['expected_global'][parent])
    source_local = C.local_rest(row['position'],row['quat'],scale)
    native_parent_step = C.multiply(parent_actual,source_local)
    # Match the PINNED factory's mathutils primitives, without creating/editing
    # any Blender object/bone, modifier, constraint, skin or source property.
    from mathutils import Matrix, Quaternion, Vector
    x,y,z,w = row['quat']
    float_local_object = Matrix.LocRotScale(Vector(row['position'])*scale,
                                          Quaternion((w,x,y,z)), (1,1,1))
    float_local = C.matrix(float_local_object)
    float_parent_step = C.matrix((db.parent.matrix_local if db.parent else Matrix.Identity(4)) @ float_local_object)
    private = {
        'format':'has_private_first_native_rest_refusal_1','private_do_not_publish':True,
        'native_mdl_sha256':BODY_SHA,'original_error_code':ERROR,'native_index':index,
        'native_name':row['name'],'native_parent_index':parent,
        'native_rest_words_uint32':row['rest_words_uint32'],
        'native_quaternion':row['quat'],'native_position':row['position'],
        'actual_global_rest':actual,'independent_native_global_rest':expected,
        'actual_parent_global_rest':parent_actual,'independent_parent_global_rest':parent_expected,
        'independent_native_local_rest':source_local,'current_parent_times_native_local':native_parent_step,
        'mathutils_local_rest':float_local,'current_parent_times_mathutils_local':float_parent_step,
        'actual_pose_matrix':C.matrix(pb.matrix),'actual_data_bone_pointer':C.pointer(db),
        'actual_pose_bone_pointer':C.pointer(pb),'actual_armature_pointer':C.pointer(local['armature']),
        'diagnostic_reads_only':True,'rest_tolerance_changed':False,'model_repaired':False,
        'export_binding_qualified':False,'native_runtime_binding_qualified':False,
    }
    public = {
        'first_native_index':index,
        'global_max_error':maximum(actual,expected),
        'global_translation_error':maximum(actual,expected,(3,7,11)),
        'global_basis_error':maximum(actual,expected,(0,1,2,4,5,6,8,9,10)),
        'global_normalized_error':normalized(actual,expected),
        'parent_global_error':maximum(parent_actual,parent_expected),
        'current_parent_native_local_error':maximum(actual,native_parent_step),
        'current_parent_mathutils_local_error':maximum(actual,float_parent_step),
        'mathutils_vs_native_local_error':maximum(float_local,source_local),
        'native_quaternion_unit_error':abs(math.sqrt(sum(x*x for x in row['quat']))-1.),
    }
    if not all(type(value) in (int,float) and math.isfinite(value) for value in public.values()):
        raise ValueError('FINITE_PUBLIC_DIAGNOSTIC_SCALARS_REQUIRED')
    private['scalar_errors'] = public
    output = Path(request['output']) / 'PRIVATE_first_rest_refusal.json'
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(private,stream,separators=(',',':'),allow_nan=False);stream.write('\n')
    print('JUNKO_PART_REST_DIAGNOSTIC '+json.dumps(public,separators=(',',':'),allow_nan=False),flush=True)


@contextmanager
def capture(C, request):
    if request.get('sha256') != BODY_SHA:
        # Other profiles retain the original proof path without observation.
        yield
        return
    original_require = C.require
    original_prove_code = C.prove_native_blender.__code__
    observed = False

    def diagnostic_require(condition, code):
        nonlocal observed
        if not condition and code == ERROR and not observed:
            frame = sys._getframe(1)
            try:
                if frame.f_code is original_prove_code:
                    observed = True
                    try:
                        emit(C,request,frame.f_locals)
                    except Exception as error:
                        # Preserve the unchanged original refusal even if a
                        # diagnostic cannot be captured. No native values leak.
                        print('JUNKO_PART_REST_DIAGNOSTIC_CAPTURE_FAILED '+json.dumps({'error_type':type(error).__name__}),flush=True)
            finally:
                del frame
        return original_require(condition,code)

    C.require = diagnostic_require
    try:
        yield
    finally:
        C.require = original_require
