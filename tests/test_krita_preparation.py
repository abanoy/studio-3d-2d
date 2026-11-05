from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zipfile,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import prepare_krita as P
import krita_assets as K

def png_bytes(width,height,pixels):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

class PreparationTests(unittest.TestCase):
    def test_atomic_response_retries_brief_windows_reader_lock(self):
        from unittest.mock import patch
        path=Path(tempfile.gettempdir())/('studio-response-'+str(os.getpid())+'.json')
        try:
            path.write_text('{"old":true}',encoding='utf-8');replace=os.replace;attempts=[]
            def blocked_once(source,target):
                attempts.append(1)
                if len(attempts)==1:
                    self.assertEqual(json.loads(path.read_bytes()),{'old':True});raise PermissionError('sharing violation')
                replace(source,target)
            with patch.object(P.os,'replace',side_effect=blocked_once):P.write_json(path,{'ready':True})
            self.assertEqual(len(attempts),2);self.assertEqual(json.loads(path.read_bytes()),{'ready':True})
        finally:path.unlink(missing_ok=True);path.with_suffix('.json.tmp').unlink(missing_ok=True)
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def source(self):
        path=self.folder/'original.kra'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('mimetype','application/x-krita');z.writestr('maindoc.xml','<DOC><IMAGE width="32" height="32" colorspacename="RGBA"><layers><layer uuid="ink" visible="1"/></layers><animation><framerate value="24"/><range from="0" to="47"/></animation></IMAGE></DOC>')
            z.writestr('paint/layer.keyframes.xml','<channel name="content"><keyframe time="0" frame="base"/><keyframe time="6" frame="next"/></channel>')
        return path
    def request(self):
        source=self.source();return {'source':str(source),'source_sha256':P.sha(source),'output':str(self.folder/'prepared'),'cancel':str(self.folder/'cancel'),'krita':__file__,'ffmpeg':__file__,'fps_num':24,'fps_den':1,'available_frames':48}
    def test_same_rate_preserves_every_frame(self):self.assertEqual(P.target_indices(48,24,24,1),list(range(48)))
    def test_double_and_half_rate_mapping(self):
        self.assertEqual(P.target_indices(4,24,48,1),[0,0,1,1,2,2,3,3]);self.assertEqual(P.target_indices(8,48,24,1),[0,2,4,6])
    def test_fractional_project_clock_maps_without_float_drift(self):
        self.assertEqual(P.target_indices(48,24,24000,1001),list(range(48)))
        result=P.target_indices(48,24,30000,1001);self.assertEqual(len(result),60);self.assertEqual(result[:10],[0,0,1,2,3,4,4,5,6,7]);self.assertEqual(result[-1],47)
    def test_timing_budgets_refuse(self):
        for args in [(241,24,24,1),(240,1,120,1),(0,24,24,1),(48,24,121,1),(48,24,True,1)]:
            with self.subTest(args=args),self.assertRaises(ValueError):P.target_indices(*args)
    def test_centered_fit_has_no_crop(self):
        self.assertEqual(P.fit(2160,3840,1920,1080),(608,1080,656,0));self.assertEqual(P.fit(2560,1440,1920,1080),(1920,1080,0,0));self.assertEqual(P.fit(1,1,1920,1080),(1080,1080,420,0))
    def test_invalid_fit_refuses(self):
        for args in [(0,2,1920,1080),(2,2,1921,1080),(2,2,True,1080)]:
            with self.subTest(args=args),self.assertRaises(ValueError):P.fit(*args)
    def test_png_stream_crc_validation(self):
        path=self.folder/'pixel.png';path.write_bytes(png_bytes(1,1,bytes([255,0,0,128])));self.assertEqual(P.png(path),(1,1,8,6))
        raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
        with self.assertRaises(ValueError):P.png(path)
    def test_png_truncation_refuses(self):
        path=self.folder/'bad.png';path.write_bytes(png_bytes(1,1,bytes(4))[:-7]);self.assertRaises(ValueError,P.png,path)
    def test_cancel_before_preparation_creates_no_output(self):
        r=self.request();Path(r['cancel']).touch()
        with self.assertRaises(P.Cancelled):P.prepare(r)
        self.assertFalse(Path(r['output']).exists())
    def test_source_change_refuses_before_conversion(self):
        r=self.request();r['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'changed'):P.prepare(r)
        self.assertFalse(Path(r['output']).exists())
    def test_scene_end_refusal_creates_no_output(self):
        r=self.request();r['available_frames']=47
        with self.assertRaisesRegex(ValueError,'beyond'):P.prepare(r)
        self.assertFalse(Path(r['output']).exists())
    def test_preparation_never_replaces_existing_folder(self):
        r=self.request();path=Path(r['output']);path.mkdir();(path/'keep').write_text('original')
        with self.assertRaisesRegex(ValueError,'fresh'):P.prepare(r)
        self.assertEqual((path/'keep').read_text(),'original')
    def test_unknown_layer_has_no_ready_manifest(self):
        r=self.request();r['layer_visibility']={'unknown':False}
        with self.assertRaises(K.KritaError):P.prepare(r)
        self.assertFalse((Path(r['output'])/'clip.json').exists());self.assertEqual(json.loads((Path(r['output'])/'progress.json').read_bytes())['stage'],'error')
    def test_inspection_rpc_preserves_identity_and_bounds_response(self):
        source=self.source();response=self.folder/'inspect.json';p=subprocess.run([sys.executable,P.__file__,'--inspect',str(source),'--result',str(response)],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);r=json.loads(response.read_bytes());self.assertTrue(r['ok']);self.assertTrue(r['inventory']['render_supported']);self.assertNotIn('channels',r['inventory']);self.assertEqual(r['inventory']['source_sha256'],P.sha(source))
    def test_preflight_error_rpc_is_readable_without_launching_converter(self):
        r=self.request();r['source_sha256']='0'*64;r['result']=str(self.folder/'result.json');request=self.folder/'request.json';request.write_text(json.dumps(r));p=subprocess.run([sys.executable,P.__file__,str(request)],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.assertEqual(p.returncode,1);report=json.loads(Path(r['result']).read_bytes());self.assertFalse(report['ok']);self.assertIn('changed',report['error']);self.assertFalse(Path(r['output']).exists())
    def test_invalid_response_destination_is_not_written(self):
        r=self.request();r['result']=str(self.folder/'unexpected.json');request=self.folder/'request.json';request.write_text(json.dumps(r));p=subprocess.run([sys.executable,P.__file__,str(request)],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.assertEqual(p.returncode,1);self.assertFalse(Path(r['result']).exists());self.assertFalse(Path(r['output']).exists())

if __name__=='__main__':unittest.main()
