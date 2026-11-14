import type {AreaDef,Building,EnemySpawn,ExitDef,InteractionDef,Point} from '../../../core/Contracts';
import {CAMPAIGN_BOSSES,CAMPAIGN_ENEMY_TEMPLATES,CAMPAIGN_LEVEL_LIST,type CampaignLevelDef} from '../../campaign/data/Campaign';
import {CAMPAIGN_ATLAS,CAMPAIGN_ROADS} from './CampaignGeography';
import {CAMPAIGN_EVENT_LIST} from '../../campaign/data/CampaignEvents';

const p=(x:number,z:number):Point=>({x,z});
/** Landmarks are authored by location; collision/roads reuse the existing scene loader. */
const LANDMARKS:Record<string,string[]>={
 H01:['山驿客舍','伤者歇脚棚','东境路碑'],H02:['岩炉镇街屋','瑟维恩研究室','征工告示院'],
 H03:['熔镜工位','镜架控制房','散热回退台'],H04:['西采面支护棚','东采面矿车场','双裂坡道'],
 H05:['封炉机房','上层绞盘井架','停机安全亭'],H06:['伤工住棚','证词登记屋','共用食棚'],
 H07:['石梁警戒屋','近桥掩车棚','旧技能石柜'],H08:['前堡值房','近岸绞盘房','桥头守军棚'],
 H09:['桥后武备台','破阵军械棚','返桥整备亭'],H10:['巨岩矿门','旧迁行记录室','采掘机支护房'],
 H11:['铁契公署','征用文书室','侧院门房'],H12:['北岗军帐','押运办公棚','号令岗亭'],
 H13:['风蚀誓廊','钟晶校准室','干涸石槽'],H14:['鹰背猎契屋','岩林警戒亭','缴契台'],
 H15:['天索机台','吊料遮棚','固定平台工房'],H16:['山南旧驿','下降山路亭','北岸路碑'],H17:['余烬窑室','转运账棚','窑沟旧工房'],
 B01:['采光出口门','旱谷路亭','撤离歇脚棚'],B02:['北岸巡路屋','旧墙岗亭','风道路碑'],
 B03:['归帆票号','艾莉丝鉴定屋','河埠镇住屋'],B04:['余烬灯坊','反光壶暗室','炭纹存放屋'],
 B05:['河湾旅店','猎径会面室','旅店后院'],B06:['风帆货棚','装载清单室','拒收登记亭'],
 B07:['山岗钟基','外环警戒屋','上堂干路亭'],B08:['沉钟旧堂','退出协议侧室','礼拜下层阶门'],
 B09:['黑签封存仓','伪签账房','侧檐验货亭'],B10:['怒潮装卸棚','同台校光台','封匣复秤房'],
 B11:['天钩吊臂房','固定卡位棚','接近桥门亭'],B12:['分潮泵房','干渠接应亭','水渠旧仓'],
 B13:['芦苇拖钩棚','干石坡屋','迷湾望亭'],B14:['沉船船腹','打捞王封锁棚','甲板侧梯房'],
 B15:['南岸农舍','古兽观察棚','旧渠路碑'],B16:['东岸古渡房','陆桥岗亭','城域旧驿'],
 B17:['旧誓墓堂','封炉年代石室','钟摆检修亭'],B18:['双契主宅','付款凭据账房','侧门会面亭'],
 F01:['外集住屋','征工车棚','城防令告示亭'],F02:['流火街工坊','工匠家属住屋','接应院门'],
 F03:['黑冠西门楼','通行登记房','西门侧岗'],F04:['铁锁工位','备用镜组室','检修安全房'],
 F05:['黑旗兵棚','旧营办公间','营后见证室'],F06:['黑印文书院','征掘令正本室','侧道读刻亭'],
 F07:['东仓旧库','暗街接应屋','实走出口亭'],F08:['铁旗岗楼','警戒镜棚','盾阵值房'],
 F09:['西境弩台机房','西台值守棚','固定销安全亭'],F10:['东境弩台机房','东台值守棚','拆机安全亭'],
 F11:['凌城连廊','天穹侧龛','墙路岗房'],F12:['决战整备亭','双台核验室','返回外城门房'],
 F13:['黑冠号令台','内弩口机房','决战庭卫房'],F14:['黑冠军械主库','同侧绞盘房','终誓侧格室'],
 F15:['黑冠档案楼','现行征令室','回访阅卷房'],F16:['干壕检修门','外城坡亭','旧渠检修屋'],F17:['铁棘扣押房','检修侧箱棚','坡上约谈亭'],
 'U1-06':['三誓陈列厅','第三剑控制位','封闭工位室'],'U1-07':['震炉主工房','冷白炉槽','安全泄压室'],
 'U1-08':['天火接触台','迁行口隔离房','静眠回退亭'],'U1-09':['悬链机台','绞盘井底房','平台控制室'],
 'U1-10':['见日出口门','采光长廊屋','撤离回退亭'],
 'U2-02':['退水干渠房','镜眼警戒室','分层泵管亭'],'U2-03':['深闸镇守台','内侧泄压室','前厅回退房'],
 'U2-04':['守库人居所','退出协议室','静思图纸房'],'U2-05':['沉钟下殿','钟纹侧室','旧堂干阶亭'],
 'U2-06':['正面原刻廊','侧光拓本室','征用侧档房'],'U2-07':['禁域镜阵厅','迁行图藏室','静眠图侧廊'],
 'U2-08':['无名囚室旧址','旧封门值房','责任记录室'],'U2-09':['堡外检修机房','内侧旧门室','干壕退路亭'],
};
function landmark(name:string,i:number):Building {
 const places=[[-38,29],[38,29],[-38,-27],[38,-27]],at=places[i%4];
 const style:Building['style']=/门|岗|堡/.test(name)?'gate':/棚|帐/.test(name)?'tent':/工|机|泵|镜|绞|炉/.test(name)?'workshop':/库|仓|军械/.test(name)?'barn':/廊|殿|龛|墓/.test(name)?'ruin':'house';
 return {name,style,x:at[0],z:at[1],width:20,depth:16,height:style==='gate'?9:style==='tent'?5:7};
}
function createArea(def:CampaignLevelDef):AreaDef {
 const underground=def.region[0]==='U',safe=def.encounter==='无';
 const kind:AreaDef['kind']=underground?'underground':/镇|街|市集|外集|旅店|农庄|工匠院/.test(def.name)?'town':/营|堡|公署|文书/.test(def.name)?'camp':/廊|堂|墓|旧|档案/.test(def.name)?'ruin':'wild';
 const palette:AreaDef['palette']=underground?def.id==='U1-08'?'warm':'cave':def.region==='R2'?'stone':def.region==='R3'?'marsh':def.region==='R4'?'stone':'forest';
 const buildings=(LANDMARKS[def.id]??[`${def.name}值房`,`${def.name}侧屋`]).map(landmark);
 const objects:InteractionDef[]=[{id:`campaign-clue-${def.id}`,label:`观察 · ${def.name}的现场`,action:'inspect',evidence:`campaign-clue-${def.id}`,x:-38,z:17,radius:2.5,description:`${def.objective}。现场的${buildings[0].name}与${buildings[1].name}由能原路折返的道路相连；记录只根据实际观察保存。`}];
 if(safe)objects.push({id:`campaign-cp-${def.id}`,label:'安全整备与保存',action:'checkpoint',x:0,z:-40,radius:2.5,description:`${def.name}的来路留有安全整备面，可以保存与整理装备；已经领取的物资、敌人和机关保持原来的世界记录。`});
 return {id:def.id,name:def.name,subtitle:def.objective,kind,palette,width:144,depth:128,spawn:p(0,-40),atlas:CAMPAIGN_ATLAS[def.id]??p(50,50),exits:[],objects,buildings,enemies:[],obstacles:buildings.map(building=>({...building,kind:'building'})),checkpoint:safe,recommendedLevel:def.encounterLevel,campaignRegion:def.region};
}
const enemyKind=(id:string):EnemySpawn['kind']=>{
 if(id.startsWith('BOSS_')||id.startsWith('ELITE_'))return 'captain';
 const role=CAMPAIGN_ENEMY_TEMPLATES[id]?.role??'';
 return /远程|控场|法术|支援/.test(role)?'archer':/盾|重击|重护|护卫/.test(role)?'shield':'raider';
};
function authoredEnemies(def:CampaignLevelDef,previous:EnemySpawn[]):EnemySpawn[] {
 const encounter=def.encounter.split('（')[0],templates:Array<string>=[];
 for(const match of encounter.matchAll(/(BOSS_[RU]\d|ELITE_\d\d|[RU]\d-\d)(?:×(\d+))?/g))for(let i=0;i<Number(match[2]??1);i++)templates.push(match[1]);
 const used=new Set<number>();
 const spots=[p(0,15),p(-13,17),p(14,19),p(-20,3),p(20,4),p(-6,28),p(8,31)];
 return templates.map((templateId,i)=>{
  const kind=enemyKind(templateId),match=previous.findIndex((enemy,index)=>!used.has(index)&&enemy.kind===kind);
  if(match>=0)used.add(match);
  const retained=match>=0?previous[match]:undefined,template=CAMPAIGN_ENEMY_TEMPLATES[templateId];
  return {...(retained??{id:`campaign-${def.id}-${templateId}-${i+1}`,kind,...spots[i%spots.length]}),kind,templateId,contentId:templateId,level:template.level??def.encounterLevel,...(template.arena?{bossId:templateId,hp:template.hp}:{})};
 });
}
type Side='north'|'south'|'east'|'west';
function side(from:AreaDef,to:AreaDef):Side {const dx=to.atlas.x-from.atlas.x,dz=to.atlas.z-from.atlas.z;return Math.abs(dx)>Math.abs(dz)?dx>0?'east':'west':dz>0?'north':'south';}
function border(area:AreaDef,direction:Side,along:number,inset:number):Point {return direction==='east'?p(area.width/2-inset,along):direction==='west'?p(-area.width/2+inset,along):direction==='north'?p(along,area.depth/2-inset):p(along,-area.depth/2+inset);}
function vacantPort(area:AreaDef,toward:AreaDef):{at:Point;entry:Point} {
 const direction=side(area,toward),length=direction==='east'||direction==='west'?area.depth:area.width;
 const choices=[0,-20,20,-40,40,-55,55].filter(n=>Math.abs(n)<length/2-6);
 const along=choices.find(n=>{const q=border(area,direction,n,2);return area.exits.every(exit=>Math.hypot(q.x-exit.x,q.z-exit.z)>7);})??0;
 return {at:border(area,direction,along,2),entry:border(area,direction,along,6)};
}
function road(areas:Record<string,AreaDef>,a:string,b:string,requirement?:string):void {
 if(areas[a].exits.some(exit=>exit.to===b))return;
 const ap=vacantPort(areas[a],areas[b]),bp=vacantPort(areas[b],areas[a]);
 areas[a].exits.push({id:`campaign-road-${a}-${b}`,to:b,label:`沿道路前往${areas[b].name}`,...ap.at,entry:bp.entry,...(requirement?{requires:requirement}:{})});
 areas[b].exits.push({id:`campaign-road-${b}-${a}`,to:a,label:`沿原路返回${areas[a].name}`,...bp.at,entry:ap.entry,...(requirement?{requires:requirement}:{})});
}
function port(areas:Record<string,AreaDef>,a:string,b:string,id:string,flag?:string,openAtFirstSide=false):void {
 const ap=vacantPort(areas[a],areas[b]),bp=vacantPort(areas[b],areas[a]);
 const gate=(from:string,to:string,at:Point,entry:Point,first:boolean):ExitDef=>({id:`${id}-${from}`,to,label:`${id} · ${first?'由本侧开启，':'沿已开通道'}前往${areas[to].name}`,...at,entry,...(flag?first&&openAtFirstSide?{unlock:flag}:{requires:flag}:{})});
 areas[a].exits.push(gate(a,b,ap.at,bp.entry,true));areas[b].exits.push(gate(b,a,bp.at,ap.entry,false));
}
const FIXED_FINDS:[string,string,string,string][]=[
 ['B04','J01','炭纹小匣','反光壶旁的炭纹小匣保存余烬之心；校光记录与这件独立装备分别记账。'],
 ['B08','W12','旧堂侧龛','礼拜干阶旁的旧堂侧龛保存灰烬祷文；不要求接受阿德里安的条件。'],
 ['B08','A03','灯座暗格','旧堂灯座背面的暗格保存烛灰冠冕，与旁边的法杖是两个固定发现。'],
 ['H13','J02','干涸石槽','钟晶校准室外的干涸石槽保存冬湖之眼；保留原物的唯一领取记录。'],
 ['F11','W14','天穹侧龛','墙路的可选侧龛保存天穹的裂隙；不领取仍能沿实体连廊前往整备庭。'],
 ['U2-07','A15','碑文暗格','迁行原图旁的碑文暗格保存无声仪式；地图与装备是独立记录，不要求战斗。'],
 ['F17','J07','检修侧箱','检修坡的侧箱保存双生契约；军械主箱只会补漏同一个永久物品。'],
];

