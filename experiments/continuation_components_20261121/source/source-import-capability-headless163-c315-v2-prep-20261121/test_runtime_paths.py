"""Authored UNRUN path/schema controls; no native runtime, Job or Main reads."""
import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('_headless163_path_policy',Path(__file__).with_name('run_headless163.py'))
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
class RunnerPaths(unittest.TestCase):
    def setUp(self):
        self.row={'bytes':1,'sha256':'a'*64,'mtime_ns':2}
        self.python='C:'+chr(92)+'Program Files'+chr(92)+'Python313'+chr(92)+'python.exe'
        self.godot='C:'+chr(92)+'a'+chr(92)+'tools'+chr(92)+'Godot'+chr(92)+'Godot_v4.6-stable_win64.exe'
    def test_actual_consumer_recognizes_normalized_python(self):
        before={'path':self.python,**self.row}
        with self.assertRaises(StopIteration):next(row for row in [before] if row['path'].lower().endswith('/python.exe'))
        after=D.runner_pin('python',self.python,self.row)
        self.assertIs(next(row for row in [after] if row['path'].lower().endswith('/python.exe')),after)
        self.assertEqual(after['path'],'C:/Program Files/Python313/python.exe')
    def test_already_forward_python_unchanged(self):
        path='C:/Program Files/Python313/python.exe'
        self.assertEqual(D.runner_pin('python',path,self.row)['path'],path)
    def test_godot_path_still_matches_unchanged_request_argv(self):
        value=D.runner_pin('godot',self.godot,self.row);command=[self.godot,'--headless']
        self.assertEqual(value['path'],command[0])
        self.assertIs(next(row for row in [value] if row['path']==command[0]),value)
    def test_raw_executable_pins_and_input_dictionary_preserved(self):
        original=copy.deepcopy(self.row);after=D.runner_pin('python',self.python,self.row)
        self.assertEqual(self.row,original);self.assertIsNot(after,self.row)
        self.assertEqual({key:after[key] for key in original},original)
    def test_invalid_path_types_refused(self):
        for path in (None,False,''):
            with self.subTest(path=path),self.assertRaises(ValueError):D.runner_pin('python',path,self.row)
    def test_unknown_runtime_kind_refused(self):
        with self.assertRaises(ValueError):D.runner_pin('other',self.python,self.row)
if __name__=='__main__':unittest.main()
