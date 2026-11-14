from pathlib import Path
import bpy,math,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data.action=bpy.data.actions.get('idle')
scene=bpy.context.scene; scene.frame_set(1)
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=640; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.world.color=(.15,.15,.15)
def aim(obj,point): obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.5,-4.8,2.3))
camera=bpy.context.object; camera.data.type='ORTHO'; camera.data.ortho_scale=2.35
aim(camera,(0,0,.96)); scene.camera=camera
for pos,energy,size in [((2,-3,4),450,3),((-3,-2,2.5),250,3),((1,2,3),450,2)]:
 bpy.ops.object.light_add(type='AREA',location=pos)
 light=bpy.context.object; light.data.energy=energy; light.data.shape='DISK'; light.data.size=size; aim(light,(0,0,1))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02))
floor=bpy.context.object; mat=bpy.data.materials.new('StudioGround'); mat.diffuse_color=(.1,.12,.11,1); floor.data.materials.append(mat)
output=ROOT/'src/screenshots/raphael-local.png'; output.parent.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
print('[CharacterRender]',output)