export function installCampaign(areas:Record<string,AreaDef>):void {
 for(const def of CAMPAIGN_LEVEL_LIST){
  const current=areas[def.id]??(areas[def.id]=createArea(def));
  current.name=def.name;current.recommendedLevel=def.encounterLevel;current.campaignRegion=def.region;
  current.objects=current.objects.filter(object=>object.action!=='boundary'&&!object.item?.startsWith('T'));
  current.enemies=authoredEnemies(def,current.enemies);
 }
 // The current catalog moved the old soldier bag to the abandoned supply post.
 const oldBag=areas.S09.objects.find(object=>object.item==='A09');
 if(oldBag){areas.S09.objects=areas.S09.objects.filter(object=>object!==oldBag);areas.S18.objects.push({...oldBag,x:29,z:-15,description:'残旗军需站的旧兵袋保存老兵的回敬；袋上的维修针脚与被划掉的配给姓名可以交叉核对，永久物只领一次。'});}
 // The first act's conclusion is a recap, while the later regions remain walkable.
 const finish=areas['U1-04'].objects.find(object=>object.action==='finish');
 if(finish){finish.label='核对撤离与扣押令，记录第一幕';finish.description='确认工匠实际撤离、扣押令与星片分别结算，再沿矿道或东境山路深入调查。第一幕记录不会结束整段旅程。';}
 for(const edge of CAMPAIGN_ROADS){
  const key=[edge.a,edge.b].sort().join('|');
  const require:Record<string,string>={'H08|H09':'m4_bridge_open','B10|B11':'harbor_access','F12|F13':'final_ready','F13|F14':'boss_defeated:BOSS_R4','U2-01|U2-02':'u2_deep_gate_open'};
  road(areas,edge.a,edge.b,require[key]);
 }
 road(areas,'S16','H01');road(areas,'H16','B02');road(areas,'S15','B15');road(areas,'B16','F01');
 port(areas,'H05','U1-09','E05','e05_open');
 port(areas,'B08','U2-05','E06');
 port(areas,'U1-10','B01','E07','e07_open');
 port(areas,'U2-09','F16','E08','e08_open');
 for(const def of CAMPAIGN_EVENT_LIST){
  const current=areas[def.area],index=current.objects.filter(object=>object.action==='campaign_event').length;
  const positions=[p(-15,-16),p(15,-16),p(-15,0),p(15,0),p(-20,-32),p(20,-32)];
  const existing=def.actor?current.objects.find(o=>o.actor===def.actor):undefined;
  current.objects.push({id:`event-${def.id}`,eventId:def.id,label:def.label,action:'campaign_event',description:def.description,...existing?{x:existing.x,z:existing.z}:def.at??positions[index%positions.length],actor:existing?undefined:def.actor,npcId:def.actor,actorModel:def.actorModel,radius:2.5});
 }
 for(const [area,item,label,description] of FIXED_FINDS)areas[area].objects.push({id:`campaign-find-${item}`,label,description,item,amount:1,action:'cache',x:38,z:17,radius:2.5});
 // Their dedicated character images are still pending. A named in-world
 // workstation keeps their account and interaction usable without loading an
 // absent actor or borrowing another person's character identity.
 areas.H02.objects.push({id:'h02-severin',label:'瑟维恩研究台：沉钟之泪',action:'merchant',merchant:'severin',description:'瑟维恩的研究台上保留现代拓本与货单，可以在现场核对研究商货。沉钟之泪只有一件，不会因回访补货。',x:38,z:17,radius:2.5});
 areas.B03.objects.push({id:'b03-elise',label:'艾莉丝鉴定台：灰烬礼袍',action:'merchant',merchant:'elise',description:'艾莉丝的鉴定台上摊开完好的旧绳货号与封签。灰烬司祭礼袍只有一件，完成现场鉴定不要求购买。',x:38,z:17,radius:2.5});
 // The expanded source budget needs a real clear firing floor in every boss scene.
 for(const boss of CAMPAIGN_BOSSES){
  const current=areas[boss.arena!];
  for(const building of current.buildings)if(Math.abs(building.x)-building.width/2<19&&Math.abs(building.z-15)-building.depth/2<14){
   const collision=current.obstacles.find(obstacle=>obstacle.kind==='building'&&obstacle.x===building.x&&obstacle.z===building.z);
   building.x=(building.x<0?-1:1)*(20+building.width/2);if(collision)collision.x=building.x;
  }
  current.obstacles=current.obstacles.filter(obstacle=>obstacle.kind!=='pillar'&&(obstacle.kind==='building'||Math.abs(obstacle.x)-obstacle.width/2>=19||Math.abs(obstacle.z-15)-obstacle.depth/2>=14));
  current.obstacles.push({kind:'pillar',x:-11,z:12,width:1.4,depth:1.4,height:2.2},{kind:'pillar',x:11,z:12,width:1.4,depth:1.4,height:2.2});
 }
}
