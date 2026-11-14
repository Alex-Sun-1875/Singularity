/** Local metre-space landforms for the 65 expanded campaign locations.
 * Existing first-chapter terrain remains owned by Terrain.ts's original tables.
 * Empty entries deliberately keep an inhabited floor or courtyard dry and level.
 */
export type CampaignRampSpec=[string,number,number,number,number,number];
export type CampaignWaterSpec=[string,number,number,number,number,'river'|'harbor'|'canal'|'pool'];
export type CampaignBridgeSpec=[string,number,number,number,number,'x'|'z','stone'|'wood'];
export type CampaignGorgeSpec=[string,number,number,number,number,number,'gorge'|'dry-moat'|'quarry',boolean];
export interface CampaignTerrainSpec {
 ramp?:CampaignRampSpec;waters?:CampaignWaterSpec[];bridges?:CampaignBridgeSpec[];gorges?:CampaignGorgeSpec[];
 note:string;
}
const rise=(id:string,height:number,x1=0,z1=-50,x2=0,z2=50):CampaignRampSpec=>[id,x1,z1,x2,z2,height];

export const CAMPAIGN_TERRAIN:Readonly<Record<string,CampaignTerrainSpec>>={
 H01:{ramp:rise('h01-mountain-road',2.4),note:'入山驿路为宽缓上坡，门前和返程口保持干燥。'},
 H02:{ramp:rise('h02-mining-town-terrace',2.2),note:'矿镇沿缓坡分层；街巷与研究台不增加水坑。'},
 H03:{ramp:rise('h03-workshop-court',2),note:'工匠院使用缓坡工作平台，镜架前保留完整地面。'},
 H04:{ramp:rise('h04-quarry-levels',3.6,-52,-48,52,-48),gorges:[['h04-east-extraction',44,-24,20,26,1.8,'quarry',true],['h04-west-extraction',-54,2,14,20,1.4,'quarry',true]],note:'双采面为有缓坡可走的干采坑，主通道和工作点均可绕行。'},
 H05:{ramp:rise('h05-mine-approach',3),note:'井架在高台，广坡提供地面与井口间的可走高差。'},
 H06:{ramp:rise('h06-shelter-street',2),note:'棚街顺山缓升，居住院面保持干净。'},
 H07:{ramp:rise('h07-stonebeam-ascent',3.2,-18,-50,-18,50),gorges:[['h07-dry-gorge',6,0,8,128,2.3,'gorge',false]],bridges:[['h07-natural-stonebeam',6,0,32,7,'x','stone']],note:'跨南北干峡谷的静态天然石梁，与H08剧情升降桥分开；桥头和各来路均可折返。'},
 H08:{ramp:rise('h08-front-fort-terrace',2.8),note:'仅塑造前堡高台，不添加绕过H08到H09机关条件的永久桥。'},
 H09:{ramp:rise('h09-armory-bank',2.2),note:'桥后武备岸是可原路返回的干燥高台，不新增跨区连接。'},
 H10:{ramp:rise('h10-ancient-mine-gate',3.4),note:'矿门与采掘设施沿宽岩坡展开。'},
 H11:{ramp:rise('h11-deed-court',2),note:'公署院落缓升，文书与交涉点保持完整干地。'},
 H12:{ramp:rise('h12-north-camp-terrace',2.6),note:'军寨高台有连续实体坡面。'},
 H13:{ramp:rise('h13-windworn-ridge',3.6,-52,0,52,0),note:'誓廊沿风蚀岩脊抬升，干涸石槽不添加蓝水。'},
 H14:{ramp:rise('h14-eagleback-rock-ridge',3.8,-52,0,52,0),note:'岩林有真实高低地面与宽缓接近坡。'},
 H15:{ramp:rise('h15-loading-cliff-approach',3.6),gorges:[['h15-dry-loading-cut',52,-27,20,32,2.8,'gorge',false]],note:'固定吊料台侧面是干崖切口；靠内侧的现有通路不被截断。'},
 H16:{ramp:rise('h16-southbound-descent',2.8,0,50,0,-50),note:'从来路沿宽缓坡下降到古道出口，保留折返。'},
 H17:{ramp:rise('h17-kiln-road',2.2),gorges:[['h17-dry-kiln-gully',44,-24,22,26,1.2,'quarry',true]],note:'窑沟是可走的浅干沟，沿干路通过。'},

 B01:{ramp:rise('b01-daylight-valley',2),gorges:[['b01-dry-valley-floor',35,-20,18,32,1.8,'dry-moat',true]],note:'见日出口接干旱谷地；这里不因属于河湾地区而加水。'},
 B02:{ramp:rise('b02-north-bank-road',1.4),waters:[['b02-river-margin',54,-24,24,32,'river']],note:'北岸河水位于未占用东南岸面，旧路和来回出口保持干地。'},
 B03:{ramp:rise('b03-ferry-town-bank',1.2),waters:[['b03-ferry-harbor',44,-25,26,28,'harbor']],bridges:[['b03-working-landing',44,-25,40,7,'x','wood']],note:'归帆镇有实际港水与木栈桥，鉴定屋和公共街面在干岸。'},
 B04:{note:'灯坊工作院保持干燥，反光壶与镜组不放进泛用水池。'},
 B05:{note:'旅店公共厅和后院保留完整干地，河湾由相邻岸区表达。'},
 B06:{ramp:rise('b06-market-bank',1),waters:[['b06-market-waterfront',54,-24,20,30,'harbor']],bridges:[['b06-cargo-landing',54,-24,34,7,'x','wood']],note:'装卸市集的水面和货栈在东南岸边，交涉街面保持干燥。'},
 B07:{ramp:rise('b07-bell-hill',3),note:'山岗有实际连续上堂坡，内外环路线保持连通。'},
 B08:{ramp:rise('b08-old-church-approach',1.4),note:'旧堂与E06干阶保持干燥，不把礼拜入口泛成水面。'},
 B09:{ramp:rise('b09-warehouse-bank',1),waters:[['b09-warehouse-side-canal',56,-17,10,44,'canal']],bridges:[['b09-inspection-crossing',56,-17,24,7,'x','wood']],note:'仓院侧渠与验货栈道相接，完好记录留在干岸。'},
 B10:{ramp:rise('b10-harbor-apron',1.2),waters:[['b10-storm-harbor',40,-26,24,32,'harbor']],bridges:[['b10-cargo-inspection-deck',19,-16,74,10,'x','wood']],note:'怒潮码头有港水和连接点验位置的同一长栈台，北侧战场及唯一B11出口不被水封。'},
 B11:{ramp:rise('b11-crane-bank',1.2),waters:[['b11-crane-basin',50,-20,20,34,'harbor']],bridges:[['b11-crane-working-deck',50,-20,34,8,'x','wood']],note:'吊臂旁为真实港池和固定工作台，跨图吊臂条件仍由原事件控制。'},
 B12:{ramp:rise('b12-dry-canal-bank',1.2),waters:[['b12-diversion-channel',40,-24,10,46,'canal']],bridges:[['b12-dry-channel-crossing',40,-22,26,7,'x','stone']],note:'分潮渠沿东侧工作带流过，中央干路与石跨渠面保证来回通行。'},
 B13:{ramp:rise('b13-reed-dry-bank',1),waters:[['b13-east-reed-pool',43,-25,24,26,'pool'],['b13-west-reed-pool',-50,-4,18,24,'pool']],note:'两个浅池之间保留宽干岸；拖钩棚、出生点和所有出口均不涉水。'},
 B14:{ramp:rise('b14-wreck-bank',1.2),waters:[['b14-wreck-waterfront',44,-24,28,32,'harbor']],bridges:[['b14-wreck-side-landing',44,-24,7,48,'z','wood']],note:'沉船岸水位于空余东南岸面，南北木栈道有两端干岸，不要求游泳。'},
 B15:{ramp:rise('b15-farm-dyke',1.2),waters:[['b15-old-irrigation-canal',52,-20,6,40,'canal']],bridges:[['b15-farm-stone-crossing',52,-20,20,6,'x','stone']],note:'农庄只补旧灌渠与石跨面，田埂和观察点留在陆上。'},
 B16:{ramp:rise('b16-old-ford-bank',1.2,-18,-50,-18,50),waters:[['b16-old-ford-river',5,-28,8,38,'river']],bridges:[['b16-natural-land-bridge',5,-22,26,8,'x','stone']],note:'古渡以真实陆桥跨过岸水，中央与两岸仍有可折返步道。'},
 B17:{ramp:rise('b17-cemetery-rise',1.4),note:'墓园与年代石室采用干燥旧石地，保留侧行路线。'},
 B18:{note:'宅院会客与账房维持干地，不添加无关机关水池。'},

 F01:{note:'外集与住屋保持完整干街面。'},
 F02:{ramp:rise('f02-workshop-street',.8),note:'居住长街有轻微街坡，家属交谈点保持可达。'},
 F03:{ramp:rise('f03-west-gate-approach',1.8),note:'西门以连续关前坡接到门楼。'},
 F04:{note:'扣押工坊的救援工位保持平整，不添加新的环境危险。'},
 F05:{ramp:rise('f05-old-camp-terrace',1.2),note:'旧营办公面和营后路沿缓台相接。'},
 F06:{note:'文书院与原刻证据地面保持干燥平整。'},
 F07:{ramp:rise('f07-warehouse-street',1),note:'接应街巷使用连续石坡，不放水封住出口。'},
 F08:{ramp:rise('f08-banner-plaza',1.4),note:'广场保持宽阔缓坡和多方向干燥接近面。'},
 F09:{ramp:rise('f09-west-wall-ascent',3.2),note:'西弩台有真正可步行的城墙上坡。'},
 F10:{ramp:rise('f10-east-wall-ascent',3.2),note:'东弩台独立抬升，来路和回路均连续。'},
 F11:{ramp:rise('f11-wall-gallery-ascent',3.8),note:'墙路连廊有真实高度，侧龛与休整庭仍可步行连接。'},
 F12:{ramp:rise('f12-rest-court-approach',1.4),note:'门外整备庭为可折返的干燥缓台，不提前打开决战条件。'},
 F13:{ramp:rise('f13-inner-court',2),note:'决战庭保持宽缓完整石地，已有掩体和退出条件不变。'},
 F14:{note:'同平台军械领奖与侧格保持干燥平整。'},
 F15:{note:'档案楼阅卷与回访地面保持平整。'},
 F16:{ramp:rise('f16-moat-exit-ramp',2.4),gorges:[['f16-drained-moat',8,-10,44,22,2,'dry-moat',true]],note:'干涸护城壕为可沿缓坡进出的真实干沟，不加蓝水或通内堡捷径。'},
 F17:{ramp:rise('f17-maintenance-slope',3.4),note:'检修坡提供实在高差和可折返的正侧两面。'},

 'U1-06':{ramp:rise('u106-armory-gallery-levels',2),note:'军械廊以宽缓台分层，机关旁路不增战斗门槛。'},
 'U1-07':{note:'冷白工坊保留平整工作地面，不改为熔岩或水牢。'},
 'U1-08':{note:'天火核心与迁行口保留干燥生命空间，不加熔岩池。'},
 'U1-09':{ramp:rise('u109-winch-approach',3),gorges:[['u109-dry-winch-shaft',52,-25,18,32,3,'gorge',false]],note:'绞盘井侧面为干井切口，E05及现有北侧通道保留可达。'},
 'U1-10':{ramp:rise('u110-daylight-approach',2.4),note:'见日长廊以连续上坡接干燥出口，E07仍从内侧开启。'},
 'U2-02':{ramp:rise('u202-dry-channel-levels',1.2),waters:[['u202-receded-stone-canal',40,-23,10,46,'canal']],bridges:[['u202-dry-stone-crossing',40,-22,26,7,'x','stone']],note:'退水侧渠与宽干路并行，镜眼接近面不要求涉水。'},
 'U2-03':{ramp:rise('u203-sluice-court',1.2),waters:[['u203-pressure-channel',44,-24,14,40,'canal']],bridges:[['u203-control-crossing',44,-22,30,8,'x','stone']],note:'闸室广场以侧渠表现水压，内侧泄压位和原出口保持干燥。'},
 'U2-04':{note:'守库人旧居保留居住干地，退出协议不放进新水池。'},
 'U2-05':{ramp:rise('u205-church-dry-steps',1.2),waters:[['u205-outer-stone-channel',54,-21,8,42,'canal']],bridges:[['u205-side-room-crossing',54,-21,22,6,'x','stone']],note:'下殿外侧旧渠有石跨面，E06与侧室入口始终在干阶。'},
 'U2-06':{note:'原刻档案与侧光拓本室保持干燥可达。'},
 'U2-07':{ramp:rise('u207-library-court',1.2),waters:[['u207-old-ritual-basin',49,-24,18,28,'canal']],bridges:[['u207-side-gallery-crossing',49,-24,32,7,'x','stone']],note:'祭仪库侧渠有干燥石跨面，迁行图与双侧廊不被水截断。'},
 'U2-08':{note:'旧囚室保留干地与封门证据，不额外添加突袭水牢。'},
 'U2-09':{ramp:rise('u209-maintenance-bank',1.2),waters:[['u209-outwork-service-canal',52,-23,8,40,'canal']],bridges:[['u209-service-stone-crossing',52,-23,24,6,'x','stone']],note:'堡外检修渠位于侧面，E08只接干壕，原图条件保持。'},
};
