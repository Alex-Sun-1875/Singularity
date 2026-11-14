from pathlib import Path
import bpy,json,hashlib,math
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None
proof=json.loads((BASE/'source-verification.json').read_text(encoding='utf-8'))
def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
assert {a.name:ah(a)for a in bpy.data.actions}==proof['afterActions']
rows=[]
for name in proof['changedClips']:
 a=bpy.data.actions[name];end=a.frame_range[1];max_loop=max(abs(c.evaluate(0)-c.evaluate(end))for c in a.fcurves)
 assert max_loop<1e-5,(name,max_loop)
 scale_error=max(abs(c.evaluate(f)-1)for c in a.fcurves if c.data_path.endswith('.scale')for f in range(int(end)+1))
 assert scale_error<2e-5,(name,scale_error)
 previous={};steps=[];detail=[];thigh_flex={'l':[],'r':[]}
 for i in range(int(end)*2+1):
  f=i*.5
  for c in a.fcurves:
   path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
  bpy.context.view_layer.update()
  for n in ['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']:
   q=rig.pose.bones[n].matrix.to_quaternion()
   if n in previous:
    angle=math.degrees(q.rotation_difference(previous[n]).angle);angle=min(angle,360-angle);steps.append(angle);detail.append((angle,n,f))
   previous[n]=q.copy()
  for side in thigh_flex:
   v=rig.pose.bones['calf_'+side].head-rig.pose.bones['thigh_'+side].head
   thigh_flex[side].append(math.degrees(math.atan2(-v.y,-v.z)))
 print('LEG_STEP',name,sorted(detail,reverse=True)[:4],flush=True)
 assert max(steps)<35,(name,max(steps))
 raised={s:sum(a>70 for a in values[:-1])/len(values[:-1])for s,values in thigh_flex.items()}
 if name in proof['changedThisRevision']:
  assert all(max(a)>86 for a in thigh_flex.values()),(name,thigh_flex)
  assert all(a>.20 for a in raised.values()),(name,raised)
 rows.append({'clip':name,'maxLoopChannelError':max_loop,'maxScaleError':scale_error,'maxHalfFrameLegRotationDegrees':max(steps),'maxForwardThighFlexion':{s:max(v)for s,v in thigh_flex.items()},'cycleFractionThighAbove70':raised})
report={'savedActionsMatch':True,'clips':rows,'unchangedOtherActions':proof['unchangedClips'],'runtimeGLBSHA256':proof['runtimeGLBSHA256']}
(BASE/'saved-source-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('SAVED_SOURCE_VERIFIED',json.dumps(report))
