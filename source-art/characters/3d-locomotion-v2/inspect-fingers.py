import bpy
bpy.ops.wm.open_mainfile(filepath='F:/workspace/Singularity/source-art/characters/3d-hairstyles-v3/raphael.blend')
r=bpy.data.objects['raphael_Native65'];a=bpy.data.actions['walk'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
print('FINGER_BONES',[(p.name,round(p.rotation_quaternion.angle,3))for p in r.pose.bones if any(x in p.name for x in ['index','middle','ring','pinky','thumb'])])
