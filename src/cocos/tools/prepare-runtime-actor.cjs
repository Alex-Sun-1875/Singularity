// Offline actor split/compaction, using the already installed MIT meshoptimizer.
// Body, face, UVs, skeleton and animation data are copied byte for byte.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {MeshoptSimplifier}=require('meshoptimizer');
const project=path.resolve(__dirname,'..'),folder=path.join(project,'assets/resources/actors/raphael');
const archive=path.resolve(project,'../../source-art/performance/runtime-actor-v2');
const file=path.join(folder,'raphael-polish.glb'),manifestFile=path.join(folder,'manifest.json');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const clone=x=>JSON.parse(JSON.stringify(x));
const width={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16},bytes={5121:1,5123:2,5125:4,5126:4};
function unpack(raw){const n=raw.readUInt32LE(12);if(raw.readUInt32LE(0)!==0x46546c67||raw.readUInt32LE(4)!==2||raw.readUInt32LE(24+n)!==0x004e4942)throw Error('Expected GLB 2');return {json:JSON.parse(raw.subarray(20,20+n)),bin:raw.subarray(28+n)};}
function accessor(g,bin,id){const a=g.accessors[id],v=g.bufferViews[a.bufferView],stride=width[a.type]*bytes[a.componentType];if(a.sparse||v.byteStride||a.byteOffset)throw Error('Unsupported accessor layout');return Buffer.from(bin.subarray(v.byteOffset??0,(v.byteOffset??0)+a.count*stride));}
function data(g,bin,id){const a=g.accessors[id],b=accessor(g,bin,id),step=bytes[a.componentType],out=a.componentType===5126?new Float32Array(b.length/step):new Uint32Array(b.length/step);for(let i=0;i<out.length;i++)out[i]=a.componentType===5126?b.readFloatLE(i*step):step===4?b.readUInt32LE(i*step):step===2?b.readUInt16LE(i*step):b.readUInt8(i);return out;}
// Rebuild only referenced accessors/views; unused embedded images never enter output.
function pack(g,bin,replacements=new Map()){
 const used=new Set();for(const m of g.meshes??[])for(const p of m.primitives){used.add(p.indices);for(const id of Object.values(p.attributes))used.add(id);for(const target of p.targets??[])for(const id of Object.values(target))used.add(id);}
 for(const s of g.skins??[])if(s.inverseBindMatrices!==undefined)used.add(s.inverseBindMatrices);
 for(const a of g.animations??[])for(const s of a.samplers){used.add(s.input);used.add(s.output);}
 const remap=new Map(),accessors=[],views=[],chunks=[];let offset=0;
 for(const old of [...used].sort((a,b)=>a-b)){
  const a=clone(g.accessors[old]),payload=replacements.get(old)??accessor(g,bin,old),padding=Buffer.alloc((-offset)&3);chunks.push(padding);offset+=padding.length;
  a.bufferView=views.length;delete a.byteOffset;remap.set(old,accessors.length);accessors.push(a);
  views.push({buffer:0,byteOffset:offset,byteLength:payload.length});chunks.push(payload);offset+=payload.length;
 }
 const convert=id=>{if(!remap.has(id))throw Error('Missing accessor '+id);return remap.get(id);};
 for(const m of g.meshes??[])for(const p of m.primitives){p.indices=convert(p.indices);for(const key in p.attributes)p.attributes[key]=convert(p.attributes[key]);for(const target of p.targets??[])for(const key in target)target[key]=convert(target[key]);}
 for(const s of g.skins??[])if(s.inverseBindMatrices!==undefined)s.inverseBindMatrices=convert(s.inverseBindMatrices);
 for(const a of g.animations??[])for(const s of a.samplers){s.input=convert(s.input);s.output=convert(s.output);}
 g.accessors=accessors;g.bufferViews=views;g.buffers=[{byteLength:offset}];delete g.images;delete g.textures;delete g.samplers;
 let json=Buffer.from(JSON.stringify(g));json=Buffer.concat([json,Buffer.alloc((-json.length)&3,32)]);
 const binary=Buffer.concat([...chunks,Buffer.alloc((-offset)&3)]),header=Buffer.alloc(20),binHeader=Buffer.alloc(8);
 header.writeUInt32LE(0x46546c67);header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+binary.length,8);header.writeUInt32LE(json.length,12);header.writeUInt32LE(0x4e4f534a,16);binHeader.writeUInt32LE(binary.length);binHeader.writeUInt32LE(0x004e4942,4);
 return Buffer.concat([header,json,binHeader,binary]);
}
(async()=>{
 await MeshoptSimplifier.ready;
 const source=fs.existsSync(path.join(archive,'raphael-polish.glb'))?path.join(archive,'raphael-polish.glb'):file;
 const raw=fs.readFileSync(source);if(sha(raw)!=='e08f6fd6d73d7bcb3a72b99f90b36216f6d91672c7f454c1327b32038bc1ab56')throw Error('Unreviewed actor source revision');
 const manifestSource=fs.existsSync(path.join(archive,'manifest.json'))?path.join(archive,'manifest.json'):manifestFile;
 const manifest=JSON.parse(fs.readFileSync(manifestSource)),originalManifest=clone(manifest),{json:g,bin}=unpack(raw);
 if((g.extensionsUsed??[]).length)throw Error('Review GLTF extensions before compacting');
 if(g.materials.some(m=>/"\w*Texture"\s*:/.test(JSON.stringify(m))))throw Error('Strip replaced texture dependencies first');
 const outputs=new Map(),hairMeshes=new Set(),stats=[];
 for(const style of manifest.hairstyles){
  if(style.nodes.length!==1)throw Error('Expected one mesh per reviewed hairstyle');
  const nodeIndex=g.nodes.findIndex(n=>n.name===style.nodes[0]),meshIndex=g.nodes[nodeIndex]?.mesh,mesh=clone(g.meshes[meshIndex]);hairMeshes.add(meshIndex);
  if(mesh.primitives.length!==1)throw Error('Expected one hair primitive');const p=mesh.primitives[0];
  const indices=data(g,bin,p.indices),positions=data(g,bin,p.attributes.POSITION),normals=data(g,bin,p.attributes.NORMAL),uv=data(g,bin,p.attributes.TEXCOORD_0),weights=data(g,bin,p.attributes.WEIGHTS_0),joints=data(g,bin,p.attributes.JOINTS_0);
  const headJoint=joints[0];for(let i=0;i<weights.length;i+=4)if(weights[i]!==1||weights[i+1]||weights[i+2]||weights[i+3]||joints[i]!==headJoint)throw Error('Hair is no longer rigid to one head joint');
  const attributes=new Float32Array(positions.length/3*5);for(let i=0;i<positions.length/3;i++){attributes.set(normals.subarray(i*3,i*3+3),i*5);attributes.set(uv.subarray(i*2,i*2+2),i*5+3);}
  const [simplified,error]=MeshoptSimplifier.simplifyWithAttributes(indices,positions,3,attributes,5,[.25,.25,.25,1,1],null,Math.floor(indices.length*.25/3)*3,.001,['LockBorder']);
  const [remap,count]=MeshoptSimplifier.compactMesh(simplified),h=clone(g),replacements=new Map();
  for(const id of Object.values(p.attributes)){
   const a=h.accessors[id],old=accessor(g,bin,id),stride=width[a.type]*bytes[a.componentType],next=Buffer.alloc(count*stride);
   for(let i=0;i<remap.length;i++)if(remap[i]!==0xffffffff)old.copy(next,remap[i]*stride,i*stride,(i+1)*stride);
   a.count=count;if(a.min){const n=width[a.type];a.min=Array(n).fill(Infinity);a.max=Array(n).fill(-Infinity);for(let i=0;i<count;i++)for(let j=0;j<n;j++){const v=next.readFloatLE((i*n+j)*4);a.min[j]=Math.min(a.min[j],v);a.max[j]=Math.max(a.max[j],v);}}
   replacements.set(id,next);
  }
  const index=Buffer.alloc(simplified.length*4);simplified.forEach((value,i)=>index.writeUInt32LE(value,i*4));h.accessors[p.indices]={...h.accessors[p.indices],componentType:5125,count:simplified.length,min:[0],max:[count-1]};replacements.set(p.indices,index);
  h.meshes=[mesh];h.materials=[clone(g.materials[p.material])];p.material=0;delete h.animations;
  h.nodes.forEach((n,i)=>{if(i===nodeIndex)n.mesh=0;else if(n.mesh!==undefined){delete n.mesh;delete n.skin;}});
  const name='hair-'+style.id;style.geometryRoot=name;outputs.set(path.join(folder,name+'.glb'),pack(h,bin,replacements));
  style.sourceTriangles=indices.length/3;style.triangles=simplified.length/3;
  stats.push({id:style.id,beforeTriangles:indices.length/3,afterTriangles:simplified.length/3,beforeVertices:positions.length/3,afterVertices:count,reportedRelativeError:error,estimatedErrorMetres:error*MeshoptSimplifier.getScale(positions,3),fileBytes:outputs.get(path.join(folder,name+'.glb')).length});
 }
 const main=clone(g),meshRemap=new Map();main.meshes=main.meshes.filter((m,i)=>{if(hairMeshes.has(i))return false;meshRemap.set(i,meshRemap.size);return true;});
 for(const n of main.nodes)if(n.mesh!==undefined){if(hairMeshes.has(n.mesh)){delete n.mesh;delete n.skin;}else n.mesh=meshRemap.get(n.mesh);}
 const materialIds=[...new Set(main.meshes.flatMap(m=>m.primitives.map(p=>p.material)))].sort((a,b)=>a-b),materialRemap=new Map(materialIds.map((id,i)=>[id,i]));
 main.materials=materialIds.map(id=>main.materials[id]);for(const m of main.meshes)for(const p of m.primitives)p.material=materialRemap.get(p.material);
 // Keep used material names stable for NativeActorMaterials' manifest matching.
 manifest.triangles=main.meshes.reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+g.accessors[p.indices].count/3,0),0);
 manifest.runtimeGeometry={revision:'runtime-actor-v2',baseTriangles:manifest.triangles,selectedHairstyleOnly:true,sourceTriangles:g.meshes.reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+g.accessors[p.indices].count/3,0),0)};
 manifest.fbx=path.relative(folder,path.join(archive,'legacy/raphael.fbx')).replaceAll('\\','/');
 const mainOutput=pack(main,bin);outputs.set(file,mainOutput);
 const verified=unpack(mainOutput);let unchanged=0;
 const verify=(old,next)=>{const a=g.accessors[old],b=verified.json.accessors[next];if(a.count!==b.count||a.componentType!==b.componentType||a.type!==b.type||!accessor(g,bin,old).equals(accessor(verified.json,verified.bin,next)))throw Error('Protected body/animation accessor changed');unchanged++;};
 for(const [old,next]of meshRemap)g.meshes[old].primitives.forEach((p,i)=>{const q=verified.json.meshes[next].primitives[i];verify(p.indices,q.indices);for(const key in p.attributes)verify(p.attributes[key],q.attributes[key]);});
 for(let i=0;i<g.animations.length;i++)g.animations[i].samplers.forEach((s,j)=>{const next=verified.json.animations[i].samplers[j];verify(s.input,next.input);verify(s.output,next.output);});
 g.skins.forEach((s,i)=>verify(s.inverseBindMatrices,verified.json.skins[i].inverseBindMatrices));
 const result={sourceSha256:sha(raw),bodyFileBytesBefore:raw.length,bodyFileBytesAfter:mainOutput.length,removedEmbeddedImageBytes:g.images.reduce((n,x)=>n+g.bufferViews[x.bufferView].byteLength,0),hair:stats,bodyAndAnimationAccessorsCopiedExactly:true,verifiedProtectedAccessorCount:unchanged,recipe:'meshoptimizer 1.1.1 MIT; attribute-aware, locked border, relative error <= 0.001; retained vertex attributes copied exactly',files:Object.fromEntries([...outputs].map(([p,b])=>[path.relative(project,p).replaceAll('\\','/'),{bytes:b.length,sha256:sha(b)}]))};
 if(process.argv.includes('--write')){
  const currentHash=sha(fs.readFileSync(file));if(currentHash!==sha(raw)&&currentHash!==sha(mainOutput))throw Error('Refusing to overwrite an unreviewed runtime actor revision');
  const currentManifest=JSON.stringify(JSON.parse(fs.readFileSync(manifestFile)));if(currentManifest!==JSON.stringify(originalManifest)&&currentManifest!==JSON.stringify(manifest))throw Error('Refusing to overwrite an unreviewed actor manifest revision');
  for(const [target,content]of outputs)if(target!==file&&fs.existsSync(target)&&sha(fs.readFileSync(target))!==sha(content))throw Error('Refusing to overwrite edited hairstyle geometry: '+target);
  fs.mkdirSync(archive,{recursive:true});if(!fs.existsSync(path.join(archive,'raphael-polish.glb'))){fs.copyFileSync(file,path.join(archive,'raphael-polish.glb'));fs.copyFileSync(manifestFile,path.join(archive,'manifest.json'));}
  for(const [target,content]of outputs){fs.writeFileSync(target,content);if(target!==file&&!fs.existsSync(target+'.meta'))fs.writeFileSync(target+'.meta',JSON.stringify({ver:'2.3.14',importer:'gltf',imported:false,uuid:crypto.randomUUID(),files:[],subMetas:{},userData:{}},null,2)+'\n');}
  fs.writeFileSync(manifestFile,JSON.stringify(manifest,null,2)+'\n');fs.writeFileSync(path.join(archive,'conversion.json'),JSON.stringify(result,null,2)+'\n');
  // These previous revisions are not referenced by the selected prefabRoot.
  // Keep their original files/UUID metadata outside Cocos' shipped asset bundle.
  const retired=path.join(archive,'legacy');fs.mkdirSync(retired,{recursive:true});const records=[];
  for(const name of ['raphael.fbx','raphael-designed.glb','raphael-refined.glb'])for(const suffix of ['', '.meta']){
   const from=path.join(folder,name+suffix),to=path.join(retired,name+suffix);if(!fs.existsSync(from))continue;
   const content=fs.readFileSync(from);if(fs.existsSync(to)&&sha(fs.readFileSync(to))!==sha(content))throw Error('Refusing to overwrite retired authoring revision: '+name+suffix);
   if(!fs.existsSync(to))fs.copyFileSync(from,to);records.push({name:name+suffix,bytes:content.length,sha256:sha(content)});fs.unlinkSync(from);
  }
  if(records.length)fs.writeFileSync(path.join(retired,'archive.json'),JSON.stringify({reason:'Unused previous actor revisions; active runtime uses manifest.prefabRoot and standalone selected hair mesh',files:records},null,2)+'\n');
 }
 console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
