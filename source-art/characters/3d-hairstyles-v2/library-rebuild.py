"""Adapt authored hair meshes with the existing library adapter, no face edits."""
from pathlib import Path
import bpy,sys,json,hashlib,math
import numpy as np
from mathutils import Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import v5_face_hair_adapter as library
SOURCE=BASE.parent/'3d-hairstyles-v1'
SPECS={'curly':('o4saken_curly01',(.205,.225,.255),1.852,.015),'dante':('short03',(.193,.214,.214),1.835,.012),'nero':('short02',(.184,.208,.172),1.830,.010),'vergil':('short04',(.181,.207,.175),1.847,.012)}

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
proof={'nonHairMeshHashes':{o.name:digest(o)for o in objects if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'));manifest['materials']=[m for m in manifest['materials']if 'hair'not in m.get('parts',[])];assets={};textures=BASE/'textures';textures.mkdir(exist_ok=True)
for style,(asset,size,top,centerY)in SPECS.items():
 meta=library._asset(asset);assets[style]=meta;hair=library._import_hair(meta);library._fit(hair,size,(0,centerY,0),top)
 if style=='curly':
  pipeline.select([hair]);dec=hair.modifiers.new('Retain authored curl flow within runtime budget','DECIMATE');dec.ratio=min(1,64000/max(1,pipeline.triangles(hair)));dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
 # Retain the artist's UVs and actual hair alpha, only adapt silver pigment.
 image=bpy.data.images.load(str(ROOT/meta['texture']),check_existing=False);w,h=image.size;a=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(a);a=a.reshape(h,w,4);luma=a[:,:,:3]@[.2126,.7152,.0722];mask=a[:,:,3]>.5
 low,high=np.percentile(luma[mask],[8,97]);tone=np.clip((luma-low)/max(.02,high-low),0,1);tone=.18+.53*tone**.72
 rgb=np.stack([tone*1.025,tone,tone*.975],axis=2);a[:,:,:3]=rgb
 silver=bpy.data.images.new('Silver_'+style,width=w,height=h,alpha=True);silver.pixels.foreach_set(a.ravel());silver.filepath_raw=str(textures/('library-'+style+'-color.png'));silver.file_format='PNG';silver.save()
 mat=bpy.data.materials.new('Hair_Library_'+style.title()+'_v2');mat.use_nodes=True;tree=mat.node_tree;bs=tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.68;bs.inputs['Metallic'].default_value=0;uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
 tex=tree.nodes.new('ShaderNodeTexImage');tex.image=silver;tree.links.new(uv.outputs[0],tex.inputs['Vector']);tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);maps={'albedo':'../hairstyles-v2/textures/library-'+style+'-color.png'}
 if meta['alpha']:tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
 if meta.get('normal')and'objnorm'not in meta['normal'].lower():
  import shutil
  name='library-'+style+'-normal.png';shutil.copy2(ROOT/meta['normal'],textures/name);node=tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(textures/name),check_existing=False);node.image.colorspace_settings.name='Non-Color';tree.links.new(uv.outputs[0],node.inputs['Vector']);normal=tree.nodes.new('ShaderNodeNormalMap');normal.uv_map='UVMap';normal.inputs['Strength'].default_value=.6;tree.links.new(node.outputs['Color'],normal.inputs['Color']);tree.links.new(normal.outputs[0],bs.inputs['Normal']);maps['normal']='../hairstyles-v2/textures/'+name
 for name in [l.name for l in hair.data.uv_layers][1:]:hair.data.uv_layers.remove(hair.data.uv_layers[name])
 hair.data.uv_layers[0].name='UVMap';hair.data.materials.clear();hair.data.materials.append(mat)
 for p in hair.data.polygons:p.material_index=0;p.use_smooth=True
 for oldName in next(s for s in manifest['hairstyles']if s['id']==style)['nodes']:
  old=bpy.data.objects.get(oldName)
  if old:bpy.data.objects.remove(old,do_unlink=True)
 hair.name='raphael_native_hair_'+style.title()+'_Authored';hair['nativePart']='hair';hair['hairstyleId']=style;hair.parent=rig;hair.matrix_parent_inverse=Matrix.Identity(4);hair.matrix_basis=Matrix.Identity(4);hair.vertex_groups.clear();group=hair.vertex_groups.new(name='Head');group.add(range(len(hair.data.vertices)),1,'REPLACE');hair.modifiers.clear();mod=hair.modifiers.new('Original native Head binding','ARMATURE');mod.object=rig
 for s in manifest['hairstyles']:
  if s['id']==style:s['nodes']=[hair.name];s['triangles']=pipeline.triangles(hair)
 manifest['materials'].append({'runtimeName':mat.name,'parts':['hair'],'maps':maps,'sourcePBR':{'effectiveFactors':{'roughness':.68,'metallic':0}},'alphaClip':meta['alpha'],'doubleSided':True,'alphaThreshold':.15})
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(objects)==16 and {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
manifest['parts']['hair']['nodes']=[n for s in manifest['hairstyles']for n in s['nodes']];manifest.update(appearanceRevision='hairstyles-v2-authored',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),appearanceReview=(BASE/'README.md').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');(BASE/'library-sources.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');proof.update(faceBodyUnchanged=True,all14ActionsUnchanged=True,source='Authored library assets, UVs and hair alpha retained; source meshes fitted, silver pigment adapted');(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('AUTHORED_HAIR_EXPORTED',manifest['triangles'],flush=True)
