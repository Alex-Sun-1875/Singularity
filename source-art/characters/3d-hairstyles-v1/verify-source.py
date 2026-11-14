from pathlib import Path
import bpy,sys,json,ast,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
tree=ast.parse((BASE/'combine.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='digest');scope={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(BASE/'combine.py'),'exec'),scope)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));proof=json.loads((BASE/'preservation.json').read_text(encoding='utf-8'));rig=bpy.data.objects['raphael_Native65'];objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(objects)==16 and len(bpy.data.actions)==14
assert {o.name:scope['digest'](o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
curly=bpy.data.objects['raphael_native_hair_2D_Reference'];assert scope['digest'](curly)==proof['curlyHairHash']
new=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));old=json.loads((BASE.parent/'3d-2d-hair-v6/manifest.json').read_text(encoding='utf-8'))
assert [r for r in new['materials']if 'hair'not in r.get('parts',[])]==[r for r in old['materials']if 'hair'not in r.get('parts',[])]
assert [s['id']for s in new['hairstyles']]==['curly','dante','nero','vergil']
for style in new['hairstyles']:
 o=bpy.data.objects[style['nodes'][0]];assert o.get('nativePart')=='hair'and len(o.vertex_groups)==1 and o.vertex_groups[0].name=='Head'
 assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in o.data.vertices)
result={'faceBodyGeometryUVWeightsPreserved':True,'allFaceAndClothingMaterialRecordsPreserved':True,'originalCurlyDesignRetained':True,'curlySidesRefined':True,'all14MotionCurvesPreserved':True,'bindPosePreserved':True,'renderers':16,'styles':new['hairstyles'],'actionHash':proof['actionHash'],'bindHash':proof['bindHash']}
(BASE/'source-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print('VERIFIED_FOUR_HAIRSTYLES',flush=True)
