import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'map.title':'旅途地图','map.region':'区域地图','map.world':'世界地图','map.local':'现场地图','map.regions':'切换区域',
 'map.legend':'图例','map.locate':'定位','map.fit':'全览','map.unknown':'黑暗处尚未探索','map.loading':'正在展开地图…','map.failed':'地图载入失败，请返回后重试。',
 'map.compactWaypoints':'传送点','map.compactTravel':'传送','map.compactEmpty':'尚未发现传送点','map.controls':'地图模式','map.gesture':'拖动地图 · 滚轮缩放','map.details':'任务',
 'legend.merchant':'商人','legend.rest':'休整点','legend.people':'人物',
 'map.waypoints':'传送阵','map.unlocked':'已解锁 · {count} 处','map.empty':'尚未发现传送阵\n亲自抵达安全整备点后解锁。',
 'map.direct':'无需返回传送阵','map.travel':'传送至{name}','map.select':'选择传送阵','map.busy':'正在传送…','map.retry':'传送失败，请重试','map.failure':'传送失败，已保留原位置。请重试。','map.arrived':'已抵达{name}',
 'map.current':'队伍所在区域','map.here':'已在传送阵旁','map.discovered':'已探索地点','map.notUnlocked':'传送阵尚未解锁','map.unavailable':'目的地暂不可用',
 'map.dead':'倒下时无法传送','map.submitting':'请先完成当前交互或结算','map.combat':'战斗尚未结束，脱战后可传送','map.projectiles':'附近仍有弹体，消散后可传送','map.level':'目的地需要 Lv{level}','map.unsafeArrival':'目的地传送阵附近仍有敌人',
 'legend.player':'队伍位置','legend.waypoint':'已解锁传送阵','legend.exit':'区域入口','legend.quest':'任务地点','legend.npc':'人物 / 商人','legend.checkpoint':'安全整备点','legend.mark':'自定标记',
 'map.walk':'前往此处','map.mark':'标记此处','map.unmark':'清除标记','map.back':'返回旅途',
};
const en:Record<keyof typeof zh,string>={
 'map.title':'Journey map','map.region':'Regional map','map.world':'World map','map.local':'Local map','map.regions':'Change region',
 'map.legend':'Legend','map.locate':'Locate','map.fit':'Fit','map.unknown':'Unexplored land','map.loading':'Opening map…','map.failed':'Map unavailable. Return and retry.',
 'map.compactWaypoints':'Waypoints','map.compactTravel':'Travel','map.compactEmpty':'No waypoints yet','map.controls':'Map mode','map.gesture':'Drag · scroll to zoom','map.details':'Tasks',
 'legend.merchant':'Merchant','legend.rest':'Rest point','legend.people':'People',
 'map.waypoints':'Waypoints','map.unlocked':'Unlocked · {count}','map.empty':'No waypoints discovered\nReach a safe preparation point to unlock one.',
 'map.direct':'Travel from anywhere safe','map.travel':'Travel to {name}','map.select':'Select a waypoint','map.busy':'Travelling…','map.retry':'Travel failed. Retry','map.failure':'Travel failed. Your original position is preserved. Retry.','map.arrived':'Arrived at {name}',
 'map.current':'Party location','map.here':'Already at this waypoint','map.discovered':'Discovered location','map.notUnlocked':'Waypoint not unlocked','map.unavailable':'Destination unavailable',
 'map.dead':'Cannot travel while defeated','map.submitting':'Finish the current interaction or reward','map.combat':'Leave combat before travelling','map.projectiles':'Wait for nearby projectiles to disappear','map.level':'Destination requires Lv{level}','map.unsafeArrival':'Enemies remain near the destination waypoint',
 'legend.player':'Party','legend.waypoint':'Unlocked waypoint','legend.exit':'Area entrance','legend.quest':'Quest','legend.npc':'People / merchants','legend.checkpoint':'Safe preparation point','legend.mark':'Custom marker',
 'map.walk':'Walk here','map.mark':'Mark here','map.unmark':'Clear marker','map.back':'Return to journey',
};
export const navigationText=registerMessages('navigation',zh,en);
