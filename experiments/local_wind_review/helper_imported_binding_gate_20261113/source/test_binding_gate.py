"""Synthetic completeness/transfer controls first. No Godot/model import."""
import copy,importlib.util,json,math,sys,time,unittest
from unittest.mock import patch
import import_synthetic as I
from pathlib import Path
import binding_gate as G
import support as S
sys.path.insert(0,str(S.TASK/"isolated-v2/tools"));sys.path.insert(0,str(S.TASK/"isolated-v2/tests"))
import wind_helper_preview as P
import secondary_helpers as H
from test_secondary_helpers import two_panel_fixture,request,write_glb
NEUTRAL={"format":"studio_source_shape_2","enabled":False,"overrides":{}}
IDENTITY=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
def doc(helper=False):
    nodes=[{"children":[1,3]},{"children":[2]},{},{"mesh":0,"skin":0}]
    if helper:nodes[2]["children"]=[4];nodes.append({})
    return {"nodes":nodes,"scenes":[{"nodes":[0]}],"skins":[{"joints":[1,2]+([4]if helper else[]),"skeleton":1}],"meshes":[{"primitives":[{"targets":[]}]}]}
def snapshot(data,prefix):
    inv=G.inventory(data);rows={}
    for node in inv["nodes"]:
        i=node["source_node"];kind="bone"if i in inv["skin_joints"]else"node"
        parent=node["parent"]
        while parent>=0 and parent not in inv["skin_joints"]:parent=inv["nodes"][parent]["parent"]
        rows[str(i)]={"runtime_parent_source_node":parent,"source_node":i,"source_parent":node["parent"],"kind":kind,"id":prefix+str(i),"base":IDENTITY.copy(),"global_base":IDENTITY.copy(),"runtime_identity":prefix+"runtime"+str(i)}
    return {"format":"has_actual_imported_bindings_1","glb_sha256":prefix*64,"node_count":inv["node_count"],"source_node_audit":inv["nodes"],"bindings":rows,"coverage":[{"source_node":i,"status":"mapped"}for i in range(inv["node_count"])],"secondary_error":"","problems":[],"shape":copy.deepcopy(NEUTRAL),"shapes":[]}
