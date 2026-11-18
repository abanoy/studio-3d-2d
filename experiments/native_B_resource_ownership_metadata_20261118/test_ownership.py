"""Small synthetic RNA fixtures only; no bpy, native assets or processes."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import ast
import copy
import hashlib
import unittest

import survey_core as Base
from ownership_metadata import collect_ownership_metadata


class RNA:
    next_id = 100
    def __init__(self, kind='ID', name='PRIVATE_FIXTURE', **values):
        RNA.next_id += 1
        self.identity = RNA.next_id
        self.bl_rna = NS(identifier=kind)
        self.name = self.name_full = name
        self.library = self.library_weak_reference = None
        self.__dict__.update(values)
    def as_pointer(self): return self.identity
    def path_from_module(self, property=''):
        if self.__dict__.get('path_unavailable'): raise ValueError('private text must not escape')
        return 'bpy.data.fixture[' + repr(self.name_full) + ']' + ('.' + property if property else '')
    def __getattr__(self, key): raise AssertionError('Forbidden/unprovided metadata getter: ' + key)


class Packed(RNA):
    def __init__(self, data):
        super().__init__('PackedFile', size=len(data)); self.payload=data; self.reads=0
    @property
    def data(self): self.reads += 1; return self.payload


def fixture():
    def image(name, path, source='FILE', kind='IMAGE'):
        packed = Packed(name.encode()) if path else None
        return RNA('Image', name, filepath=path, filepath_raw=path, source=source, type=kind,
                   alpha_mode='STRAIGHT', colorspace_settings=NS(name='sRGB'), is_dirty=False,
                   has_data=False, use_multiview=False, is_multiview=False, is_stereo_3d=False,
                   users=0, packed_file=packed,
                   packed_files=[] if packed is None else [NS(packed_file=packed,filepath=path,view=0,tile_number=1001)])
    images=[image('PRIVATE_A','//textures/a.png'),image('PRIVATE_B','//textures/b.png'),
            image('PRIVATE_VIEW_A','', 'VIEWER','RENDER_RESULT'),image('PRIVATE_VIEW_B','', 'VIEWER','COMPOSITING')]
    trees=[]; materials=[]
    for n in range(2):
        nodes=[RNA('Node', bl_idname='ShaderNodeTexImage',image=im) for im in images[:2]]
        tree=RNA('ShaderNodeTree',bl_idname='ShaderNodeTree',nodes=nodes); trees.append(tree)
        materials.append(RNA('Material',use_nodes=True,node_tree=tree))
    unknown='//assets/does_not_establish_role.blend'
    brush=RNA('Brush','PRIVATE_OWNER')
    brush.library_weak_reference=RNA('LibraryWeakReference',filepath=unknown,id_name='BRPRIVATE_TARGET')
    scene=RNA('Scene'); screen=RNA('Screen',areas=[])
    meshes=[RNA('Object',name,type='MESH',hide_render=False,hide_get=lambda:False) for name in ['Hat.smd','hair.smd']]
    ids=[*images,*materials,*trees,brush,scene,screen,*meshes]
    users={value:set() for value in ids}
    for im in images[:2]: users[im]=set(trees)
    for tree,mat in zip(trees,materials): users[tree]={mat}
    paths=[(images[0],images[0].filepath),(images[1],images[1].filepath),(brush,unknown)]
    bpy=NS(data=NS(libraries=[],images=images,materials=materials,screens=[screen]),
           context=NS(scene=NS(objects=meshes)), calls=[],visitor_returns=[],path_replacements=[])
    bpy.data.user_map=lambda:users
    def visit(fn, **kw):
        bpy.calls.append(kw)
        for owner,path in paths:
            result=fn(owner,path,None); bpy.visitor_returns.append(result)
            if result is not None: bpy.path_replacements.append(result)
    bpy.data.file_path_foreach=visit
    bpy.utils=NS(blend_paths=lambda **kw:[images[0].filepath,images[1].filepath,unknown])
    return bpy,NS(images=images,materials=materials,trees=trees,brush=brush,scene=scene,screen=screen,
                  users=users,paths=paths,unknown=unknown)


def baseline(bpy): return Base.collect_resources(bpy,r'C:\protected\original.blend')


class OwnershipTests(unittest.TestCase):
    def test_six_original_refusals_status_and_hash_are_preserved(self):
        bpy,f=fixture(); private,public=baseline(bpy); before=Base.canonical(private)
        extra,summary=collect_ownership_metadata(bpy,private,public)
        self.assertEqual(len(private['issues']),6)
        self.assertEqual([row['code'] for row in private['issues']],
                         ['UNSUPPORTED_IMAGE_SOURCE_OR_TYPE','EMPTY_FILE_IMAGE_WITHOUT_PACKED_DATA']*2+
                         ['UNCLASSIFIED_EXTERNAL_REFERENCE_REFUSED']*2)
        self.assertEqual(extra['original_issues'],private['issues'])
        self.assertEqual(summary['original_resource_summary'],public)
        self.assertEqual(summary['status'],'RESOURCE_PROFILE_REFUSED')
        self.assertEqual(before,Base.canonical(private))
        self.assertEqual(summary['ownership_metadata_sha256'],hashlib.sha256(Base.canonical(extra)).hexdigest())
        for value in ['PRIVATE_',f.unknown,'C:']: self.assertNotIn(value,Base.canonical(summary).decode())

    def test_weak_path_records_actual_owner_type_rna_path_and_exact_join(self):
        bpy,f=fixture(); extra,public=collect_ownership_metadata(bpy,*baseline(bpy))
        owner=next(row for row in extra['owners'] if row['session_identity']==f.brush.identity)
        self.assertEqual(owner['rna_type'],'Brush')
        self.assertEqual(owner['data_path']['status'],'OBSERVED')
        weak=extra['ID_library_weak_references'][0]
        self.assertEqual((weak['rna_type'],weak['filepath'],weak['id_name']),
                         ('LibraryWeakReference',f.unknown,'BRPRIVATE_TARGET'))
        self.assertEqual(len([row for row in extra['external_reference_owner_joins']
                              if row['exact_owner_and_library_weak_reference_rows']==[0]]),2)
        self.assertEqual(bpy.calls,[{'flags':{'SKIP_PACKED'}}])
        self.assertTrue(all(value is None for value in bpy.visitor_returns))
        self.assertEqual(bpy.path_replacements,[])

    def test_filename_does_not_assign_brush_role(self):
        bpy,f=fixture(); f.brush.bl_rna.identifier='World'; f.paths[-1]=(f.brush,'//essentials_brushes-gp_draw.blend')
        private,public=baseline(bpy); extra,_=collect_ownership_metadata(bpy,private,public)
        owner=next(row for row in extra['owners'] if row['session_identity']==f.brush.identity)
        self.assertEqual(owner['rna_type'],'World')
        self.assertFalse(extra['filename_or_basename_role_inference'])
        self.assertEqual(extra['external_reference_owner_joins'][2]['status'],'OWNER_UNOBSERVED')

    def test_unmatched_weak_descriptor_does_not_establish_path_relationship(self):
        bpy,f=fixture(); f.paths[-1]=(f.scene,f.unknown)
        extra,_=collect_ownership_metadata(bpy,*baseline(bpy))
        for row in extra['external_reference_owner_joins']:
            if row['path_index']==2:
                self.assertEqual(row['exact_raw_owner_ids'],[f.scene.identity])
                self.assertEqual(row['nested_reference_property_status'],'UNOBSERVED')

    def test_viewer_other_owner_and_transitive_material_graph_cycle(self):
        bpy,f=fixture(); f.users[f.images[2]]={f.scene}; f.users[f.scene]={f.trees[0]}
        f.users[f.materials[0]]={f.scene}
        extra,_=collect_ownership_metadata(bpy,*baseline(bpy))
        viewer=extra['viewer_reachability'][0]
        self.assertEqual(viewer['reachable_material_ids'],[f.materials[0].identity])
        self.assertIn(f.scene.identity,viewer['reachable_other_id_owners'])
        self.assertEqual(viewer['original_material_node_references'],[])
        self.assertFalse(viewer['resource_excluded_or_accepted'])

    def test_zero_users_does_not_hide_observed_image_editor_owner(self):
        bpy,f=fixture(); space=RNA('SpaceImageEditor',type='IMAGE_EDITOR',image=f.images[2])
        f.screen.areas=[NS(spaces=[space])]
        extra,_=collect_ownership_metadata(bpy,*baseline(bpy))
        viewer=extra['viewer_reachability'][0]
        self.assertEqual(viewer['original_users'],0)
        self.assertEqual(len(viewer['image_editor_references']),1)
        self.assertEqual(viewer['image_editor_references'][0]['owner'],f.screen.identity)
        self.assertIn('non_IMAGE_EDITOR_UI',viewer['unobserved_owner_scopes'])

    def test_valid_rna_without_global_path_is_explicitly_unobserved(self):
        bpy,f=fixture(); f.brush.path_unavailable=True
        extra,_=collect_ownership_metadata(bpy,*baseline(bpy))
        owner=next(row for row in extra['owners'] if row['session_identity']==f.brush.identity)
        self.assertEqual(owner['data_path'],{'status':'UNOBSERVED','value':None})
        self.assertEqual(extra['ID_library_weak_references'][0]['property_data_path']['status'],'UNOBSERVED')

    def test_malformed_map_and_boolean_pointer_fail_without_changing_baseline(self):
        for bad in ['map','pointer']:
            bpy,f=fixture(); private,public=baseline(bpy); before=Base.canonical(private)
            if bad=='map': bpy.data.user_map=lambda:[]
            else: f.brush.identity=True
            with self.assertRaises(Base.SurveyError): collect_ownership_metadata(bpy,private,public)
            self.assertEqual(Base.canonical(private),before)

    def test_stale_or_forged_baseline_fails_before_owner_api(self):
        for bad in ['hash','images','status']:
            bpy,f=fixture(); private,public=baseline(bpy)
            bpy.data.user_map=lambda:(_ for _ in ()).throw(AssertionError('owner API called'))
            if bad=='hash': public['private_metadata_sha256']='0'*64
            elif bad=='status': public['status']='ACCEPTED'
            else: f.images[0].identity+=9999
            with self.assertRaises(Base.SurveyError): collect_ownership_metadata(bpy,private,public)

    def test_visitor_failures_still_return_none_and_never_replace_paths(self):
        bpy,f=fixture(); private,public=baseline(bpy); f.paths[:]=[(f.brush,7),(f.brush,'//later')]
        with self.assertRaises(Base.SurveyError): collect_ownership_metadata(bpy,private,public)
        self.assertEqual(bpy.visitor_returns,[None,None]); self.assertEqual(bpy.path_replacements,[])
        self.assertEqual(len(private['issues']),6)

    def test_invalidated_rna_callback_does_not_escape_as_partial_success(self):
        bpy,f=fixture(); private,public=baseline(bpy)
        dead=RNA(); dead.as_pointer=lambda:(_ for _ in ()).throw(ReferenceError('invalid RNA'))
        f.paths[:]=[(dead,'//unobserved'),(f.brush,'//later')]
        with self.assertRaises(ReferenceError): collect_ownership_metadata(bpy,private,public)
        self.assertEqual(bpy.visitor_returns,[None,None]); self.assertEqual(bpy.path_replacements,[])
        self.assertEqual(len(private['issues']),6)

    def test_bounds_malformed_weak_metadata_and_ui_identity_are_not_accepted(self):
        for bad in ['edges','weak','ui']:
            bpy,f=fixture(); private,public=baseline(bpy)
            limit=Base.Limits()
            if bad=='edges': limit=replace(limit,image_references=1)
            elif bad=='weak': f.brush.library_weak_reference.filepath=7
            else: f.screen.areas=[NS(spaces=[RNA('SpaceImageEditor',type='IMAGE_EDITOR',image=RNA('Image'))])]
            with self.assertRaises(Base.SurveyError): collect_ownership_metadata(bpy,private,public,limit)
            self.assertEqual(len(private['issues']),6)

    def test_no_file_io_or_additional_packed_pixel_geometry_access(self):
        bpy,f=fixture(); private,public=baseline(bpy)
        before=[im.packed_file.reads for im in f.images if im.packed_file is not None]
        with patch('builtins.open',side_effect=AssertionError('file open')),patch.object(Path,'stat',side_effect=AssertionError('stat')):
            extra,summary=collect_ownership_metadata(bpy,private,public)
        self.assertEqual(before,[im.packed_file.reads for im in f.images if im.packed_file is not None])
        self.assertFalse(extra['external_path_contents_opened_or_statted'])
        self.assertFalse(extra['pixel_geometry_matrix_weight_arrays_read'])
        self.assertFalse(summary['strict31_native_qualified'])
        self.assertFalse(summary['normal_tolerance_or_fidelity_qualified'])
        self.assertFalse(summary['export_repair_carrier_or_adoption_qualified'])

    def test_source_and_original_parent_collector_are_bounded_source_only(self):
        here=Path(__file__).resolve().parent
        self.assertEqual(hashlib.sha256((here/'survey_core.py').read_bytes()).hexdigest(),
                         '39a417bfe8e024704f4d400f824293640370074c28446e40613aa401247a4e28')
        source=ast.parse((here/'ownership_metadata.py').read_bytes())
        imports={n.names[0].name for n in source.body if isinstance(n,ast.Import)}
        self.assertEqual(imports,{'hashlib','json'})
        calls=[n for n in ast.walk(source) if isinstance(n,ast.Call)]
        forbidden={'open','stat','load','reload','save','read','write','path_resolve','orphans_purge','batch_remove','evaluated_get'}
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in forbidden for n in calls))


if __name__=='__main__': unittest.main()
