"""Bounded static Source brush lightmaps baked into portable glTF emission atlases.

No Source shader/proxy execution. HDR lumps, styled lights and displacement
surfaces remain explicit unsupported cases. Original files are never modified.
"""
import json
import math
from pathlib import Path
import struct
from collections import Counter

MAX_LIGHTING=64*1024*1024
MAX_FACES=16384
MAX_ATLAS=2048
MAX_CELL=512
PAD=2

def key(points):
    # Blender stores source vertices at float32 precision, as does pinned SourceIO.
    return tuple(sorted(set(tuple(struct.unpack('<f',struct.pack('<f',float(v)))[0] for v in point) for point in points)))

def face_info(face,lighting_size):
    width=int(face.lightmap_width)+1;height=int(face.lightmap_height)+1;offset=int(face.light_offset)
    styles=[int(x)&255 for x in face.styles]
    if offset<0:return None,'no static light samples'
    if not styles or styles[0]!=0 or any(x!=255 for x in styles[1:]):return None,'styled lightmap'
    if not 1<=width<=1024 or not 1<=height<=1024 or offset%4 or offset+width*height*4>lighting_size:return None,'invalid lightmap bounds'
    mins=tuple(face.lightmap_texture_mins_in_luxels)
    if len(mins)!=2 or any(type(x) is not int or abs(x)>1000000 for x in mins):return None,'invalid lightmap origin'
    return {'width':width,'height':height,'offset':offset,'mins':mins},''

def affine(points,values):
    """Map planar luxel coordinates to existing material UVs, without UV guessing."""
    a=points[0];u=values[0]
    for i in range(1,len(points)-1):
        b=points[i];c=points[i+1];dx=b[0]-a[0];dy=b[1]-a[1];ex=c[0]-a[0];ey=c[1]-a[1];det=dx*ey-dy*ex
        if abs(det)<1e-10:continue
        rows=[]
        for channel in range(2):
            db=values[i][channel]-u[channel];dc=values[i+1][channel]-u[channel]
            p=(db*ey-dc*dy)/det;q=(dx*dc-ex*db)/det;rows.append((p,q,u[channel]-p*a[0]-q*a[1]))
        if any(not math.isfinite(v) for row in rows for v in row):break
        if all(abs(sum(rows[ch][j]*point[j] for j in range(2))+rows[ch][2]-value[ch])<.0001 for point,value in zip(points,values) for ch in range(2)):return rows
    raise ValueError('Nonplanar or ambiguous lightmap/material UV mapping')

def shelves(sizes,width=MAX_ATLAS):
    x=y=height=0;placed=[]
    for w,h in sizes:
        if w+2*PAD>width or h+2*PAD>width:placed.append(None);continue
        if x+w+2*PAD>width:x=0;y+=height;height=0
        if y+h+2*PAD>width:placed.append(None);continue
        placed.append((x+PAD,y+PAD));x+=w+2*PAD;height=max(height,h+2*PAD)
    used=max((p[1]+h+PAD for p,(w,h) in zip(placed,sizes) if p is not None),default=0)
    return placed,1<<(max(1,used)-1).bit_length()

def capture(handler,model_id,obj,cache):
    """Pinned SourceIO decoded-record boundary; retain stable geometry identities."""
    bsp=handler._bsp;tag=id(bsp)
    if tag not in cache:
        lump=bsp.get_lump('LUMP_LIGHTING');blob=lump.lightmap_data.tobytes() if lump is not None else b''
        if len(blob)>MAX_LIGHTING:raise ValueError('Source LDR lighting exceeds64MiB')
        cache[tag]=blob
    lighting=cache[tag]
    if not lighting:raise ValueError('No supported LDR brush lightmap lump; HDR-only lighting is not baked')
    model=bsp.get_lump('LUMP_MODELS').models[model_id]
    if model.face_count>MAX_FACES:raise ValueError('Source brush exceeds bounded lightmap face count')
    vertices=bsp.get_lump('LUMP_VERTICES').vertices;edges=bsp.get_lump('LUMP_EDGES').edges;surf=bsp.get_lump('LUMP_SURFEDGES').surf_edges;faces=bsp.get_lump('LUMP_FACES').faces;tex=bsp.get_lump('LUMP_TEXINFO').texture_info
    index={};skipped=Counter()
    if model.first_face<0 or model.face_count<0 or model.first_face+model.face_count>len(faces):raise ValueError('Invalid source brush face span')
    for face in faces[model.first_face:model.first_face+model.face_count]:
        if face.disp_info_id!=-1:skipped['displacement lightmap']+=1;continue
        if face.first_edge<0 or not 3<=face.edge_count<=8192 or face.first_edge+face.edge_count>len(surf) or not 0<=face.tex_info_id<len(tex):skipped['invalid brush indices']+=1;continue
        used=surf[face.first_edge:face.first_edge+face.edge_count]
        if any(abs(int(edge))>=len(edges) for edge in used):skipped['invalid brush indices']+=1;continue
        ids=[int(edges[abs(int(edge))][1 if int(edge)<0 else 0]) for edge in used]
        if any(v<0 or v>=len(vertices) for v in ids):skipped['invalid brush indices']+=1;continue
        if len(set(ids))<3:continue
        # Keep NumPy's float32 multiplication, matching the pinned mesh decoder.
        identity=key(vertices[ids]*handler.scale)
        if identity in index:index[identity]=None;skipped['duplicate brush face identity']+=1;continue
        info,why=face_info(face,len(lighting))
        if why:index[identity]=None;skipped[why]+=1;continue
        info['vectors']=tuple(tuple(float(v) for v in row) for row in tex[face.tex_info_id].lightmap_vectors)
        if len(info['vectors'])!=2 or any(len(row)!=4 or any(not math.isfinite(v) for v in row) for row in info['vectors']):raise ValueError('Invalid source lightmap projection')
        index[identity]=info
    return {'object':obj,'scale':handler.scale,'lighting':lighting,'faces':index,'skipped':skipped}

