"""Pure scalar projection with an opaque root-private-certificate commitment.

This module performs no file/process/API operation and cannot publish an archive.
Hash syntax is checked here; certificate contents and authority are not checked.
"""
import re

import projection_core as Base
import source_registry as Source


def project(report, *, root_private_validation_certificate_sha256):
    value = root_private_validation_certificate_sha256
    Base.need(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
              'Opaque private validation certificate SHA256 commitment required')
    registry = {
        'expected_result_keys': list(Source.EXPECTED_RESULT_KEYS),
        'expected_core_process_keys': list(Source.EXPECTED_CORE_PROCESS_KEYS),
        'expected_movie_keys': list(Source.EXPECTED_MOVIE_KEYS),
    }
    out = Base.project(report, registry, list(Source.BEHAVIOR_NAMES))
    out['format'] = 'has_successful_full_scalar_projection_private_commitment_source_1'
    out['source_binding'] = {
        'source_commit': Source.SOURCE_COMMIT,
        'result_registry_sha256': Source.RESULT_REGISTRY_SHA256,
        'behavior_source_sha256': Source.BEHAVIOR_SOURCE_SHA256,
    }
    out['root_private_validation_certificate'] = {
        'sha256': value,
        'commitment_only': True,
        'certificate_contents_or_authority_validated_by_projection': False,
        'omitted_private_data_independently_validated_by_public_extract': False,
    }
    out['private_full_validation_and_closed_input_admission_required_before_publication'] = True
    return out


def activate_archive(*unused, **also_unused):
    raise Base.Refusal('Archive unavailable: root private validation, future terminal proof and closed input inventory required')
