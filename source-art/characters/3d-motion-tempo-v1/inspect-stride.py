"""Measure the accepted native pose's actual foot travel, without editing it."""
from pathlib import Path
import bpy,json,math
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-weapon-contact-v2/authored-bow.blend'))
rig=bpy.data.objects['raphael_Native65'];report={}
for name in ['walk','run']:
    action=bpy.data.actions[name];rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    frames=[]
    for frame in range(int(action.frame_range[1])+1):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        frames.append({'frame':frame,**{bone:list((rig.matrix_world@rig.pose.bones[bone].matrix).translation)for bone in ['foot_l','foot_r']}})
    velocities=[]
    for bone in ['foot_l','foot_r']:
        floor=min(row[bone][2]for row in frames)
        for a,b in zip(frames,frames[1:]):
            if max(a[bone][2],b[bone][2])<floor+.055:
                dx=b[bone][0]-a[bone][0];dy=b[bone][1]-a[bone][1]
                velocities.append(math.hypot(dx,dy)*30)
    report[name]={'samples':frames,'plantedFootSpeedsAtOriginalPlayback':velocities,'median':sorted(velocities)[len(velocities)//2]if velocities else None}
(BASE/'stride-measurement.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('MEASURED_STRIDE',json.dumps({k:{'median':v['median'],'min':min(v['plantedFootSpeedsAtOriginalPlayback']),'max':max(v['plantedFootSpeedsAtOriginalPlayback'])}for k,v in report.items()}))