class Controls(unittest.TestCase):
    def setUp(self):self.before=doc();self.after=doc(True);self.a=snapshot(self.before,"a");self.b=snapshot(self.after,"b")
    def gate(self):return G.transfer(self.a,self.b,G.inventory(self.before),G.inventory(self.after),"a"*64,"b"*64,P,NEUTRAL)
    def test_explicit_source_node_id_remap_and_new_helpers(self):
        self.b["bindings"]={key:self.b["bindings"][key]for key in reversed(self.b["bindings"])}
        result=self.gate();self.assertEqual(set(result["bindings"]),{"0","1","2","3"});self.assertEqual(result["added_helper_nodes"],[4])
        self.assertNotEqual(result["bindings"]["2"]["source_binding"]["id"],result["bindings"]["2"]["candidate_binding"]["id"])
    def test_wrong_local_base_refused(self):
        self.b["bindings"]["2"]["base"][12]=.1
        with self.assertRaisesRegex(ValueError,"base transform"):self.gate()
    def test_wrong_global_base_refused(self):
        self.b["bindings"]["2"]["global_base"][12]=.1
        with self.assertRaisesRegex(ValueError,"global base"):self.gate()
    def test_alias_runtime_or_id_refused(self):
        for key in("runtime_identity","id"):
            self.setUp();self.b["bindings"]["2"][key]=self.b["bindings"]["1"][key]
            with self.assertRaisesRegex(ValueError,"alias"):self.gate()
    def test_missing_original_in_both_tables_does_not_fake_complete_coverage(self):
        for value in(self.a,self.b):value["bindings"].pop("2");value["coverage"][2]["status"]="unmapped"
        with self.assertRaisesRegex(ValueError,"Incomplete original/declared coverage"):self.gate()
    def test_missing_added_helper_refused(self):
        self.b["bindings"].pop("4");self.b["coverage"][4]["status"]="unmapped"
        with self.assertRaisesRegex(ValueError,"coverage"):self.gate()
    def test_added_helper_cannot_borrow_runtime_identity(self):
        self.b["bindings"]["4"]["runtime_identity"]=self.b["bindings"]["2"]["runtime_identity"]
        with self.assertRaisesRegex(ValueError,"alias"):self.gate()
    def test_wrong_source_node_table_key_refused(self):
        self.b["bindings"]["2"]["source_node"]=1
        with self.assertRaisesRegex(ValueError,"correspondence"):self.gate()
    def test_wrong_source_inventory_refused(self):
        self.b["source_node_audit"][2]["parent"]=0
        with self.assertRaisesRegex(ValueError,"inventory correspondence"):self.gate()
    def test_wrong_binding_kind_for_declared_skin_joint_refused(self):
        self.b["bindings"]["2"]["kind"]="node"
        with self.assertRaisesRegex(ValueError,"skin joint"):self.gate()
    def test_nonfinite_or_short_matrix_refused(self):
        for value in([1.]*15,[float("nan")]*16):
            self.b["bindings"]["2"]["base"]=value
            with self.assertRaisesRegex(ValueError,"matrices"):self.gate()
    def test_incomplete_coverage_ledger_refused(self):
        self.b["coverage"].pop()
        with self.assertRaisesRegex(ValueError,"coverage ledger"):self.gate()
    def test_missing_inactive_declared_node_is_still_refused(self):
        self.before["nodes"].append({});self.before["skins"][0]["joints"].append(4)
        inv=G.inventory(self.before);self.assertIn(4,inv["required_nodes"])
        with self.assertRaises(ValueError):G.validate_snapshot(self.a,inv,"a"*64,NEUTRAL)
    def test_offset_can_share_only_explicit_parent_bone_id(self):
        data=doc();data["nodes"][2]["children"]=[4];data["nodes"].append({})
        value=snapshot(data,"a");value["bindings"]["4"].update(kind="offset",id=value["bindings"]["2"]["id"],runtime_attachment_parent_source_node=2,observed_node_local=IDENTITY.copy(),offset_composed_global=IDENTITY.copy())
        G.validate_snapshot(value,G.inventory(data),"a"*64,NEUTRAL)
        value["bindings"]["4"]["id"]=value["bindings"]["1"]["id"]
        with self.assertRaisesRegex(ValueError,"parent bone"):G.validate_snapshot(value,G.inventory(data),"a"*64,NEUTRAL)
    def test_actual_identity_parent_change_refused_even_at_same_neutral_matrices(self):
        self.b["bindings"]["2"]["runtime_parent_source_node"]=4
        with self.assertRaisesRegex(ValueError,"Actual bone parent"):self.gate()
    def test_snapshot_problem_flag_cannot_bypass_pure_transfer(self):
        self.a["problems"]=["unsupported import"]
        with self.assertRaisesRegex(ValueError,"snapshot problems"):self.gate()
    def test_duplicate_coverage_ledger_row_refused(self):
        self.b["coverage"].append(copy.deepcopy(self.b["coverage"][0]))
        with self.assertRaisesRegex(ValueError,"coverage ledger"):self.gate()
    def test_static_morph_requested_effective_actual_and_missing_rows_refused(self):
        data=doc();data["meshes"][0]["primitives"][0]["targets"]=[{}];data["meshes"][0]["weights"]=[.25]
        value=snapshot(data,"a");wanted={"format":"studio_source_shape_2","enabled":True,"overrides":{}}
        value["shape"]=copy.deepcopy(wanted);value["shapes"]=[{"source_node":3,"effective_weights":[.25],"actual_weights":[.25]}]
        G.validate_snapshot(value,G.inventory(data),"a"*64,wanted)
        for field,wrong in(("shape",NEUTRAL),("shapes",[])):
            changed=copy.deepcopy(value);changed[field]=wrong
            with self.assertRaises(ValueError):G.validate_snapshot(changed,G.inventory(data),"a"*64,wanted)
        for field in("effective_weights","actual_weights"):
            changed=copy.deepcopy(value);changed["shapes"][0][field]=[0.]
            with self.assertRaisesRegex(ValueError,"morph weights"):G.validate_snapshot(changed,G.inventory(data),"a"*64,wanted)
    def test_declared_offset_requires_descriptor_and_actual_attachment(self):
        data=doc();data["nodes"][2]["children"]=[4];data["nodes"].append({})
        data["extensions"]={"VRMC_springBone":{"springs":[{"joints":[{"node":2},{"node":4}]}]}}
        value=snapshot(data,"a");value["bindings"]["4"].update(kind="offset",id=value["bindings"]["2"]["id"],runtime_attachment_parent_source_node=2,observed_node_local=IDENTITY.copy(),offset_composed_global=IDENTITY.copy(),secondary_offset_matrix=IDENTITY.copy())
        G.validate_snapshot(value,G.inventory(data),"a"*64,NEUTRAL)
        missing=copy.deepcopy(value);missing["bindings"]["4"].pop("secondary_offset_matrix")
        with self.assertRaisesRegex(ValueError,"lacks actual secondary descriptor"):G.validate_snapshot(missing,G.inventory(data),"a"*64,NEUTRAL)
        for field in("secondary_offset_matrix","observed_node_local","offset_composed_global"):
            changed=copy.deepcopy(value);changed["bindings"]["4"][field][12]=.1
            with self.assertRaises(ValueError):G.validate_snapshot(changed,G.inventory(data),"a"*64,NEUTRAL)
        value["bindings"]["4"]["runtime_attachment_parent_source_node"]=1
        with self.assertRaisesRegex(ValueError,"BoneAttachment"):G.validate_snapshot(value,G.inventory(data),"a"*64,NEUTRAL)
    def test_missing_file_and_context_failures_retain_final_receipt_before_raising(self):
        folder=RUN/"missing-protection";folder.mkdir();path=folder/"owned-fixture.txt";path.write_text("owned synthetic data")
        record=S.stamp(path);path.unlink()
        private={"files":[],"runtime_executables":[]}
        before=S.own_sources();outcome={"status":"PASS","earlier_error":"preserved"}
        with patch.object(S,"head",return_value="wrong"):
            with self.assertRaisesRegex(ValueError,"receipts retained"):S.finish(folder,outcome,[record],private,before)
        kept=json.loads((folder/"result.json").read_bytes())
        self.assertEqual(kept["status"],"FAILED_PRESERVATION_RETAIN_ALL");self.assertEqual(kept["earlier_error"],"preserved")
        self.assertFalse(kept["preservation"]["gates"]["original_0"]["passed"])
        self.assertFalse(kept["preservation"]["gates"]["root_head"]["passed"])
    def test_timeout_retains_partial_logs_without_retry_or_runtime(self):
        folder=RUN/"timeout";folder.mkdir()
        error=I.subprocess.TimeoutExpired(["not-runtime"],1,output=b"partial stdout",stderr=b"partial stderr")
        with patch.object(I.subprocess,"run",side_effect=error)as mocked:
            with self.assertRaises(I.subprocess.TimeoutExpired):I.captured(["not-runtime"],folder,1)
            self.assertEqual(mocked.call_count,1)
        self.assertEqual((folder/"process.log").read_text(),"partial stdoutpartial stderr")
        receipt=json.loads((folder/"execution.json").read_bytes());self.assertEqual(receipt["status"],"TIMEOUT_UNACCEPTED_RETAIN_ALL");self.assertFalse(receipt["retry"])
    def test_default_and_nonzero_reviewed_static_morph_build_preserves_originals(self):
        for options in({"source_morph_defaults":True},{"source_morph_defaults":False,"morph_weights":{"3":[.5]}}):
            folder=RUN/("morph-"+str(len(list(RUN.iterdir()))));folder.mkdir()
            source=folder/"source.glb";g=two_panel_fixture(source,"v1");g.doc["meshes"][0]["weights"]=[.25];write_glb(source,g.doc,bytes(g.binary));g=H.GLB(source)
            before=S.stamp(source);item=request(g);item.update(options)
            review=H.preview(source,item);self.assertTrue(review["can_apply"])
            result=H.build(source,folder/"derived",item);after=H.GLB(result["glb"])
            retained=P.retained_bindings(g,after)
            self.assertEqual(retained["original_nodes"],len(g.doc["nodes"]));self.assertGreater(len(after.doc["nodes"]),len(g.doc["nodes"]))
            self.assertEqual(before,S.stamp(source))
            self.assertEqual(g.morph_weights(3,item),[.25]if options["source_morph_defaults"]else[.5])
            SYNTHETIC.append({"source":str(source),"derived":result["glb"],"shape":options,"source_identity":before,"request":item,"retained_nodes":retained["original_nodes"]})
if __name__=="__main__":
    RUN=S.owned(S.TASK/"synthetic"/str(time.time_ns()));RUN.mkdir(parents=True);SYNTHETIC=[]
    before=S.private_sources();own_before={p.name:S.stamp(p)for p in(S.TASK/"source").glob("*")if p.is_file()}
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    preserved=before==S.private_sources() and own_before=={p.name:S.stamp(p)for p in(S.TASK/"source").glob("*")if p.is_file()}
    S.publish(S.TASK/("synthetic-cpu-"+str(time.time_ns())+".json"),{"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"failure_details":[{"test":str(t),"detail":detail}for t,detail in result.failures+result.errors],"sources_preserved":preserved,"own_source_before":own_before,"own_source_after":S.own_sources(),"synthetic_inputs":SYNTHETIC,"godot":"UNRUN","retained_actual_assets":"UNRUN"})
    raise SystemExit(0 if result.wasSuccessful()and preserved else 1)
