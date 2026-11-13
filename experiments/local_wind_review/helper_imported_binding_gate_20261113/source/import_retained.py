"""Checksum-bound owned retained inputs; headless imports/pure Python derivation."""
from pathlib import Path
import collections,json,sys,time
import support as S
import binding_gate as G
from import_synthetic import observe,shape_config
sys.path.insert(0,str(S.TASK/"isolated-v2/tools"))
import secondary_helpers as H
import wind_helper_preview as P
MANIFEST_SHA="293c6827f3b2312ee7a56062290ec0281990a8fd0609c238a1419236a4ad5fb8"
def main():
    S.require(S.head()==S.REVISION,"Exact reviewed root context")
    synthetic=sorted((S.TASK/"synthetic-imports-v2").glob("*/result.json"));S.require(synthetic and json.loads(synthetic[-1].read_bytes())["status"]=="PASS","Synthetic actual imports must pass first")
    manifest=S.ROOT/"output/wind-review-inputs.json";stage=S.ROOT/"output/wind-main-fixtures-1794548724013390200/staging-receipt.json"
    private=S.private_sources();own_before=S.own_sources()
    protected=[];results=[];unexpected=[];assets=[]
    folder=S.owned(S.TASK/"retained-imports-v2"/str(time.time_ns()));folder.mkdir(parents=True)
    try:
        protected.extend([S.stamp(manifest),S.stamp(stage)])
        S.require(protected[0]["sha256"]==MANIFEST_SHA,"Checksum-bound input manifest differs")
        inputs=json.loads(manifest.read_bytes());original=json.loads(stage.read_bytes());rows={Path(r["destination"]):r for r in original["files"]}
        for role,item in inputs["inputs"].items():
            case=S.owned(folder/role);case.mkdir();copies={}
            for kind,key,name in(("source","source","scene.glb"),("parameters","parameters","parameters.json")):
                path=S.no_reparse(S.ROOT/"output"/item[key]);S.require(path in rows and rows[path]["role"]==role and rows[path]["kind"]==kind,"Manifest/staging role membership differs")
                identity=S.stamp(path);expected=rows[path]["identity"]
                S.require((identity["sha256"],identity["bytes"])==(expected["sha256"],expected["bytes"]),"Retained bundle checksum/size differs")
                protected.append(identity);target=case/name
                with target.open("xb")as stream:stream.write(path.read_bytes())
                S.require(S.stamp(target)["sha256"]==identity["sha256"],"Owned input copy differs");copies[kind]=str(target)
            assets.append({"role":role,"alias":"backhair input is staged ribbon; not a separate Back Hair file"if role=="backhair"else role,"case":str(case),"copies":copies})
        S.publish(folder/"staging.json",{"inputs_manifest_sha256":MANIFEST_SHA,"assets":assets,"protected_originals":protected,"native_converters_steam_or_downloads_used":False})
        for asset in assets:
            role=asset["role"];case=Path(asset["case"]);source=Path(asset["copies"]["source"]);record={"role":role,"alias":asset["alias"],"source_identity":S.stamp(source)}
            results.append(record)
            try:
                options={"source_morph_defaults":True};shape=shape_config(options)
                snapshot=observe(source,shape,case/"original-import")
                glb=H.GLB(source);inv=G.inventory(glb.doc)
                record.update(original_import="COMPLETE_BINDING_COVERAGE",original_nodes=inv["node_count"],original_bound_nodes=len(snapshot["bindings"]),original_required_nodes=len(inv["required_nodes"]),original_binding_kinds=dict(collections.Counter(r["kind"]for r in snapshot["bindings"].values())),secondary_chains=snapshot["secondary_chains"],secondary_colliders=snapshot["secondary_colliders"])
                assessment=H.inspect(source,options)
                # Metadata-only assessment disclosure; do not save preview raw vertex arrays.
                S.publish(case/"assessment.json",assessment)
                proposals=[];refusals=[]
                ordered=sorted(assessment["regions"],key=lambda r:(0 if r.get("existing_chain")else 1,r["node"],r["primitive"],r["component"]))
                for region in ordered[:64]:
                    request={"source_sha256":glb.sha,"node":region["node"],"primitive":region["primitive"],"component":region["component"],"anchor_node":region["anchor_node"],"segments":3,"reviewed":True,**options}
                    if region.get("existing_chain"):request["use_existing_joints"]=True
                    try:
                        preview=H.preview(source,request)
                        if not preview.get("can_apply",False):raise ValueError("No bounded usable proposal")
                        proposals.append(request);break
                    except ValueError as error:refusals.append({"node":region["node"],"primitive":region["primitive"],"component":region["component"],"reason":str(error)})
                S.publish(case/"proposal-selection.json",{"policy":"Binding experiment only: prefer an actual unconfigured existing_chain, then source-node/primitive/component order; at most64 candidates; not artist/physics acceptance","request":proposals[0]if proposals else None,"refusals":refusals})
                if not proposals:
                    record["derivation"]="NO_BOUNDED_EXISTING_BUILDER_PROPOSAL";continue
                built=H.build(source,case/"derived",proposals[0]);candidate=H.GLB(built["glb"])
                retained=P.retained_bindings(glb,candidate)
                S.publish(case/"retained-glb-bindings.json",retained)
                after=observe(Path(built["glb"]),shape,case/"candidate-import")
                transfer=G.transfer(snapshot,after,inv,G.inventory(candidate.doc),glb.sha,candidate.sha,P,shape)
                S.publish(case/"imported-binding-transfer.json",transfer)
                record.update(derivation="COMPLETE_ACTUAL_BINDING_TRANSFER",candidate_sha256=candidate.sha,added_helper_nodes=transfer["added_helper_nodes"],original_transferred_nodes=transfer["original_bound_nodes"],builder_mode="existing_joints"if proposals[0].get("use_existing_joints")else"weighted")
            except Exception as error:
                record["status"]="REFUSED_OR_FAILED_RETAIN_ALL";record["error"]=type(error).__name__+": "+str(error);unexpected.append({"role":role,"error":record["error"]})
    except Exception as error:unexpected.append({"phase":"staging_or_outer","error":type(error).__name__+": "+str(error)})
    status="FAILED_RETAIN_ALL"if unexpected else("BOUND_COVERAGE_WITH_EXPLICIT_NO_PROPOSAL"if any(r.get("derivation")=="NO_BOUNDED_EXISTING_BUILDER_PROPOSAL"for r in results)else"COMPLETE_BINDING_TRANSFER")
    result={"status":status,"cases":results,"refusals_or_failures":unexpected,"protected_before":protected,"scope":"Actual retained derived-bundle headless binding/base coverage and pure-Python helper derivation only","gpu_ui_physics_native_fidelity_or_live_body_interop":"UNTESTED"}
    S.finish(folder,result,protected,private,own_before)
    S.require(not unexpected,"Unexpected retained-case failure; all evidence retained")
    print(json.dumps({"folder":str(folder),"status":result["status"],"cases":results}))
if __name__=="__main__":main()
