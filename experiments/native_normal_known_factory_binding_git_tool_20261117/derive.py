"""Pure installed-Git link-policy successor; no execution or filesystem IO."""
import hashlib

PARENT_INDEX = '097e93267f9c438358cc6a0519615a20b4d6dcede2473c7480ca9514a3c00891'
PARENT_SOURCE = '7b171aacc66c23a4d48f02f6801abf553b042349f2ffd105f791d9b2dd9b0d00'
OLD = b'reader.identity(S.safe(GIT), single_link=True)'
NEW = b'reader.identity(S.safe(GIT), single_link=False)'


def render(raw):
    if hashlib.sha256(raw).hexdigest() != PARENT_SOURCE or raw.count(OLD) != 2 or NEW in raw:
        raise ValueError('Exact sealed parent and both installed-Git checks required')
    result = raw.replace(OLD, NEW)
    if result.count(NEW) != 2 or result.replace(NEW, OLD) != raw:
        raise ValueError('Whole-source inverse must restore the exact parent')
    compile(result, 'prepare_root.py', 'exec')
    return result
