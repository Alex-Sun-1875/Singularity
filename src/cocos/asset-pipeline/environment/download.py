"""Download official CC0 Poly Haven source GLTFs; retain checksums and file provenance."""
import concurrent.futures,hashlib,json,pathlib,requests,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
CACHE=ROOT/'temp/environment-source';CACHE.mkdir(parents=True,exist_ok=True)
ASSETS={
 'table':('dining_table',2000), 'round-table':('round_wooden_table_02',4500),
 'chair':('WoodenChair_01',4500), 'stool':('wooden_stool_01',2000),
 'shelf':('wooden_bookshelf_worn',6000),'barrel':('wine_barrel_01',3000),
 'crate':('wooden_crate_01',4000),'chest':('treasure_chest',6500),
 'lantern':('wooden_lantern_01',4000),'jug':('jug_01',2000),
 'bowl':('wooden_bowl_02',1800),'candlestick':('wooden_candlestick',1600),
 'books':('book_encyclopedia_set_01',3000),'rocks':('rock_moss_set_01',10000),
 'tree':('tree_small_02',12000),'fern':('fern_02',3200),
 'firepit':('stone_fire_pit',3500),'door':('large_castle_door',5000),'stump':('tree_stump_01',3000),'grass':('grass_medium_01',2600),
}
def download(path,entry):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and hashlib.md5(path.read_bytes()).hexdigest()==entry['md5']:return
 for attempt in range(4):
  try:
   r=requests.get(entry['url'],timeout=120,headers={'User-Agent':'Singularity-CC0-Environment-Adapter/1.0'});r.raise_for_status();data=r.content
   assert hashlib.md5(data).hexdigest()==entry['md5'],entry['url']
   path.write_bytes(data);return
  except Exception:
   if attempt==3:raise
   time.sleep(1+attempt)
def one(item):
 key,(asset,budget)=item
 r=requests.get('https://api.polyhaven.com/files/'+asset,timeout=60);r.raise_for_status();files=r.json()
 (CACHE/(asset+'-files.json')).write_text(json.dumps(files,indent=2))
 f=files['gltf']['1k']['gltf'];folder=CACHE/asset
 allfiles={asset+'.gltf':f,**f.get('include',{})}
 if key=='tree':allfiles[asset+'.blend']=files['blend']['1k']['blend']
 for name,formats in files.items():
  if 'alpha' in name.lower() and '1k' in formats and 'png' in formats['1k']:allfiles['textures/'+name+'-opacity.png']=formats['1k']['png']
 for path,entry in allfiles.items():download(folder/path,entry)
 out={'key':key,'asset':asset,'budget':budget,'page':'https://polyhaven.com/a/'+asset,'license':'CC0-1.0','licenseUrl':'https://polyhaven.com/license','api':'https://api.polyhaven.com/files/'+asset,'files':[]}
 for path,entry in allfiles.items():
  data=(folder/path).read_bytes();out['files'].append({'path':path,'url':entry['url'],'md5':entry['md5'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
 print(key,sum(x['bytes'] for x in out['files']),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:result=list(pool.map(one,ASSETS.items()))
(ROOT/'asset-pipeline/environment/sources.json').write_text(json.dumps({'retrieved':'2026-11-04','source':'Poly Haven official public API','assets':result},indent=2))
