from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from export_blender_character import export_character
root=Path(__file__).resolve().parents[2]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
export_character(rig,root/'src/assets/model/raphael','model/raphael')
