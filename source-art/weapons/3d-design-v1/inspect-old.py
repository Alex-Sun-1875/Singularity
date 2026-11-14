import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
rows=[]
for id in ['sword','bow','staff','greatsword']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(root/'src/cocos/assets/resources/actors/props-native'/id/(id+'.fbx')))
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  points=[o.matrix_world@v.co for v in o.data.vertices]
  row={'id':id,'name':o.name,'min':[min(v[k] for v in points) for k in range(3)],'max':[max(v[k] for v in points) for k in range(3)],'vertices':len(points),'matrix':[list(v)for v in o.matrix_world]}
  if o.data.shape_keys:
   row['shapes']={s.name:{'min':[min((o.matrix_world@v.co)[k]for v in s.data)for k in range(3)],'max':[max((o.matrix_world@v.co)[k]for v in s.data)for k in range(3)]}for s in o.data.shape_keys.key_blocks}
   row['sampleVertices']=[{'base':list(points[i]),'draw':list(o.matrix_world@o.data.shape_keys.key_blocks['Draw'].data[i].co)}for i in range(0,len(points),max(1,len(points)//30))]
  rows.append(row)
(root/'source-art/weapons/3d-design-v1/old-geometry.json').write_text(json.dumps(rows,indent=2))
print('INSPECTED')
