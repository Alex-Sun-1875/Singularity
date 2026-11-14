"""Create the authored boot scene from the installed Cocos scene schema.

Re-run only when the bootstrap scene/configuration intentionally changes.
UUIDs are Cocos UUIDs, unrelated to UrhoX resource metadata.
"""
from pathlib import Path
import json,uuid,copy
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=Path('C:/ProgramData/cocos/editors/Creator/3.8.8/resources/templates/hello-3d-world/assets/scene/main.scene')
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def compress(value):
 chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
 text=value.replace('-','');out=text[:5]
 for i in range(5,32,3):
  n=int(text[i:i+3],16);out+=chars[n>>6]+chars[n&63]
 return out
script=ROOT/'assets/scripts/app/ChapterGame.ts'
meta=Path(str(script)+'.meta')
sid=json.loads(meta.read_text())['uuid'] if meta.exists() else str(uuid.uuid4())
write(meta,{'ver':'4.0.24','importer':'typescript','imported':True,'uuid':sid,'files':[],'subMetas':{},'userData':{}})
sceneid='e0158e35-9bac-42ca-a8e1-16cdd7e71953'
node={'__type__':'cc.Node','_name':'ChapterGame','_objFlags':0,'_parent':{'__id__':1},'_children':[],'_active':True,'_components':[{'__id__':3}],'_prefab':None,'_lpos':{'__type__':'cc.Vec3','x':0,'y':0,'z':0},'_lrot':{'__type__':'cc.Quat','x':0,'y':0,'z':0,'w':1},'_lscale':{'__type__':'cc.Vec3','x':1,'y':1,'z':1},'_layer':1073741824,'_euler':{'__type__':'cc.Vec3','x':0,'y':0,'z':0},'_id':str(uuid.uuid4())}
data=[{'__type__':'cc.SceneAsset','_name':'FirstChapter','_objFlags':0,'_native':'','scene':{'__id__':1}}, {'__type__':'cc.Scene','_name':'FirstChapter','_objFlags':0,'_parent':None,'_children':[{'__id__':2}],'_active':True,'_components':[],'_prefab':None,'autoReleaseAssets':True,'_globals':{'__id__':4},'_id':sceneid},node,{'__type__':compress(sid),'_name':'','_objFlags':0,'node':{'__id__':2},'_enabled':True,'__prefab':None,'_id':str(uuid.uuid4())}]
source=json.loads(TEMPLATE.read_text());old=source[1]['_globals']['__id__'];index={}
def extract(i):
 if i in index:return index[i]
 dest=len(data);index[i]=dest;data.append(None)
 def convert(v):
  if isinstance(v,dict):
   if '__id__' in v:return {'__id__':extract(v['__id__'])}
   return {k:convert(x) for k,x in v.items()}
  if isinstance(v,list):return [convert(x) for x in v]
  return v
 data[dest]=convert(copy.deepcopy(source[i]));return dest
extract(old)
for obj in data:
 if isinstance(obj,dict) and obj.get('__type__')=='cc.SkyboxInfo':obj['_enabled']=False;obj['_envmap']=None
write(ROOT/'assets/FirstChapter.scene',data)
write(ROOT/'assets/FirstChapter.scene.meta',{'ver':'1.1.50','importer':'scene','imported':True,'uuid':sceneid,'files':['.json'],'subMetas':{},'userData':{}})
write(ROOT/'settings/v2/packages/project.json',{'__version__':'1.0.6','general':{'designResolution':{'width':1558,'height':720,'fitWidth':False,'fitHeight':True}}})
if not (ROOT/'settings/v2/packages/engine.json').exists(): write(ROOT/'settings/v2/packages/engine.json',{'__version__': '1.0.12', 'modules': {'configs': {'chapter': {'name': 'Chapter3D', 'cache': {'base': {'_value': True}, 'gfx-webgl': {'_value': False}, 'gfx-webgl2': {'_value': True}, '3d': {'_value': True}, '2d': {'_value': True}, 'ui': {'_value': True}, 'graphics': {'_value': True}, 'animation': {'_value': True}, 'skeletal-animation': {'_value': True}, 'physics-framework': {'_value': True}, 'physics-ammo': {'_value': True}, 'audio': {'_value': True}, 'primitive': {'_value': True}, 'tween': {'_value': True}}, 'flags': {}, 'includeModules': ['base', 'gfx-webgl2', '3d', '2d', 'ui', 'graphics', 'animation', 'skeletal-animation', 'physics-framework', 'physics-ammo', 'audio', 'primitive', 'tween']}}, 'globalConfigKey': 'chapter'}})
write(ROOT/'settings/v2/packages/preview.json',{'__version__':'1.0.0','startScene':sceneid})
write(ROOT/'settings/v2/packages/builder.json',{'__version__':'1.3.0','common':{'name':'SwordAndFire','mainBundleCompressionType':'merge_dep','platform':'web-desktop','buildPath':'project://build','startScene':sceneid,'scenes':[{'url':'db://assets/FirstChapter.scene','uuid':sceneid}]}})
print('Boot scene:',sceneid,'script:',sid)
