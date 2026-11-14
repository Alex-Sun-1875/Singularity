import type {SkillId} from '../common/SkillChecks';
export interface SkillCheckDefinition {id:string;area:string;sourceId:string;skill:SkillId;dc:number;title:string;prompt:string;successText:string;failureText:string}
export const SKILL_CHECKS:Record<string,SkillCheckDefinition>={
 'mira-motive':{id:'mira-motive',area:'S01-T1',sourceId:'t1-mira',skill:'insight',dc:12,title:'她收起信时的停顿',prompt:'留意纸袋的折痕、指节上的旧墨，以及她听见信使姓名时的反应。',successText:'旧墨与求援日期吻合。你抓住一处可核对的细节，接下来对证时可以从两次掷骰中择高。',failureText:'她收起了纸袋，细节没有拼成完整线索。接下来对证时局势不利；也可以按原约接约，或去寻找抄件。'},
 'mira-terms':{id:'mira-terms',area:'S01-T1',sourceId:'t1-mira',skill:'persuasion',dc:14,title:'抄件与附约之间',prompt:'把信使绕路的时间与契约落款并排核对，找出没有被写进正文的那一页。',successText:'两处日期无法同时成立。弥菈补出信使的绕路与附页，你记录独立线索，获得1点余烬。预支仍按原约结算。',failureText:'现有记录还不能相互印证。你可以先按原约行动，也可以拒约后继续独立调查。'},
 'inn-lockbox':{id:'inn-lockbox',area:'S01-T1',sourceId:'t1-lockbox',skill:'sleight',dc:13,title:'遗落在旅店的铜簧匣',prompt:'旧铜锁只有一道弯簧。试着沿磨损方向把锁舌拨回去，取出无人认领的旅费。',successText:'锁舌退开。匣中有12金币与2块可回收废铁，补给仅可领取一次。',failureText:'弯簧卡进锁槽，今天无法再徒手开启。你没有失去关键物品，也不影响与弥菈谈委托。'},
 'grave-record':{id:'grave-record',area:'S03',sourceId:'s03-dated-grave',skill:'investigation',dc:11,title:'空墓上的第二层刻痕',prompt:'比对“阵亡”日期与工役锤痕：这块石碑究竟在纪念死者，还是替活人结案？',successText:'日期被后刻过。工役锤痕证明有人在“阵亡”后仍在地下做工。你记录独立线索，之后核对弥菈的细节时可两骰择高，并获得1点余烬。',failureText:'风化石屑遮住了旧日期，你无法下定论。附近目击记录、信使副本与其他调查道路仍然可用。'},
 'quarry-runes':{id:'quarry-runes',area:'S13',sourceId:'s13-sequence-runes',skill:'investigation',dc:13,title:'三短一长的检修记号',prompt:'把新锤痕与废料标记排成顺序，找出下城诱片的检修规律。',successText:'你读出拆片顺序。获得2块废铁、1点余烬；之后拆除下城诱片时可两骰择高。',failureText:'几处刮痕彼此矛盾，检修顺序仍不清楚。固定梯和采掘廊入口保持可通行。'},
 'undercity-disarm':{id:'undercity-disarm',area:'U1-05',sourceId:'u105-precision-disarm',skill:'sleight',dc:14,title:'逆转诱片的连动锁',prompt:'从检修口逆转锁片，让扣押间的连动失效。失败会消耗20专注，仍可另走侧廊或处理守军。',successText:'锁片安静地落下。诱片失效，救援退路已经准备好；专注恢复20，获得1点余烬。',failureText:'锁片弹回，尖锐的震动打乱了呼吸：专注−20。仍可从旁边检修侧廊拆除诱片，或击败守军释放工匠。'},
};
export const INSPIRATION_SOURCES=['read-letter','ask-truth','release-workers','captain',...Object.keys(SKILL_CHECKS).map(id=>'check:'+id)];
