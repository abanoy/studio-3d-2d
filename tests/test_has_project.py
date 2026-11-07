from pathlib import Path
import json
import copy
import stat
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has


class HasTests(unittest.TestCase):
    def test_solo_audio_roundtrip_and_independent_fades(self):
        for storage in ('packed','linked'):
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,manifest,_,_=self.audio_fixture(root)
                request['storage']=storage;manifest['audio']['format']='studio_audio_5'
                manifest['audio']['clips'][0].update(solo=True,fade_in_ms=100,fade_out_ms=200,source_out_sample=4800)
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))
                has.pack(request);result=self.unpack(root,request)
                self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['audio'],manifest['audio'])

    def test_invalid_or_unversioned_solo_preserves_valid_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.audio_fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            for version,value in [('studio_audio_2',True),('studio_audio_3',False),('studio_audio_4',True),('studio_audio_5',1),('studio_audio_5',0),('studio_audio_5','yes'),('studio_audio_5',None)]:
                bad=copy.deepcopy(manifest);bad['audio']['format']=version;bad['audio']['clips'][0]['solo']=value
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                with self.subTest(version=version,value=value),self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_faded_audio_packed_and_linked_roundtrip(self):
        for storage in ('packed','linked'):
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,manifest,_,_=self.audio_fixture(root)
                request['storage']=storage;manifest['audio']['format']='studio_audio_4'
                manifest['audio']['clips'][0].update(fade_in_ms=100,fade_out_ms=200,source_out_sample=4800)
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request)
                result=self.unpack(root,request)
                self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['audio'],manifest['audio'])

    def test_invalid_fade_preserves_existing_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.audio_fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            for version,value in [('studio_audio_3',100),('studio_audio_4',0),('studio_audio_4',-1),('studio_audio_4',1.5),('studio_audio_4',float('nan')),('studio_audio_4',60001),('studio_audio_4',True)]:
                bad=copy.deepcopy(manifest);bad['audio']['format']=version;bad['audio']['clips'][0]['fade_in_ms']=value
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_trimmed_audio_version_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.audio_fixture(root)
            manifest['audio']['format']='studio_audio_3';manifest['audio']['clips'][0]['source_out_sample']=4800
            (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request)
            result=self.unpack(root,request)
            reopened=json.loads((Path(result['folder'])/'project.json').read_bytes())
            self.assertEqual(reopened['audio'],manifest['audio'])

    def test_invalid_trim_preserves_prior_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.audio_fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            for version,end in [('studio_audio_2',4800),('studio_audio_3',0),('studio_audio_3',-1),('studio_audio_3',float('nan')),('studio_audio_3',1.5),('studio_audio_3',60*96000+1)]:
                bad=copy.deepcopy(manifest);bad['audio']['format']=version;bad['audio']['clips'][0]['source_out_sample']=end
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def audio_fixture(self,root):
        request,_,_=self.fixture(root);folder=Path(request['folder'])
        sound=root/'voice.wav';sound.write_bytes(b'bounded audio container fixture'*100)
        digest=has.sha(sound);name='assets/'+digest+'.wav';(folder/name).write_bytes(sound.read_bytes())
        row={'id':'voice','path':name,'sha256':digest,'source_name':'Voice.wav','start_frame':0,'source_in_sample':0,'gain_db':-6,'muted':False}
        other={**row,'id':'effect','start_frame':24}
        manifest=json.loads((folder/'project.json').read_bytes());manifest['audio']={'format':'studio_audio_2','clips':[row,other]};manifest['video']={'duration_frames':48}
        (folder/'project.json').write_bytes(has.json_bytes(manifest));request['references'][name]=str(sound)
        return request,manifest,name,sound

    def test_multiple_audio_embedded_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,name,sound=self.audio_fixture(root);has.pack(request)
            with zipfile.ZipFile(request['path'])as archive:self.assertEqual(archive.namelist().count(name),1)
            sound.unlink();(Path(request['folder'])/name).unlink();result=self.unpack(root,request)
            reopened=json.loads((Path(result['folder'])/'project.json').read_bytes())
            self.assertEqual(reopened['audio'],manifest['audio']);self.assertTrue((Path(result['folder'])/name).exists())

    def test_multiple_audio_linked_and_relinked(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);request,_,name,sound=self.audio_fixture(root);request['storage']='linked';has.pack(request)
            moved=root/'moved.wav';sound.rename(moved);result=self.unpack(root,request)
            self.assertFalse(result['ok']);self.assertEqual(len(result['missing']),1)
            self.assertTrue(self.unpack(root,request,relinks={name:str(moved)})['ok'])

    def test_invalid_audio_collection_preserves_last_has(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);request,manifest,_,_=self.audio_fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            cases=[]
            bad=copy.deepcopy(manifest);bad['audio']['format']='future_audio';cases.append(bad)
            bad=copy.deepcopy(manifest);bad['audio']['clips'][1]['id']='voice';cases.append(bad)
            bad=copy.deepcopy(manifest);bad['audio']['clips']*=9;cases.append(bad)
            bad=copy.deepcopy(manifest);bad['audio']['clips'][0]['gain_db']=float('nan');cases.append(bad)
            bad=copy.deepcopy(manifest);bad['audio']['clips'][0]['path']='../outside.wav';cases.append(bad)
            for bad in cases:
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_output_size_roundtrip(self):
        for value in ('1080p','720p','540p'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,_,_=self.fixture(root);path=Path(request['folder'])/'project.json'
                data=json.loads(path.read_bytes());data['video']={'output_size':value};path.write_bytes(has.json_bytes(data));has.pack(request)
                out=self.unpack(root,request);reopened=json.loads((Path(out['folder'])/'project.json').read_bytes())
                self.assertEqual(reopened['video']['output_size'],value)

    def test_invalid_output_size_preserves_previous_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes();path=Path(request['folder'])/'project.json';data=json.loads(path.read_bytes())
            for value in (None,True,720,[],{},'', '4k'):
                with self.subTest(value=value):
                    data['video']={'output_size':value};path.write_bytes(has.json_bytes(data))
                    with self.assertRaises(has.HasError):has.pack(request)
                    self.assertEqual(Path(request['path']).read_bytes(),before)

    def fixture(self, root):
        folder=root/'snapshot';folder.mkdir()
        original=root/'external.glb';original.write_bytes(b'controlled geometry fixture'*200)
        digest=has.sha(original); name='assets/'+digest+'.glb'
        (folder/'assets').mkdir();(folder/name).write_bytes(original.read_bytes())
        (folder/'cels').mkdir();(folder/'cels/test.png').write_bytes(b'controlled PNG payload')
        manifest={'schema_version':3,'scene':{'path':name,'sha256':digest},'model':{},'audio':{},'layers':[{'cels':[{'path':'cels/test.png'}]}]}
        (folder/'project.json').write_bytes(has.json_bytes(manifest))
        return {'action':'pack','folder':str(folder),'path':str(root/'film.has'),'storage':'packed','references':{name:str(original)},'cache_root':str(root/'cache')},name,original

    def unpack(self, root, request, **options):
        return has.unpack({'path':request['path'],'folder':str(root/'opened'),**options})

    def test_packed_portable_without_original_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,original=self.fixture(root);has.pack(req)
            original.unlink();(Path(req['folder'])/name).unlink()
            out=self.unpack(root,req)
            self.assertTrue(out['ok']);self.assertTrue((Path(out['folder'])/name).is_file())
            self.assertEqual(out['origins'],{})

    def test_linked_missing_then_checksum_relink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,original=self.fixture(root);req['storage']='linked';has.pack(req)
            with zipfile.ZipFile(req['path']) as z:self.assertNotIn(name,z.namelist())
            moved=root/'moved.glb';original.rename(moved)
            missing=self.unpack(root,req)
            self.assertFalse(missing['ok']);self.assertEqual(missing['missing'][0]['asset'],name)
            self.assertFalse((root/'opened').exists())
            out=self.unpack(root,req,relinks={name:str(moved)})
            self.assertEqual(out['origins'][str((root/'opened'/name).resolve())],str(moved.resolve()))

    def test_changed_link_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,original=self.fixture(root);req['storage']='linked';has.pack(req)
            original.write_bytes(b'changed')
            self.assertFalse(self.unpack(root,req)['ok'])

    def test_cache_links_externalized_to_stable_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,original=self.fixture(root);cache=root/'cache';cache.mkdir();local=cache/'asset.glb';local.write_bytes(original.read_bytes())
            req['references'][name]=str(local);req['storage']='linked';has.pack(req);local.unlink()
            self.assertTrue(self.unpack(root,req)['ok']);self.assertTrue((root/'film.assets'/Path(name).name).is_file())

    def test_previous_save_backup_and_cancel(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,_,_=self.fixture(root);has.pack(req);before=Path(req['path']).read_bytes();has.pack(req)
            self.assertEqual(Path(req['path']+'.backup').read_bytes(),before)
            cancel=root/'cancel';cancel.write_text('cancel');req['cancel']=str(cancel)
            with self.assertRaises(has.HasError):has.pack(req)
            self.assertEqual(Path(req['path']).read_bytes(),before)

    def test_additional_managed_import_cache_externalizes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,original=self.fixture(root)
            managed=root/'imports';managed.mkdir();cached=managed/'revision.glb';cached.write_bytes(original.read_bytes())
            req.update(storage='linked',cache_roots=[str(managed)])
            req['references'][name]=str(cached);has.pack(req);cached.unlink()
            self.assertTrue(self.unpack(root,req)['ok'])
            self.assertEqual(has.sha(root/'film.assets'/Path(name).name),has.sha(original))

    def test_invalid_save_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,name,_=self.fixture(root);has.pack(req);before=Path(req['path']).read_bytes()
            (Path(req['folder'])/name).write_bytes(b'wrong')
            with self.assertRaises(has.HasError):has.pack(req)
            self.assertEqual(Path(req['path']).read_bytes(),before)

    def test_safe_paths_and_network_links(self):
        for name in ('../escape','/escape','C:/escape','assets\\x','cels/NUL.png','cels/x.','cels//x'):
            with self.assertRaises(has.HasError):has.safe(name)
        for name in ('https://example.test/a.glb','\\\\server\\share\\a.glb','//server/share/a.glb'):
            with self.assertRaises(has.HasError):has.local_reference(name)

    def test_duplicate_symlink_traversal_and_excessive_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);file=root/'bad.has'
            for kind in ('duplicate','symlink','traversal','large','compression'):
                with zipfile.ZipFile(file,'w',compression=zipfile.ZIP_DEFLATED) as z:
                    if kind=='duplicate':z.writestr('a',b'1');z.writestr('A',b'2')
                    elif kind=='traversal':z.writestr('../escape',b'x')
                    elif kind=='symlink':
                        info=zipfile.ZipInfo('link');info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'target')
                    elif kind=='compression':z.writestr('compressed',b'data',compress_type=zipfile.ZIP_LZMA)
                    else:z.writestr('project.json',b'0'*(has.MAX_META+1))
                    if kind!='duplicate':z.writestr('sentinel',b'')
                with self.assertRaises((has.HasError,KeyError)):has.unpack({'path':str(file),'folder':str(root/'open')})
                self.assertFalse((root/'open').exists())

    def test_unlisted_payload_and_unknown_version(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,_,_=self.fixture(root);has.pack(req)
            with zipfile.ZipFile(req['path'],'a') as z:z.writestr('extra.txt','not allowed')
            with self.assertRaises(has.HasError):self.unpack(root,req)
            self.assertFalse((root/'opened').exists())
            with zipfile.ZipFile(req['path']) as z: entries={n:z.read(n) for n in z.namelist() if n!='extra.txt'}
            header=json.loads(entries['has.json']);header['version']=99;entries['has.json']=has.json_bytes(header)
            with zipfile.ZipFile(req['path'],'w') as z:
                for name,blob in entries.items():z.writestr(name,blob)
            with self.assertRaises(has.HasError):self.unpack(root,req)

    def test_directory_count_bounded_before_zip_parser_allocation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'bad.has'
            path.write_bytes(struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,65000,65000,0,0,0))
            with self.assertRaises(has.HasError):has.preflight_archive(path)

    def test_unicode_project_filename(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,_,_=self.fixture(root)
            req['path']=str(root/'作品 shots'/'сцена.has')
            has.pack(req)
            self.assertTrue(self.unpack(root,req)['ok'])

    def test_payload_sha_detects_changed_bytes_with_valid_zip_crc(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,_,_=self.fixture(root);has.pack(req)
            with zipfile.ZipFile(req['path']) as z: entries={n:z.read(n) for n in z.namelist()}
            entries['cels/test.png']=b'X'*len(entries['cels/test.png'])
            with zipfile.ZipFile(req['path'],'w') as z:
                for name,blob in entries.items():z.writestr(name,blob)
            with self.assertRaisesRegex(has.HasError,'checksum'):self.unpack(root,req)

    def test_reference_opacity_roundtrip_and_invalid_atomic_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,name,_=self.fixture(root)
            manifest=json.loads((Path(request['folder'])/'project.json').read_bytes())
            manifest['model']=dict(manifest['scene'],reference_opacity=.25)
            (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request)
            result=self.unpack(root,request)
            self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['model']['reference_opacity'],.25)
            before=Path(request['path']).read_bytes()
            for bad in [-.1,1.1,float('nan'),float('inf'),True,'.5',None]:
                manifest['model']['reference_opacity']=bad
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))
                with self.assertRaisesRegex(has.HasError,'Reference opacity'):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_pack_waits_for_owned_snapshot_and_uses_linked_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,name,original=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            request.update(storage='linked',result=str(root/'job-result.json'),snapshot_ready=str(root/'job-snapshot.json'))
            manifest=json.loads((Path(request['folder'])/'project.json').read_bytes());manifest['palette']=[{'name':'New','rgba':'ff0000ff'}];(Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))
            outcome=[]
            def run():
                try:outcome.append(has.pack(request))
                except Exception as error:outcome.append(error)
            thread=threading.Thread(target=run);thread.start()
            try:
                time.sleep(.06);self.assertTrue(thread.is_alive());self.assertEqual(Path(request['path']).read_bytes(),before)
            finally:
                Path(request['snapshot_ready']).write_bytes(has.json_bytes(dict(format='studio_has_snapshot_ready_1',ok=True,error='',references={name:str(original)})))
                thread.join(10)
            self.assertFalse(thread.is_alive());self.assertEqual(len(outcome),1);self.assertIsInstance(outcome[0],dict);self.assertTrue(outcome[0]['ok'])
            self.assertEqual(Path(str(request['path'])+'.backup').read_bytes(),before)
            result=self.unpack(root,request);self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['palette'],manifest['palette'])

    def test_pending_snapshot_cancellation_preserves_prior_good_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            request.update(result=str(root/'job-result.json'),snapshot_ready=str(root/'job-snapshot.json'),cancel=str(root/'cancel'));Path(request['cancel']).write_text('cancel')
            with self.assertRaisesRegex(has.HasError,'cancelled'):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_failed_or_malformed_snapshot_status_preserves_prior_good_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            request.update(result=str(root/'job-result.json'),snapshot_ready=str(root/'job-snapshot.json'))
            good=dict(format='studio_has_snapshot_ready_1',ok=True,error='',references={})
            for bad in [dict(good,ok=False,error='Snapshot failed'),dict(good,ok=1),dict(good,format='unknown'),dict(good,references=[]),dict(good,references={'asset':1}),dict(good,extra=True)]:
                Path(request['snapshot_ready']).write_bytes(has.json_bytes(bad))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_snapshot_status_address_and_symlink_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            request.update(result=str(root/'job-result.json'),snapshot_ready=str(root/'unrelated.json'))
            with self.assertRaisesRegex(has.HasError,'belong'):has.pack(request)
            target=root/'status.json';target.write_bytes(has.json_bytes(dict(format='studio_has_snapshot_ready_1',ok=True,error='',references={})));ready=root/'job-snapshot.json';ready.symlink_to(target);request['snapshot_ready']=str(ready)
            with self.assertRaisesRegex(has.HasError,'Linked'):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_snapshot_wait_has_separate_bounded_preparation_allowance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            request.update(result=str(root/'job-result.json'),snapshot_ready=str(root/'job-snapshot.json'))
            with mock.patch.object(has.time,'monotonic',side_effect=[0.,121.,601.]) as clock, mock.patch.object(has.time,'sleep'):
                with self.assertRaisesRegex(has.HasError,'preparation timed out'):has.pack(request)
                self.assertEqual(clock.call_count,3)
            self.assertEqual(Path(request['path']).read_bytes(),before)


if __name__=='__main__':unittest.main()
