from pathlib import Path
import bpy,sys,json,hashlib,ast
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
module=ast.parse((BASE/'build.py').read_text(encoding='utf-8'));fn=next(n for n in module.body if isinstance(n,ast.FunctionDef)and n.name=='digest');scope={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(BASE/'build.py'),'exec'),scope)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));proof=json.loads((BASE/'preservation.json').read_text());rig=bpy.data.objects['raphael_Native65'];objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert {o.name:scope['digest'](o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']and len(objects)==13
hair=next(o for o in objects if o.get('nativePart')=='hair');assert hair.name=='raphael_native_hair_2D_Curls'
new=json.loads((BASE/'manifest.json').read_text());old=json.loads((BASE.parent/'3d-native-hair-v4/manifest.json').read_text())
assert [r for r in new['materials']if 'hair'not in r.get('parts',[])]==[r for r in old['materials']if 'hair'not in r.get('parts',[])]
result={'faceBodyGeometryUVWeightsPreserved':True,'allFaceAndClothingMaterialRecordsPreserved':True,'all14MotionCurvesPreserved':True,'bindPosePreserved':True,'renderers':13,'hairSource':'Original reference-shaped guides, Blender bundled CC0 curl/profile assets','triangles':sum(pipeline.triangles(o)for o in objects),'hairTriangles':pipeline.triangles(hair),'actionHash':proof['actionHash'],'bindHash':proof['bindHash']}
(BASE/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print('VERIFIED_2D_CURL_HAIR_ONLY',json.dumps(result),flush=True)
