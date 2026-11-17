"""Pure exact early factory-capture insertion/inverse; no native IO."""
import hashlib
BASE_HOST_SHA256 = '1b289ed174b0235c30903375f6bbe195b4bad6cfe0b2e507db4bb4dc255e32da'
MARKER = "    for name in ('load_pre', 'load_post', 'load_post_fail', 'depsgraph_update_pre', 'depsgraph_update_post',"
INSERT = "    # Intentional factory metadata capture; old resource guards remain below.\n    from handler_metadata import capture_handlers\n    factory_raw, factory_summary = capture_handlers(bpy.app.handlers)\n    S.need(r.identity(original, single_link=True) == request['original_identity']\n           and r.identity(owned, single_link=True) == request['owned_identity']\n           and S.digest(request_path.read_bytes()) == args.request_sha256, 'Host inputs changed during diagnostic')\n    S.need(S.check_inputs(request['admission_path'], request['admission_sha256'], request['packet_sha256']) == admitted,\n           'Host root/source/tool/original context changed')\n    with (stage / 'PRIVATE_FACTORY_HANDLERS.json').open('xb') as stream: stream.write(factory_raw)\n    print('HAS_B_FACTORY_HANDLERS_CAPTURE ' + json.dumps(factory_summary, sort_keys=True, allow_nan=False))\n    return  # Before handler admission, sentinel, open_mainfile or resource queries.\n"

def need(ok, message):
    if not ok: raise ValueError(message)

def restore(source):
    need(source.count(INSERT + MARKER) == 1, 'Exact capture inverse fragment required')
    old = source.replace(INSERT + MARKER, MARKER, 1)
    need(hashlib.sha256(old.encode()).hexdigest() == BASE_HOST_SHA256, 'Exact predecessor host inverse required')
    return old

def derive(source):
    need(hashlib.sha256(source.encode()).hexdigest() == BASE_HOST_SHA256 and source.count(MARKER) == 1,
         'Exact sealed import-fix host required')
    result = source.replace(MARKER, INSERT + MARKER, 1)
    need(restore(result) == source, 'Capture source inverse differs')
    return result
