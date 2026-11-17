import {Color,JsonAsset,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,Vec3,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import {SkillFireSprites} from './SkillFireSprites';

type Point={x:number;z:number};
type RockGeometry={positions:number[];normals:number[];uvs:number[];indices:number[]};
type Comet={key:string;position:Vec3;active:boolean;touched:boolean;rock?:Node;target:Vec3;progress:number;size:number};

/** The existing resolved fall carries a small textured rock core. Its flowing
 * orange-gold sheath belongs to the shared fire pool, with no extra hit clock. */
export class SkillMeteorBody {
 private static mesh:Mesh|undefined;
 private static material:Material|undefined;
 private static texture:Texture2D|undefined;
 private static leadingSupport=new Vec3();
 private static centreFromNose=new Vec3();
 private static pending:Promise<void>|null=null;
 private static revision=0;
 private readonly comets:Comet[]=[];
 private readonly direction=new Vec3(-4.42,-8,3.06).normalize();
 private readonly tailDirection=Vec3.negate(new Vec3(),this.direction);
 private readonly alignment=Quat.rotationTo(new Quat(),new Vec3(0,1,0),this.tailDirection);
 private readonly roll=new Quat();
 private readonly rotation=new Quat();
 private readonly root:Node|undefined;
 private disposed=false;
 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const revision=this.revision;
  const geometry=new Promise<JsonAsset>((resolve,reject)=>resources.load('vfx/production/meteor-rock-v9',JsonAsset,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  const texture=new Promise<Texture2D>((resolve,reject)=>resources.load('vfx/production/meteor-rock-warm-v28/texture',Texture2D,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  this.pending=(async()=>{
   // Wait for both callbacks before releasing a partial load or a cancelled
   // generation; a late success must never retain an orphaned reference.
   const [g,t]=await Promise.allSettled([geometry,texture]);
   if(g.status==='rejected'||t.status==='rejected'||revision!==this.revision){
    if(g.status==='fulfilled')g.value.decRef();if(t.status==='fulfilled')t.value.decRef();
    throw g.status==='rejected'?g.reason:t.status==='rejected'?t.reason:new Error('Meteor core load cancelled');
   }
   let mesh:Mesh|undefined,material:Material|undefined;
   try{
    const data=g.value.json as RockGeometry;
    // The actual minimum-Y support is the leading nose. Rebase the shared
    // existing rock there, preserving its UVs, so no arbitrary body-centre
    // offset can move the leading point away from the resolved seal centre.
    let noseIndex=0;
    for(let i=1;i<data.positions.length/3;i++)if(data.positions[i*3+1]<data.positions[noseIndex*3+1])noseIndex=i;
    const nose=new Vec3(data.positions[noseIndex*3],data.positions[noseIndex*3+1],data.positions[noseIndex*3+2]);
    const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(let i=0;i<data.positions.length;i++) {const axis=i%3;min[axis]=Math.min(min[axis],data.positions[i]);max[axis]=Math.max(max[axis],data.positions[i]);}
    this.leadingSupport.set(nose);this.centreFromNose.set((min[0]+max[0])*.5-nose.x,(min[1]+max[1])*.5-nose.y,(min[2]+max[2])*.5-nose.z);
    const positions:number[]=[],normals:number[]=[],uvs:number[]=[],indices:number[]=[];
    for(let i=0;i<data.indices.length;i+=3){
     const ia=data.indices[i]*3,ib=data.indices[i+1]*3,ic=data.indices[i+2]*3,abx=data.positions[ib]-data.positions[ia],aby=data.positions[ib+1]-data.positions[ia+1],abz=data.positions[ib+2]-data.positions[ia+2],acx=data.positions[ic]-data.positions[ia],acy=data.positions[ic+1]-data.positions[ia+1],acz=data.positions[ic+2]-data.positions[ia+2];
     let nx=aby*acz-abz*acy,ny=abz*acx-abx*acz,nz=abx*acy-aby*acx;
     const length=Math.max(.00001,Math.hypot(nx,ny,nz));nx/=length;ny/=length;nz/=length;
     if(nx*data.normals[ia]+ny*data.normals[ia+1]+nz*data.normals[ia+2]<0){nx=-nx;ny=-ny;nz=-nz;}
     for(const vertex of [data.indices[i],data.indices[i+1],data.indices[i+2]]){
      positions.push(data.positions[vertex*3]-nose.x,data.positions[vertex*3+1]-nose.y,data.positions[vertex*3+2]-nose.z);normals.push(nx,ny,nz);uvs.push(data.uvs[vertex*2],data.uvs[vertex*2+1]);indices.push(indices.length);
     }
    }
    mesh=utils.createMesh({positions,normals,uvs,indices});mesh.name='MeteorNoseAnchoredFacetedRockV32';
    t.value.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);t.value.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);
    material=new Material();material.name='MeteorDeepWarmRockV32';
    material.initialize({effectName:'builtin-standard',defines:{USE_ALBEDO_MAP:true,USE_EMISSIVE_MAP:true}});
    material.setProperty('mainTexture',t.value);material.setProperty('mainColor',new Color(155,132,111,255));
    material.setProperty('albedoScale',new Vec3(.72,.76,.80));material.setProperty('roughness',.94);material.setProperty('metallic',0);material.setProperty('specularIntensity',.12);
    // A little self illumination keeps the existing rock texture readable in
    // shadow, while the transparent flame remains the brightest surface.
    material.setProperty('emissiveMap',t.value);material.setProperty('emissiveScale',new Vec3(.03,.02,.01));
    this.mesh=mesh;this.material=material;this.texture=t.value;
   }catch(error){mesh?.destroy();material?.destroy();t.value.decRef();throw error;}
   finally{g.value.decRef();}
  })().catch(error=>{if(revision===this.revision)this.pending=null;throw error;});
  return this.pending;
 }
 /** Called after the old renderers have detached from these shared assets. */
 static dispose(){this.revision++;this.mesh?.destroy();this.material?.destroy();this.texture?.decRef();this.mesh=undefined;this.material=undefined;this.texture=undefined;this.pending=null;}
 constructor(private readonly groundHeight:(p:Point)=>number,private readonly fire:SkillFireSprites,parent?:Node){
  if(parent){this.root=new Node('MeteorRockCores');this.root.layer=parent.layer;parent.addChild(this.root);}
 }
 begin(){for(const comet of this.comets)comet.touched=false;}
 draw(key:string,target:Point,rank:number,progress:number,time:number){
  if(this.disposed||progress>=1)return;
  let comet=this.comets.find(c=>c.key===key)??this.comets.find(c=>!c.active);
  if(!comet){if(this.comets.length>=4)return;comet={key,position:new Vec3(),active:false,touched:false,target:new Vec3(),progress:0,size:0};this.comets.push(comet);}
  const t=Math.max(0,Math.min(1,progress)),fall=.4*t+.6*t*t,size=1.05+rank*.11;
  // Same accelerated 8m descent and event clock, mirrored horizontally to
  // match the selected right-upper to left-lower comet. The nose, flame and
  // seal all converge at height(target)+.045, with no size-dependent offset.
  const landing=this.groundHeight(target)+.045;
  comet.position.set(target.x+4.42*(1-fall),landing+8*(1-fall),target.z-3.06*(1-fall));
  comet.key=key;comet.touched=true;comet.active=true;comet.target.set(target.x,landing,target.z);comet.progress=t;comet.size=size;
  if(!comet.rock&&this.root&&SkillMeteorBody.mesh&&SkillMeteorBody.material){
   const rock=new Node('MeteorRockCore');rock.layer=this.root.layer;this.root.addChild(rock);
   const renderer=rock.addComponent(MeshRenderer);renderer.mesh=SkillMeteorBody.mesh;renderer.setSharedMaterial(SkillMeteorBody.material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   comet.rock=rock;
  }
  if(comet.rock){
   comet.rock.active=true;comet.rock.setWorldPosition(comet.position);comet.rock.setScale(size*.46,size*.82,size*.44);
   Quat.fromAxisAngle(this.roll,new Vec3(0,1,0),rank*.43+(this.fire.reducedMotion?0:time*.18));Quat.multiply(this.rotation,this.alignment,this.roll);comet.rock.setWorldRotation(this.rotation);
  }
  this.fire.drawComet(key,comet.position,this.direction,size,time,255);
 }
 end(){for(const comet of this.comets)if(!comet.touched){comet.active=false;if(comet.rock)comet.rock.active=false;}}
 clear(){for(const comet of this.comets){comet.active=false;comet.touched=false;comet.key='';if(comet.rock)comet.rock.active=false;}}
 private bodyCentre(comet:Comet){const p=SkillMeteorBody.centreFromNose,centre=new Vec3(p.x*comet.size*.46,p.y*comet.size*.82,p.z*comet.size*.44);if(comet.rock)Vec3.transformQuat(centre,centre,comet.rock.worldRotation);return centre.add(comet.position);}
 inspect(){return{model:'reference-nose-anchored-comet-v32',capacity:4,sharedRockMeshes:SkillMeteorBody.mesh?1:0,sharedRockMaterials:SkillMeteorBody.material?1:0,leadingSupport:{x:SkillMeteorBody.leadingSupport.x,y:SkillMeteorBody.leadingSupport.y,z:SkillMeteorBody.leadingSupport.z},opaqueRockMeshes:this.comets.filter(c=>c.rock).length,active:this.comets.filter(c=>c.active).map(c=>({key:c.key,rockVisible:!!c.rock?.active,progress:c.progress,size:c.size,rockScale:{x:c.size*.46,y:c.size*.82,z:c.size*.44},target:{x:c.target.x,y:c.target.y,z:c.target.z},nose:{x:c.position.x,y:c.position.y,z:c.position.z},bodyCentre:this.bodyCentre(c),direction:{x:this.direction.x,y:this.direction.y,z:this.direction.z},position:{x:c.position.x,y:c.position.y,z:c.position.z}}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.root?.destroy();this.comets.length=0;}
}
