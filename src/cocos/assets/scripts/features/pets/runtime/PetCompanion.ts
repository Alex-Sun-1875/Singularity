import {Node,MeshRenderer} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {Point} from '../../../core/Contracts';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';

interface Motion {node:Node;kind:'leg'|'tail'|'wing';x:number;y:number;z:number;side:number}
/** Small native animal forms share scene meshes/materials. Final creature art
 * is reviewed separately. Closed content allocates no animal nodes. */
export class PetCompanion {
 private root:Node|undefined;
 private species='';
 private motion:Motion[]=[];
 private escort:PetCompanion|undefined;
 constructor(private world:SceneBuilder,private questOnly=false){}
 private part(name:string,kind:string,at:number[],scale:number[],color:string,rotation:number[]=[0,0,0]){
  const node=new Node('Pet:'+name);this.root!.addChild(node);node.setPosition(at[0],at[1],at[2]);node.setScale(scale[0],scale[1],scale[2]);node.setRotationFromEuler(rotation[0],rotation[1],rotation[2]);
  const renderer=node.addComponent(MeshRenderer);renderer.mesh=this.world.mesh(kind);renderer.setSharedMaterial(this.world.material('PetAnimal',color),0);return node;
 }
 private animate(node:Node,kind:Motion['kind'],rotation:number[]=[0,0,0],side=1){this.motion.push({node,kind,x:rotation[0],y:rotation[1],z:rotation[2],side});return node;}
 private eyes(x:number,y:number,z:number,size=.04){for(const side of [-1,1])this.part('eye','sphere',[side*x,y,z],[size,size*1.1,size*.7],'#262c2c');}
 private feet(x:number,y:number,z:number,width:number,height:number,color:string){for(const side of [-1,1])for(const front of [-1,1])this.animate(this.part('leg','sphere',[side*x,y,front*z],[width,height,width*1.35],color),'leg',[0,0,0],side*front);}
 private canid(style:'fox'|'dog'|'wolf'){
  const fox=style==='fox',dog=style==='dog',fur=fox?'#bd7144':dog?'#9c8465':'#8a918a',light=fox?'#e4d3ad':dog?'#d4c6a5':'#c4c8b9';
  this.part('canine-body','sphere',[0,.45,-.03],[fox?.48:.57,fox?.46:.55,fox?.77:.9],fur);this.feet(.19,.2,.27,.13,.39,'#645f53');
  this.part('head','sphere',[0,.77,.36],[.43,.39,.42],fur);this.part('muzzle','cone',[0,.66,.59],[.25,.34,.22],light,[-85,0,0]);this.part('nose','sphere',[0,.68,.76],[.11,.07,.07],'#353c3b');
  for(const side of [-1,1]){
   if(dog)this.part('floppy-ear','sphere',[side*.22,.76,.28],[.15,.4,.19],'#635e4f',[0,0,side*15]);
   else{this.part('pointed-ear','cone',[side*.15,1.01,.29],[.18,.32,.17],'#555d54');this.part('ear-inner','cone',[side*.15,1.01,.315],[.1,.19,.065],light);}
   if(!fox&&!dog)this.part('neck-ruff','cone',[side*.22,.59,.17],[.23,.4,.28],light,[0,0,side*-23]);
  }
  this.eyes(.13,.8,.52);
  const rotation=dog?[-28,0,0]:[-59,0,0],tail=this.part('bushy-tail','cone',[0,.51,-.59],[fox?.36:.25,fox?.81:.7,fox?.35:.24],fur,rotation);this.animate(tail,'tail',rotation);if(fox)this.part('pale-tail-tip','sphere',[0,.73,-.88],[.22,.24,.24],light);
  if(fox)this.root!.setScale(.98,.98,.98);
 }
 private turtle(){
  this.part('shell','sphere',[0,.4,0],[1.02,.69,1.08],'#6e7a6d');this.part('keel','box',[0,.65,0],[.22,.13,.66],'#b3b297');
  for(const side of [-1,1])for(const z of [-.25,.13])this.part('scute','sphere',[side*.22,.59,z],[.31,.18,.32],'#8d9582');
  this.feet(.4,.11,.31,.26,.22,'#9da27f');this.part('head','sphere',[0,.28,.64],[.35,.29,.36],'#c0bd95');this.eyes(.11,.33,.78);this.part('tail','cone',[0,.18,-.58],[.15,.31,.15],'#9da27f',[55,0,0]);
 }
 private rabbit(){
  this.part('round-body','sphere',[0,.37,-.05],[.58,.58,.7],'#d7d6c7');this.part('head','sphere',[0,.7,.24],[.44,.42,.42],'#e6e2d1');
  for(const side of [-1,1]){this.part('long-ear','sphere',[side*.12,1.04,.16],[.15,.59,.13],'#e0decc',[0,0,side*-10]);this.part('pink-ear','sphere',[side*.12,1.055,.22],[.07,.4,.035],'#bb9e91',[0,0,side*-10]);this.part('hind-leg','sphere',[side*.23,.18,-.19],[.25,.27,.39],'#c6cab9');this.part('forepaw','sphere',[side*.13,.12,.29],[.12,.2,.22],'#dcd8c6');}
  this.eyes(.14,.74,.39,.045);this.part('nose','sphere',[0,.64,.46],[.075,.055,.045],'#b69c8c');this.part('round-tail','sphere',[0,.38,-.42],[.22,.22,.22],'#ece8d9');
 }
 private feline(style:'cat'|'tiger'|'white'){
  const cat=style==='cat',white=style==='white',fur=cat?'#a49378':white?'#d6d8ce':'#ba8753',stripe=white?'#596669':'#5c5549';
  this.part('feline-body','sphere',[0,.47,-.02],[cat?.46:.64,cat?.46:.58,cat?.73:.96],fur);this.feet(cat?.17:.23,.2,cat?.24:.3,cat?.12:.18,cat?.37:.41,fur);
  this.part('head','sphere',[0,.78,.38],[cat?.4:.52,cat?.38:.46,.4],fur);this.part('muzzle','sphere',[0,.67,.59],[.3,.18,.19],white?'#ece9d9':'#d9c6a4');
  for(const side of [-1,1]){this.part('ear','cone',[side*.16,.99,.32],[.18,cat?.25:.16,.16],fur);this.part('ear-inner','cone',[side*.16,.99,.35],[.09,cat?.15:.09,.05],'#a98d7d');for(let i=0;i<3;i++)this.part('stripe','box',[side*(cat?.22:.3),.49+i*.04,.22-i*.24],[.045,.27,.07],stripe,[0,side*12,side*-20]);}
  this.eyes(.13,.82,.54,.045);this.part('nose','sphere',[0,.7,.685],[.095,.06,.045],'#645e55');
  this.animate(this.part('long-tail','cylinder',[0,.63,-.61],[.07,.77,.07],fur,[-35,0,0]),'tail',[-35,0,0]);this.part('tail-tip','sphere',[0,.94,-.84],[.1,.17,.1],stripe);
  if(cat)this.root!.setScale(.93,.93,.93);if(white){this.part('white-cheek','sphere',[0,.59,.47],[.49,.2,.24],'#e7e7da');this.root!.setScale(1.02,1.05,1.02);}
 }
 private hawk(){
  this.part('bird-body','sphere',[0,.6,0],[.4,.58,.52],'#8d9791');this.part('breast','sphere',[0,.57,.16],[.32,.42,.21],'#c7c9b7');this.part('head','sphere',[0,.9,.18],[.33,.32,.32],'#b5bdaf');this.part('beak','cone',[0,.84,.4],[.14,.23,.13],'#ae9b6c',[-90,0,0]);this.eyes(.11,.92,.3);
  for(const side of [-1,1]){this.animate(this.part('broad-wing','sphere',[side*.35,.66,-.08],[.72,.17,.48],'#66777a',[0,side*-30,side*18]),'wing',[0,side*-30,side*18],side);this.part('talon','cylinder',[side*.1,.23,.08],[.06,.25,.06],'#9f9473');}
  for(const side of [-1,0,1])this.part('tail-feather','box',[side*.09,.4,-.4],[.1,.07,.44],'#627478',[12,side*15,0]);
 }
 private deer(white:boolean){
  const fur=white?'#d9dacb':'#a88b64';this.part('deer-body','sphere',[0,.65,0],[.5,.48,.8],fur);this.feet(.18,.29,.25,.095,.59,white?'#b9c3b6':'#7f7e61');this.part('neck','sphere',[0,.94,.31],[.24,.61,.26],fur,[-18,0,0]);this.part('head','sphere',[0,1.23,.43],[.28,.31,.39],fur);this.eyes(.09,1.26,.57,.035);
  for(const side of [-1,1]){this.part('ear','sphere',[side*.17,1.34,.32],[.26,.1,.15],white?'#b9c5b6':'#b0a47f',[0,side*20,side*25]);this.part('antler','cylinder',[side*.12,1.52,.34],[.045,.4,.045],white?'#bfcbb9':'#af9e79',[0,0,side*-15]);this.part('antler-fork','cylinder',[side*.22,1.59,.34],[.035,.22,.035],white?'#d3d8bd':'#bdaf86',[0,0,side*-45]);if(white)this.part('antler-inner','cylinder',[side*.09,1.62,.32],[.025,.18,.025],'#c8d0b9',[0,0,side*28]);else for(let i=0;i<3;i++)this.part('fur-spot','sphere',[side*.23,.74,.22-i*.21],[.045,.045,.07],'#ddcfaa');}
  this.part('short-tail','sphere',[0,.77,-.43],[.14,.2,.2],white?'#e1e3d4':'#c2ad86');this.root!.setScale(.8,.8,.8);
 }
 private phoenix(){
  this.part('phoenix-body','sphere',[0,.61,-.04],[.43,.65,.62],'#b64e2f');this.part('golden-breast','sphere',[0,.63,.17],[.34,.46,.22],'#d99645');
  this.part('feather-neck','sphere',[0,.9,.18],[.25,.43,.28],'#c96b32');this.part('bird-head','sphere',[0,1.08,.27],[.3,.3,.31],'#db9b46');this.part('bird-beak','cone',[0,1.02,.49],[.13,.26,.12],'#c6aa61',[-80,0,0]);this.eyes(.09,1.11,.385,.035);
  for(const side of [-1,1]){
   const wingRotation=[0,side*-24,side*20];this.animate(this.part('phoenix-wing','sphere',[side*.4,.78,-.12],[.79,.17,.57],'#c26332',wingRotation),'wing',wingRotation,side);
   for(let i=0;i<3;i++){const rotation=[0,side*(-23-i*5),side*20];this.animate(this.part('golden-flight-feather','sphere',[side*(.52+i*.12),.72-i*.025,-.28-i*.06],[.15,.07,.5-i*.05],i===1?'#daa64c':'#c88339',rotation),'wing',rotation,side);}
   this.part('bird-talon','cylinder',[side*.1,.23,.04],[.045,.28,.045],'#9b7946');this.part('bird-foot','sphere',[side*.1,.095,.1],[.12,.055,.19],'#b18c4b');
  }
  for(let i=-1;i<=1;i++){
   this.part('crown-feather','cone',[i*.085,1.3-Math.abs(i)*.04,.2],[.075,.3-Math.abs(i)*.05,.09],i?'#cf8038':'#e0b45a',[0,0,-i*18]);
   const rotation=[-12,i*15,0];this.animate(this.part('long-tail-feather','sphere',[i*.16,.42,-.67-Math.abs(i)*.05],[.14,.085,1.03-Math.abs(i)*.11],i?'#cb7931':'#dda447',rotation),'tail',rotation,i||1);
  }
  this.root!.setScale(.86,.86,.86);
 }
 private dragon(){
  this.part('dragon-body','sphere',[0,.53,-.06],[.7,.69,.97],'#667e76');this.feet(.24,.21,.28,.19,.43,'#566c66');this.part('scaled-belly','sphere',[0,.46,.23],[.48,.44,.26],'#b6b79b');
  this.part('dragon-neck','sphere',[0,.91,.27],[.36,.66,.36],'#698478',[-12,0,0]);this.part('horned-head','sphere',[0,1.16,.42],[.47,.4,.49],'#789486');this.part('muzzle','sphere',[0,1.02,.69],[.36,.24,.36],'#91a58e');this.eyes(.15,1.2,.59,.045);
  for(const side of [-1,1]){this.part('horn','cone',[side*.16,1.43,.3],[.12,.36,.13],'#c5bc97',[0,0,side*-15]);this.animate(this.part('leathery-wing','cone',[side*.51,.93,-.15],[.71,.83,.12],'#8e9f84',[0,side*18,side*-46]),'wing',[0,side*18,side*-46],side);this.part('wing-bone','cylinder',[side*.42,1.04,-.13],[.045,.83,.045],'#647c70',[0,0,side*-48]);for(let i=0;i<3;i++)this.part('claw','cone',[side*.24+(i-1)*.055,.06,.43],[.04,.15,.04],'#c6bf9f',[-75,0,0]);}
  for(let i=0;i<4;i++){this.part('tapered-tail','sphere',[0,.38-i*.055,-.58-i*.19],[.36-i*.065,.3-i*.045,.4],'#6c8374');this.part('back-spine','cone',[0,.89-i*.09,-.2-i*.24],[.13,.21,.16],'#9d9c7c');}
  this.root!.setScale(.78,.78,.78);
 }
 private build(species:string){
  this.root?.destroy();this.motion=[];this.species=species;this.root=new Node((this.questOnly?'QuestCompanion:':'PetCompanion:')+species);this.world.root.addChild(this.root);
  switch(species){case'ember_fox':this.canid('fox');break;case'stone_turtle':this.turtle();break;case'dew_sprite':this.rabbit();break;case'tabby_cat':this.feline('cat');break;case'hunting_dog':this.canid('dog');break;case'grey_wolf':this.canid('wolf');break;case'mountain_tiger':this.feline('tiger');break;case'hunting_hawk':this.hawk();break;case'spotted_deer':this.deer(false);break;case'griffin':this.phoenix();break;case'white_tiger':this.feline('white');break;case'dragon':this.dragon();break;default:this.root.destroy();this.root=undefined;}
 }
 private present(species:string,at:Point,time:number,angle:number,moving=true){
  if(!this.root||this.species!==species)this.build(species);if(!this.root)return;
  this.root.active=true;const flying=species==='hunting_hawk'||species==='griffin',bob=flying?.1+Math.sin(time*2.6)*.025:Math.sin(time*4)*.006;
  this.root.setPosition(at.x,this.world.height(at)+bob,at.z);this.root.setRotationFromEuler(0,angle*180/Math.PI,0);
  for(const m of this.motion){const phase=Math.sin(time*(m.kind==='wing'?4:3))*m.side;m.node.setRotationFromEuler(m.x+(m.kind==='leg'&&moving?phase*7:0),m.y+(m.kind==='tail'?phase*7:0),m.z+(m.kind==='wing'?phase*8:0));}
 }
 update(game:GameSession,visible=true){
  if(!this.questOnly&&game.petJourneys)for(const [id,node]of this.world.propNodes)if(id.startsWith('petj:'))node.active=visible&&game.petJourneys.visibility(id);
  const s=game.state,quest=game.petJourneys?.escortView();
  if(!this.questOnly&&quest&&visible){if(!this.escort)this.escort=new PetCompanion(this.world,true);this.escort.present(quest.species,quest.at,s.time,s.player.angle,quest.walking);}else if(this.escort?.root)this.escort.root.active=false;
  const view=game.petCombatView();if(!view||!visible||quest?.species===view.profile.species){if(this.root)this.root.active=false;return;}
  this.present(view.profile.species,view.at,s.time,s.player.angle,!!s.player.movingTime);
 }
 destroy(){this.root?.destroy();this.root=undefined;this.motion=[];this.escort?.destroy();this.escort=undefined;}
}
