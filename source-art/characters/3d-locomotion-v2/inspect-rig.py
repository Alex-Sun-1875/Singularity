from pathlib import Path
import bpy,json
bpy.ops.wm.open_mainfile(filepath='F:/workspace/Singularity/source-art/characters/3d-hairstyles-v3/raphael.blend')
r=bpy.data.objects['raphael_Native65'];s=bpy.context.scene
out={'meshes':[(o.name,o.get('nativePart'))for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')],'actions':[(a.name,list(a.frame_range))for a in bpy.data.actions],'poses':{}}
for name in ['idle','walk','walk_staff']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out['poses'][name]={}
 for f in [0,5,10,20]:
  s.frame_set(f);bpy.context.view_layer.update()
  out['poses'][name][f]={p.name:{'q':list(p.rotation_quaternion),'loc':list(p.location),'head':list(r.matrix_world@p.head),'tail':list(r.matrix_world@p.tail)}for p in r.pose.bones if any(x in p.name.lower()for x in ['arm','spine','clav','neck','pelvis','head','root','hand'])}
Path('F:/workspace/Singularity/source-art/characters/3d-locomotion-v2/rig-inspect.json').write_text(json.dumps(out,indent=2))
print('INSPECTED',list(out['poses']))
