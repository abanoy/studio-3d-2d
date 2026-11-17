"""Pure source derivation after Root supplies the actual published commit.

This entry never reads a cache, invokes Git/network, or creates a remote proof.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'experiments/verify_neon_cleanup85_source_checkpoint_remote_20261117.py'
PARENT_SHA = '4fd7af60703026aee2c1fe6e2a57f154e35e640da3cb25e9f0318785ee64ff6d'
TARGET = ROOT / 'experiments/verify_neon_mmd_source_checkpoint_remote_20261117.py'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--commit', required=True)
    parser.add_argument('--cache-prefix', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-f0-9]{40}', args.commit)
    assert args.commit != '265d3030b848b37f01036dd356840269fca9475b'
    assert args.cache_prefix == args.commit[:4] + '-all-remote-batch-'
    original = PARENT.read_bytes(); assert sha(original) == PARENT_SHA
    rules = [
        ('public27-file', 'public113-file', 1),
        ('265d3030b848b37f01036dd356840269fca9475b', args.commit, 1),
        ('output/neon-cleanup85-source-checkpoint-20261117-manifest.json',
         'output/neon-mmd-source-checkpoint-20261117-manifest.json', 1),
        ('experiments/neon_cleanup85_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json',
         'experiments/neon_mmd_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json', 2),
        ('assert len(paths) == len(set(paths)) == 27', 'assert len(paths) == len(set(paths)) == 113', 1),
        ('for start in range(0, 27, 20):', 'for start in range(0, 113, 20):', 1),
        ('output/265d-all-remote-batch-', 'output/' + args.cache_prefix, 1),
        ('4e992d08568e4da3cb8a54fbbcc6e767867bf184dbe4c1cac06ae0553de1bd72',
         'a39af42de3ef8ff5a76bc1c23ce4c6b01cd60d44d9afb599c793351cabf4cb88', 1),
        ('experiments/neon_cleanup85_source_checkpoint_remote_20261117/COMPLETE_READBACK.json',
         'experiments/neon_mmd_source_checkpoint_remote_20261117/COMPLETE_READBACK.json', 1),
    ]
    result = original
    for before, after, count in rules:
        before, after = before.encode(), after.encode()
        assert result.count(before) == count and after not in result
        result = result.replace(before, after)
    inverse = result
    for before, after, count in reversed(rules):
        before, after = before.encode(), after.encode()
        assert inverse.count(after) == count
        inverse = inverse.replace(after, before)
    assert inverse == original
    ast.parse(result)
    with TARGET.open('xb') as stream: stream.write(result)
    report = {'format': 'has_neon_mmd_remote_verifier_literal_source_derivation_1',
              'parent_sha256': PARENT_SHA, 'verifier_sha256': sha(result),
              'Root_supplied_published_commit': args.commit, 'cache_prefix': args.cache_prefix,
              'literal_rules': rules, 'whole_source_inverse_exact': True,
              'Git_blob_byte_base64_fallback_and_EOL_guards_unchanged': True,
              'verifier_executed_or_remote_proof_claimed': False,
              'Git_network_native_private_or_current_run_access': False}
    with (HERE / 'SOURCE_DERIVATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({'verifier_sha256': sha(result), 'literal_rules': len(rules),
                      'literal_occurrences': sum(row[2] for row in rules),
                      'whole_inverse_exact': True, 'verifier_executed': False}))


if __name__ == '__main__': main()
