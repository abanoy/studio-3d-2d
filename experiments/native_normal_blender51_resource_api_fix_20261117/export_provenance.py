"""Hash-only public reference classifier; does not decode original parameters or guess options."""

PINS = {'blend': 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6',
        'glb': '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d',
        'parameters': 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'}
SIZES = {'blend': 2423175, 'glb': 2322644, 'parameters': 159684}


def classify_public_reference(metadata):
    if type(metadata) is not dict or metadata.get('format') != 'has_source_normal_followup_hash_only_inputs_1':
        raise ValueError('Known public reference metadata required')
    records = metadata.get('files')
    if type(records) is not dict: raise ValueError('Known public file records required')
    for role, digest in PINS.items():
        record = records.get(role)
        if type(record) is not dict or record.get('sha256') != digest or type(record.get('bytes')) is not int or record['bytes'] != SIZES[role]:
            raise ValueError('Original B reference identity differs')
    # This known retained public document records identities, not the historical
    # exporter invocation. Even a newly inserted branch label cannot establish it.
    return {'format': 'has_original_B_export_provenance_survey_1',
            'original_B_hash_references_match': True, 'export_branch': 'UNKNOWN',
            'reason': 'Allowlisted hash-only metadata does not bind an original export invocation/options record',
            'unqualified_explicit_branch_label_present': 'original_export_invocation' in metadata,
            'plain_branch_assumed': False, 'bone_collector_branch_assumed': False,
            'parameters_body_decoded': False, 'native_profile_or_export_equivalence_qualified': False}
