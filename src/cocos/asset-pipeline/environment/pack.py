"""Use Cocos BufferAsset instead of shipping multi-megabyte numeric JSON arrays."""
import array,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'assets/resources/environment'
data=json.loads((ROOT/'temp/environment-source/library-unpacked.json').read_text())
blob=bytearray()
for model in data['models'].values():
 for part in model['parts']:
  for key in ['positions','normals','uvs','indices']:
   values=part[key];kind='I' if key=='indices' else 'f';packed=array.array(kind,values).tobytes();part[key]=[len(blob),len(values)];blob.extend(packed)
data['version']=2;data['geometry']='geometry'
(BASE/'library.json').write_text(json.dumps(data,separators=(',',':')));(BASE/'geometry.bin').write_bytes(blob)
print('Packed',len(data['models']),'models into',len(blob),'bytes')
