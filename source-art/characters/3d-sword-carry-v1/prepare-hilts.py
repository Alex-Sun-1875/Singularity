"""Reuse the installed sword hilts/UVs for sheathed carry; no new textures.
The battle meshes remain untouched. Blender's native plane cut removes only
the blade inside the scabbard in the separate static carry prefab.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent/'hilts';OUT.mkdir(exist_ok=True)
production=ROOT/'src/cocos/assets/resources/actors/props-native'
rows=[]
for name in ['sword','oath-sword','greatsword']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=production/name/(name+'.fbx');bpy.ops.import_scene.fbx(filepath=str(source))
    kept=[];before=0;after=0
    for obj in list(bpy.data.objects):
        if obj.type!='MESH':continue
        before+=len(obj.data.polygons)
        world=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=Matrix.Identity(4);obj.data.transform(world)
        mesh=bmesh.new();mesh.from_mesh(obj.data)
        bmesh.ops.bisect_plane(mesh,geom=list(mesh.verts)+list(mesh.edges)+list(mesh.faces),plane_co=Vector((0,0,.14)),plane_no=Vector((0,0,1)),clear_outer=True,clear_inner=False,dist=1e-6)
        bmesh.ops.recalc_face_normals(mesh,faces=list(mesh.faces));mesh.to_mesh(obj.data);mesh.free();obj.data.update()
        if not obj.data.polygons:bpy.data.objects.remove(obj,do_unlink=True);continue
        kept.append(obj);after+=len(obj.data.polygons)
    folder=OUT/('stowed-'+name);folder.mkdir(exist_ok=True)
    for image in bpy.data.images:
        if image.source=='FILE':image.filepath=str(OUT/'textures'/Path(bpy.path.abspath(image.filepath)).name)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in kept:obj.select_set(True)
    bpy.context.view_layer.objects.active=kept[0]
    target=folder/('stowed-'+name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,path_mode='RELATIVE',colors_type='NONE',embed_textures=False)
    rows.append({'source':str(source.relative_to(ROOT)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':str(target.relative_to(ROOT)),'outputSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'facesBefore':before,'facesAfter':after,'cut':'World Z <= .14 m, built-in bmesh.bisect_plane','UVAndMaterial':'Original runtime atlas and UV layers retained; no generated textures'})
(OUT/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
print('HILTS_READY',json.dumps(rows),flush=True)
