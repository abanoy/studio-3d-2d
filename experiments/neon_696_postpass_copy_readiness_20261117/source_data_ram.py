"""RAM-only assemblers for existing catalogue/recipe schemas; no IO or activation."""
import hashlib
import re


def need(ok, message):
    if not ok:
        raise ValueError(message)


def archive_entries(Q, listing):
    """Use existing owner archive/name policy; return bounded entries and Git input."""
    need(type(listing) is bytes, 'Raw ls-tree bytes required')
    entries = {}
    for row in listing.split(b'\0'):
        if not row:
            continue
        metadata, path = row.split(b'\t', 1)
        mode, kind, oid = metadata.split()
        name = path.decode('utf-8')
        if not Q.archive_included(name):
            continue
        Q.validate_git_name(name)
        need(mode in (b'100644', b'100755') and kind == b'blob' and name not in entries
             and re.fullmatch(b'[a-f0-9]{40}', oid), 'Exact committed blob entry')
        entries[name] = (mode.decode(), oid.decode())
    need(0 < len(entries) <= 50000 and len({name.casefold() for name in entries}) == len(entries), 'Owner entry/case bounds')
    request = b''.join(oid.encode('ascii') + b'\n' for mode, oid in entries.values())
    return entries, request


def archive_sizes(entries, raw):
    """Call before fetching blob bodies; retain original 128 MiB/512 MiB ceilings."""
    need(type(raw) is bytes, 'Raw batch-check bytes required')
    rows = raw.splitlines(); need(len(rows) == len(entries), 'Size response membership')
    sizes = {}; total = 0
    for (name, (mode, expected)), row in zip(entries.items(), rows):
        oid, kind, count = row.split()
        need(oid.decode('ascii') == expected and kind == b'blob' and count.isdigit(), 'Size response identity')
        size = int(count); total += size
        need(size <= 128 * 1024 * 1024 and total <= 512 * 1024 * 1024, 'Existing archive byte ceilings')
        sizes[name] = size
    return sizes


def owner_catalogue(A, revision, entries, sizes, batch):
    """Assemble exact metadata and RAM blobs from already bounded Git responses."""
    need(type(revision) is str and re.fullmatch('[a-f0-9]{40}', revision), 'Exact actual merged revision')
    need(set(entries) == set(sizes) and type(batch) is bytes, 'Exact bounded blob membership')
    files = {}; blobs = {}; offset = 0
    for name, (mode, expected) in entries.items():
        line_end = batch.index(b'\n', offset)
        oid, kind, count = batch[offset:line_end].split()
        need(oid.decode('ascii') == expected and kind == b'blob' and count.isdigit(), 'Blob header identity')
        size = int(count); start = line_end + 1; end = start + size
        need(type(sizes[name]) is int and size == sizes[name] and 0 <= size <= 128 * 1024 * 1024
             and end < len(batch) and batch[end:end + 1] == b'\n', 'Bounded blob framing')
        body = batch[start:end]
        need(hashlib.sha1(b'blob ' + str(size).encode('ascii') + b'\0' + body).hexdigest() == expected, 'Git blob body/OID join')
        files[name] = {'mode': mode, 'git_oid': expected, 'bytes': size, 'sha256': A.digest(body)}
        blobs[name] = body; offset = end + 1
    need(offset == len(batch) and sum(sizes.values()) <= 512 * 1024 * 1024, 'Exact bounded archive extent')
    return {'format': 'has_neon_owner_committed_archive_catalogue_1', 'revision': revision, 'files': files}, blobs


def merged_recipe(A, revision, tested, working, committed, allow_checkout_eol=False):
    """Produce only the existing four-field recipe, then run its original guard."""
    need(type(allow_checkout_eol) is bool and set(tested) == set(working) and set(tested) <= set(committed), 'Explicit exact source inputs')
    git = {name: committed[name] for name in tested}
    recipe = {name: {'tested_working_sha256': A.digest(raw), 'git_blob_sha256': A.digest(git[name]),
                     'canonical_content_sha256': A.digest(A.canonical(raw, name)),
                     'source_mode': 'exact_Git_and_tested_working_bytes' if raw == git[name]
                         else 'candidate_tested_raw_with_explicit_Git_CRLF_LF_bridge'}
              for name, raw in working.items()}
    proof = A.check_merged_sources(tested, working, git, recipe, revision, allow_checkout_eol)
    return recipe, proof
