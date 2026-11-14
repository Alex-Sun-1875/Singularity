from pathlib import Path
import bpy,sys,json,hashlib
root=Path('F:/workspace/Singularity');sys.path.insert(0,str(root/'tools/model-pipeline'))
from locomotion_refinement import apply_reviewed_locomotion
bpy.ops.wm.open_mainfile(filepath=str(root/'source-art/characters/3d-hairstyles-v3/raphael.blend'))
m=json.loads((root/'source-art/characters/3d-hairstyles-v3/manifest.json').read_text(encoding='utf-8'))
changed=apply_reviewed_locomotion(bpy.data.objects['raphael_Native65'],m,root);assert changed==['walk','walk_staff','run','run_staff'];assert len(bpy.data.actions)==14;assert m['locomotionRevision']=='locomotion-v7';print('APPEARANCE_REEXPORT_MOTION_ADAPTER_VERIFIED',changed)
