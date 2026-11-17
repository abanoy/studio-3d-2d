"""Pure exact one-line import-path successor and raw inverse; no native IO."""
import hashlib
BASE_HOST_SHA256 = 'f35fde033beb9cfd0aefd7edcedfca3b16aa778bea88c9273014bbd578a8dfcd'
BEFORE = 'import traceback\nimport diagnostic_support as S\n'
AFTER = 'import traceback\nsys.path.insert(0, str(Path(__file__).resolve().parent))\nimport diagnostic_support as S\n'

def need(ok, message):
    if not ok: raise ValueError(message)

def restore(source):
    need(source.count(AFTER) == 1, 'Exact import-fix inverse fragment required')
    previous = source.replace(AFTER, BEFORE, 1)
    need(hashlib.sha256(previous.encode('utf-8')).hexdigest() == BASE_HOST_SHA256, 'Exact predecessor host inverse required')
    return previous

def derive(source):
    need(hashlib.sha256(source.encode('utf-8')).hexdigest() == BASE_HOST_SHA256 and source.count(BEFORE) == 1,
         'Exact sealed predecessor host required')
    result = source.replace(BEFORE, AFTER, 1)
    need(restore(result) == source, 'Raw host inverse differs')
    return result