def _sample(np,image,x,y,repeat=False):
    h,w=image.shape[:2]
    if repeat:x=x%w;y=y%h
    else:x=np.clip(x,0,w-1);y=np.clip(y,0,h-1)
    x0=np.floor(x).astype(np.int32);y0=np.floor(y).astype(np.int32);fx=(x-x0)[...,None];fy=(y-y0)[...,None]
    x1=(x0+1)%w if repeat else np.minimum(x0+1,w-1);y1=(y0+1)%h if repeat else np.minimum(y0+1,h-1)
    return (image[y0,x0]*(1-fx)+image[y0,x1]*fx)*(1-fy)+(image[y1,x0]*(1-fx)+image[y1,x1]*fx)*fy

def bake(bpy,jobs,budget):
    import numpy as np
    report={'format':'studio_source_lightmaps_1','atlases':0,'faces':0,'decoded_bytes':0,'skipped':{},'objects':[],'materials':[],'downsampled_faces':0};skipped=Counter()
    for job in jobs:
        obj=job['object'];mesh=obj.data;skipped.update(job['skipped']);rows=[];cached={}
        for polygon in mesh.polygons:
            info=job['faces'].get(key([mesh.vertices[v].co for v in polygon.vertices]))
            if not info:continue
            if polygon.material_index>=len(mesh.materials) or not mesh.materials[polygon.material_index]:skipped['missing surface material']+=1;continue
            material=mesh.materials[polygon.material_index];shader=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if not shader or not mesh.uv_layers.active:skipped['unsupported surface shader']+=1;continue
            points=[];uvs=[]
            for loop in polygon.loop_indices:
                p=mesh.vertices[mesh.loops[loop].vertex_index].co/job['scale'];points.append(tuple(sum(p[i]*v[i] for i in range(3))+v[3]-info['mins'][ch] for ch,v in enumerate(info['vectors'])));uvs.append(tuple(mesh.uv_layers.active.data[loop].uv))
            try:projection=affine(points,uvs)
            except ValueError:skipped['nonplanar surface UVs']+=1;continue
            image=None
            links=shader.inputs['Base Color'].links
            if links and links[0].from_node.type=='TEX_IMAGE':image=links[0].from_node.image
            elif links:skipped['unsupported surface color graph']+=1;continue
            iw,ih=image.size if image else (1,1)
            desired_w=math.ceil((max(u[0] for u in uvs)-min(u[0] for u in uvs))*iw);desired_h=math.ceil((max(u[1] for u in uvs)-min(u[1] for u in uvs))*ih)
            w=max(info['width'],min(MAX_CELL,desired_w));h=max(info['height'],min(MAX_CELL,desired_h))
            if max(w,h)>MAX_CELL:skipped['lightmap face resolution exceeds512']+=1;continue
            rows.append({'polygon':polygon.index,'info':info,'points':points,'projection':projection,'material':material,'shader':shader,'image':image,'size':(max(1,w),max(1,h)),'downsampled':max(desired_w,desired_h)>MAX_CELL})
        if not rows:continue
        width=MAX_ATLAS
        while width>=16 and width*width*16>budget-report['decoded_bytes']:width//=2
        if width<16:skipped['decoded texture budget']+=len(rows);continue
        placed,height=shelves([r['size'] for r in rows],width)
        if not any(p is not None for p in placed):skipped['atlas capacity']+=len(rows);continue
        atlas=np.zeros((height,width,4),dtype=np.float32);atlas[:,:,3]=1;accepted=[];peak=1.
        for row,position in zip(rows,placed):
            if position is None:skipped['atlas capacity']+=1;continue
            info=row['info'];w,h=row['size'];x,y=position
            raw=np.frombuffer(job['lighting'],dtype=np.uint8,count=info['width']*info['height']*4,offset=info['offset']).reshape(info['height'],info['width'],4)
            light=(raw[:,:,:3].astype(np.float32)/255.)*np.exp2(raw[:,:,3].view(np.int8).astype(np.float32))[...,None]
            if not np.all(np.isfinite(light)) or light.max()>65504:skipped['light intensity exceeds portable range']+=1;continue
            lx,ly=np.meshgrid((np.arange(w)+.5)*info['width']/w-.5,(1-(np.arange(h)+.5)/h)*info['height']-.5)
            rgb=_sample(np,light,lx,ly)
            image=row['image']
            if image:
                tag=image.as_pointer()
                if tag not in cached:
                    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels);cached[tag]=pixels.reshape(image.size[1],image.size[0],4)
                uv=[a*lx+b*ly+c for a,b,c in row['projection']];base=_sample(np,cached[tag],uv[0]*image.size[0]-.5,uv[1]*image.size[1]-.5,True)[:,:,:3]
            else:base=np.array(row['shader'].inputs['Base Color'].default_value[:3],dtype=np.float32)
            rgb=rgb*base
            if not np.all(np.isfinite(rgb)) or rgb.max()>65504:skipped['baked color exceeds portable range']+=1;continue
            peak=max(peak,float(rgb.max()));atlas[y:y+h,x:x+w,:3]=rgb
            # Duplicate border texels so bilinear filtering cannot borrow another face.
            atlas[y-PAD:y+h+PAD,x-PAD:x+w+PAD]=np.pad(atlas[y:y+h,x:x+w],((PAD,PAD),(PAD,PAD),(0,0)),mode='edge')
            accepted.append((row,position))
            if row['downsampled']:report['downsampled_faces']+=1
        if not accepted:continue
        atlas[:,:,:3]/=peak
        image=bpy.data.images.new('HAS static Source lightmap',width=width,height=height,alpha=True);image.pixels.foreach_set(atlas.ravel());image.pack()
        uv_layer=mesh.uv_layers.get('lightmap') or mesh.uv_layers.new(name='lightmap');materials={}
        for row,(x,y) in accepted:
            original=row['material'];tag=original.as_pointer()
            if tag not in materials:
                material=original.copy();material.name=original.name+' — baked Source light';shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                # Retain the native base color/texture for the Unshaded view.
                if 'Specular IOR Level' in shader.inputs:shader.inputs['Specular IOR Level'].default_value=0
                node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.extension='EXTEND';uv=material.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='lightmap';material.node_tree.links.new(uv.outputs['UV'],node.inputs['Vector']);material.node_tree.links.new(node.outputs['Color'],shader.inputs['Emission Color']);shader.inputs['Emission Strength'].default_value=peak
                mesh.materials.append(material);materials[tag]=len(mesh.materials)-1;report['materials'].append(material.name)
            polygon=mesh.polygons[row['polygon']];polygon.material_index=materials[tag];w,h=row['size'];info=row['info']
            for loop,point in zip(polygon.loop_indices,row['points']):uv_layer.data[loop].uv=((x+(point[0]+.5)*w/info['width'])/width,(y+(1-(point[1]+.5)/info['height'])*h)/height)
        used=width*height*16;report['atlases']+=1;report['faces']+=len(accepted);report['decoded_bytes']+=used;report['objects'].append({'name':obj.name,'faces':len(accepted),'atlas':[width,height],'emission_strength':peak})
    report['skipped']=dict(sorted(skipped.items()));return report

def tag_glb(path,material_names):
    """Tag only freshly emitted materials; keep BIN chunks and asset UVs intact."""
    path=Path(path);blob=path.read_bytes()
    if len(blob)<20 or blob[:4]!=b'glTF' or struct.unpack_from('<II',blob,4)!=(2,len(blob)):raise ValueError('Invalid emitted GLB')
    size,kind=struct.unpack_from('<II',blob,12)
    if kind!=0x4e4f534a or size>8*1024*1024 or 20+size>len(blob):raise ValueError('Invalid emitted GLB metadata')
    doc=json.loads(blob[20:20+size]);names=set(material_names);found=set()
    for material in doc.get('materials',[]):
        if material.get('name') in names:
            material.setdefault('extras',{})['has_static_source_lightmap']='studio_source_lightmaps_1';found.add(material['name'])
    if found!=names:raise ValueError('Cannot identify all emitted baked-lightmap materials')
    text=json.dumps(doc,separators=(',',':'),ensure_ascii=True).encode();text+=b' '*((-len(text))%4);tail=blob[20+size:]
    path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(text)+len(tail),len(text),0x4e4f534a)+text+tail)
