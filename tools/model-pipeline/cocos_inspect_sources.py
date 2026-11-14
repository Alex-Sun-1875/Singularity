from pathlib import Path
import bpy,json
root=Path(__file__).resolve().parents[2]
out=root/'source-art/characters/cocos'
out.mkdir(parents=True,exist_ok=True)
report={}
for name in ['raphael','mira','raider']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'source-art/characters'/f'{name}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    report[name]={'rig':rig.name,'scale':list(rig.scale),'bones':{b.name:[list(b.head_local),list(b.tail_local)] for b in rig.data.bones},'actions':{a.name:list(a.frame_range) for a in bpy.data.actions},'meshes':{o.name:{'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials],'bounds':[[min(v.co[i] for v in o.data.vertices) for i in range(3)],[max(v.co[i] for v in o.data.vertices) for i in range(3)]]} for o in bpy.data.objects if o.type=='MESH'},'images':{im.name:im.filepath for im in bpy.data.images}}
(out/'source-inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['raphael'],indent=2))
