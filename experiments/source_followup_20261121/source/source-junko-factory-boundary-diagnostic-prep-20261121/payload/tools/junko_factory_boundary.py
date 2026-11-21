"""Read-only observations of one pinned factory's existing bone operations."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import math
import sys

BODY_SHA = 'd916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7'
FACTORY = 'blender_bindings/models/mdl44/import_mdl.py'
FACTORY_SHA = '080b91589e0fec462e3eea4b55793aec41399ff95f6d9f2d561d5cda9dddada8'
INDEX = 38
ACTIVE = None


def matrix(value):
    result = tuple(float(value[r][c]) for r in range(4) for c in range(4))
    if not all(math.isfinite(x) for x in result):
        raise ValueError('FINITE_FACTORY_MATRIX_REQUIRED')
    return result


def bone_snapshot(bone):
    result = {'matrix': matrix(bone.matrix), 'head': tuple(float(x) for x in bone.head),
              'tail': tuple(float(x) for x in bone.tail), 'roll': float(bone.roll),
              'length': float(bone.length)}
    if not all(math.isfinite(x) for key in ('head', 'tail') for x in result[key]):
        raise ValueError('FINITE_FACTORY_ENDPOINTS_REQUIRED')
    if not math.isfinite(result['roll']) or not math.isfinite(result['length']):
        raise ValueError('FINITE_FACTORY_BONE_SCALARS_REQUIRED')
    return result


class Observation:
    def __init__(self, request):
        self.path = (Path(request['sourceio']) / FACTORY).resolve(strict=True)
        if hashlib.sha256(self.path.read_bytes()).hexdigest() != FACTORY_SHA:
            raise ValueError('EXACT_FACTORY_SOURCE_REQUIRED')
        self.code = None
        self.mdl = None
        self.armature_pointer = None
        self.pending = False
        self.before = None
        self.assigned = None
        self.after = None
        self.pre_object = None
        self.returned = None
        self.returned_pose = None
        self.load_refpose = None
        self.refpose_branch = False
        self.factory_calls = 0
        self.assignments = 0
        self.failure = None

    def trace(self, frame, event, arg):
        # No unrelated frame receives a local trace. Match the pinned pathname
        # and function, then retain the actual code object for all later events.
        try:
            if event == 'call':
                if frame.f_code.co_name != 'create_armature' or Path(frame.f_code.co_filename).resolve() != self.path:
                    return None
                self.factory_calls += 1
                if self.factory_calls != 1:
                    raise ValueError('ONE_SELECTED_FACTORY_CALL_REQUIRED')
                local = frame.f_locals
                mdl = local['mdl']
                if mdl.header.version != 49 or len(mdl.bones) != 145 or local['scale'] != 0.01905:
                    raise ValueError('EXACT_BODY_FACTORY_DOMAIN_REQUIRED')
                if type(local['load_refpose']) is not bool:
                    raise ValueError('ACTUAL_BOOLEAN_REFPOSE_REQUIRED')
                self.code = frame.f_code
                self.mdl = mdl
                self.load_refpose = local['load_refpose']
                return self.trace
            if frame.f_code is not self.code:
                return None
            local = frame.f_locals
            if self.pending and event in ('line', 'return'):
                # The next Python event occurs after the original setter.
                self.after = bone_snapshot(local['bl_bone'])
                self.pending = False
            if event == 'line' and frame.f_lineno in (60, 62) and local.get('i') == INDEX:
                bone = local['bone']
                if bone is not self.mdl.bones[INDEX] or bone.bone_id != INDEX:
                    raise ValueError('EXACT_NATIVE_INDEX_OBJECT_REQUIRED')
                self.assignments += 1
                if self.assignments != 1:
                    raise ValueError('ONE_INITIAL_ASSIGNMENT_REQUIRED')
                edit = local['bl_bone']
                self.before = bone_snapshot(edit)
                intended = local['mat'] if bone.parent_id == -1 else local['armature'].edit_bones[bone.parent_id].matrix @ local['mat']
                self.assigned = matrix(intended)
                self.pending = True
                # Never retain an EditBone/RNA reference across mode changes.
            if event == 'line' and frame.f_lineno == 65:
                self.refpose_branch = True
            if event == 'line' and frame.f_lineno == 79:
                name = self.mdl.bones[INDEX].name[:63]
                self.pre_object = bone_snapshot(local['armature'].edit_bones[name])
            if event == 'return':
                armature = local['armature_obj']
                if arg is not armature or self.pending:
                    raise ValueError('EXACT_FACTORY_RETURN_REQUIRED')
                self.armature_pointer = int(armature.as_pointer())
                name = self.mdl.bones[INDEX].name[:63]
                self.returned = matrix(armature.data.bones[name].matrix_local)
                self.returned_pose = matrix(armature.pose.bones[name].matrix)
        except Exception as error:
            # An observation error must not replace the original import proof.
            self.failure = type(error).__name__
            return None
        return self.trace

    def attach(self, C, local):
        if self.failure or self.factory_calls != 1 or self.assignments != 1 or self.pending:
            raise ValueError('COMPLETE_FACTORY_TRACE_REQUIRED')
        if local['row']['index'] != INDEX or local['mdl'] is not self.mdl or C.pointer(local['armature']) != self.armature_pointer:
            raise ValueError('ACTUAL_FACTORY_TO_PROOF_IDENTITY_REQUIRED')
        if any(value is None for value in (self.before, self.assigned, self.after, self.pre_object, self.returned, self.returned_pose)):
            raise ValueError('ALL_FACTORY_BOUNDARIES_REQUIRED')
        actual = tuple(local['actual'])
        gap = lambda a, b: max(abs(x-y) for x,y in zip(a,b))
        scalars = {
            'factory_assignment_to_edit_error': gap(self.assigned, self.after['matrix']),
            'factory_edit_later_error': gap(self.after['matrix'], self.pre_object['matrix']),
            'factory_edit_to_object_error': gap(self.pre_object['matrix'], self.returned),
            'factory_object_to_final_error': gap(self.returned, actual),
            'factory_return_pose_error': gap(self.returned_pose, self.returned),
            'factory_assignment_to_reference_error': gap(self.assigned, tuple(local['expected'])),
            'factory_before_length': self.before['length'],
            'factory_after_length': self.after['length'],
        }
        if not all(math.isfinite(x) for x in scalars.values()):
            raise ValueError('FINITE_FACTORY_BOUNDARY_ERRORS_REQUIRED')
        private = {'format': 'has_private_factory_boundaries_1', 'private_do_not_publish': True,
                   'native_index': INDEX, 'actual_load_refpose': self.load_refpose,
                   'actual_refpose_branch_entered': self.refpose_branch,
                   'factory_calls': self.factory_calls, 'assignments': self.assignments,
                   'before_assignment': self.before, 'assigned_matrix': self.assigned,
                   'immediate_edit_getter': self.after, 'before_object_conversion': self.pre_object,
                   'object_return_matrix': self.returned,
                   'object_return_pose': self.returned_pose, 'scalar_errors': scalars,
                   'readonly_trace': True, 'tolerance_changed': False, 'cause_established': False}
        return private, scalars


@contextmanager
def observe(request):
    global ACTIVE
    if request.get('sha256') != BODY_SHA:
        yield
        return
    if ACTIVE is not None or sys.gettrace() is not None:
        raise ValueError('EXCLUSIVE_EMPTY_TRACE_SLOT_REQUIRED')
    observer = Observation(request)
    ACTIVE = observer
    try:
        sys.settrace(observer.trace)
        yield
    finally:
        try:
            sys.settrace(None)
        finally:
            ACTIVE = None


def attach(C, request, local):
    if request.get('sha256') != BODY_SHA or ACTIVE is None:
        raise ValueError('ACTIVE_BODY_FACTORY_TRACE_REQUIRED')
    return ACTIVE.attach(C, local)
