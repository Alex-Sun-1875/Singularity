// Offline, lossless index locality pass. Uses the already installed MIT
// meshoptimizer 1.1.1 dependency; does not download or modify vertex data.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {MeshoptEncoder}=require('meshoptimizer');
const project=path.resolve(__dirname,'../..');
const file=path.join(project,'assets/resources/actors/raphael/raphael-polish.glb');
const beforeHash='147aa9e3d166062c95cd0d4dd4ba5152a84230c1f8930b62912cd4d0bf2f7e5a';
const afterHash='7355fc0d6c39e7ba3578f1f30c4720d019f8273b3b38312e9866e6007d8595cc';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function triangles(list){
 const result=new Map();
 for(let i=0;i<list.length;i+=3){
  const key=[[list[i],list[i+1],list[i+2]],[list[i+1],list[i+2],list[i]],[list[i+2],list[i],list[i+1]]].map(t=>t.join(',')).sort()[0];
  result.set(key,(result.get(key)||0)+1);
 }
 return JSON.stringify([...result].sort((a,b)=>a[0].localeCompare(b[0])));
}
(async()=>{
 const original=fs.readFileSync(file),inputHash=sha(original);
 if(inputHash===afterHash){console.log('Already optimized; SHA-256 verified.');return;}
 if(inputHash!==beforeHash)throw Error('Unknown actor revision: review its materials and geometry before regenerating this recipe.');
 const encoderPackage=JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve('meshoptimizer')),'package.json')));
 if(encoderPackage.version!=='1.1.1')throw Error('This recipe is validated with meshoptimizer 1.1.1.');
 await MeshoptEncoder.ready;
 const next=Buffer.from(original),jsonLength=original.readUInt32LE(12);
 if(original.readUInt32LE(0)!==0x46546c67||original.readUInt32LE(4)!==2)throw Error('Expected GLB 2.');
 const json=JSON.parse(original.subarray(20,20+jsonLength)),binStart=20+jsonLength+8;
 if(original.readUInt32LE(binStart-4)!==0x004e4942)throw Error('Missing BIN chunk.');
 const manifest=JSON.parse(fs.readFileSync(path.join(path.dirname(file),'manifest.json'))),done=new Set(),ranges=[];
 for(const mesh of json.meshes)for(const primitive of mesh.primitives){
  if((primitive.mode??4)!==4||primitive.indices===undefined)continue;
  const material=json.materials[primitive.material],record=manifest.materials.find(m=>m.runtimeName===material.name);
  // Existing NativeActorMaterials uses opaque alpha-test for this hair profile.
  // Sorting indices is unsafe for an actual alpha-blended material.
  if(material.alphaMode==='BLEND'&&!(manifest.runtimeProfile==='native-kit-v1'&&record?.alphaClip))throw Error('Order-dependent material: '+material.name);
  if(done.has(primitive.indices))continue;done.add(primitive.indices);
  const a=json.accessors[primitive.indices],view=json.bufferViews[a.bufferView];
  if(a.type!=='SCALAR'||a.sparse||view.byteStride||![5123,5125].includes(a.componentType))throw Error('Unsupported index layout.');
  const stride=a.componentType===5123?2:4,offset=binStart+(view.byteOffset??0)+(a.byteOffset??0);
  const read=i=>stride===2?original.readUInt16LE(offset+i*stride):original.readUInt32LE(offset+i*stride);
  const before=Array.from({length:a.count},(_,i)=>read(i)),indices=Uint32Array.from(before);
  const [remap,count]=MeshoptEncoder.reorderMesh(indices,true,false),inverse=new Uint32Array(count);
  // Undo the encoder's vertex remap: retain every original vertex and accessor.
  for(let i=0;i<remap.length;i++)if(remap[i]!==0xffffffff)inverse[remap[i]]=i;
  const after=Array.from(indices,i=>inverse[i]);
  if(triangles(before)!==triangles(after))throw Error('Triangle/winding mismatch.');
  for(let i=0;i<a.count;i++){if(stride===2)next.writeUInt16LE(after[i],offset+i*stride);else next.writeUInt32LE(after[i],offset+i*stride);}
  ranges.push([offset,offset+a.count*stride]);
 }
 const mask=new Uint8Array(original.length);for(const [from,to]of ranges)mask.fill(1,from,to);
 for(let i=0;i<original.length;i++)if(!mask[i]&&original[i]!==next[i])throw Error('Non-index byte changed.');
 if(sha(next)!==afterHash)throw Error('Output does not match the validated asset.');
 if(process.argv.includes('--write'))fs.writeFileSync(file,next);
 console.log(JSON.stringify({status:'passed',written:process.argv.includes('--write'),primitives:done.size,bytes:next.length,beforeSha256:beforeHash,afterSha256:afterHash,allNonIndexBytesUnchanged:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
