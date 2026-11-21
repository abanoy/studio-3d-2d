"""Schema10 archive admission for retained model variants; no native/engine IO.

The original manifest remains archived. Only a temporary fully validated view
without the new fields is passed to the unchanged legacy membership readers.
"""
import copy
import math
import sys
sys.dont_write_bytecode=True
try: from . import model_variant_plan as V
except ImportError: import model_variant_plan as V

VERSION=10
MARKER='variant_capability'
CONTENT='variant_content_schema_version'
META='model_variants'
FIELD='variant_selection'

class VariantError(ValueError): pass

def need(ok,code):
    if not ok: raise VariantError(code)
def integer(value,low,high):
    need(type(value) in (int,float) and (type(value) is int or math.isfinite(value)) and low<=value<=high and value==int(value),'Variant integer field')
    return int(value)
def actors(document):
    result=[document[key] for key in ('model','scene') if type(document.get(key)) is dict and document[key]]
    world=document.get('world',{})
    if type(world) is dict and 'objects' in world:
        need(type(world['objects']) is list and len(world['objects'])<=64,'Variant actor budget')
        need(all(type(row) is dict for row in world['objects']),'Variant actor entry')
        result.extend(world['objects'])
    return result

def feature_tree(document,depth=0):
    if type(document) is not dict or depth>1:return False
    if document.get('schema_version')==VERSION or MARKER in document or CONTENT in document:return True
    try: rows=actors(document)
    except VariantError: rows=[]
    if any(FIELD in row or type(row.get('metadata')) is dict and META in row['metadata'] for row in rows):return True
    graph=document.get('sequence_graph',{})
    return type(graph) is dict and type(graph.get('assets')) is list and any(
        type(row) is dict and feature_tree(row.get('scene'),depth+1) for row in graph['assets'][:4])

def validate_actor(actor):
    metadata=actor.get('metadata',{})
    present=type(metadata) is dict and META in metadata
    if not present:
        need(FIELD not in actor,'Variant selection without declaration')
        return False
    need(actor.get('kind','model')=='model','Variant model actor required')
    declared=copy.deepcopy(metadata[META])
    try:
        V.fields(declared,('format','asset_sha256','default_skin','skins','groups','surfaces'),'Variant declaration fields')
        need(declared['asset_sha256']==actor.get('sha256'),'Variant asset identity')
        V.bounded(declared['skins'],1,64,'Variant skins')
        declared['default_skin']=integer(declared['default_skin'],0,len(declared['skins'])-1)
        for row in declared['skins']:
            V.fields(row,('id','name'),'Variant skin fields');row['id']=integer(row['id'],0,63)
        V.bounded(declared['groups'],0,32,'Variant groups')
        for group in declared['groups']:
            V.fields(group,('id','name','default','choices'),'Variant group fields')
            group['id']=integer(group['id'],0,31);group['default']=integer(group['default'],0,63)
            V.bounded(group['choices'],1,64,'Variant choices')
            for choice in group['choices']:
                V.fields(choice,('id','name','blank','nodes'),'Variant choice fields')
                choice['id']=integer(choice['id'],0,63)
                V.bounded(choice['nodes'],0,4096,'Variant choice nodes')
                choice['nodes']=[integer(node,0,99999) for node in choice['nodes']]
        V.bounded(declared['surfaces'],1,16384,'Variant surfaces')
        nodes={};highest=0
        for row in declared['surfaces']:
            V.fields(row,('node','surface','materials'),'Variant surface fields')
            row['node']=integer(row['node'],0,99999);row['surface']=integer(row['surface'],0,255)
            V.bounded(row['materials'],len(declared['skins']),len(declared['skins']),'Variant surface skins')
            row['materials']=[integer(material,0,255) for material in row['materials']]
            highest=max(highest,*row['materials'])
            node=nodes.setdefault(row['node'],{})
            need(row['surface'] not in node,'Variant duplicate surface')
            node[row['surface']]=row['materials'][declared['default_skin']]
        inventory=[]
        for node,surfaces in sorted(nodes.items()):
            need(set(surfaces)==set(range(len(surfaces))),'Variant surface gap')
            inventory.append(dict(node=node,parent_mesh=None,surface_materials=[surfaces[i] for i in range(len(surfaces))]))
        clean=V.validate_manifest(declared,dict(format=V.INVENTORY,asset_sha256=actor.get('sha256'),material_count=highest+1,mesh_nodes=inventory))
        if FIELD in actor:
            selected=copy.deepcopy(actor[FIELD]);V.fields(selected,('format','skin','groups'),'Variant selection fields')
            selected['skin']=integer(selected['skin'],0,63)
            need(type(selected['groups']) is dict,'Variant selection groups')
            selected['groups']={key:integer(value,0,63) for key,value in selected['groups'].items()}
            V._selection(selected,clean)
    except V.Refusal as error: raise VariantError(str(error)) from None
    return True

def validation_view(document,require_capability=True,drop_fields=True,depth=0):
    if not feature_tree(document,depth):return copy.deepcopy(document)
    need(type(document) is dict and depth<=1,'Variant project shape')
    version=integer(document.get('schema_version'),1,VERSION)
    result=copy.deepcopy(document);wrapped=version==VERSION
    if wrapped:
        need(result.get(MARKER)==V.FORMAT,'Variant project capability marker')
        result['schema_version']=integer(result.get(CONTENT),3,9)
        del result[MARKER];del result[CONTENT]
    else:need(MARKER not in result and CONTENT not in result,'Unwrapped variant marker')
    required=False
    for actor in actors(result):
        if validate_actor(actor):
            required=True
            if drop_fields:actor['metadata'].pop(META);actor.pop(FIELD,None)
    graph=result.get('sequence_graph',{})
    if type(graph) is dict and 'assets' in graph:
        need(type(graph['assets']) is list and len(graph['assets'])<=4,'Variant sequence budget')
        for row in graph['assets']:
            need(type(row) is dict and type(row.get('scene')) is dict,'Variant sequence scene')
            child_required=feature_tree(row['scene'],depth+1)
            row['scene']=validation_view(row['scene'],require_capability,drop_fields,depth+1)
            required=required or child_required
    if require_capability:need(wrapped==required,'Appearance choices require project schema10')
    return result
