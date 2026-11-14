from pathlib import Path
import bpy,sys,json,hashlib,ast
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'));import cocos_v5_character_redesign as pipeline
module=ast.parse((BASE/'build.py').read_text(encoding='utf-8'));function=next(n for n in module.body if isinstance(n,ast.FunctionDef)and n.name=='mesh_digest');scope={'hashlib':hashlib};exec(compile(ast.Module(body=[function],type_ignores=[]),str(BASE/'build.py'),'exec'),scope);digest=scope['mesh_digest']
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));record=json.loads((BASE/'preservation.json').read_text(encoding='utf-8'));objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];rig=bpy.data.objects['raphael_Native65']
assert {o.name:digest(o)for o in objects if o.get('nativePart')in ['head','eyes','brows']}==record['faceMeshHashes']
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==record['bodyMeshHashes']
assert pipeline.curves()==record['actionHash']and pipeline.skeleton(rig)==record['bindHash']and len(objects)==13
result={'faceGeometryUVWeightsPreserved':True,'allBodyClothingGeometryUVWeightsPreserved':True,'all14MotionCurvesPreserved':True,'bindPosePreserved':True,'headAndBodyMeshHashes':record['bodyMeshHashes'],'actionHash':record['actionHash'],'bindHash':record['bindHash'],'renderers':13,'triangles':sum(pipeline.triangles(o)for o in objects)}
(BASE/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('VERIFIED_ORIGINAL_FACE_BODY_AND_MOTIONS')
