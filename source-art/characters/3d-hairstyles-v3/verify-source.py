from pathlib import Path
import bpy,sys,json,ast,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
tree=ast.parse((BASE/'reproject-rebuild.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='digest');scope={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(BASE/'reproject-rebuild.py'),'exec'),scope)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));proof=json.loads((BASE/'preservation.json').read_text(encoding='utf-8'));rig=bpy.data.objects['raphael_Native65'];objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(objects)==16 and len(bpy.data.actions)==14
assert {o.name:scope['digest'](o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
new=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));old=json.loads((BASE.parent/'3d-hairstyles-v1/manifest.json').read_text(encoding='utf-8'))
assert [r for r in new['materials']if 'hair'not in r.get('parts',[])]==[r for r in old['materials']if 'hair'not in r.get('parts',[])]
assert [s['id']for s in new['hairstyles']]==['curly','dante','nero','vergil']and new['appearanceRevision']=='hairstyles-v3-refined'
for style in new['hairstyles']:
 o=bpy.data.objects[style['nodes'][0]];assert o.get('nativePart')=='hair'and len(o.vertex_groups)==1 and o.vertex_groups[0].name=='Head'
 assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in o.data.vertices)
blob=(BASE/'raphael-polish.glb').read_bytes();length=int.from_bytes(blob[12:16],'little');gltf=json.loads(blob[20:20+length]);assert len(gltf['animations'])==14
assert not any('Authored'in n.get('name','')for n in gltf['nodes'])
assert not any('Hair_Strands_v2'in m.get('name','')or 'Hair_Library_'in m.get('name','')for m in gltf['materials'])
result={'faceBodyGeometryUVWeightsPreserved':True,'allFaceAndClothingMaterialRecordsPreserved':True,'all14MotionCurvesPreserved':True,'bindPosePreserved':True,'rejectedPrototypeMaterialsAbsent':True,'runtimeGLBSHA256':hashlib.sha256(blob).hexdigest(),'renderers':16,'styles':new['hairstyles'],'actionHash':proof['actionHash'],'bindHash':proof['bindHash']}
(BASE/'source-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print('VERIFIED_HAIR_REDESIGN',flush=True)
