"""Editable v5 weapon sources, native Blender UVs/bakes, candidate-only FBX export.

First authoring: blender -b -t 2 --python this.py -- --author --preview
Later export:   blender -b -t 2 --python this.py -- --preview
--props sword,bow limits work. Existing .blend sources are NEVER re-imported or
re-authored unless --author --force is explicitly supplied. No production writes.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math, sys
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'source-art/characters/redesign-v6/props'
OUT = ROOT/'src/.tmp/character-redesign-v6/props'
NATIVE = ROOT/'src/.tmp/native-production/source/props/native-props.blend'
LIBRARY = ROOT/'src/.tools/research-animation-kaykit/adventurers-free-2.0/KayKit_Adventurers_2.0_FREE/Assets/gltf'
WOOD = ROOT/'source-art/materials/chapter-one-v3/pbr-library/wood_planks_grey'
LEATHER = ROOT/'assets/materials/chapter-one-v3/ui/ui-smoked-leather-albedo-v1.png'
HAMMER = ROOT/'src/.tools/makehuman-community/clothes/culturalibre_war_hammer/warhammer.obj'
EQUIPMENT = {'W01':'sword','W02':'oath-sword','L01':'greatsword','W07':'bow','W08':'wind-bow','L02':'astra-bow','W11':'staff'}
PROFILES = {
 'sword':dict(base='sword',length=1.05,size=512),
 'oath-sword':dict(base='sword',length=1.05,size=512),
 'greatsword':dict(base='greatsword',length=1.30,size=512),
 'bow':dict(base='bow',length=1.40,size=512),
 'wind-bow':dict(base='bow',length=1.40,size=512),
 'astra-bow':dict(base='bow',length=1.40,size=512),
 'arrow':dict(base='arrow',length=.70,size=256),
 'staff':dict(base='staff',length=1.75,size=512),
 'dagger':dict(base='dagger',length=.48,size=256),
 'shield':dict(base='shield',length=.70,size=512),
 'lorn-shield':dict(base='shield_square',length=1.00,size=512),
 'captain-shield':dict(base='shield_square',length=.92,size=512),
 'hammer':dict(base='hammer',length=.92,size=512),
 'map-kit':dict(base='map-kit',length=.58,size=256),
}

def rel(path): return Path(path).relative_to(ROOT).as_posix()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def meshes(): return [o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('v5_prop')]
def activate(objects):
 bpy.ops.object.select_all(action='DESELECT')
 for obj in objects: obj.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
def tris(obj): obj.data.calc_loop_triangles(); return len(obj.data.loop_triangles)
def tag(obj, role): obj['v5_prop']=True;obj['v5_role']=role;return obj

def multiply(nodes,links,color,factor):
 n=nodes.new('ShaderNodeMixRGB');n.blend_type='MULTIPLY';n.inputs[0].default_value=1;n.inputs[2].default_value=(*factor,1);links.new(color,n.inputs[1]);return n.outputs[0]

def source_material(role, variant):
 """Image-backed wood/leather and native physical metal; all are baked in Blender."""
 name='Source_'+variant+'_'+role
 if bpy.data.materials.get(name):return bpy.data.materials[name]
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
 bs=n.get('Principled BSDF');out=n.get('Material Output');coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeMapping');l.new(coord.outputs['Object'],mapping.inputs[0])
 mapping.inputs['Scale'].default_value=(4,4,1.4)
 def tex(path,noncolor=False):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path),check_existing=True)
  if noncolor:t.image.colorspace_settings.name='Non-Color'
  t.projection='BOX';t.projection_blend=.16;l.new(mapping.outputs[0],t.inputs[0]);return t
 metallic=0;rough=.62
 if role=='wood':
  diffuse=tex(WOOD/'wood_planks_grey_diff_1k.png');normal=tex(WOOD/'wood_planks_grey_nor_gl_1k.png',True);r=tex(WOOD/'wood_planks_grey_rough_1k.png',True)
  tint=(.72,.49,.28) if variant not in ['wind-bow','astra-bow'] else ((.65,.63,.48) if variant=='wind-bow' else(.27,.37,.39))
  l.new(multiply(n,l,diffuse.outputs['Color'],tint),bs.inputs['Base Color']);l.new(r.outputs['Color'],bs.inputs['Roughness'])
  # Box projection cannot use a tangent normal from unrelated UVs. Its real scan
  # luminance provides relief; Blender bakes the resulting surface normal to UV0.
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00065;l.new(diffuse.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
 elif role=='leather':
  t=tex(LEATHER);mapping.inputs['Scale'].default_value=(7,7,7)
  tint=(.40,.27,.19) if variant!='oath-sword' else(.55,.12,.10)
  l.new(multiply(n,l,t.outputs['Color'],tint),bs.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.0008;l.new(t.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal']);rough=.72
 elif role in ['steel','brass']:
  metallic=.92 if role=='steel' else .85;rough=.29 if role=='steel' else .36
  bs.inputs['Base Color'].default_value=(*((.48,.54,.59)if role=='steel'else(.43,.255,.085)),1)
  # Native directional grind marks; no invented photograph or random PNG.
  wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z';wave.inputs['Scale'].default_value=180;wave.inputs['Distortion'].default_value=.4;l.new(mapping.outputs[0],wave.inputs[0])
  ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=rough-.06;ramp.inputs['To Max'].default_value=rough+.08;l.new(wave.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Roughness'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.00012;l.new(wave.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
 elif role=='gem':
  bs.inputs['Base Color'].default_value=(*((.34,.028,.015)if variant=='oath-sword'else(.028,.24,.255)),1);rough=.20;metallic=.2
 elif role=='paper':
  bs.inputs['Base Color'].default_value=(.72,.63,.43,1);rough=.84
 elif role=='string':
  bs.inputs['Base Color'].default_value=(.54,.40,.21,1);rough=.9
 bs.inputs['Metallic'].default_value=metallic
 if not bs.inputs['Roughness'].is_linked:bs.inputs['Roughness'].default_value=rough
 return m

def cube(name,loc,scale,role,variant,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Native edge bevel','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(source_material(role,variant));return tag(o,role)

def cylinder(name,loc,radius,depth,role,variant,vertices=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(source_material(role,variant));return tag(o,role)

def cord(name,points,radius,role,variant):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=1;data.resolution_u=2
 s=data.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);activate([o]);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.data.materials.append(source_material(role,variant));return tag(o,role)

def official(base):
 if base=='shield_square':
  bpy.ops.import_scene.gltf(filepath=str(LIBRARY/'shield_square.gltf'));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
  extent=max(v.co.z for v in obj.data.vertices)-min(v.co.z for v in obj.data.vertices);scale=1/extent;obj.data.transform(Matrix.Scale(scale,4))
  return obj
 with bpy.data.libraries.load(str(NATIVE),link=False)as(src,dst):dst.objects=['KayKit_'+base]
 obj=dst.objects[0];bpy.context.collection.objects.link(obj);return obj

def classify(obj,base,variant):
 # Preserve the author's actual wood/metal surface assignment for shields;
 # spatial thresholds would incorrectly paint the raised metal boss as wood.
 palette=None;uv=obj.data.uv_layers.active
 if base in ['shield','shield_square']:
  source_image=next((n.image for m in obj.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image),None)
  if source_image:palette=(list(source_image.pixels),*source_image.size)
 roles=['wood','leather','steel','brass','gem','string','paper'];obj.data.materials.clear()
 for role in roles:obj.data.materials.append(source_material(role,variant))
 verts=obj.data.vertices
 for p in obj.data.polygons:
  v=sum((verts[i].co for i in p.vertices),Vector())/len(p.vertices);x,y,z=v;role='steel'
  if base in ['sword','greatsword','dagger']:
   low=-.15 if base!='dagger'else-.065
   role='leather'if low<z<.075 else'brass'if z<.09 else'steel'
  elif base=='bow':
   # String is the straight, tiny cross-section at the rear x coordinate.
   role='string'if x<-.235 and abs(y)<.012 else'leather'if abs(z)<.105 and x>-.10 else'wood'
  elif base=='arrow':role='steel'if z>.25 else'paper'if z<-.23 else'wood'
  elif base=='staff':
   # Measured source shaft vertices: lower -.5468..-.127, upper .1273..
   # .4417 metres. The original atlas reuses its metal patch along those
   # shafts; assign the actual long wood sections and retain cuff/wrap zones.
   role='wood'if(-.55<z<-.13 or .13<z<.44)else'leather'if abs(z)<.13 else'gem'if z>.77 else'brass'
  elif base in ['shield','shield_square']:
   if palette and uv:
    tex,w,h=palette;t=sum((uv.data[i].uv for i in p.loop_indices),Vector((0,0)))/len(p.loop_indices);offset=(min(h-1,max(0,int(t.y*h)))*w+min(w-1,max(0,int(t.x*w))))*4;r,g,b=tex[offset:offset+3];role='wood'if r>g*1.18 and g>b*1.15 else'steel'
   else:role='wood'if abs(x)<.29 and abs(z)<.29 else'steel'
  elif base=='hammer':role='wood'if z<.43 else'steel'
  p.material_index=roles.index(role)

def hammer():
 bpy.ops.wm.obj_import(filepath=str(HAMMER));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 arr=np.array([tuple(v.co)for v in obj.data.vertices]);center=arr.mean(axis=0);values,basis=np.linalg.eigh(np.cov((arr-center).T))
 # This archived OBJ starts with alternating vertices on the two 24-vertex
 # circular shaft end rings. Their centers supply the actual handle axis and
 # transverse origin; the mass centroid is displaced by the steel head.
 ring_top=arr[:48:2].mean(axis=0);ring_bottom=arr[1:48:2].mean(axis=0);long=ring_top-ring_bottom;long/=np.linalg.norm(long)
 width=basis[:,1]-long*np.dot(basis[:,1],long);width/=np.linalg.norm(width);thin=np.cross(long,width)
 adapted=np.stack([(arr-ring_bottom)@width,(arr-ring_bottom)@thin,(arr-ring_bottom)@long],axis=1)
 adapted*=.92/np.ptp(adapted[:,2]);adapted[:,2]-=adapted[:,2].min()+.20
 for v,p in zip(obj.data.vertices,adapted):v.co=p
 obj.matrix_world=Matrix.Identity(4)
 # The community OBJ contains 256 zero-area triangles. Native cleanup removes
 # them before UV projection; no hand-authored remesher or UV repair solver.
 activate([obj]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=1e-6);bpy.ops.mesh.dissolve_degenerate(threshold=1e-6);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 return obj

def ornaments(name,base):
 original=next((o for o in meshes()if o.get('v5_role')=='base'),None)
 def front_y(x,z):
  hit,p,normal,index=original.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))
  return p.y if hit else min(v.co.y for v in original.data.vertices)
 if base in ['sword','greatsword','dagger']:
  # Tangible cord winding over the author's handle, not a painted color band.
  radius=.037 if base!='dagger'else .019;bottom=-.14 if base!='dagger'else-.06;top=.035
  cord('Grip leather winding',[(radius*math.cos(t),radius*math.sin(t),bottom+(top-bottom)*i/96)for i in range(97)for t in [i/96*math.tau*7]],.0035,'leather',name)
  if name in ['oath-sword','greatsword']:
   for i in range(4 if name=='oath-sword' else 6):
    z=(.26 if name=='oath-sword'else .44)+i*.075;mark=cube('Blade brass inlay',(.0,front_y(0,z)-.002,z),(.011,.003,.039),'brass',name,.001);mark.rotation_euler[1]=.5 if i%2 else-.5
   gem=cube('Guard inset stone',(0,-.043,.11),(.035,.025,.045),'gem',name,.005)
 elif base=='bow':
  # Only the stationary wooden grip receives independent hardware. The authored
  # flexing limbs and string retain their exact Basis/Draw positions.
  for z in [-.09,.09]:cylinder('Grip binding',(.008,0,z),.037,.013,'brass'if name=='astra-bow'else'steel',name)
  if name!='bow':
   hit,p,normal,index=original.ray_cast(Vector((2,0,0)),Vector((-1,0,0)));seal_x=(p.x if hit else .04)+.004
   seal=cylinder('Silver deer seal'if name=='wind-bow'else'Astra star seal',(seal_x,0,0),.037,.008,'steel'if name=='wind-bow'else'brass',name,16);seal.rotation_euler[1]=math.pi/2
   if name=='wind-bow':
    for side in[-1,1]:cord('Deer antler engraving',[(seal_x+.005,0,-.021),(seal_x+.005,side*.012,.002),(seal_x+.005,side*.021,.022)],.0022,'brass',name)
   if name=='astra-bow':
    for i in range(4):
     t=i*math.pi/2;ray=cube('Star ray',(seal_x+.005,math.sin(t)*.055,math.cos(t)*.055),(.008,.009,.045),'brass',name,.001);ray.rotation_euler[0]=-t
 elif base in ['shield','shield_square']:
  if name=='lorn-shield':
   # Visible native plate repairs, rivets and offset brass splice straps.
   for x,z,angle in [(-.17,-.20,-.33),(.17,.19,-.33)]:
    plate=cube('Lorn repair plate',(x,front_y(x,z)-.014,z),(.26,.024,.09),'steel',name,.006);plate.rotation_euler[1]=angle
   for x in [-.21,.21]:
    for z in [-.31,.31]:
     rivet=cylinder('Repair brass rivet',(x,front_y(x,z)-.012,z),.015,.014,'brass',name);rivet.rotation_euler[0]=math.pi/2
  elif name=='captain-shield':
   for x in [-.15,.15]:cube('Captain shield brace',(x,front_y(x,0)-.014,0),(.048,.024,.73),'steel',name,.006)
 elif base=='hammer':
  cord('Hammer leather winding',[(.036*math.cos(t),.036*math.sin(t),-.14+i/80*.25)for i in range(81)for t in[i/80*math.tau*8]],.004,'leather',name)
 elif base=='staff':
  for z in [-.12,.05,.50]:cylinder('Staff brass ferrule',(0,0,z),.036,.025,'brass',name)

def map_kit(name):
 cylinder('Kael map tube',(0,0,0),.046,.48,'leather',name,16)
 for z in[-.25,.25]:cylinder('Tube brass cap',(0,0,z),.052,.035,'brass',name,16)
 cylinder('Visible rolled map',(0,0,.282),.035,.045,'paper',name,16)
 pts=[(.056*math.cos(t),.056*math.sin(t),-.07+i/100*.052)for i in range(101)for t in[i/100*math.tau*6]]
 cord('Coiled measuring line',pts,.003,'string',name)
 cord('Measuring plumb line',[(.056,0,-.018),(.13,0,-.17),(.13,0,-.25)],.0025,'string',name)
 cylinder('Brass measuring plumb',(.13,0,-.26),.017,.044,'brass',name)

def unwrap(objects):
 for obj in objects:
  if obj.data.uv_layers.active:obj.data.uv_layers.active.name='AuthorUV'
  uv=obj.data.uv_layers.new(name='RuntimeUV');obj.data.uv_layers.active=uv;uv.active_render=True
 activate(objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025,area_weight=.6,correct_aspect=True,scale_to_bounds=True)
 bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.018);bpy.ops.object.mode_set(mode='OBJECT')
 for o in objects:o.data.uv_layers.active=o.data.uv_layers['RuntimeUV'];o.data.uv_layers['RuntimeUV'].active_render=True

def author(name,force=False):
 path=SOURCE/(name+'.blend')
 if path.exists()and not force:return
 bpy.ops.wm.read_factory_settings(use_empty=True);cfg=PROFILES[name];base=cfg['base'];evidence=[]
 if base=='map-kit':map_kit(name);evidence.append({'method':'Blender Cylinder and beveled Curve adapters; no matching map tube in downloaded libraries'})
 else:
  obj=hammer()if base=='hammer'else official(base);obj.name='V5_'+name;tag(obj,'base')
  if base=='shield_square':obj.data.transform(Matrix.Scale(cfg['length'],4))
  if base=='sword':
   # Recondition the two large stylized bite marks in the supplied blade.
   # Move their existing edge vertices to the neighboring straight edge;
   # retain the author's bevel/central ridge and use native cleanup below.
   blade=[v for v in obj.data.vertices if .30<v.co.z<.70];edge=max(abs(v.co.x)for v in blade)
   for v in blade:
    if .055<abs(v.co.x)<.075:v.co.x=math.copysign(edge,v.co.x);v.co.y=0
   activate([obj]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=1e-6);bpy.ops.mesh.dissolve_degenerate(threshold=1e-6);bpy.ops.object.mode_set(mode='OBJECT')
  if base in ['sword','greatsword','dagger','hammer']:
   activate([obj]);bevel=obj.modifiers.new('Maintained metal edge bevel','BEVEL');bevel.width=.0016;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(35);bpy.ops.object.modifier_apply(modifier=bevel.name)
  classify(obj,base,name);ornaments(name,base)
  src=HAMMER if base=='hammer'else LIBRARY/'shield_square.gltf'if base=='shield_square'else NATIVE
  evidence.append({'source':rel(src),'sha256':sha(src),'operation':'Original Bow Basis/Draw positions retained; UV-only edits and separate rigid grip accessories'if base=='bow'else'Native axis/grip adaptation, maintained bevel edges and accessory details; hammer zero-area faces cleaned with Blender native operations'})
 objects=meshes()
 for index,obj in enumerate(objects):obj.name=f'V5_{name.replace("-","_")}_{index:02}'
 if base=='bow':
  obj=next(o for o in objects if o.get('v5_role')=='base');obj['v5_original_geometry_sha256']=geometry_digest(obj)
 unwrap(objects)
 if base=='bow':
  bow=next(o for o in objects if o.get('v5_role')=='base');assert bow.data.shape_keys and 'Draw'in bow.data.shape_keys.key_blocks
 bpy.context.scene['v5_name']=name;bpy.context.scene['v5_provenance']=json.dumps(evidence)
 bpy.context.scene['v5_uv']='Blender native Smart UV Project, average island scale and Pack Islands; AuthorUV retained in editable source, final UV0 is RuntimeUV'
 SOURCE.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
 for img in bpy.data.images:
  if img.source=='FILE'and Path(bpy.path.abspath(img.filepath)).is_file():img.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(path));print('[V5_PROP_SOURCE]',name,flush=True)

def image_target(name,size,kind):
 image=bpy.data.images.new('V5_'+name+'_'+kind,width=size,height=size,alpha=False)
 image.colorspace_settings.name='sRGB'if kind=='albedo'else'Non-Color';image.file_format='PNG';return image

def bake(objects,image,kind):
 activate(objects);materials=set(m for o in objects for m in o.data.materials if m);saved=[]
 for m in materials:
  n=m.node_tree.nodes;l=m.node_tree.links;target=n.new('ShaderNodeTexImage');target.name='Runtime bake target';target.image=image;n.active=target
  if kind in ['orm','albedo']:
   out=n.get('Material Output');link=out.inputs['Surface'].links[0];saved.append((m,link.from_socket,out.inputs['Surface']));l.remove(link)
   bs=n.get('Principled BSDF');emission=n.new('ShaderNodeEmission')
   if kind=='orm':
    combine=n.new('ShaderNodeCombineXYZ');combine.inputs[0].default_value=1
    for index,socket in[(1,bs.inputs['Roughness']),(2,bs.inputs['Metallic'])]:
     if socket.is_linked:l.new(socket.links[0].from_socket,combine.inputs[index])
     else:combine.inputs[index].default_value=socket.default_value
    l.new(combine.outputs[0],emission.inputs[0])
   else:
    color=bs.inputs['Base Color']
    if color.is_linked:l.new(color.links[0].from_socket,emission.inputs[0])
    else:emission.inputs[0].default_value=color.default_value
   l.new(emission.outputs[0],out.inputs['Surface'])
 scene=bpy.context.scene;scene.render.bake.use_clear=False;scene.render.bake.margin=8;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
 bpy.ops.object.bake(type='NORMAL'if kind=='normal'else'EMIT',normal_space='TANGENT')
 for m,old,out in saved:m.node_tree.links.new(old,out)
 for m in materials:
  for n in list(m.node_tree.nodes):
   if n.name=='Runtime bake target':m.node_tree.nodes.remove(n)
 path=OUT/'textures'/(name_token(image.name)+'.png');image.filepath_raw=str(path);image.save();return path

def name_token(value):return value.replace('V5_','').replace(' ','-')

def mesh_state(objects):
 result={}
 for o in objects:
  keys=o.data.shape_keys
  result[o.name]={'vertices':len(o.data.vertices),'triangles':tris(o),'uv':[list(v.uv)for v in o.data.uv_layers.active.data],'positions':[list(o.matrix_world@v.co)for v in o.data.vertices],
   'shapes':{k.name:[list(o.matrix_world@v.co)for v in k.data]for k in keys.key_blocks[1:]}if keys else{}}
 return result

def geometry_digest(obj):
 positions=[list(v.co)for v in obj.data.vertices];shapes={k.name:[list(v.co)for v in k.data]for k in obj.data.shape_keys.key_blocks}if obj.data.shape_keys else{}
 return hashlib.sha256(json.dumps([positions,shapes],separators=(',',':')).encode()).hexdigest()

def verify_uv(objects):
 total=zero=0;uvs=[]
 for obj in objects:
  obj.data.calc_loop_triangles();uv=obj.data.uv_layers.active.data
  local_zero=geometric_zero=0
  for triangle in obj.data.loop_triangles:
   a,b,c=[uv[i].uv for i in triangle.loops];area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5;zero+=area<1e-12;local_zero+=area<1e-12;total+=1;uvs.extend([tuple(a),tuple(b),tuple(c)])
   a,b,c=[obj.data.vertices[i].co for i in triangle.vertices];geometric_zero+=(b-a).cross(c-a).length<1e-12
  if local_zero:print('[UV_DIAGNOSTIC]',obj.name,local_zero,'uv-zero',geometric_zero,'geometry-zero',flush=True)
 assert zero==0,(zero,total)
 return {'triangles':total,'zeroAreaUVTriangles':zero,'uniqueUVs':len(set(uvs)),'method':'Native Blender UV operations; export RuntimeUV as UV0'}

def verify_roundtrip(before,after):
 position_error=morph_error=uv_error=0
 for name,original in before.items():
  candidate=next(v for n,v in after.items()if n.rsplit('.',1)[0]==name or n==name)
  assert original['triangles']==candidate['triangles'],name
  assert set(original['shapes'])==set(candidate['shapes']),name
  assert len(original['uv'])==len(candidate['uv']),name
  uv_error=max(uv_error,max(abs(a-b)for p,q in zip(sorted(original['uv']),sorted(candidate['uv']))for a,b in zip(p,q)))
  tree=KDTree(len(candidate['positions']))
  for index,p in enumerate(candidate['positions']):tree.insert(Vector(p),index)
  tree.balance()
  for index,p in enumerate(original['positions']):
   nearest,other,error=tree.find(Vector(p));position_error=max(position_error,error)
   for shape in original['shapes']:
    morph_error=max(morph_error,(Vector(original['shapes'][shape][index])-Vector(candidate['shapes'][shape][other])).length)
 assert position_error<2e-5,position_error
 assert morph_error<2e-5,morph_error
 assert uv_error<2e-5,uv_error
 return {'passed':True,'maxPositionErrorMeters':position_error,'maxMorphPositionErrorMeters':morph_error,'maxUVError':uv_error,'trianglesBefore':sum(x['triangles']for x in before.values()),'trianglesAfter':sum(x['triangles']for x in after.values()),'shapeNamesAfterFBXImport':sorted(set(k for x in after.values()for k in x['shapes']))}

def export(name,preview=False):
 path=SOURCE/(name+'.blend');assert path.exists(),f'Author source first: {path}'
 bpy.ops.wm.open_mainfile(filepath=str(path));objects=meshes();before=mesh_state(objects);uv_check=verify_uv(objects);scene=bpy.context.scene
 for obj in objects:
  if obj.get('v5_original_geometry_sha256'):assert geometry_digest(obj)==obj['v5_original_geometry_sha256'],'Authored bow geometry changed; revalidate dynamic grip/Draw contact before changing the contract'
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=2
 maps={}
 for kind in ['albedo','normal','orm']:
  size=PROFILES[name]['size']if kind=='albedo' else 256
  img=image_target(name,size,kind);p=bake(objects,img,kind);maps[kind]=p
 material=bpy.data.materials.new('V5_'+name.replace('-','_')+'_Atlas');material.use_nodes=True;bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=1;bs.inputs['Metallic'].default_value=1
 for kind,p in maps.items():
  t=material.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(p),check_existing=True)
  if kind!='albedo':t.image.colorspace_settings.name='Non-Color'
  if kind=='albedo':material.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color'])
  elif kind=='normal':
   n=material.node_tree.nodes.new('ShaderNodeNormalMap');material.node_tree.links.new(t.outputs[0],n.inputs[1]);material.node_tree.links.new(n.outputs[0],bs.inputs['Normal'])
  else:
   s=material.node_tree.nodes.new('ShaderNodeSeparateColor');material.node_tree.links.new(t.outputs[0],s.inputs[0]);material.node_tree.links.new(s.outputs[1],bs.inputs['Roughness']);material.node_tree.links.new(s.outputs[2],bs.inputs['Metallic'])
 for obj in objects:
  obj.data.materials.clear();obj.data.materials.append(material)
  for p in obj.data.polygons:p.material_index=0
  for uv in list(obj.data.uv_layers):
   if uv.name!='RuntimeUV':obj.data.uv_layers.remove(uv)
  assert len(obj.data.uv_layers)==1
 folder=OUT/name;folder.mkdir(parents=True,exist_ok=True);fbx=folder/(name+'.fbx');activate(objects)
 bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},axis_forward='Z',axis_up='Y',bake_space_transform=True,add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='RELATIVE',apply_unit_scale=True,mesh_smooth_type='OFF')
 assert mesh_state(objects)==before,'Export preparation mutated base geometry or morph'
 evidence=json.loads(scene['v5_provenance']);record={'id':name,'resource':f'actors/props-native/{name}/{name}/{name}','source':rel(path),'sourceSHA256':sha(path),'fbx':rel(fbx),'exportSHA256':sha(fbx),'license':'Project-authored adaptation of CC0 sources','sources':evidence,'uv':uv_check,'triangles':sum(tris(o)for o in objects),'materials':[{'runtimeName':material.name,'maps':{k:'../props-native/textures/'+p.name for k,p in maps.items()},'sourcePBR':{'effectiveFactors':{'roughness':1,'metallic':1}},'ormChannels':{'occlusion':'R','roughness':'G','metallic':'B'}}],'textures':[{'path':rel(p),'sha256':sha(p),'role':k,'dimensions':list(bpy.data.images.load(str(p),check_existing=True).size)}for k,p in maps.items()],'geometry':{k:{a:v for a,v in value.items()if a not in ['positions','shapes','uv']}for k,value in before.items()},'morph':{'shapeName':'Draw','baseVerticesPreserved':True,'drawPositionsPreserved':True,'originPreserved':True}if PROFILES[name]['base']=='bow'else None}
 # Roundtrip in a separate collection, retaining the real authored scene for preview.
 old=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(fbx));imported=[o for o in bpy.data.objects if o not in old and o.type=='MESH'];after=mesh_state(imported)
 assert sum(x['triangles']for x in before.values())==sum(x['triangles']for x in after.values())
 if record['morph']:assert any('Draw'in x['shapes']for x in after.values()),'Draw lost through FBX'
 record['fbxRoundtrip']=verify_roundtrip(before,after)
 for obj in [o for o in bpy.data.objects if o not in old]:bpy.data.objects.remove(obj,do_unlink=True)
 if preview:render_preview(name,objects)
 print('[V5_PROP_EXPORTED]',name,record['triangles'],'triangles',flush=True);return record

def render_preview(name,objects):
 scene=bpy.context.scene;scene.cycles.samples=24;scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 pts=[o.matrix_world@Vector(v)for o in objects for v in o.bound_box];lo=Vector(tuple(min(p[i]for p in pts)for i in range(3)));hi=Vector(tuple(max(p[i]for p in pts)for i in range(3)));center=(lo+hi)*.5
 if scene.world is None:scene.world=bpy.data.worlds.new('Neutral weapon review')
 scene.world.color=(.20,.20,.20);scene.view_settings.view_transform='AgX'
 bpy.ops.object.camera_add(location=center+Vector((1.6,-3.5,1.15)));camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=max((hi-lo).z,(hi-lo).x)*1.32;scene.camera=camera
 for offset,energy,size in [((-2,-3,4),400,3),((2,1,2),300,2)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(offset));lamp=bpy.context.object;lamp.data.energy=energy;lamp.data.shape='DISK';lamp.data.size=size;lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler()
 scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 if PROFILES[name]['base']=='bow':
  for obj in objects:
   if obj.data.shape_keys:obj.data.shape_keys.key_blocks['Draw'].value=1
  scene.render.filepath=str(OUT/'previews'/(name+'-draw1.png'));bpy.ops.render.render(write_still=True)
  for obj in objects:
   if obj.data.shape_keys:obj.data.shape_keys.key_blocks['Draw'].value=0

def main():
 argv=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[];p=argparse.ArgumentParser();p.add_argument('--author',action='store_true');p.add_argument('--force',action='store_true');p.add_argument('--preview',action='store_true');p.add_argument('--props',default=','.join(PROFILES));args=p.parse_args(argv)
 SOURCE.mkdir(parents=True,exist_ok=True);(OUT/'textures').mkdir(parents=True,exist_ok=True);(OUT/'previews').mkdir(parents=True,exist_ok=True)
 target=OUT/'manifest.json';manifest=json.loads(target.read_text(encoding='utf-8'))if target.exists()else{'version':'v5-redesign-v6','status':'candidate-not-installed','runtimeProfile':'native-kit-v1','equipmentResources':EQUIPMENT,'props':{},'materialProvenance':[{'source':rel(WOOD),'license':'CC0-1.0','provider':'Poly Haven','asset':'wood_planks_grey'},{'source':rel(LEATHER),'license':'Project-owned artwork','method':'Reused leather albedo; Blender bump relief baked to tangent normal'},{'source':'Native Blender Wave Texture','method':'Directional brushed-metal roughness and microscopic relief; no claimed scanned steel'}]}
 manifest.update({'profileResources':{'mira':['dagger','dagger'],'lorn':['sword','lorn-shield'],'captain':['hammer','captain-shield'],'nightqi':['wind-bow','arrow'],'kael':['map-kit'],'evelyn':{'environmentModel':'lantern','sourceAsset':'wooden_lantern_01','sourceManifest':'src/cocos/asset-pipeline/environment/sources.json','license':'CC0-1.0','height':.48,'palmToModelSole':[0,-.445,0],'additionalPointLights':0},'raider':['sword'],'raider-shield':['sword','shield'],'raider-archer':['bow','arrow']},'cocosBinding':{'bowEuler':[90,0,180],'arrowEuler':[0,0,0],'arrowPosition':[0,.35595446825027466,0],'policy':'Keep original dynamic attach_bow_l/attach_arrow_r and animated Draw sampling'},'bake':{'tool':'Blender 4.5.15 LTS native Smart UV Project, Pack Islands and Cycles bake','albedo':'Base Color emitted into sRGB image, including metallic surfaces','normal':'Tangent-space normal from source image relief and native directional metal finishing','orm':'R=1 unoccluded, G=actual roughness, B=actual metallic; linear image','uv0':'Independent packed RuntimeUV; no collapsed source-atlas corners','budget':'Main albedo512, tiny albedo256, all normal/ORM256'},'sourceLicenses':[{'creator':'Kay Lousberg / KayKit','package':'Adventurers Free 2.0','license':'CC0-1.0','officialURL':'https://kaylousberg.itch.io/kaykit-adventurers','file':rel(LIBRARY.parents[1]/'License.txt'),'sha256':sha(LIBRARY.parents[1]/'License.txt')},{'creator':'culturalibre','asset':'culturalibre_war_hammer','license':'CC0 as declared by asset metadata and .mhclo','source':'http://www.makehumancommunity.org/node/2051','assetMetadata':'src/.tools/makehuman-community/packs/equipment01.json','assetLicenseFile':rel(HAMMER.parent/'culturalibre_war_hammer.mhclo'),'objHeaderNote':'OBJ carries generic MakeClothes Unknown/AGPL3 exporter header; archive metadata and asset-specific .mhclo both explicitly identify culturalibre and CC0. Both are retained for provenance.'}]})
 for name in args.props.split(','):
  assert name in PROFILES,name
  if args.author:author(name,args.force)
  manifest['props'][name]=export(name,args.preview);target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('[V5_PROPS_READY]',rel(target),flush=True)

if __name__=='__main__':main()
