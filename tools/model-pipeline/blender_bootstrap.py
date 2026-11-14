"""Workspace-local MPFB startup for Blender background authoring, no cloud calls."""
from pathlib import Path
import sys
import bpy
import addon_utils

ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/'src/.tools'
sys.path.insert(0,str(TOOLS/'mpfb2-2.0.18/src'))
import mpfb

# MPFB ships as an extension, but a background tool imports it from the pinned
# source package. Keep its per-user extension storage within this workspace.
_extension_path=bpy.utils.extension_path_user
_user_resource=bpy.utils.user_resource
def _local_user_resource(resource_type,*,path='',create=False):
    if resource_type=='CONFIG':
        result=TOOLS/'blender-config'/path
        if create: result.mkdir(parents=True,exist_ok=True)
        return str(result)
    return _user_resource(resource_type,path=path,create=create)
bpy.utils.user_resource=_local_user_resource
def _local_extension_path(package,*,path='',create=False):
    if package=='mpfb':
        result=TOOLS/'mpfb-user'/path
        if create: result.mkdir(parents=True,exist_ok=True)
        return str(result)
    return _extension_path(package,path=path,create=create)
bpy.utils.extension_path_user=_local_extension_path
mpfb.bl_info=mpfb.fake_bl_info
addon_utils.enable('mpfb',default_set=True,persistent=False)
assert mpfb.ClassManager is not None,'MPFB did not initialize'
prefs=bpy.context.preferences.addons['mpfb'].preferences
prefs.mpfb_user_data=str(TOOLS/'mpfb-user')
prefs.mh_auto_user_data=False
from mpfb.services import HumanService,TargetService,LocationService,ExportService,ObjectService

def make_body(name='Raphael',gender=1.0):
    info=TargetService.get_default_macro_info_dict()
    info.update(gender=gender,age=0.5,muscle=0.58,weight=0.48,height=0.52,
                race={'caucasian':0.72,'african':0.16,'asian':0.12})
    body=HumanService.create_human(macro_detail_dict=info)
    body.name=name+'_body'
    rig=HumanService.add_builtin_rig(body,'game_engine')
    rig.name=name+'_rig'
    return body,rig
