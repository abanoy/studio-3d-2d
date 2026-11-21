"""Pure AST observer insertion around the pinned importer setter and validate calls."""
import ast,copy

CALLBACK='_HAS_NORMAL_OBSERVER'
def observed_import_function(source):
    module=ast.parse(source);matches=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='import_model']
    if len(matches)!=1:raise ValueError('One pinned import_model function required')
    original=matches[0]
    if original.decorator_list:raise ValueError('Unexpected importer decorators')
    counts={'setter':0,'validate':0}
    class Observe(ast.NodeTransformer):
        def visit_Expr(self,node):
            value=node.value
            if not(isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute) and isinstance(value.func.value,ast.Name) and value.func.value.id=='mesh_data'):return self.generic_visit(node)
            name=value.func.attr
            if name=='normals_split_custom_set_from_vertices':
                if len(value.args)!=1 or value.keywords or ast.dump(value.args[0],include_attributes=False)!=ast.dump(ast.parse("vertices['normal']",mode='eval').body,include_attributes=False):raise ValueError('Pinned normal setter signature changed')
                kind='setter';phases=('before_setter','after_setter')
            elif name=='validate':
                if value.args or value.keywords:raise ValueError('Pinned mesh validate signature changed')
                kind='validate';phases=('before_validate','after_validate')
            else:return self.generic_visit(node)
            counts[kind]+=1
            def hook(phase):
                return ast.copy_location(ast.Expr(value=ast.Call(func=ast.Name(id=CALLBACK,ctx=ast.Load()),args=[ast.Constant(phase),*[ast.Name(id=x,ctx=ast.Load()) for x in ('model','mesh_obj','mesh_data','vertices','vtx_vertices')]],keywords=[])),node)
            return [hook(phases[0]),node,hook(phases[1])]
    changed=Observe().visit(copy.deepcopy(original));ast.fix_missing_locations(changed)
    if counts!={'setter':1,'validate':1}:raise ValueError('Exactly one source setter and validate boundary required')
    class Remove(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id==CALLBACK:return None
            return self.generic_visit(node)
    restored=Remove().visit(copy.deepcopy(changed));ast.fix_missing_locations(restored)
    if ast.dump(restored,include_attributes=False)!=ast.dump(original,include_attributes=False):raise ValueError('Observer inverse does not restore original importer AST')
    return ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),{'setter_sites':1,'validate_sites':1,'observer_calls':4,'original_function_AST_restored':True}

def scalar_stats(values,threshold=2e-5):
    import math
    if any(type(v) not in (int,float) for v in values):raise ValueError('Numeric observations required')
    values=sorted(float(v) for v in values)
    if any(not math.isfinite(v) or v<0 for v in values):raise ValueError('Finite nonnegative observations required')
    return {'count':len(values),'min':min(values) if values else None,'max':max(values) if values else None,'mean':sum(values)/len(values) if values else None,'above_2e_5':sum(v>threshold for v in values)}
