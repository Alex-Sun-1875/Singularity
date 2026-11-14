"""Offline Blender render of the real mesh/action; no browser access needed."""
from pathlib import Path
import bpy,math,json,sys,hashlib
from mathutils import Vector
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'preview';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None
with bpy.data.libraries.load(str(BASE.parent/'3d-locomotion-v9/raphael.blend'))as(src,dst):dst.actions=['run']
old=dst.actions[0];old.name='PREVIEW_PREVIOUS_RUN';current=bpy.data.actions['run']
meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
for o in list(bpy.data.objects):
 if o not in meshes and o!=rig:bpy.data.objects.remove(o,do_unlink=True)
for o in meshes:
 o.hide_render=o.get('nativePart')=='hair'and o.get('hairstyleId')!='curly'
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=384;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=16
scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('PreviewWorld');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.18,.21,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
stage=bpy.data.objects.new('PreviewStage',None);scene.collection.objects.link(stage)
members=set(meshes+[rig])
for o in members:
 if o.parent not in members:
  matrix=o.matrix_world.copy();o.parent=stage;o.matrix_world=matrix
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=1
 return m
floor=material('PreviewFloor',(.12,.16,.14));grid=material('PreviewGrid',(.19,.24,.20))
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.008));bpy.context.object.data.materials.append(floor)
m=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));nominal=m['libraryMotion']['clips']['run']['nominalSpeedMetresPerSecond'];rate=5.2/nominal;spacing=nominal*(20/30)/5
for axis in [0,1]:
 for i in range(-29,30):
  p=[0,0,-.006];p[axis]=i*spacing;bpy.ops.mesh.primitive_plane_add(size=1,location=p)
  o=bpy.context.object;o.scale=(.007,30,1)if axis==0 else(30,.007,1);o.data.materials.append(grid)
for name,pos,power,size in [('Key',(-3,-4,6),1100,4),('Fill',(4,2,4),850,5),('Rim',(-2,4,4),800,3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();o.parent=stage
data=bpy.data.cameras.new('PreviewCamera');data.type='ORTHO';data.ortho_scale=2.4
camera=bpy.data.objects.new('PreviewCamera',data);scene.collection.objects.link(camera);scene.camera=camera
def sample(a,f):
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update()
pilot='--pilot'in sys.argv;frames=[0,5,10,15]if pilot else list(range(20))
signature=hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest();record=OUT/'render-source.json'
same=record.exists()and json.loads(record.read_text())['glbSHA256']==signature
for angle,pos in [('back',Vector((0,5,3.55))),('side',Vector((5,0,3.55)))]:
 for label,action in [('before',old),('after',current)]:
  for f in frames:
   target=OUT/f'{label}-{angle}-{f:02d}.png'
   if same and target.exists():continue
   sample(action,f);distance=5.2*f/(30*rate);stage.location=(0,-distance,0)
   camera.location=pos+stage.location;camera.rotation_euler=(Vector((0,-distance,.95))-camera.location).to_track_quat('-Z','Y').to_euler()
   bpy.context.view_layer.update();scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)
  print('OFFLINE_PREVIEW',label,angle,len(frames),flush=True)
record.write_text(json.dumps({'glbSHA256':signature,'renderer':'Blender 4.5.15 EEVEE offline source-action review, not a Cocos screenshot','gameRunSpeed':5.2,'rate':rate,'nativeFramesPerCycle':20,'cycleMilliseconds':20/30/rate*1000,'gridSpacingMetres':spacing,'browserUsed':False},indent=2)+'\n')
