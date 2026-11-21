import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-live-normal-bridge-v2-prep-20261120'
out=root/'output/source-live-normal-bridge-v2-cpu-20261120-01'
pins={'deps/creation_support.py': (72518, '2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea'), 'deps/current_id_ledger.py': (14885, 'ab2d0d3076f63d6a398b209a5a39c2334f3b00664c0fa38d152d4587a54ffee9'), 'deps/native_point_expectation.py': (27615, 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d'), 'deps/weight_policy.py': (20860, 'f838e0d893969aa1ad884a1c1d92e28ba019454f313632855f2a33c55fc3415c'), 'deps/import_instrumentation.py': (3306, '361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895'), 'deps/normal_export_adapter.py': (23576, '5d19134b9a4fbfd7a93777d9eb3026173d52b6380e3beb80a8211dedf9afc24e'), 'deps/vvd_normals.py': (4184, 'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb'), 'deps/normal_identity_carrier.py': (17632, '37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08'), 'deps/material_inspection.py': (24579, '5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17'), 'deps/export_hook_proposal.py': (48895, 'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511'), 'deps/resource_gate_proposal.py': (55481, '4ce714dc84712384d089fc2d0b5b5a93c25c1f3dfe90f53ccee76477a3d1cee8'), 'deps/shared_image_cache_proposal.py': (36158, 'b4aed0a276e5a469274e961e11bddff6183e6d56d4ff91af9e339af4712617e6'), 'deps/observer_instrumentation.py': (7829, '15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b'), 'deps/gather_binding.py': (17534, '617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850'), 'deps/carrier_export.py': (33129, '867b8ca6dbd11818edca22d6dc8a0e0671e0855d7d9c7c87ba317e5059868941'), 'deps/cold_image_readiness.py': (14496, 'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'), 'deps/semantic_compare.py': (22754, 'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00'), 'deps/input_domain.py': (16109, 'c679d873aa45aac4fad553f014e83c8e42a9a458c8189151e9e3695072be8c74'), 'source_native_normal_export.py': (29852, '9e79cbb74a5d59707f58fdb042b6ea4033269459582e73d20d7b0381303cfbcf'), 'test_source_native_normal_export.py': (22345, 'f6e2ca5ed9121522003579ef9a520fef3a8a6c06a30a1b893ebda60cfcfbc4db'), 'blender_source_bridge_candidate.py': (30508, '4164cb6e264bfac1e3d7e6e9426370398eb6828ffe49735334893aff64f7f633')}
def snap():
    rows={}
    for name,(size,digest) in pins.items():
        p=suite/name; b=p.read_bytes(); s=p.stat()
        assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,name
        rows[name]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
start=time.monotonic()
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p','test_source_native_normal_export.py'],cwd=root,capture_output=True)
elapsed=time.monotonic()-start
(out/'stdout.log').write_bytes(r.stdout); (out/'stderr.log').write_bytes(r.stderr)
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_live_normal_bridge_v2_cpu_root_1','status':'PASS' if r.returncode==0 and before==after else 'FAIL','returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':19}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); print(r.stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if result['status']=='PASS' else 1)