from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
rows=[]
for relative in ['source-art/characters/3d-motion-tempo-v1/compact-jog.blend','source-art/characters/cocos/raphael.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/relative));scene=bpy.context.scene
    for rig in [o for o in bpy.data.objects if o.type=='ARMATURE']:
        idle=bpy.data.actions.get('idle')
        if idle:
            rig.animation_data_create();rig.animation_data.action=idle
            if idle.slots:rig.animation_data.action_slot=idle.slots[0]
    scene.frame_set(0);bpy.context.view_layer.update();objects=[]
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        pts=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i]for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)]
        objects.append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'bounds':[lo,hi],'materials':[m.name if m else None for m in o.data.materials],'groups':[g.name for g in o.vertex_groups][:12]})
    rows.append({'source':relative,'objects':objects})
(BASE/'source-inventory.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows))
