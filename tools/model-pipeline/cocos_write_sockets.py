"""Record hand paths and upright idle-grip quaternions from the actual rigs."""
from pathlib import Path
import bpy,json
from bpy_extras.io_utils import axis_conversion
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'source-art/characters/cocos';OUT=ROOT/'src/cocos/assets/resources/actors'
C=axis_conversion(to_forward='Z',to_up='Y').to_4x4();all_sockets={}
for identity in ['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');action=bpy.data.actions['idle'];rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();sockets={}
    for side in ['r','l']:
        name='hand_'+side;bone=rig.data.bones[name];path=[]
        while bone:path.append(bone.name);bone=bone.parent
        matrix=C@rig.matrix_world@rig.pose.bones[name].matrix;q=matrix.to_quaternion().inverted()
        sockets[name]={'path':'/'.join(reversed(path)),'localPosition':[0,.055,0],'uprightIdleRotationXYZW':[q.x,q.y,q.z,q.w],'note':'Use on standalone prop prefab root; keep imported child transforms intact. The +Y-long prop points upright in the idle pose.'}
    all_sockets[identity]=sockets
    manifest_path=OUT/identity/'manifest.json';manifest=json.loads(manifest_path.read_text());manifest['sockets']['grips']=sockets;manifest_path.write_text(json.dumps(manifest,indent=2))
(OUT/'socket-grips.json').write_text(json.dumps(all_sockets,indent=2))
print('[SOCKET_GRIPS]',json.dumps(all_sockets['mira']))
