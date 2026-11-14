import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,Material,Mesh,MeshRenderer,Node,Texture2D,Vec3,gfx,primitives,utils} from 'cc';
import type {SceneBuilder} from './SceneBuilder';
import {FlatWorldLayers} from './FlatWorldLayers';
import {PortalPresentation} from '../../portals/runtime/PortalPresentation';
import type {GameSession} from '../../../core/GameSession';

/** Reversible map-image presentation over the existing metre-based X/Z world.
 * Construct immediately after SceneBuilder, before adding Actors or Effects:
 * only the environment renderers present at construction are hidden. Nodes,
 * physics colliders, navigation, world.height and camera controls stay live.
 *
 * The image covers [-width/2,+width/2] x [-depth/2,+depth/2]. Native plane UVs
 * put u=0 at west (-X), v=0 at north (+Z); the artwork must use that layout.
 * This does not align arbitrary illustrated obstacles to logical colliders.
 */
export class FlatWorldPresentation {
 private readonly previousRenderers = new Map<MeshRenderer,boolean>();
 private node:Node|null=null;
 private mesh:Mesh|null=null;
 private material:Material|null=null;
 private texture:Texture2D|null=null;
 private resourcePath='';
 private revision=0;
 private disposed=false;
 private layers:FlatWorldLayers|null=null;
 private portals:PortalPresentation|null=null;

 constructor(private readonly world:SceneBuilder,private camera:Camera){
  for(const renderer of world.root.getComponentsInChildren(MeshRenderer))this.previousRenderers.set(renderer,renderer.enabled);
 }

 async build(backgroundResourcePath?:string):Promise<void>{
  if(this.disposed)throw new Error('Flat world presentation has been destroyed');
  if(!backgroundResourcePath&&this.world.area.id!=='S01-T1'){
   this.layers??=new FlatWorldLayers(this.world,this.camera);await Promise.all([this.layers.build(),this.buildPortals()]);return;
  }
  backgroundResourcePath??='flat2d/maps/inn-readable-v4';
  const request=++this.revision;
  const path=backgroundResourcePath.replace(/\\/g,'/').replace(/\.(?:png|webp|jpe?g)$/i,'').replace(/\/texture$/,'')+'/texture';
  const texture=await new Promise<Texture2D>((resolve,reject)=>this.world.loadAsset(path,Texture2D,(error,asset)=>{
   if(error)reject(new Error('Flat world background '+path+': '+error.message));else resolve(asset);
  }));
  if(this.disposed||request!==this.revision||!this.world.root.isValid)return;

  if(!this.node){
   const {width,depth}=this.world.area;
   // The engine owns tessellation and UV generation. Sampling the unchanged
   // walk surface also supports existing ramps; interiors remain a flat XZ map.
   const geometry=primitives.plane({width,length:depth,widthSegments:Math.max(1,Math.min(64,Math.ceil(width/4))),lengthSegments:Math.max(1,Math.min(64,Math.ceil(depth/4)))});
   let low=Infinity,high=-Infinity;
   for(let i=0;i<geometry.positions.length;i+=3){
    const y=this.world.height({x:geometry.positions[i],z:geometry.positions[i+2]})-.025;
    geometry.positions[i+1]=y;low=Math.min(low,y);high=Math.max(high,y);
   }
   geometry.minPos=new Vec3(-width/2,low,-depth/2);geometry.maxPos=new Vec3(width/2,high,depth/2);
   geometry.boundingRadius=Math.hypot(width/2,Math.max(Math.abs(low),Math.abs(high)),depth/2);
   this.mesh=utils.createMesh(geometry);
   this.material=new Material();this.material.name='FlatWorldMap-Unlit';
   this.material.initialize({effectName:'builtin-unlit',defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE}}});
   this.material.setProperty('mainColor',Color.WHITE);
   this.node=new Node('FlatWorldMap');this.node.layer=this.world.root.layer;this.world.root.addChild(this.node);
   const renderer=this.node.addComponent(MeshRenderer);renderer.mesh=this.mesh;renderer.setSharedMaterial(this.material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  }
  if(this.texture!==texture){texture.addRef();this.texture?.decRef();this.texture=texture;}
  this.material!.setProperty('mainTexture',texture);
  // Keep the busy inn floor below the actor's cloth/skin values. Local lamp
  // colors remain in the map; this does not tint the actor or the HUD.
  this.material!.setProperty('mainColor',path.includes('/inn-readable-v4/')?new Color(205,210,215):Color.WHITE);this.resourcePath=path;
  // Disable components rather than nodes: SceneBuilder's collision/aim rays
  // still hit the original geometry and all saved logic coordinates are intact.
  for(const renderer of this.previousRenderers.keys())if(renderer.isValid)renderer.enabled=false;
  await this.buildPortals();
 }

 private async buildPortals():Promise<void>{
  if(this.disposed||!this.world.root.isValid)return;
  this.portals??=new PortalPresentation(this.world,this.camera);await this.portals.build();
 }

 /** Background coordinates do not follow the camera; the original orthographic
  * camera may pan/zoom/aim exactly as before. No per-frame geometry is rebuilt. */
 update(camera?:Camera,game?:GameSession):void {if(camera)this.camera=camera;this.layers?.update(camera);this.portals?.update(camera,game);}

 inspect(){
  if(this.layers)return {...this.layers.inspect(),portals:this.portals?.inspect()};
  return {mode:'flat-world-image',ready:!!this.node?.isValid&&!this.disposed,resource:this.resourcePath,
   area:this.world.area.id,width:this.world.area.width,depth:this.world.area.depth,
   hiddenEnvironmentRenderers:Array.from(this.previousRenderers.keys()).filter(r=>r.isValid&&!r.enabled).length,
   originalVolumeRenderersVisible:Array.from(this.previousRenderers.keys()).filter(r=>r.isValid&&r.enabled).length,
   retainedTexturedWalkSurfaces:0,paintedCutouts:0,unmappedSourceKeys:[] as string[],
   cameraProjection:this.camera.projection,coordinateFrame:'+X east / +Z north; native plane UV0; original world.height',portals:this.portals?.inspect()};
 }

 destroy():void {
  if(this.disposed)return;this.disposed=true;this.revision++;
  this.portals?.destroy();this.portals=null;
  this.layers?.destroy();this.layers=null;
  if(this.node?.isValid){this.node.active=false;this.node.destroy();}
  for(const [renderer,enabled]of this.previousRenderers)if(renderer.isValid)renderer.enabled=enabled;
  this.previousRenderers.clear();this.mesh?.destroy();this.material?.destroy();this.texture?.decRef();
  this.node=null;this.mesh=null;this.material=null;this.texture=null;
 }
}
