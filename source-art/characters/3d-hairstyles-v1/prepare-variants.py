"""Adapt the established Blender reconstruction pipeline to three hairstyles."""
from pathlib import Path
import json,re,subprocess
BASE=Path(__file__).resolve().parent
OLD=BASE.parent/'3d-2d-hair-v6'
specs={
 'nero':{'boxes':[[58,15,562,482],[646,15,1225,560],[69,636,559,1198],[649,640,1224,1190]],'width':.089,'top':1.835,'frontBottom':1.700,'bottom':1.655,'depth':[-.097,.132],'round':[.101,.143,1.685,.155],'polys':6000},
 'dante':{'boxes':[[89,25,562,565],[688,30,1201,578],[86,653,568,1210],[671,654,1199,1204]],'width':.097,'top':1.835,'frontBottom':1.575,'bottom':1.565,'depth':[-.118,.136],'round':[.113,.150,1.650,.204],'polys':8000},
 'vergil':{'boxes':[[58,9,572,530],[687,13,1192,571],[66,635,565,1222],[684,639,1205,1208]],'width':.092,'top':1.855,'frontBottom':1.680,'bottom':1.650,'depth':[-.099,.132],'round':[.105,.146,1.690,.171],'polys':8000}}
for name,s in specs.items():
 folder=BASE/name;views={}
 for i,view in enumerate(['front','right','back','left']):
  views[view]={'box':s['boxes'][i],'axes':[1 if view in ['right','left']else 0,2],'range':[s['depth']if view in ['right','left']else[-s['width'],s['width']],[s['frontBottom']if view=='front'else s['bottom'],s['top']]],'flip':view in ['right','back']}
 (folder/'config.json').write_text(json.dumps({'id':name,'views':views,'round':s['round']},indent=2)+'\n',encoding='utf-8',newline='\n')
 prepare=(OLD/'prepare.py').read_text(encoding='utf-8')
 start=prepare.index('views={');end=prepare.index('arrays={}',start)
 prepare=prepare[:start]+"config=json.loads((BASE/'config.json').read_text(encoding='utf-8'));views=config['views']\n"+prepare[end:]
 prepare=prepare.replace("lo=np.array([-.122,-.128,1.575]);dims=np.array([124,145,151])","lo=np.array([-.123,-.135,1.545]);dims=np.array([125,151,171])")
 prepare=prepare.replace("outline=project(grid,'front','silhouette')","outline=project(grid,'front','silhouette');outline=np.maximum(outline,np.clip((grid[...,1]-.010)/.035,0,1))")
 prepare=prepare.replace("rounding=(grid[...,0]/.132)**2+((grid[...,1]-.015)/.163)**2+((grid[...,2]-1.675)/.205)**2","rx,ry,cz,rz=config['round'];rounding=(grid[...,0]/rx)**2+((grid[...,1]-.015)/ry)**2+((grid[...,2]-cz)/rz)**2")
 prepare=prepare.replace('occ=nd.gaussian_filter(density,.65)>.48',"if config['id']=='dante':\n window=(grid[...,0]/.073)**2+((grid[...,2]-1.655)/.105)**2\n protection=np.clip((1-window)*30+.5,0,1)*np.clip((.020-grid[...,1])/.04,0,1)\n density*=1-protection\nocc=nd.gaussian_filter(density,.65)>.48")
 (folder/'prepare.py').write_text(prepare,encoding='utf-8',newline='\n')
 build=(OLD/'build.py').read_text(encoding='utf-8').replace('BASE.parents[2]','BASE.parents[3]').replace("SOURCE=BASE.parent/'3d-native-hair-v4'","SOURCE=BASE.parent.parent/'3d-native-hair-v4'")
 build=build.replace("'range':[[-.115,.115],[-.120,.148]]","'range':[views['back']['range'][0],views['right']['range'][0]]")
 build=build.replace('22000/max',str(s['polys'])+'/max').replace("'2d-reference-hair',2048","'style-"+name+"',2048")
 build=build.replace("for i,name in enumerate(names):w[:,i]*=.001+.999*sample(data[name+'_mask'],uv_for(co,views[name]))","for i,name in enumerate(names):\n projected=uv_for(co,views[name]);valid=np.all((projected>=0)&(projected<=1),axis=1);w[:,i]*=.0001+.9999*sample(data[name+'_mask'],projected)*valid")
 build=build.replace('hair-reference-color.png','hair-'+name+'-color.png').replace('Hair_2D_Reference_v6','Hair_Style_'+name.title()).replace('raphael_native_hair_2D_Reference','raphael_native_hair_'+name.title()).replace('../hair-2d-v6/textures/','../hairstyles-v1/textures/').replace('reference-silver-curls-v6','hairstyle-'+name+'-v1').replace('3d-2d-hair-v6/README.md','3d-hairstyles-v1/README.md')
 build=re.sub(r'^bpy\.ops\.export_scene\.gltf\(.*$',"# Shared-rig export is performed once by combine.py.",build,flags=re.M)
 build=build.replace("manifest['hairstyle']={'asset'","manifest['hairstyle']={'meshData':hair.data.name,'asset'")
 (folder/'build.py').write_text(build,encoding='utf-8',newline='\n')
 padding=(OLD/'finish-padding.py').read_text(encoding='utf-8').replace('hair-reference-color.png','hair-'+name+'-color.png')
 (folder/'finish-padding.py').write_text(padding,encoding='utf-8',newline='\n')
 subprocess.run(['C:/Python314/python.exe',str(folder/'prepare.py')],check=True)
print('Prepared three distinct silhouette configurations',flush=True)
