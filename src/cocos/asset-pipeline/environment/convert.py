"""Offline Blender 4.5 adapter: retain CC0 source UVs and normals, decimate to fixed budgets.
Outputs resource JSON consumed by EnvironmentAssets; no runtime GLTF dependency.
"""
import bpy,json,pathlib,sys,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];CACHE=ROOT/'temp/environment-source';OUT=ROOT/'assets/resources/environment';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=json.loads((ROOT/'asset-pipeline/environment/sources.json').read_text())['assets']
models={};materials={};stats=[]
ONLY=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if ONLY and (CACHE/'library-unpacked.json').exists():
 old=json.loads((CACHE/'library-unpacked.json').read_text());models=old['models'];materials=old['materials'];stats=json.loads((ROOT/'asset-pipeline/environment/converted-stats.json').read_text());stats=[x for x in stats if x['key'] not in ONLY]
for source in SOURCES:
 key=source['key'];asset=source['asset'];budget=source['budget']
 if ONLY and key not in ONLY:continue
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if key=='tree' and asset=='tree_small_02':
  bpy.ops.wm.open_mainfile(filepath=str(CACHE/asset/(asset+'.blend')))
  exec((ROOT/'asset-pipeline/environment/tree_cards.py').read_text(),globals())
  obj=bpy.data.objects['tree_small_02_LOD1'];scene=bpy.data.scenes.new('ChapterTreeConversion');bpy.context.window.scene=scene;scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT');objects=[o for o in scene.objects if o.type=='MESH' and not any(m and m.name=='tree_small_02_leaves' for m in o.data.materials)];objects.append(tree_cards(scene))
 else:
  bpy.ops.import_scene.gltf(filepath=str(CACHE/asset/(asset+'.gltf')),import_pack_images=False)
  objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 objects.sort(key=lambda o:o.name)
 # A source collection contains alternatives laid out in rows. Preserve alternatives,
 # never place the entire preview grid into a game prop.
 variants=key in ['rocks','fern','grass']
 if key=='grass':objects=sorted(objects,key=lambda o:len(o.data.polygons))[-4:]
 groups=[[o] for o in objects] if variants else [objects]
 raw=json.loads((CACHE/asset/(asset+'.gltf')).read_text())
 rawmat={m.get('name',''):m for m in raw.get('materials',[])}
 for mi,mat in enumerate(raw.get('materials',[])):
  mid=key+'-'+str(mi);pbr=mat.get('pbrMetallicRoughness',{})
  def image_path(tex):
   if not tex:return None
   return raw['images'][raw['textures'][tex['index']]['source']]['uri']
  color=image_path(pbr.get('baseColorTexture'));normal=image_path(mat.get('normalTexture'))
  opacity=None
  for name in json.loads((CACHE/(asset+'-files.json')).read_text()):
   if 'alpha' in name.lower() and (name.lower()=='alpha' or name.lower().replace('_alpha','') in mat.get('name','').lower()):
    candidate=CACHE/asset/'textures'/(name+'-opacity.png')
    if candidate.exists():opacity=str(candidate.relative_to(CACHE/asset))
  materials[mid]={'asset':asset,'sourceMaterial':mat.get('name'), 'colorSource':color,'normalSource':normal,'opacitySource':opacity,'color':'textures/'+mid+'-color','normal':'textures/'+mid+'-normal' if normal else None,'cutout':bool(opacity),'doubleSided':bool(mat.get('doubleSided',False)),'roughness':.82,'metallic':pbr.get('metallicFactor',0),'tint':pbr.get('baseColorFactor',[1,1,1,1])}
 for gi,group in enumerate(groups):
  points=[o.matrix_world@Vector(c) for o in group for c in o.bound_box]
  low=Vector((min(v.x for v in points),min(v.y for v in points),min(v.z for v in points)));high=Vector((max(v.x for v in points),max(v.y for v in points),max(v.z for v in points)))
  origin=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z));dims=high-low
  total=sum(len(o.data.polygons) for o in group);parts={};triangles=0
  for obj in group:
   bpy.context.view_layer.objects.active=obj
   target=max(40,int(budget*(len(obj.data.polygons)/total))) if not variants else max(40,int(budget/len(groups)))
   if key=='tree':
    material_name=' '.join(m.name for m in obj.data.materials if m);target=1800 if 'trunk' in material_name else 10500 if 'leaves' in material_name else 1100
   if len(obj.data.polygons)>target:
    mod=obj.modifiers.new('ChapterOneBudget','DECIMATE');obj.data.calc_loop_triangles();mod.ratio=max(.001,target/len(obj.data.loop_triangles));mod.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
   mesh=obj.data;mesh.calc_loop_triangles();normal_matrix=obj.matrix_world.to_3x3().inverted().transposed();uv=mesh.uv_layers.active
   for tri in mesh.loop_triangles:
    material=obj.material_slots[tri.material_index].material if tri.material_index<len(obj.material_slots) else None
    name=material.name.split('.')[0] if material else ''
    # Blender only suffixes duplicate names; source material underscores stay intact.
    original=next((i for i,m in enumerate(raw.get('materials',[])) if material and (material.name==m.get('name') or material.name.startswith(m.get('name','')+'.'))),0)
    mid=key+'-'+str(original);part=parts.setdefault(mid,{'material':mid,'positions':[],'normals':[],'uvs':[],'indices':[]});triangles+=1
    for loop_i in tri.loops:
     v=obj.matrix_world@mesh.vertices[mesh.loops[loop_i].vertex_index].co-origin;n=normal_matrix@mesh.corner_normals[loop_i].vector;n.normalize();t=uv.data[loop_i].uv if uv else (0,0)
     # Blender Z-up to GLTF/Cocos Y-up, proper rotation (positive determinant).
     part['indices'].append(len(part['positions'])//3);part['positions'] += [round(v.x,5),round(v.z,5),round(-v.y,5)];part['normals'] += [round(n.x,5),round(n.z,5),round(-n.y,5)];part['uvs'] += [round(t[0],6),round(1-t[1],6)]
  modelkey=key+'-'+str(gi) if variants else key
  # Deduplicate UV/normal seams, retaining exact source tangent discontinuities.
  for part in parts.values():
   old=part;vertices={};p=[];n=[];u=[];indices=[]
   for i in range(len(old['positions'])//3):
    v=tuple(old['positions'][i*3:i*3+3]+old['normals'][i*3:i*3+3]+old['uvs'][i*2:i*2+2]);index=vertices.get(v)
    if index is None:index=len(p)//3;vertices[v]=index;p+=list(v[:3]);n+=list(v[3:6]);u+=list(v[6:])
    indices.append(index)
   part.update(positions=p,normals=n,uvs=u,indices=indices)
  coords=[v for part in parts.values() for v in part['positions']];low=[min(coords[axis::3]) for axis in range(3)];high=[max(coords[axis::3]) for axis in range(3)];offset=[(low[0]+high[0])/2,low[1],(low[2]+high[2])/2]
  for part in parts.values():part['positions']=[round(value-offset[i%3],5) for i,value in enumerate(part['positions'])]
  models[modelkey]={'dimensions':[round(high[i]-low[i],5) for i in range(3)],'parts':list(parts.values())}
  stats.append({'key':modelkey,'triangles':triangles,'parts':len(parts),'dimensions':models[modelkey]['dimensions']})
  print(modelkey,triangles,'tris',len(parts),'parts',list(dims),flush=True)
 result={'version':1,'models':models,'materials':materials}
 (CACHE/'library-unpacked.json').write_text(json.dumps(result,separators=(',',':')))
 (ROOT/'asset-pipeline/environment/converted-stats.json').write_text(json.dumps(stats,indent=2))
print('Exported',len(models),'models',flush=True)
