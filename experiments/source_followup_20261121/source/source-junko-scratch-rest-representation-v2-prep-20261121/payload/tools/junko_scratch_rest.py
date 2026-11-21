"""Owned scratch bones only. Never edits the observed armature or SourceIO."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import sys

PRIVATE_SHA = 'a929dcc301d6d85f51a66ad9ca6ffc691958fd80393a8ae0360c593633a8f4cd'
BODY_SHA = 'd916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7'
LENGTHS = (.01905, .05, .1, .25, .5, 1., 2.)
METHODS = ('setter', 'setter_align', 'gltf_axes')


def need(ok, code):
    if not ok:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def matrix(value):
    result = tuple(float(value[r][c]) for r in range(4) for c in range(4))
    need(all(math.isfinite(x) for x in result), 'FINITE_SCRATCH_MATRIX')
    return result


def finite_matrix(value):
    need(type(value) in (list, tuple) and len(value) == 16 and
         all(type(x) in (int, float) and math.isfinite(x) for x in value), 'EXACT_FINITE_MATRIX')
    return tuple(value)


def maximum(a, b):
    return max(abs(x-y) for x,y in zip(a,b))


def schedule():
    return [('original_baseline', None)] + [(method, length) for method in METHODS for length in LENGTHS]


def profile(raw):
    need(sha(raw) == PRIVATE_SHA, 'EXACT_PRIVATE_FACTORY_CAPTURE')
    value = json.loads(raw)
    need(value.get('format') == 'has_private_first_native_rest_refusal_1' and
         value.get('private_do_not_publish') is True and value.get('native_mdl_sha256') == BODY_SHA and
         type(value.get('native_index')) is int and value['native_index'] == 38,
         'EXACT_NATIVE38_CAPTURE')
    boundary = value.get('factory_boundaries')
    need(type(boundary) is dict and boundary.get('actual_load_refpose') is False and
         boundary.get('actual_refpose_branch_entered') is False and
         boundary.get('factory_calls') == 1 and boundary.get('assignments') == 1,
         'OBSERVED_INACTIVE_REFPOSE')
    for key in ('assigned_matrix', 'object_return_matrix'):
        finite_matrix(boundary[key])
    for key in ('before_assignment', 'immediate_edit_getter'):
        row = boundary[key]
        finite_matrix(row['matrix'])
        for field in ('head', 'tail'):
            need(type(row[field]) is list and len(row[field]) == 3 and
                 all(type(x) in (int,float) and math.isfinite(x) for x in row[field]), 'FINITE_ENDPOINTS')
        need(type(row['roll']) in (int,float) and math.isfinite(row['roll']), 'FINITE_ROLL')
    finite_matrix(value['independent_native_global_rest'])
    return value


def load_close(raw, expected_sha):
    need(sha(raw) == expected_sha, 'PINNED_REFERENCE_CLOSE_SOURCE')
    nodes = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef) and node.name == 'close']
    need(len(nodes) == 1, 'ONE_REFERENCE_CLOSE')
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'pinned-close-only', 'exec'), namespace)
    return namespace['close']


def measured_row(method, requested_length, getter, rest, reference, assigned, close):
    getter = finite_matrix(getter); rest = finite_matrix(rest)
    return {'method': method, 'requested_length': requested_length,
            'getter_to_assignment_error': maximum(getter, assigned),
            'rest_to_assignment_error': maximum(rest, assigned),
            'rest_to_native_reference_error': maximum(rest, reference),
            'getter_to_rest_error': maximum(getter, rest),
            'original_close_rest_assignment': bool(close(rest, assigned)),
            'original_close_rest_native': bool(close(rest, reference))}


def run_owned(value, close):
    import bpy
    from mathutils import Matrix, Vector
    need(tuple(bpy.app.version[:2]) == (5,1) and bpy.context.window is not None and
         bpy.context.mode == 'OBJECT', 'FRESH_BLENDER51_OBJECT_CONTEXT')
    window = bpy.context.window; original_scene = window.scene
    original_active = bpy.context.view_layer.objects.active
    original_active_pointer = int(original_active.as_pointer()) if original_active else 0
    original_selection = tuple(sorted(int(obj.as_pointer()) for obj in bpy.context.selected_objects))
    def inventory():
        return {'objects': tuple(sorted((int(obj.as_pointer()), tuple(matrix(obj.matrix_world)),
                     int(obj.data.as_pointer()) if obj.data else 0) for obj in bpy.data.objects)),
                'armatures': tuple(sorted(int(x.as_pointer()) for x in bpy.data.armatures)),
                'scenes': tuple(sorted(int(x.as_pointer()) for x in bpy.data.scenes))}
    before = inventory(); scene = None; data = None; obj = None
    rows = []; private_rows = []; cleanup = False
    boundary = value['factory_boundaries']; before_bone = boundary['before_assignment']
    assigned = finite_matrix(boundary['assigned_matrix'])
    reference = finite_matrix(value['independent_native_global_rest'])
    target = Matrix(tuple(tuple(assigned[r*4+c] for c in range(4)) for r in range(4)))
    try:
        scene = bpy.data.scenes.new('HAS_OWNED_SCRATCH_REST')
        window.scene = scene
        data = bpy.data.armatures.new('HAS_OWNED_SCRATCH_REST')
        obj = bpy.data.objects.new('HAS_OWNED_SCRATCH_REST', data)
        scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj; obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        getters = []
        for number, (method, length) in enumerate(schedule()):
            bone = data.edit_bones.new('case_' + str(number))
            bone.use_connect = False
            if method == 'original_baseline':
                bone.head = before_bone['head']; bone.tail = before_bone['tail']; bone.roll = before_bone['roll']
                bone.matrix = target
            elif method in ('setter', 'setter_align'):
                # Reproduce SourceIO's initial unscaled head and +Z display tail.
                bone.head = before_bone['head']
                bone.tail = bone.head + Vector((0.,0.,1.)) * length
                bone.roll = before_bone['roll']; bone.matrix = target
                if method == 'setter_align':
                    bone.align_roll(target @ Vector((0.,0.,1.)) - target.translation)
            else:
                # Same construction used by the installed Blender glTF importer.
                bone.head = target @ Vector((0.,0.,0.))
                bone.tail = target @ Vector((0.,1.,0.))
                bone.length = length
                bone.align_roll(target @ Vector((0.,0.,1.)) - bone.head)
            getters.append(matrix(bone.matrix))
        # Drop the EditBone wrapper before the original transition API runs.
        del bone
        bpy.ops.object.mode_set(mode='OBJECT')
        for number, (method,length) in enumerate(schedule()):
            rest = matrix(data.bones['case_'+str(number)].matrix_local)
            rows.append(measured_row(method,length,getters[number],rest,reference,assigned,close))
            private_rows.append({'method':method,'requested_length':length,
                                 'getter':getters[number],'rest':rest})
        need(getters[0] == tuple(boundary['immediate_edit_getter']['matrix']) and
             private_rows[0]['rest'] == tuple(boundary['object_return_matrix']),
             'SCRATCH_ORIGINAL_BASELINE_EXACT_REPRODUCTION_REQUIRED')
        need(not close(private_rows[0]['rest'], reference), 'ORIGINAL_NATIVE_REFUSAL_RETAINED')
        need(matrix(target) == assigned, 'EXACT_ASSIGNMENT_MATRIX_UNCHANGED')
    finally:
        if obj is not None and obj.mode != 'OBJECT' and bpy.context.object is not None and int(bpy.context.object.as_pointer()) == int(obj.as_pointer()):
            bpy.ops.object.mode_set(mode='OBJECT')
        window.scene = original_scene
        if obj is not None: bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None: bpy.data.armatures.remove(data)
        if scene is not None: bpy.data.scenes.remove(scene)
        active_after = bpy.context.view_layer.objects.active
        cleanup = (inventory() == before and (int(active_after.as_pointer()) if active_after else 0) == original_active_pointer and
                   tuple(sorted(int(x.as_pointer()) for x in bpy.context.selected_objects)) == original_selection)
        need(cleanup, 'ALL_OWNED_SCRATCH_DATABLOCKS_REMOVED_AND_ORIGINAL_CONTEXT_UNCHANGED')
    return rows, private_rows, cleanup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-input', type=Path, required=True)
    parser.add_argument('--reference-close', type=Path, required=True)
    parser.add_argument('--reference-close-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    raw = args.private_input.read_bytes(); close_raw = args.reference_close.read_bytes()
    value = profile(raw); close = load_close(close_raw, args.reference_close_sha256)
    need(args.output.is_dir() and not any(args.output.iterdir()), 'FRESH_EMPTY_OWNED_OUTPUT')
    rows, private_rows, cleanup = run_owned(value, close)
    need(args.private_input.read_bytes() == raw and args.reference_close.read_bytes() == close_raw,
         'READONLY_INPUTS_PRESERVED')
    private = {'format':'has_private_scratch_rest_representations_1','private_do_not_publish':True,
               'assignment':value['factory_boundaries']['assigned_matrix'],
               'native_reference':value['independent_native_global_rest'],'rows':private_rows}
    with (args.output/'PRIVATE_scratch_rest.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(private,stream,separators=(',',':'),allow_nan=False);stream.write('\n')
    report = {'format':'has_scratch_rest_measurements_1','status':'MEASURED_SCRATCH_REPRESENTATIONS',
              'cases':rows,'case_count':len(rows),'baseline_reproduced_exactly':True,
              'all_scratch_deleted_original_context_preserved':cleanup,
              'source_capture_sha256':sha(raw),'actual_model_repairs':0,
              'native_export_qualified':False,'tolerance_changed':False,'SDK_written':False}
    with (args.output/'PUBLIC_RESULT.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,separators=(',',':'),allow_nan=False);stream.write('\n')
    print('JUNKO_SCRATCH_REST '+json.dumps(report,separators=(',',':'),allow_nan=False),flush=True)


if __name__ == '__main__':
    main()
