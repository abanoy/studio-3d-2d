"""Pure exact two-literal source-registry successor/inverse; no IO or activation."""
import hashlib
BASE_SHA256 = '624b73844ef7189c8976457c595fff94338352e0348dcb15e6d195689cb8dc5a'
CHANGES = [("SOURCE_COMMIT = '00bf0f916a549f5e858cb39dd91a149071fd5181'", "SOURCE_COMMIT = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'"), ("RESULT_REGISTRY_SHA256 = 'b03dc3bf06baf6044a034d17b0c9a430f2cfb364bac762f399fcc53c6a9013eb'", "RESULT_REGISTRY_SHA256 = '722e2847821f4aad33ec6581765c8308510ecac7443647f894b74b39ee170b2e'")]

def need(value, message):
    if not value: raise ValueError(message)

def restore(source):
    for before, after in reversed(CHANGES):
        need(source.count(after) == 1, 'Exact successor literal required')
        source = source.replace(after, before, 1)
    need(hashlib.sha256(source.encode()).hexdigest() == BASE_SHA256, 'Exact predecessor source inverse required')
    return source

def derive(source):
    need(hashlib.sha256(source.encode()).hexdigest() == BASE_SHA256, 'Exact predecessor source required')
    original = source
    for before, after in CHANGES:
        need(source.count(before) == 1, 'One approved literal required')
        source = source.replace(before, after, 1)
    need(restore(source) == original, 'Raw inverse mismatch')
    return source
