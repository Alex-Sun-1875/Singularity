"""Final collar clearance and loose-vertex cleanup on editable Cocos sources.

This reuses the authored actions; it does not regenerate motion or touch legacy
source files. Shoulder bands are identified by connected topology and weights.
"""
from pathlib import Path
import bpy,bmesh,json
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'source-art/characters/cocos';OUT=ROOT/'src/cocos/assets/resources/actors'
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
for identity in IDS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['idle'];bpy.context.scene.frame_set(1)
    modified=0
    for obj in rig.children_recursive:
        if obj.type!='MESH':continue
        if obj.name==identity+'_vest_surface':
            adjacent=[set() for v in obj.data.vertices]
            for edge in obj.data.edges:
                a,b=edge.vertices;adjacent[a].add(b);adjacent[b].add(a)
            seen=set()
            for vertex in obj.data.vertices:
                if vertex.index in seen:continue
                stack=[vertex.index];component=[]
                while stack:
                    index=stack.pop()
                    if index in seen:continue
                    seen.add(index);component.append(index);stack.extend(adjacent[index]-seen)
                groups={obj.vertex_groups[g.group].name for index in component for g in obj.data.vertices[index].groups if g.weight>1e-5}
                if len(component)==180 and groups=={'spine_03'}:
                    for index in component:
                        v=obj.data.vertices[index]
                        if abs(v.co.x)<.105:v.co.x=.105 if v.co.x>0 else -.105;modified+=1
        if not obj.data.shape_keys:
            bm=bmesh.new();bm.from_mesh(obj.data);loose=[v for v in bm.verts if not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            bm.to_mesh(obj.data);bm.free()
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for obj in rig.children_recursive:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/identity/f'{identity}.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='RELATIVE',embed_textures=False)
    manifest_path=OUT/identity/'manifest.json';manifest=json.loads(manifest_path.read_text());manifest['resource']=f'actors/{identity}/{identity}/{identity}';manifest['sourceResource']=f'actors/{identity}/{identity}';manifest['polish']={'collarClearanceVertices':modified,'removedLooseVertices':True};manifest_path.write_text(json.dumps(manifest,indent=2))
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{identity}.blend'),relative_remap=False)
    print('[POLISHED]',identity,modified,'collar vertices',flush=True)
