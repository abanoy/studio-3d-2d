"""Pure source/CPU observer construction; no Blender import, file IO or native launcher."""
import ast
import builtins
import copy
from contextlib import contextmanager
import hashlib
import types

EXPORTER_SHA256 = '455a3566d833481b230141b457452b5bf4ff4a1661d4dd6765a568488e0a2769'
CALLBACK = '_HAS_CARRIER_POINT_OBSERVER'
METHODS = ('primitive_creation_shared', 'primitive_creation_not_shared')
ANCHORS = {'primitive_creation_shared': ('dots', 834),
           'primitive_creation_not_shared': ('prim_dots', 917)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _assignment(name):
    return ast.parse("self.blender_idxs = self.%s['vertex_index']" % name).body[0]


def _class_module(node, futures):
    return ast.fix_missing_locations(ast.Module(body=[*copy.deepcopy(futures), node], type_ignores=[]))


def _instrument(source, anchors):
    """Internal generic transform for synthetic tests; production uses fixed pinned wrapper."""
    module = ast.parse(source)
    classes = [node for node in module.body if isinstance(node, ast.ClassDef) and node.name == 'PrimitiveCreator']
    require(len(classes) == 1, 'One complete PrimitiveCreator class required')
    original = classes[0]
    require(not original.bases and not original.keywords and not original.decorator_list, 'Unexpected exporter class construction')
    require(all(isinstance(node, ast.FunctionDef) for node in original.body), 'Class-level evaluation outside profile')
    for method in original.body:
        require(all(isinstance(node, ast.Name) and node.id in ('classmethod', 'staticmethod') for node in method.decorator_list), 'Unexpected method decorator')
        require(all(isinstance(node, ast.Constant) for node in method.args.defaults), 'Evaluated method default outside profile')
        require(not method.args.kw_defaults and method.returns is None and all(arg.annotation is None for arg in [*method.args.posonlyargs, *method.args.args, *method.args.kwonlyargs]), 'Evaluated annotation/default outside profile')
    methods = {name: [node for node in original.body if node.name == name] for name in METHODS}
    require(all(len(value) == 1 for value in methods.values()), 'Exact two exporter methods required')
    changed = copy.deepcopy(original)
    sites = []
    for method in changed.body:
        if method.name not in METHODS:
            continue
        require(not method.decorator_list and not any(isinstance(node, ast.Name) and node.id in ('PrimitiveCreator', '__class__', 'super') for node in ast.walk(method)), 'Observed method class/free-variable profile differs')
        field, line = anchors[method.name]
        candidates = [node for node in ast.walk(method) if isinstance(node, ast.Assign) and _dump(node) == _dump(_assignment(field))]
        require(len(candidates) == 1 and (line is None or candidates[0].lineno == line), 'Pinned point-identity assignment differs')
        anchor = candidates[0]
        branch = 'shared' if field == 'dots' else 'not_shared'
        if branch == 'shared':
            text = CALLBACK + "(self, 'shared', self.blender_idxs, None, None, None)"
        else:
            text = CALLBACK + "(self, 'not_shared', self.blender_idxs, material_idx, indices, len(primitives))"
        hook = ast.copy_location(ast.parse(text).body[0], anchor)
        class Insert(ast.NodeTransformer):
            def visit_Assign(self, node):
                return [node, copy.deepcopy(hook)] if node is anchor else self.generic_visit(node)
        Insert().visit(method)
        sites.append({'method': method.name, 'source_line': anchor.lineno, 'source_identity_field': field + "['vertex_index']"})
    class Remove(ast.NodeTransformer):
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == CALLBACK:
                return None
            return self.generic_visit(node)
    inverse = Remove().visit(copy.deepcopy(changed))
    require(_dump(inverse) == _dump(original), 'Observer inverse changed original complete class AST')
    require(sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == CALLBACK for node in ast.walk(changed)) == 2, 'Exactly two observer calls required')
    futures = [node for node in module.body if isinstance(node, ast.ImportFrom) and node.module == '__future__']
    proof = {'format': 'has_full_class_carrier_observer_AST_1', 'sites': sites,
             'callback_count': 2, 'original_complete_class_AST_restored': True,
             'original_class_AST_sha256': hashlib.sha256(_dump(original).encode()).hexdigest(),
             'observed_class_AST_sha256': hashlib.sha256(_dump(changed).encode()).hexdigest(),
             'callback_reads_carrier_attribute': False, 'installed_disk_patch': False}
    return _class_module(original, futures), _class_module(changed, futures), proof


def instrument_pinned_class(source):
    require(type(source) is str and hashlib.sha256(source.encode('utf-8')).hexdigest() == EXPORTER_SHA256, 'Exact approved exporter source required')
    return _instrument(source, ANCHORS)


def _compiled_class(module_ast, namespace, filename):
    temporary = dict(namespace)
    for name in ('classmethod', 'staticmethod'):
        require(name not in temporary or temporary[name] is getattr(builtins, name), 'Decorator global was replaced')
    exec(compile(module_ast, filename, 'exec', dont_inherit=True), temporary)
    return temporary['PrimitiveCreator']


@contextmanager
def _install(module, callback, source, originals_ast, observed_ast, proof):
    require(isinstance(module, types.ModuleType) and callable(callback), 'Actual module and observer callable required')
    original_class = module.PrimitiveCreator
    require(type(original_class) is type and original_class.__name__ == 'PrimitiveCreator', 'Exact runtime class identity required')
    originals = {name: original_class.__dict__[name] for name in METHODS}
    require(all(isinstance(value, types.FunctionType) and not value.__code__.co_freevars for value in originals.values()), 'Original methods must be plain closed functions')
    filenames = {method.__code__.co_filename for method in originals.values()}
    require(len(filenames) == 1, 'Original method source filenames differ')
    filename = next(iter(filenames))
    require(filename == module.__file__, 'Loaded runtime method source differs from module')
    clean_class = _compiled_class(originals_ast, module.__dict__, filename)
    require(all(originals[name].__code__ == clean_class.__dict__[name].__code__ for name in METHODS), 'Original runtime method bytecode differs from pinned complete-class compile')
    namespace = dict(module.__dict__)
    require(CALLBACK not in namespace, 'Observer global collision')
    namespace[CALLBACK] = callback
    observed_class = _compiled_class(observed_ast, namespace, filename)
    before = dict(original_class.__dict__)
    try:
        for name in METHODS: setattr(original_class, name, observed_class.__dict__[name])
        require(before.keys() == original_class.__dict__.keys() and all(name in METHODS or value is original_class.__dict__[name] for name, value in before.items()), 'An unrelated runtime class field changed')
        yield proof
    finally:
        for name, method in originals.items(): setattr(original_class, name, method)
        require(before.keys() == original_class.__dict__.keys() and all(value is original_class.__dict__[name] for name, value in before.items()), 'Runtime class was not restored exactly')


def install_pinned_observer(module, callback, source):
    original, changed, proof = instrument_pinned_class(source)
    return _install(module, callback, source, original, changed, proof)
