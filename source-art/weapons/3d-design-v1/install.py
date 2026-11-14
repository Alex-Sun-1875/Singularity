"""Install reviewed local FBX/PBR assets; retain prior shared/NPC resources.
Run after build.py and geometry review. No downloads or generation services.
"""
from pathlib import Path
import json,hashlib,shutil,math,sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
from weapon_carry_calibration import apply_bow_carry_calibration
DEST=ROOT/'src/cocos/assets/resources/actors/props-native'
rows=json.loads((BASE/'prepared/models.json').read_text(encoding='utf-8'))

def write(path,data):
    tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def srgb(x):return 12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055

colors={'steel':(.13,.16,.19),'bronze':(.22,.12,.048),'wood':(.105,.065,.033),'greywood':(.13,.115,.090),'leather':(.070,.033,.018),'string':(.22,.16,.09),'blue':(.035,.09,.22)}
leather=ROOT/'assets/materials/chapter-one-v3/ui/ui-smoked-leather-albedo-v1.png'
wood=ROOT/'source-art/materials/chapter-one-v3/pbr-library/wood_planks_grey/wood_planks_grey_diff_1k.png'
for role,color in colors.items():
    source=leather if role=='leather' else wood
    grain=np.array(Image.open(source).convert('RGB').resize((128,128))).astype(float)/255
    grain=grain.mean(axis=2);grain=grain/max(.01,np.median(grain));grain=np.clip(grain,.65,1.35)
    if role in ['steel','bronze','blue','string']:grain=1+(grain-1)*.18
    base=np.array([srgb(x)for x in color]);albedo=np.clip(grain[:,:,None]*base,0,1)
    prefix=BASE/'textures'/('design-edge-'+role)
    Image.fromarray(np.uint8(albedo*255)).save(str(prefix)+'-albedo.png')
    height=ndi.gaussian_filter(grain,.5)-ndi.gaussian_filter(grain,3);dy,dx=np.gradient(height)
    normal=np.dstack((-dx*.08,dy*.08,np.ones_like(dx)));normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    Image.fromarray(np.uint8((normal*.5+.5)*255)).save(str(prefix)+'-normal.png')
    rough=.31 if role=='steel'else .40 if role=='bronze'else .7;metal=.85 if role in ['steel','bronze']else 0
    orm=np.dstack((np.ones_like(grain),np.clip(rough+height*.06,0,1),np.full_like(grain,metal)))
    Image.fromarray(np.uint8(orm*255)).save(str(prefix)+'-orm.png')

manifest_path=DEST/'manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
if not (BASE/'before-native-manifest.json').exists():write(BASE/'before-native-manifest.json',manifest)
records=[]
for row in rows+[{'id':'quiver'}]:
    record=json.loads((BASE/'models'/(row['id']+'.json')).read_text(encoding='utf-8'))
    for entry in [record]+([record['stowedModel']]if record.get('stowedModel')else[]):
        name=entry['id'];source=ROOT/entry['fbx'];folder=DEST/name;folder.mkdir(exist_ok=True);target=folder/(name+'.fbx');shutil.copyfile(source,target)
        mats=[]
        for material in entry['materials']:
            prefix='design-edge-'+material.removeprefix('DesignEdge_') if material.startswith('DesignEdge_') else 'design-'+row['id'].lower()
            mats.append({'runtimeName':material,'maps':{k:'../props-native/textures/'+prefix+'-'+k+'.png'for k in ['albedo','normal','orm']},'sourcePBR':{'effectiveFactors':{'roughness':1,'metallic':.5}},'ormChannels':{'occlusion':'R','roughness':'G','metallic':'B'}})
        manifest['props'][name]={'id':name,'resource':f'actors/props-native/{name}/{name}/{name}','source':record['source'],'sourceSHA256':digest(ROOT/record['source']),'exportSHA256':digest(target),'license':'Project-authored 3D geometry using existing project-owned 2D artwork; original CC0 Bow Draw/string retained for bows','materials':mats,'triangles':entry['triangles'],'design2D':row.get('source'),'design2DSHA256':row.get('sourceSHA256'),'review':'source-art/weapons/3d-design-v1/README.md','morph':{'shapeName':'Draw','string':'Original native topology/Draw nock; original serving pinned, tips adapted to new body with native BVH; physical length adapted','body':'Blender native Surface Deform transfer'}if row.get('kind')=='bow'else None}
        if entry is record and record.get('stowedModel'):manifest['props'][name]['stowedResource']=record['stowedModel']['id']
        records.append({'equipment':row['id'],'resource':name,'fbx':target.relative_to(ROOT).as_posix(),'sha256':digest(target),'triangles':entry['triangles']})
for source in (BASE/'textures').glob('*.png'):shutil.copyfile(source,DEST/'textures'/source.name)
manifest.update({'version':'native-props+2d-design-v1','status':'installed-local-review','equipmentResources':{r['id']:'design-'+r['id'].lower()for r in rows},'weaponDesignReview':'source-art/weapons/3d-design-v1/README.md'})
write(manifest_path,manifest)

actor_path=ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json';actor=json.loads(actor_path.read_text(encoding='utf-8'))
if not (BASE/'before-actor-manifest.json').exists():write(BASE/'before-actor-manifest.json',actor)
def placement(position,blade):return {'position':position,'blade':blade,'normal':[0,0,-1]}
items={};quivers={}
for row in rows:
    id=row['id'];kind=row['modelKind']
    if kind=='sword':
        dx=.3878 if id=='W02' else .297;items[id]=placement([-.145,1.63,-.29],[dx,-math.sqrt(1-dx*dx),0])
    elif kind=='hammer':items[id]=placement([-.11,1.10,-.33],[-.22,.9755,0])
    elif kind=='staff':items[id]=placement([-.19,1.31 if id=='W11'else 1.15,-.30],[-.08,.9968,0])
    else:
        right=id in ['W08','DU2-04'];x=-.22 if right else .22
        items[id]=placement([x,1.20,-.34],[.06 if right else -.06,.9982,0])
        quivers[id]=placement([.13 if right else -.13,1.27,-.32],[.17 if right else -.17,.9854,0])
actor['cocosBinding']['swordBackCarry']={'bone':'spine_03','hiltScale':1,'embeddedCases':True,'placements':{'sword':items['W01'],'greatsword':items['L01'],'bow':items['W07'],'staff':items['W11']},'items':items,'quiver':{'resource':'design-quiver','placements':quivers}}
actor['cocosBinding']['bowDrawWeightByItem']={r['id']:json.loads((BASE/'models'/(r['id']+'-draw-calibration.json')).read_text()) for r in rows if r['kind']=='bow'}
actor['weaponDesignReview']='source-art/weapons/3d-design-v1/README.md'
apply_bow_carry_calibration(actor,ROOT)
write(actor_path,actor)
write(BASE/'install-record.json',{'weapons':len(rows),'records':records,'textures':len(list((BASE/'textures').glob('*.png'))),'bodySHA256':digest(ROOT/'src/cocos/assets/resources/actors/raphael/raphael.fbx'),'method':'Local Blender authoring / native FBX, existing artwork deterministic PBR maps; no generated images, downloads or body pose changes'})
print('INSTALLED',len(rows),'weapons;',len(records),'held/stowed/quiver resources')
