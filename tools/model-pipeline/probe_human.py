from pathlib import Path
import sys,json
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_bootstrap import make_body,ROOT

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
body,rig=make_body()
report={'vertices':len(body.data.vertices),'bones':len(rig.data.bones),
        'bone_names':[b.name for b in rig.data.bones],
        'groups':[g.name for g in body.vertex_groups],
        'dimensions':list(body.dimensions)}
(ROOT/'src/.tmp/human-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('[HumanProbe]',report['vertices'],'vertices',report['bones'],'bones',report['dimensions'])
