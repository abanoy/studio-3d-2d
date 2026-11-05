from pathlib import Path
import hashlib,importlib.util,struct,tempfile,unittest,warnings,zipfile
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('krita_assets',ROOT/'tools/krita_assets.py');K=importlib.util.module_from_spec(spec);spec.loader.exec_module(K)

class KritaInventoryTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def document(self,**changes):
        values={'width':'2560','height':'1440','fps':'24','start':'3','end':'8','current':'11'};values.update(changes)
        return ('<DOC xmlns="http://www.calligra.org/DTD/krita"><IMAGE name="painting" width="{width}" height="{height}" colorspacename="RGBA" profile="sRGB"><layers><layer name="Ink" uuid="ink-id" filename="layer1" nodetype="paintlayer" visible="1"/></layers><animation><framerate value="{fps}"/><range from="{start}" to="{end}"/><currentTime value="{current}"/></animation></IMAGE></DOC>').format(**values)
    def make(self,name='日本語 sample.kra',doc=None,channels=True,extra=None):
        path=self.folder/name
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('mimetype','application/x-krita');z.writestr('maindoc.xml',self.document() if doc is None else doc)
            z.writestr('mergedimage.png',b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',2560,1440))
            if channels:z.writestr('painting/layers/layer1.keyframes.xml','<channel xmlns="http://www.calligra.org/DTD/krita" name="content"><keyframe time="3" frame="layer1"/><keyframe time="7" frame="layer1.f1"/></channel>')
            for n,v in (extra or {}).items():z.writestr(n,v)
        return path
    def test_native_metadata_and_source_identity(self):
        path=self.make();before=path.read_bytes();r=K.inspect(path)
        self.assertEqual((r['width'],r['height'],r['fps']),(2560,1440,24));self.assertEqual(r['range'],{'start':3,'end_inclusive':8,'frames':6});self.assertEqual(r['saved_current_frame'],11)
        self.assertTrue(r['animated']);self.assertEqual(r['keyframe_count'],2);self.assertEqual(r['layers'][0]['name'],'Ink');self.assertFalse(r['rendered']);self.assertFalse(r['saved_still']['animation'])
        self.assertEqual(r['source_sha256'],hashlib.sha256(before).hexdigest());self.assertEqual(path.read_bytes(),before)
    def test_static_still_never_claims_animation(self):self.assertFalse(K.inspect(self.make(channels=False))['animated'])
    def test_reading_without_full_hash_is_explicit(self):self.assertNotIn('source_sha256',K.inspect(self.make(),with_hash=False))
    def test_range_and_numeric_guards(self):
        for i,changes in enumerate([{'end':'2'},{'fps':'0'},{'width':'0'},{'height':'999999'},{'current':'NaN'}]):
            with self.subTest(changes=changes),self.assertRaises(K.KritaError):K.inspect(self.make(name=f'bad{i}.kra',doc=self.document(**changes)))
    def test_member_traversal_refuses_without_extraction(self):
        with self.assertRaises(K.KritaError):K.inspect(self.make(extra={'../outside':'bad'}))
        self.assertFalse((self.folder.parent/'outside').exists())
    def test_xml_entities_refuse(self):
        with self.assertRaises(K.KritaError):K.inspect(self.make(doc='<!DOCTYPE doc [<!ENTITY a "example">]><DOC/>'))
    def test_bad_container_refuses(self):
        path=self.folder/'not.kra';path.write_bytes(b'not a zip');self.assertRaises(K.KritaError,K.inspect,path)
    def test_metadata_budget_refuses(self):
        path=self.make(doc=' '* (K.MAX_XML+1));self.assertRaises(K.KritaError,K.inspect,path)
    def test_member_and_document_namespaced_parsing(self):
        r=K.inspect(self.make());self.assertEqual(r['channels'][0]['member'],'painting/layers/layer1.keyframes.xml');self.assertEqual([k['time'] for k in r['channels'][0]['keys']],[3,7])
    def test_remote_paths_and_missing_files_refuse(self):
        for path in ['https://example.invalid/model.kra','\\\\server.invalid/share/model.kra',self.folder/'absent.kra']:
            with self.subTest(path=path),self.assertRaises(K.KritaError):K.inspect(path)
    def test_multibyte_entity_evasion_refuses(self):
        path=self.make(doc='<!DOCTYPE doc [<!ENTITY a "example">]><DOC/>'.encode('utf-16'))
        with self.assertRaises(K.KritaError):K.inspect(path)
    def test_duplicate_members_refuse(self):
        path=self.make()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(path,'a') as z:z.writestr('maindoc.xml',self.document())
        with self.assertRaises(K.KritaError):K.inspect(path)
    def test_wrong_mimetype_refuses(self):
        path=self.folder/'wrong.kra'
        with zipfile.ZipFile(path,'w') as z:z.writestr('mimetype','image/png');z.writestr('maindoc.xml',self.document())
        with self.assertRaises(K.KritaError):K.inspect(path)
    def test_noncontent_channels_also_count_as_animation(self):
        path=self.make(channels=False,extra={'painting/layer.keyframes.xml':'<channel name="opacity"><keyframe time="0" value="0"/><keyframe time="2" value="1"/></channel>'})
        self.assertTrue(K.inspect(path)['animated'])
    def test_reviewed_copy_changes_only_explicit_visibility(self):
        source=self.make(extra={'painting/pixels.bin':b'original native bytes'});before=source.read_bytes();review=self.folder/'review.kra'
        K.render_copy(K.inspect(source),{'ink-id':False},review);r=K.inspect(review)
        self.assertEqual(r['layers'][0]['visible'],'0');self.assertEqual(source.read_bytes(),before)
        with zipfile.ZipFile(source) as a,zipfile.ZipFile(review) as b:
            self.assertEqual(a.namelist(),b.namelist())
            for name in a.namelist():
                if name!='maindoc.xml':self.assertEqual(a.read(name),b.read(name))
    def test_review_refuses_unknown_layers_and_nonboolean_choices(self):
        source=self.make();r=K.inspect(source)
        for i,choice in enumerate([{'missing':False},{'ink-id':0},[],{'ink-id':'false'}]):
            with self.subTest(choice=choice),self.assertRaises(K.KritaError):K.render_copy(r,choice,self.folder/f'bad-copy{i}.kra')
    def test_review_never_overwrites_original(self):
        source=self.make();r=K.inspect(source)
        with self.assertRaises(K.KritaError):K.render_copy(r,{'ink-id':False},source)
    def test_review_copy_cancellation_preserves_original(self):
        source=self.make();r=K.inspect(source);before=source.read_bytes()
        def cancel():raise InterruptedError('cancelled')
        with self.assertRaises(InterruptedError):K.render_copy(r,{'ink-id':False},self.folder/'cancelled.kra',cancel)
        self.assertEqual(source.read_bytes(),before)
    def test_modern_animation_index_overrides_legacy_timing(self):
        path=self.make(extra={'painting/animation/index.xml':'<animation-metadata><framerate value="30"/><range from="5" to="10"/><currentTime value="17"/></animation-metadata>'});r=K.inspect(path)
        self.assertEqual(r['fps'],30);self.assertEqual(r['range'],{'start':5,'end_inclusive':10,'frames':6});self.assertEqual(r['saved_current_frame'],17);self.assertEqual(r['legacy_timing']['fps'],24);self.assertEqual(r['animation_metadata'],'painting/animation/index.xml')
    def test_partial_index_preserves_legacy_fields_it_does_not_override(self):
        r=K.inspect(self.make(extra={'painting/animation/index.xml':'<animation-metadata><currentTime value="6"/></animation-metadata>'}))
        self.assertEqual(r['saved_current_frame'],6);self.assertEqual(r['fps'],24);self.assertEqual(r['range']['start'],3)
    def test_duplicate_index_timing_is_ambiguous(self):
        with self.assertRaises(K.KritaError):K.inspect(self.make(extra={'painting/animation/index.xml':'<animation-metadata><framerate value="24"/><framerate value="30"/></animation-metadata>'}))

if __name__=='__main__':unittest.main()
