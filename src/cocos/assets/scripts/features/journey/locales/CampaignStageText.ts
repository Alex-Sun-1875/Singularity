import {registerMessages} from '../../../shared/i18n/Localization';

const english:Record<string,[string,string]>={
 'c1-traces':['Tracks at Dusk','Read the crossing tracks and give the refugees a safe way out.'],
 'c1-mill':['Reclaim the Broken Wheel Mill','Rescue the keeper after the battle and investigate the footsteps below.'],
 'c1-herd':['Push Back the Hunt','Count six real kills, then help the migrating herd through its last obstacle.'],
 'c1-camp':['The Greycloak Camp','Defeat the guards and compare the detention order with the missing workers.'],
 'c1-letter':['The Recent Date on the Letter','Recover the case and read the appeal that contradicts an eighteen-year-old death record.'],
 'c1-sentinel':['The Old Army Wakes','Pass the sentinels and verify what their old orders still protect.'],
 'c1-table':['Supper with the Fallen','Hear Evelyn and Mira at the table. Ask questions or keep your independence.'],
 'c1-cells':['Two Approaches to the Cells','Check the service route and free the workers through combat or dismantling the lure.'],
 'c1-exit':['Actually Leaving the Cells','Secure the support, inspect the far end and leave through a verified exit.'],
 'c1-captain':['The Greycloak Captain','Defeat the real captain guarding the pass.'],
 'c1-gate':['Raise the Barrier Yourself','Raise the barrier and keep the original source of the Unfading Oath reward.'],
 'c1-return':['Those Who Returned','Make room for the workers, then return to the table. Cooperation and independence both finish the chapter.'],
 'c2-front':['The Mountain Inn at War','Hear the workers, guards and residents before deciding where to go.'],
 'c2-orders':['Who Receives the Requisition','Verify the seal and follow the order to its actual handover point.'],
 'c2-workshop':['Defend the Mirror Workshop','Defeat the fixed formation threatening the workers evacuation route.'],
 'c2-stop':['Bring the Workshop to Rest','Evacuate the workers and verify both sides of the shutdown.'],
 'c2-heat':['A Reversible Trial','Turn the cooling vanes and read both the heating and return marks.'],
 'c2-quarry':['Two Pieces of Quarry Evidence','Inspect the brake, then rescue a witness or preserve the cargo tags.'],
 'c2-evidence':['After Taking the Evidence','Arrange a witness reception or verify the tags. Do not repeat the mutually exclusive route.'],
 'c2-post':['The Ridge Post Decision','Negotiate, isolate the alarm before fighting, or face the real defenders.'],
 'c2-post-return':['After the Post Lets You Through','Resolve the reception, armament storage or battle damage left by your chosen method.'],
 'c2-command':['Orders and the Old Record','Compare the modern command with old records and the power supply.'],
 'c2-oath':['The Oath Array Answers','Stop the three consoles or fight, then verify the consequences on site.'],
 'c2-pressure':['A Way Back from the Furnace','Release pressure in stages and verify a route you can retreat along.'],
 'c2-guardian':['The Armored Bridge Guard','Defeat the real guard at the fortress.'],
 'c2-bridge':['Reconnect the Handle and Lower the Bridge','Restore the two-way road to the armament shore yourself.'],
 'c2-armory':['The Armory Beyond the Bridge','Claim the existing equipment and supplies once, through their original source.'],
 'c2-contact':['A Contact You Can End','Test the disconnect and report back at the inn. Refusing the core still completes the chapter.'],
};
/** Semantic stage IDs own their bundled copy, independently of reward receipts. */
export function localizeCampaignStages<T extends {id:string;name:string;story:string}>(stages:T[]):void {
 const zh:Record<string,string>={},en:Record<string,string>={};
 for(const stage of stages){zh[stage.id+'.title']=stage.name;zh[stage.id+'.story']=stage.story;const copy=english[stage.id];if(!copy)throw new Error('Missing stage translation: '+stage.id);en[stage.id+'.title']=copy[0];en[stage.id+'.story']=copy[1];}
 const text=registerMessages('campaign-stages',zh,en);
 for(const stage of stages){stage.name=text(stage.id+'.title',{},'zh-CN');stage.story=text(stage.id+'.story',{},'zh-CN');}
}
