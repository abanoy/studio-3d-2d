from pathlib import Path
import sys, tempfile, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from prepare_source import conversion_failure

class SourceFailureTests(unittest.TestCase):
    def test_bounded_worker_refusal_keeps_the_action_and_log_address(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'conversion.log'
            reason='Source map exceeds64supported static lights; split or simplify the map before import'
            path.write_bytes(b'x'*20000+('\nValueError: '+reason+'\nBlender quit\n').encode())
            self.assertEqual(conversion_failure(path,1),f'Conversion failed (exit 1): {reason}; see {path}')
    def test_windows_log_and_last_exception_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'conversion.log'
            path.write_bytes(b'ValueError: earlier\r\nRuntimeError: Missing map texture; supply materials\r\n')
            self.assertIn('Missing map texture; supply materials',conversion_failure(path,1))
    def test_absent_or_unrecognized_logs_keep_explicit_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'conversion.log'
            self.assertEqual(conversion_failure(path,2),f'Conversion failed (exit 2); see {path}')
            path.write_text('Blender exited without a supported exception')
            self.assertEqual(conversion_failure(path,3),f'Conversion failed (exit 3); see {path}')

if __name__=='__main__':unittest.main()
