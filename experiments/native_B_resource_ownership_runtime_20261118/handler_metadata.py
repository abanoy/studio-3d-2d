"""Pure bounded factory-handler metadata; never calls a callback or opens a path."""
import hashlib
import json
import types

HANDLERS = ('load_pre', 'load_post', 'load_post_fail', 'depsgraph_update_pre', 'depsgraph_update_post',
            'frame_change_pre', 'frame_change_post', 'render_pre', 'render_post', 'save_pre', 'save_post')

def need(ok, message):
    if not ok: raise ValueError(message)

def capture_handlers(handlers):
    rows = []; counts = {}; text_bytes = 0
    def text(value):
        nonlocal text_bytes
        if value is None: return None
        need(type(value) is str, 'Handler metadata must be text')
        size = len(value.encode('utf-8')); text_bytes += size
        need(size <= 4096 and text_bytes <= 65536 and '\0' not in value, 'Handler metadata text bound')
        return value
    for name in HANDLERS:
        values = getattr(handlers, name)
        need(type(values) in (list, tuple) and len(values) <= 64, 'Factory handler-list bound/type')
        counts[name] = len(values)
        for index, callback in enumerate(tuple(values)):
            need(len(rows) < 256, 'Factory total handler bound')
            target = callback.__func__ if type(callback) is types.MethodType else callback
            kind = 'UNSUPPORTED_CALLBACK_TYPE_METADATA_UNOBSERVED'
            module = qualname = callback_name = code = None
            if type(target) is types.FunctionType:
                kind = 'BOUND_PYTHON_METHOD' if type(callback) is types.MethodType else 'PYTHON_FUNCTION'
                module = target.__module__ if type(target.__module__) is str else None
                callback_name = target.__name__; qualname = target.__qualname__; code = target.__code__
            elif type(target) is types.BuiltinFunctionType:
                kind = 'BUILTIN_NO_PYTHON_CODE'
                module = target.__module__ if type(target.__module__) is str else None
                callback_name = target.__name__; qualname = target.__qualname__
            # Unknown callable objects are not introspected through custom getters.
            need(code is None or type(code) is types.CodeType, 'Exact Python code type required')
            bytecode = code.co_code if code is not None else None
            need(bytecode is None or type(bytecode) is bytes and len(bytecode) <= 1048576, 'Bytecode metadata bound')
            rows.append({'handler_list': name, 'index': index, 'kind': kind,
                         'name': text(callback_name), 'module': text(module), 'qualname': text(qualname),
                         'code_filename': text(code.co_filename) if code is not None else None,
                         'first_line': code.co_firstlineno if code is not None else None,
                         'bytecode_sha256': hashlib.sha256(bytecode).hexdigest() if bytecode is not None else None})
    private = {'format': 'has_private_Blender_factory_handler_metadata_1',
               'phase': 'FACTORY_BEFORE_KNOWN_B_OPEN', 'handler_list_counts': counts, 'callbacks': rows,
               'callbacks_called': False, 'code_paths_opened': False, 'known_B_opened': False,
               'resource_collector_invoked': False, 'resource_or_native_PASS': False}
    raw = (json.dumps(private, indent=2, allow_nan=False) + '\n').encode('utf-8')
    need(len(raw) <= 524288, 'Factory metadata JSON bound')
    summary = {'format': 'has_Blender_factory_handler_capture_summary_1',
               'status': 'FACTORY_HANDLER_METADATA_CAPTURED_BEFORE_B_OPEN', 'handler_lists': len(HANDLERS),
               'callbacks': len(rows), 'private_metadata_bytes': len(raw),
               'private_metadata_sha256': hashlib.sha256(raw).hexdigest(),
               'callbacks_called': False, 'known_B_opened': False, 'resource_or_native_PASS': False}
    return raw, summary
