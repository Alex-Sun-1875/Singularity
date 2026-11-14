"""Reuse the project's FBX roundtrip inspection; also provide portable GLBs."""
from pathlib import Path
import bpy,json,importlib.util
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
spec=importlib.util.spec_from_file_location('existing_props_pipeline',ROOT/'tools/model-pipeline/cocos_v5_weapon_redesign.py');pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
rows=json.loads((BASE/'designs.json').read_text(encoding='utf-8'));reports=[];(BASE/'glb').mkdir(exist_ok=True)
for row in rows:
    id=row['id'];bpy.ops.wm.open_mainfile(filepath=str(BASE/'sources'/(id+'.blend')))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];before=pipeline.mesh_state(objects)
    previous=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(BASE/'models'/('design-'+id.lower())/('design-'+id.lower()+'.fbx')))
    imported=[o for o in bpy.data.objects if o not in previous and o.type=='MESH'];after=pipeline.mesh_state(imported)
    check=pipeline.verify_roundtrip(before,after)
    for o in list(bpy.data.objects):
        if o not in previous:bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(BASE/'glb'/(id+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_yup=True)
    reports.append({'id':id,**check});(BASE/'geometry-review.json').write_text(json.dumps(reports,indent=2)+'\n')
    print('GEOMETRY_REVIEWED',id,check['trianglesAfter'],check['shapeNamesAfterFBXImport'],flush=True)
