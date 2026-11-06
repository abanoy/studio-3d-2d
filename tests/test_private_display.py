"""Private Linux tests must never fall through to another graphical display."""
from pathlib import Path
import os,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run

@unittest.skipUnless(sys.platform=='linux','Private X11 transport is Linux-specific')
class PrivateDisplayTests(unittest.TestCase):
    def setUp(self):
        self.patchers=[patch.dict(os.environ,{},clear=False),patch.object(run,'_PRIVATE_DISPLAY',None),patch.object(run,'_check_private_display'),patch.object(run,'engine_path',return_value='/fake/Godot'),patch.object(run.subprocess,'check_output',return_value='4.6.stable.test')]
        for item in self.patchers:item.start()
        for item in self.patchers:self.addCleanup(item.stop)
    def test_explicit_local_selection(self):
        for value in [':102',':102.0']:
            run.configure_private_display(value);self.assertEqual(os.environ['DISPLAY'],value);self.assertEqual(run._PRIVATE_DISPLAY,value)
    def test_invalid_selection_changes_no_state(self):
        os.environ['DISPLAY']=':102'
        for value in ['',None,False,'localhost:99',':',':1.2.3',':1 --headless']:
            with self.subTest(value=value),self.assertRaises(ValueError):run.configure_private_display(value)
            self.assertIsNone(run._PRIVATE_DISPLAY);self.assertEqual(os.environ['DISPLAY'],':102')
    def test_wayland_fallback_is_confined(self):
        import stat
        os.environ['XDG_RUNTIME_DIR']='/tmp/shared-runtime';os.environ['WAYLAND_DISPLAY']='wayland-0'
        run.configure_private_display(':102')
        private=os.environ['XDG_RUNTIME_DIR']
        self.assertNotEqual(private,'/tmp/shared-runtime');self.assertEqual(stat.S_IMODE(Path(private).stat().st_mode),0o700)
        self.assertEqual(os.environ['WAYLAND_DISPLAY'],'has-disabled-wayland');self.assertFalse((Path(private)/os.environ['WAYLAND_DISPLAY']).exists())
    def test_unavailable_x11_refuses_before_command_launch(self):
        run.configure_private_display(':102')
        with patch.object(run,'_check_private_display',side_effect=RuntimeError('private display missing')),self.assertRaisesRegex(RuntimeError,'private display missing'):run.command('res://test.gd')
    def test_normal_launcher_unchanged(self):
        args=run.command('res://test.gd');self.assertNotIn('--display-driver',args)
    def test_gui_pins_before_user_arguments(self):
        run.configure_private_display(':102')
        args=run.command('res://test.gd',extra=['--','--display-driver','wayland'])
        boundary=args.index('--');self.assertEqual(args[boundary-2:boundary],['--display-driver','x11']);self.assertEqual(args[boundary+1:],['--display-driver','wayland'])
    def test_normal_startup_scene_is_pinned(self):
        run.configure_private_display(':102');args=run.command(extra=['/tmp/startup.tscn','--','/tmp/fixtures'])
        self.assertEqual(args[args.index('--')-2:args.index('--')],['--display-driver','x11'])
    def test_pathlike_startup_argument_is_supported(self):
        run.configure_private_display(':102');args=run.command(extra=[Path('/tmp/startup.tscn')])
        self.assertIn('--display-driver',args)
    def test_headless_does_not_need_display(self):
        run.configure_private_display(':102');os.environ.pop('DISPLAY')
        args=run.command('res://test.gd',headless=True);self.assertIn('--headless',args);self.assertNotIn('--display-driver',args)
    def test_headless_extra_is_preserved(self):
        run.configure_private_display(':102');args=run.command(extra=['--headless']);self.assertIn('--headless',args);self.assertNotIn('--display-driver',args)
    def test_changed_display_fails_closed(self):
        run.configure_private_display(':102');os.environ['DISPLAY']=':0'
        with self.assertRaisesRegex(RuntimeError,'no graphical fallback'):run.command('res://test.gd')
    def test_competing_engine_driver_refuses(self):
        run.configure_private_display(':102')
        for extra in [['--display-driver','wayland'],['--display-driver=wayland']]:
            with self.subTest(extra=extra),self.assertRaisesRegex(RuntimeError,'competing display driver'):run.command(extra=extra)
    def test_headless_cannot_be_overridden_by_graphics(self):
        run.configure_private_display(':102')
        with self.assertRaisesRegex(RuntimeError,'competing display driver'):run.command(headless=True,extra=['--display-driver','x11'])
    def test_nonlinux_selection_refuses(self):
        with patch.object(run.sys,'platform','darwin'),self.assertRaises(ValueError):run.configure_private_display(':102')
    def test_all_explicit_private_wrappers_use_the_guard(self):
        import ast
        wrappers=[]
        for p in (Path(__file__).parent).glob('verify*.py'):
            text=p.read_text()
            if '--isolated-display' not in text:continue
            wrappers.append(p)
            tree=ast.parse(text)
            self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='configure_private_display' for n in ast.walk(tree)),p)
        self.assertGreaterEqual(len(wrappers),24)

if __name__=='__main__':unittest.main()
