"""Synthetic trace boundaries only; no Blender/SDK/native input/process."""
from pathlib import Path
import sys
import types
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import junko_factory_boundary as F


def identity():
    return [[float(r == c) for c in range(4)] for r in range(4)]


def shifted(amount):
    value = identity(); value[0][0] += amount
    return value


class BoundaryGuards(unittest.TestCase):
    def fixture(self):
        value = F.Observation.__new__(F.Observation)
        value.path = Path(__file__).resolve().parent / 'synthetic_factory.py'
        for key in ('code','mdl','armature_pointer','before','assigned','after','pre_object','returned','returned_pose','load_refpose','failure'):
            setattr(value,key,None)
        value.pending = False; value.refpose_branch = False
        value.factory_calls = 0; value.assignments = 0
        code = compile('def create_armature(): pass',str(value.path),'exec')
        namespace = {}; exec(code,namespace)
        bone = types.SimpleNamespace(bone_id=38,parent_id=-1,name='synthetic')
        mdl = types.SimpleNamespace(header=types.SimpleNamespace(version=49),bones=[None]*145)
        mdl.bones[38] = bone
        edit = types.SimpleNamespace(matrix=identity(),head=(0.,0.,0.),tail=(0.,0.,1.),roll=0.,length=1.)
        arm = types.SimpleNamespace(as_pointer=lambda:123,
            data=types.SimpleNamespace(bones={'synthetic':types.SimpleNamespace(matrix_local=identity())}),
            pose=types.SimpleNamespace(bones={'synthetic':types.SimpleNamespace(matrix=identity())}))
        local = dict(mdl=mdl,scale=.01905,load_refpose=False,bone=bone,i=38,bl_bone=edit,mat=identity(),armature_obj=arm,armature=types.SimpleNamespace(edit_bones={'synthetic':edit}))
        frame = types.SimpleNamespace(f_code=namespace['create_armature'].__code__,f_lineno=35,f_locals=local)
        return value,frame,edit,arm

    def complete(self):
        value,frame,edit,arm = self.fixture()
        value.trace(frame,'call',None)
        frame.f_lineno=60; value.trace(frame,'line',None)
        frame.f_lineno=50; value.trace(frame,'line',None)
        frame.f_lineno=79; value.trace(frame,'line',None)
        value.trace(frame,'return',arm)
        C = types.SimpleNamespace(pointer=lambda obj:int(obj.as_pointer()))
        local = dict(row={'index':38},mdl=frame.f_locals['mdl'],armature=arm,
                     actual=F.matrix(arm.data.bones['synthetic'].matrix_local),expected=F.matrix(identity()))
        return value,frame,C,local

    def test_complete_boundary_identity(self):
        value,_,C,local=self.complete(); private,scalars=value.attach(C,local)
        self.assertEqual(scalars['factory_assignment_to_edit_error'],0.)
        self.assertTrue(private['readonly_trace']); self.assertFalse(private['cause_established'])

    def test_child_assignment_uses_actual_parent_operand(self):
        value,frame,_,_=self.fixture()
        calls=[]
        class ParentMatrix:
            def __matmul__(self,other):
                calls.append(other)
                return shifted(.02)
        frame.f_locals['bone'].parent_id=0
        frame.f_locals['armature'].edit_bones[0]=types.SimpleNamespace(matrix=ParentMatrix())
        value.trace(frame,'call',None);frame.f_lineno=62;value.trace(frame,'line',None)
        self.assertAlmostEqual(value.assigned[0],1.02)
        self.assertEqual(calls,[frame.f_locals['mat']])

    def test_setter_discrepancy_distinguished(self):
        value,frame,edit,arm=self.fixture(); value.trace(frame,'call',None)
        frame.f_lineno=60;value.trace(frame,'line',None);edit.matrix=shifted(.01)
        frame.f_lineno=50;value.trace(frame,'line',None)
        self.assertAlmostEqual(abs(value.after['matrix'][0]-value.assigned[0]),.01)

    def test_object_conversion_discrepancy_distinguished(self):
        value,_,C,local=self.complete();value.returned=F.matrix(shifted(.02))
        _,scalars=value.attach(C,local);self.assertAlmostEqual(scalars['factory_edit_to_object_error'],.02)

    def test_later_edit_writer_discrepancy_distinguished(self):
        value,_,C,local=self.complete();value.pre_object['matrix']=F.matrix(shifted(.04))
        _,scalars=value.attach(C,local);self.assertAlmostEqual(scalars['factory_edit_later_error'],.04)

    def test_later_writer_discrepancy_distinguished(self):
        value,_,C,local=self.complete();local['actual']=F.matrix(shifted(.03))
        _,scalars=value.attach(C,local);self.assertAlmostEqual(scalars['factory_object_to_final_error'],.03)

    def test_nonmatching_function_not_traced(self):
        value,frame,_,_=self.fixture();frame.f_code=(lambda:None).__code__
        self.assertIsNone(value.trace(frame,'call',None));self.assertEqual(value.factory_calls,0)

    def test_wrong_domain_latches_only(self):
        value,frame,_,_=self.fixture();frame.f_locals['scale']=1.
        self.assertIsNone(value.trace(frame,'call',None));self.assertEqual(value.failure,'ValueError')

    def test_wrong_native_index_identity_latches(self):
        value,frame,_,_=self.fixture();value.trace(frame,'call',None)
        frame.f_locals['bone']=types.SimpleNamespace(bone_id=38)
        frame.f_lineno=60;self.assertIsNone(value.trace(frame,'line',None));self.assertEqual(value.failure,'ValueError')

    def test_repeated_factory_refuses(self):
        value,frame,_,_=self.fixture();value.trace(frame,'call',None)
        self.assertIsNone(value.trace(frame,'call',None));self.assertEqual(value.failure,'ValueError')

    def test_refpose_branch_observed_separately(self):
        value,frame,_,_=self.fixture();frame.f_locals['load_refpose']=True
        value.trace(frame,'call',None);frame.f_lineno=65;value.trace(frame,'line',None)
        self.assertTrue(value.refpose_branch);self.assertTrue(value.load_refpose)

    def test_nonboolean_refpose_refuses(self):
        value,frame,_,_=self.fixture();frame.f_locals['load_refpose']=0
        value.trace(frame,'call',None);self.assertEqual(value.failure,'ValueError')

    def test_wrong_final_mdl_join_refuses(self):
        value,_,C,local=self.complete();local['mdl']=object()
        with self.assertRaisesRegex(ValueError,'ACTUAL_FACTORY_TO_PROOF'):value.attach(C,local)

    def test_wrong_final_armature_join_refuses(self):
        value,_,C,local=self.complete();local['armature']=types.SimpleNamespace(as_pointer=lambda:456)
        with self.assertRaisesRegex(ValueError,'ACTUAL_FACTORY_TO_PROOF'):value.attach(C,local)

    def test_incomplete_trace_refuses(self):
        value,_,C,local=self.complete();value.after=None
        with self.assertRaisesRegex(ValueError,'ALL_FACTORY_BOUNDARIES'):value.attach(C,local)

    def test_no_trace_for_other_profile(self):
        with mock.patch.object(F,'Observation') as ctor:
            with F.observe({'sha256':'0'*64}):pass
        ctor.assert_not_called()

    def test_existing_trace_refused_and_preserved(self):
        sentinel=object()
        with mock.patch.object(F.sys,'gettrace',return_value=sentinel),mock.patch.object(F.sys,'settrace') as setter:
            with self.assertRaisesRegex(ValueError,'EXCLUSIVE_EMPTY_TRACE'): 
                with F.observe({'sha256':F.BODY_SHA}):pass
            setter.assert_not_called()

    def test_trace_restored_after_original_error(self):
        observer=types.SimpleNamespace(trace=object())
        with mock.patch.object(F,'Observation',return_value=observer),mock.patch.object(F.sys,'gettrace',return_value=None),mock.patch.object(F.sys,'settrace') as setter:
            with self.assertRaisesRegex(RuntimeError,'original'):
                with F.observe({'sha256':F.BODY_SHA}):raise RuntimeError('original')
            self.assertEqual(setter.call_args_list,[mock.call(observer.trace),mock.call(None)])
        self.assertIsNone(F.ACTIVE)

    def test_nonfinite_matrix_refuses(self):
        value=identity();value[0][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'FINITE_FACTORY_MATRIX'):F.matrix(value)

    def test_public_projection_scalars_only(self):
        value,_,C,local=self.complete();_,scalars=value.attach(C,local)
        self.assertEqual(len(scalars),8)
        self.assertTrue(all(type(x) is float for x in scalars.values()))


if __name__=='__main__':unittest.main(verbosity=2)
