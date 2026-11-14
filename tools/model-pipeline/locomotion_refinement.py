"""Keep reviewed locomotion when the current appearance is re-exported."""
from pathlib import Path
import json,hashlib

def apply_reviewed_locomotion(rig,manifest,root):
 import bpy
 base=Path(root)/'source-art/characters/3d-locomotion-v9'
 source=base/'raphael.blend';proof=json.loads((base/'source-verification.json').read_text(encoding='utf-8'))
 def action_hash(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
 old={n:bpy.data.actions[n]for n in proof['changedClips']}
 # Same Native65 rig and rest matrices; reuse authored actions directly.
 bind=hashlib.sha256(repr([(b.name,b.parent.name if b.parent else None,[tuple(r)for r in b.matrix_local],b.use_deform)for b in rig.data.bones]).encode()).hexdigest()
 assert bind==proof['bindHash'],'Reviewed motion requires the same Native65 bind pose'
 with bpy.data.libraries.load(str(source),link=False)as(src,dst):dst.actions=list(old)
 for name,new in zip(old,dst.actions):
  assert new and action_hash(new)==proof['afterActions'][name]
  old[name].name='REPLACED_'+name;new.name=name;new.use_fake_user=True;bpy.data.actions.remove(old[name])
 revised=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
 for name in old:
  manifest['clips'][name]=revised['clips'][name];manifest['libraryMotion']['clips'][name]=revised['libraryMotion']['clips'][name]
 for key in ['locomotionRevision','locomotionReview']:manifest[key]=revised[key]
 manifest['locomotionSource']=source.relative_to(root).as_posix()
 return list(old)
