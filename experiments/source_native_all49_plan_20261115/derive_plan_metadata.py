"""Read pinned parameter metadata only; emit topology/counts, never native arrays."""
from pathlib import Path
from collections import Counter, defaultdict
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685/parameters.json'
REPORT_SHA = 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'
GLB_SHA = '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'
READS = []


def read(path):
    raw = path.read_bytes()
    READS.append({'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    return raw


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def main():
    raw = read(REPORT)
    assert hashlib.sha256(raw).hexdigest() == REPORT_SHA
    report = json.loads(raw)
    native = report['native_parameters']
    bones = native['bones']
    jiggle = native['source_jiggle']
    rules = jiggle['rules']
    by_id = {rule['native_bone_index']: rule for rule in rules}
    selected = set(by_id)
    assert len(bones) == 69 and len(rules) == len(by_id) == 49 and report['scale'] == 0.01905
    assert native['source_export_crosswalk']['glb_sha256'] == GLB_SHA
    assert jiggle['applied'] is False and jiggle['full_native_rule_layout_verified'] is False
    assert jiggle['status'] == 'retained_inert'
    children = defaultdict(list)
    for index, bone in enumerate(bones):
        parent = bone['parent']
        assert type(parent) is int and -1 <= parent < len(bones) and parent != index
        if parent >= 0:
            children[parent].append(index)
        seen = set()
        ancestor = index
        while ancestor >= 0:
            assert ancestor not in seen
            seen.add(ancestor)
            ancestor = bones[ancestor]['parent']
    for index, rule in by_id.items():
        assert rule['native_parent_index'] == bones[index]['parent']
        assert rule['native_bone_name'] == bones[index]['name']
        assert rule['raw_rule_flags'] == 0x31 and rule['unknown_rule_flag_bits'] == 0
        assert set(rule['known_rule_flags']) == {'IS_FLEXIBLE', 'HAS_ANGLE_CONSTRAINT', 'HAS_LENGTH_CONSTRAINT'}
        assert rule['applied'] is False and len(rule['parameters']) == 29
    roots = sorted(index for index in selected if bones[index]['parent'] not in selected)
    branches = []
    covered = set()
    for root in roots:
        chain = []
        index = root
        while True:
            assert index not in covered
            covered.add(index); chain.append(index)
            all_children = children[index]
            assert len(all_children) <= 1 and all(child in selected for child in all_children)
            if not all_children:
                break
            index = all_children[0]
        branches.append({'root_native_index': root, 'authored_parent_native_index': bones[root]['parent'],
                         'rule_count': len(chain), 'native_indices': chain,
                         'names': [bones[index]['name'] for index in chain]})
    assert covered == selected and len(branches) == 26
    distribution = Counter(branch['rule_count'] for branch in branches)
    assert distribution == {1: 13, 2: 5, 3: 6, 4: 2}
    nonrule = sorted(set(range(69)) - selected)
    assert len(nonrule) == 20 and 25 in nonrule
    assert all(not any(ancestor in selected for ancestor in ancestors(index, bones)) for index in nonrule)
    groups = defaultdict(list)
    for index, rule in sorted(by_id.items()):
        p = rule['parameters']
        assert p['yaw_stiffness'] == p['pitch_stiffness']
        groups[(p['yaw_stiffness'], rule['binary_provenance']['prefix_sha256'])].append(index)
    assert sorted(len(group) for group in groups.values()) == [17, 32]
    public_groups = [{'yaw_and_pitch_stiffness': key[0], 'native_prefix_sha256': key[1],
                      'rule_count': len(indices), 'native_indices': indices}
                     for key, indices in sorted(groups.items())]
    pair_profile = json.loads(read(ROOT / 'experiments/source_0x31_chains_20261115/PUBLIC_PROFILE.json'))
    assert pair_profile['bones'] == 69 and pair_profile['rules'] == 49
    assert [(row['native_index'], row['parent']) for row in pair_profile['selected']] == [(17,7),(18,17),(26,25),(27,26)]
    assert pair_profile['influence_counts']['union']['vertices'] == 9661
    for relative in ('experiments/source_0x31_chains_20261115/chain_solver.gd',
                     'experiments/source_0x31_chains_20261115/model_adapter.gd',
                     'experiments/source_0x31_chains_20261115/chain_harness.gd',
                     'experiments/source_0x31_chains_20261115/chain_capture.gd',
                     'experiments/source_0x31_chains_20261115/README.md',
                     'src/source_secondary.gd', 'src/source_jiggle_math.gd',
                     'src/source_bone_bindings.gd', 'src/secondary_live.gd'):
        read(ROOT / relative)
    save('PROFILE_TOPOLOGY.json', {
        'format': 'has_all49_native_qualification_plan_metadata_1',
        'status': 'METADATA_DERIVED_FUTURE_PROBE_NOT_IMPLEMENTED_OR_EXECUTED',
        'parameter_report_sha256': REPORT_SHA, 'glb_sha256_reference_only_not_read': GLB_SHA,
        'bones': 69, 'rules': 49, 'source_scale': 0.01905,
        'retained_source_status': jiggle['status'], 'retained_applied': False,
        'full_native_rule_layout_verified': False,
        'native_layout_scope': 'SourceIO flags plus29-float120-byte prefix; complete SDK/client motion parity is not established.',
        'flag_categories': [{'raw_flags_hex': '0x31', 'rules': 49, 'unknown_flag_bits': 0,
                             'known_flags': ['IS_FLEXIBLE', 'HAS_ANGLE_CONSTRAINT', 'HAS_LENGTH_CONSTRAINT'],
                             'implemented_active_coefficient_fields': 7,
                             'retained_inactive_coefficient_fields': 22,
                             'inactive_along_fields': 2}],
        'coefficient_prefix_groups': public_groups,
        'rule_roots': len(roots), 'branch_rule_length_distribution': {str(k): v for k,v in sorted(distribution.items())},
        'rule_parent_edges': 23, 'rule_leaves': 26, 'maximum_rule_depth': 4,
        'nonrule_bones': 20, 'nonrule_native_indices': nonrule,
        'nonrule_below_any_rule': 0, 'nonrule_between_selected_rule_ancestors': 0,
        'authored_back_hair_intermediates': [25,28,31,34,38,42,46,50,54],
        'authored_hat_ancestors': [58,59,64],
        'branches': branches,
        'bone_topology': [{'native_index': i, 'name': b['name'], 'parent_native_index': b['parent'],
                           'has_retained_rule': i in selected} for i,b in enumerate(bones)],
        'expected_full49_unaffected_world_bones': 20,
        'expected_full49_world_affected_rule_bones': 49,
        'existing_measured_mesh_counts_reference_only': {'vertices': 9661, 'surfaces': 4},
        'all49_weighted_affected_shared_unaffected_counts': 'UNMEASURED_REQUIRES_FUTURE_OWNED_IN_MEMORY_CAPTURE',
        'existing_four_rule_capture_reference': pair_profile['influence_counts']['union'],
        'proposed_full49_tick_budget': {'root_placements': 2, 'profiles_per_placement': 6,
                                       'ticks_per_profile': 120, 'actor_ticks': 1440,
                                       'rule_evaluations': 70560, 'executed': False},
        'native_source_arrays_geometry_coordinates_or_media_published': False,
        'native_glb_mdl_vvd_or_weight_arrays_read_by_this_derivation': False})
    save('SOURCE_READS.json', {'format': 'has_all49_plan_read_provenance_1',
                             'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                             'scope': 'Read-only parameter JSON and existing code/public-profile metadata; no model binary, geometry, runtime or Git.',
                             'files': READS})
    print(json.dumps({'passed': True, 'metadata_read_files': len(READS), 'bones': 69, 'rules': 49,
                      'independent_rule_branches': 26, 'nonrule_bones': 20,
                      'all49_runtime_status': 'NOT_IMPLEMENTED_OR_EXECUTED'}))


def ancestors(index, bones):
    result = []
    parent = bones[index]['parent']
    while parent >= 0:
        result.append(parent)
        parent = bones[parent]['parent']
    return result


if __name__ == '__main__':
    main()
