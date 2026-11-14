"""Share the approved native face, clothes, rig and all 14 actions across hair."""
from pathlib import Path
import bpy,json,hashlib,sys
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
SOURCE=BASE.parent/'3d-2d-hair-v6'

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
proof={'nonHairMeshHashes':{o.name:digest(o)for o in objects if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
originalHair=next(o for o in objects if o.get('nativePart')=='hair');originalCurlyHash=digest(originalHair)
head=next(o for o in objects if o.get('nativePart')=='head');scalp=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
def clearance(hair):
 for v in hair.data.vertices:
  if v.co.z<1.69 or abs(v.co.x)<.055 or v.co.y<-.025:continue
  near,normal,_,distance=scalp.find_nearest(v.co)
  if near is not None and distance<.018 and (v.co-near).dot(normal)<.0015:v.co=near+normal*.0015
 hair.data.update()
# Keep the approved curl flow, crown height and UVs; refine only temple volume.
for v in originalHair.data.vertices:
 side=max(0,min(1,(abs(v.co.x)-.045)/.045));lower=1-max(0,min(1,(v.co.z-1.76)/.09))
 v.co.x*=1-.12*side*lower
 if v.co.y>.075:v.co.y-=.006*side*lower
clearance(originalHair);curlyHash=digest(originalHair)
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
styles=[{'id':'curly','label':'银白卷发','description':'原作造型 · 松卷与蓬松层次','nodes':[originalHair.name],'triangles':pipeline.triangles(originalHair)}]
for name,label,description in [('dante','但丁','中长分帘 · 自然垂落的层次发尾'),('nero','尼禄','短碎剪裁 · 紧凑鬓角与微翘发梢'),('vergil','维吉尔','整齐后梳 · 露额与向后的流线')]:
 definition=json.loads((BASE/name/'manifest.json').read_text(encoding='utf-8'));dataName=definition['hairstyle']['meshData']
 with bpy.data.libraries.load(str(BASE/name/'raphael.blend'),link=False)as(src,dst):dst.meshes=[dataName]
 mesh=dst.meshes[0];assert mesh is not None
 hair=bpy.data.objects.new('raphael_native_hair_'+name.title(),mesh);bpy.context.scene.collection.objects.link(hair);hair['nativePart']='hair';hair['hairstyleId']=name
 hair.parent=rig;hair.matrix_parent_inverse=Matrix.Identity(4);hair.matrix_basis=Matrix.Identity(4);hair.vertex_groups.clear();group=hair.vertex_groups.new(name='Head');group.add(range(len(mesh.vertices)),1,'REPLACE');mod=hair.modifiers.new('Shared native head binding','ARMATURE');mod.object=rig
 clearance(hair)
 manifest['materials'] += [m for m in definition['materials']if 'hair'in m.get('parts',[])]
 styles.append({'id':name,'label':label,'description':description,'nodes':[hair.name],'triangles':pipeline.triangles(hair)})
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(objects)==16 and digest(originalHair)==curlyHash
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']and len(bpy.data.actions)==14
manifest['parts']['hair']['nodes']=[n for s in styles for n in s['nodes']]
manifest.update(hairstyles=styles,defaultHairstyle='curly',appearanceRevision='hairstyles-v1',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),appearanceReview=(BASE/'README.md').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
manifest['hairstyle']={'asset':'Four interchangeable silver hairstyles','default':'curly','source':'Project curly reference and custom DMC5-inspired Dante/Nero/Vergil hair','binding':'Shared original Head bone; one visible hairstyle at a time','generation':'Three hair-only sheets by cloud OpenAI image_gen, rebuilt and projected using the existing Blender pipeline'}
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o!=originalHair
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
proof.update(faceBodyUnchanged=True,originalCurlyDesignRetained=True,curlySidesRefined=True,originalCurlyHairHash=originalCurlyHash,curlyHairHash=curlyHash,all14ActionsUnchanged=True,bindPoseUnchanged=True,styles=styles,renderers=16,triangles=manifest['triangles'])
(BASE/'preservation.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('EXPORTED_FOUR_HAIRSTYLES',manifest['triangles'],flush=True)
