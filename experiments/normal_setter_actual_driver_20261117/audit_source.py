"""Parse driver and run pure metadata fixtures; never import driver or call a process."""
from pathlib import Path
import ast
from copy import deepcopy
import hashlib
import json
import math
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACKET=ROOT/'experiments/normal_setter_boundary_sentinel_20261117'
source=(HERE/'run_owned.py').read_text(encoding='utf-8')
tree=ast.parse(source)
checks={}


def mark(name,ok):
    assert name not in checks
    checks[name]=bool(ok)
    assert ok,name


def main():
    compile(tree,str(HERE/'run_owned.py'),'exec')
    mark('driver_source_compiles_without_import',True)
    functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
    pure_names={'sha','load','safe','same','scalar_metadata','checked_policy','check_placement'}
    pure=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in pure_names],type_ignores=[])
    environment={'Path':Path,'hashlib':hashlib,'json':json,'math':math}
    exec(compile(ast.fix_missing_locations(pure),'<pure metadata source>','exec'),environment)
    same=environment['same'];scalar=environment['scalar_metadata'];placement=environment['check_placement']
    mark('strict_false_is_not_zero',not same(False,0))
    mark('strict_true_is_not_one',not same(True,1))
    mark('metadata_zero_size_integer_types',same([0,0],[0,0]) and not same([0.0,0.0],[0,0]))
    scalar({'background_isolation_sentinel':{'requested_size_pixels':[0,0],'disabled':True}})
    mark('bounded_scalar_metadata_allowed',True)
    for name,value in [('nested_native_array',{'normals':[[0.,0.,1.]]}),('large_native_array',{'normals':[0.,0.,1.,0.,0.,1.]}),('nonfinite',float('nan'))]:
        rejected=False
        try:scalar(value)
        except AssertionError:rejected=True
        mark('reject_public_'+name,rejected)
    requirements=json.loads((PACKET/'ROOT_ADDITIONAL_REQUIREMENTS.json').read_bytes())
    mark('actual_successor_metadata_policy_pin',hashlib.sha256((PACKET/'ISOLATION_POLICY.json').read_bytes()).hexdigest()=='8dc902af4b7b8970634593e516d75228308112220f000b1cf22ca4914d4062ba')
    # Synthetic temporary files contain no native arrays; the actual policy is read-only.
    with tempfile.TemporaryDirectory(prefix='synthetic_metadata_',dir=HERE) as temporary:
        folder=Path(temporary).resolve()
        assert folder.is_relative_to(HERE.resolve()) and folder.parent==HERE.resolve()
        public=folder/'PUBLIC_SETTER.json';private=folder/'PRIVATE_SETTER.json';sidecar=folder/'PUBLIC_PLACEMENT.json'
        public.write_text('{"format":"SYNTHETIC_METADATA_FIXTURE_ONLY"}\n',encoding='utf-8')
        private.write_bytes(b'SYNTHETIC_PRIVATE_HASH_FIXTURE_ONLY\n')
        digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        lease={'additional_metadata_policy':deepcopy(requirements['metadata_policy'])}
        valid={'format':requirements['sidecar_format'],'public_setter_sha256':digest(public),'private_setter_sha256':digest(private),
            'background_isolation_sentinel':deepcopy(requirements['public_field_required_values']),
            'metadata_policy_sha256':requirements['metadata_policy']['sha256'],'numeric_public_and_private_outputs_unchanged':True}
        marker=requirements['additional_stdout_marker']
        def write_payload(payload):sidecar.write_text(json.dumps(payload)+'\n',encoding='utf-8')
        write_payload(valid)
        result=placement(PACKET,requirements,lease,marker+json.dumps(valid)+'\n',public,private)
        mark('actual_policy_valid_synthetic_sidecar_accepted',result['public_placement_sha256']==digest(sidecar))
        cases=[]
        for name,key,value in [('public_hash','public_setter_sha256','0'*64),('private_hash','private_setter_sha256','0'*64),
                ('policy_hash','metadata_policy_sha256','0'*64),('changed_output','numeric_public_and_private_outputs_unchanged',False),('format','format','other')]:
            changed=deepcopy(valid);changed[key]=value;cases.append((name,changed))
        changed=deepcopy(valid);changed['background_isolation_sentinel']['requested_size_pixels']=[0.,0.];cases.append(('float_dimensions',changed))
        changed=deepcopy(valid);changed['background_isolation_sentinel']['destroyed_in_finally']=False;cases.append(('cleanup_not_confirmed',changed))
        changed=deepcopy(valid);changed['background_isolation_sentinel']['disabled']=1;cases.append(('truthy_nonboolean',changed))
        for name,payload in cases:
            write_payload(payload);rejected=False
            try:placement(PACKET,requirements,lease,marker+json.dumps(payload)+'\n',public,private)
            except (AssertionError,KeyError):rejected=True
            mark('reject_sidecar_'+name,rejected)
        write_payload(valid)
        for name,stdout in [('missing_marker',''),('double_marker',(marker+json.dumps(valid)+'\n')*2),('marker_payload_mismatch',marker+'{}\n')]:
            rejected=False
            try:placement(PACKET,requirements,lease,stdout,public,private)
            except (AssertionError,KeyError):rejected=True
            mark('reject_'+name,rejected)
        changed_lease=deepcopy(lease);changed_lease['additional_metadata_policy']['sha256']='0'*64
        rejected=False
        try:placement(PACKET,requirements,changed_lease,marker+json.dumps(valid)+'\n',public,private)
        except AssertionError:rejected=True
        mark('reject_lease_policy_mismatch',rejected)
        assert folder.resolve().is_relative_to(HERE.resolve())  # checked before automatic cleanup
    mark('original26_role_gate_called_before_and_after',source.count("support.check_lease(lease_path,packet/'setter_probe.py')")==2)
    mark('165_outer_150_inner_timeout_pinned','communicate(timeout=165)' in source and "'--timeout','150'" in source)
    mark('both_runtime_scopes_and_coordinators_checked',all(value in source for value in ['has-acceptance-session-20261111','has-neon-review-20261116-c2d52ff','run_canonical_owned','main_count','neon_count','ProcessId -ne $PID']))
    mark('no_PID_based_termination_command','taskkill' not in source and 'Stop-Process' not in source)
    mark('root_owned_wrapper_reaped_before_after_closure',source.index("capture,stdout=invoke")<source.index("after=closure(folder,'after')"))
    mark('logs_are_private_only',all(name in source for name in ['PRIVATE_CAPTURE_STDOUT.log','PRIVATE_CAPTURE_STDERR.log','PRIVATE_DRIVER_FAILURE.log']))
    mark('private_native_result_never_JSON_parsed','load(private_path)' not in source and 'private_path.read_bytes' not in source)
    mark('normal_fidelity_never_promoted',"'normal_fidelity_pass_claimed':False" in source)
    mark('real_command_authority_format_and_exact_array_checked',"'has_setter_probe_future_root_commands_1'" in source and "commands['capture_command']==expected" in source)
    mark('packet_and_lease_and_head_explicit_root_pins',all(name in source for name in ['--packet-index-sha256','--lease-sha256','--expected-head']))
    value={'format':'has_root_setter_driver_source_audit_1','passed':all(checks.values()),'checks':len(checks),'named_checks':checks,
        'driver_sha256':hashlib.sha256((HERE/'run_owned.py').read_bytes()).hexdigest(),'driver_imported_or_executed':False,
        'engine_or_CIM_or_Git_executed':False,'synthetic_metadata_fixture_only':True,'actual_successor_policy_sha256':'8dc902af4b7b8970634593e516d75228308112220f000b1cf22ca4914d4062ba'}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':value['passed'],'checks':len(checks),'driver_sha256':value['driver_sha256']}))


if __name__=='__main__':main()
