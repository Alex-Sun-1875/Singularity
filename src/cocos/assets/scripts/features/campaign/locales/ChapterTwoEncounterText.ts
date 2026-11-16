import {registerMessages} from '../../../shared/i18n/Localization';

/** Chapter-two encounter copy and UI hints share one semantic catalog. */
const messages = {
  "ui.taskPanel": [
    "冒险日志",
    "Adventure journal"
  ],
  "ui.finishDescription": [
    "兽潮之夜与群山战火的共同关底均已击败。可在任务面板继续未完成的主线与支线，也可继续Boss再战、狩猎与收集装备。支线在第二章中途即可完成，不以关底胜利为前提。\n\n目前开放第一、第二章，第3—8章尚未开放。",
    "The common bosses of chapters one and two are defeated. Continue unfinished main and side quests in Quests, or rematch bosses, hunt and collect equipment. Chapter-two side quests can be completed before the boss.\n\nChapters one and two are available. Chapters three through eight remain unavailable."
  ],
  "ui.tab.main": [
    "主线",
    "Main"
  ],
  "ui.tab.side": [
    "支线",
    "Side"
  ],
  "ui.mainHelp": [
    "主线按章推进；查看当前条件与奖励，再选择自动前往。寻路遇敌暂停，抵达交互仍需确认。",
    "Main quests advance by chapter. Review objectives and rewards, then travel automatically. Navigation pauses at enemies; interactions still need confirmation."
  ],
  "ui.sideHelp": [
    "支线独立保存现场步骤，不占用主线进度。点开任务可查看下一步、前置去向和已选处置。",
    "Side quests record their own field steps. Open a quest to review its next step, prerequisites and recorded choices."
  ],
  "ui.sideSteps": [
    "依次完成现场步骤。可执行步骤支持自动前往；前置未满足时可查看原因与准备地点。",
    "Complete the field steps in order. Available steps support automatic travel; blocked steps show requirements and preparation locations."
  ],
  "ui.currentMain": [
    "第{chapter}章当前主线 · {name}",
    "Chapter {chapter} current main quest · {name}"
  ],
  "ui.chapterTasks": [
    "第{chapter}章 · {name}",
    "Chapter {chapter} · {name}"
  ],
  "ui.mainProgress": [
    "主线 {count}/{total}",
    "Main quests {count}/{total}"
  ],
  "ui.sideName": [
    "第{chapter}章支线 · {name}",
    "Chapter {chapter} side quest · {name}"
  ],
  "ui.taskInProgress": [
    "未完成",
    "Unfinished"
  ],
  "ui.chapterLevelGate": [
    "尚未开放 · Lv11进入第二章",
    "Locked · Chapter two opens at Lv11"
  ],
  "ui.bossDone": [
    "关底已胜利",
    "Boss defeated"
  ],
  "ui.bossPending": [
    "关底未胜利",
    "Boss undefeated"
  ],
  "ui.backSide": [
    "返回支线",
    "Back to side quests"
  ],
  "ui.backTaskPanel": [
    "返回任务",
    "Back to quests"
  ],
  "ui.returnJourney": [
    "返回旅途",
    "Return to journey"
  ],
  "ui.chaptersRewards": [
    "章节与奖励",
    "Chapters and rewards"
  ],
  "ui.goal.encounter": [
    "完成任一有效现场解法",
    "Resolve the encounter with a valid approach"
  ],
  "ui.goal.hunt": [
    "游荡怪 {count}/{total}",
    "Wandering enemies {count}/{total}"
  ],
  "ui.goal.clear": [
    "击败本地固定敌阵及其增援",
    "Defeat the fixed encounter and its reinforcements"
  ],
  "ui.goal.observe": [
    "抵达现场并确认调查",
    "Reach the scene and confirm the investigation"
  ],
  "ui.autoGo": [
    "自动前往",
    "Travel automatically"
  ],
  "ui.autoPrerequisite": [
    "自动前往前置",
    "Travel to prerequisite"
  ],
  "ui.hudTaskBlocked": [
    "打开任务查看",
    "Open quests to review"
  ],
  "ui.hudTaskOpen": [
    "打开任务查看详情",
    "Open quests for details"
  ],
  "ui.recordedChoice": [
    "已选处置：{choice}",
    "Recorded resolution: {choice}"
  ],
  "method.investigate": [
    "调查",
    "Investigation"
  ],
  "method.rescue": [
    "救援",
    "Rescue"
  ],
  "method.negotiate": [
    "交涉",
    "Negotiation"
  ],
  "method.sabotage": [
    "破坏警报",
    "Alarm sabotage"
  ],
  "method.battle": [
    "战斗",
    "Combat"
  ],
  "method.mechanism": [
    "机关",
    "Mechanism"
  ],
  "ui.actionCompleted": [
    "这一步已完成",
    "Step complete"
  ],
  "ui.routeFighting": [
    "战斗进行中",
    "Combat in progress"
  ],
  "ui.returnBattle": [
    "前往战斗目标",
    "Go to combat target"
  ],
  "ui.actionRecorded": [
    "进度已保留，可继续选择后续行动。",
    "Progress is recorded. Continue with another on-site action."
  ],
  "ui.combatInProgress": [
    "战斗已开始，处理现场固定守军后结算。",
    "Combat has begun. Defeat the fixed guards to resolve it."
  ],
  "outcome.oathProgress": [
    "本轮已断开 {count}/3 段供能；已读顺序可在已获线索复查。",
    "Disconnected {count}/3 power lines this attempt. Review the recorded order in your clues."
  ],
  "ui.solutions": [
    "行动与解法",
    "Actions and approaches"
  ],
  "ui.solutionsHint": [
    "这项任务有多种解法。先查看线索与影响，再前往现场确认行动。",
    "This task has multiple approaches. Review clues and known consequences, then confirm actions on site."
  ],
  "ui.routes": [
    "可选现场行动",
    "On-site actions"
  ],
  "ui.routeReady": [
    "可前往",
    "Ready to visit"
  ],
  "ui.routeBlocked": [
    "尚需准备",
    "Preparation needed"
  ],
  "ui.routeComplete": [
    "处置已完成",
    "Resolution recorded"
  ],
  "ui.clues": [
    "已获线索 {known}/{total}",
    "Clues found {known}/{total}"
  ],
  "ui.clueKnown": [
    "已掌握 · {name}",
    "Known · {name}"
  ],
  "ui.clueUnknown": [
    "尚未记录 · 可继续现场调查",
    "Not recorded · Investigate the scene"
  ],
  "ui.noClues": [
    "尚未记录线索，可先到现场调查。",
    "No clues recorded yet. Start by investigating the scene."
  ],
  "ui.outcome": [
    "你的处置",
    "Your resolution"
  ],
  "ui.awaitingOutcome": [
    "尚未作出最终处置，已记录的线索会保留。",
    "No final resolution yet. Recorded clues remain available."
  ],
  "ui.awaitingReward": [
    "处置已记录，完成前一项任务后结算本项奖励。",
    "Resolution recorded. This task pays out after the preceding task is complete."
  ],
  "ui.availableDetail": [
    "查看行动条件与影响",
    "View requirements and known consequences"
  ],
  "ui.confirmOnSite": [
    "前往现场只开启交互，不替你作出选择。",
    "Going to the scene opens the interaction without choosing for you."
  ],
  "ui.go": [
    "前往现场",
    "Go to the scene"
  ],
  "ui.goPrerequisite": [
    "前往准备行动",
    "Go to preparation"
  ],
  "ui.map": [
    "查看地图",
    "View map"
  ],
  "ui.backTask": [
    "返回当前任务",
    "Back to task"
  ],
  "ui.backChapter": [
    "返回第二章",
    "Back to chapter two"
  ],
  "ui.reward": [
    "任务奖励：经验 {experience} · 金币 {gold} · 铁 {iron}",
    "Task reward: XP {experience} · Gold {gold} · Iron {iron}"
  ],
  "ui.rewardLevel": [
    "领取后预计 Lv{level}，当前 Lv{current}",
    "Expected Lv{level} after claiming; current Lv{current}"
  ],
  "ui.rewardClaimed": [
    "本项任务奖励已领取，改换解法不重复发放。",
    "This task reward has been claimed. Other approaches do not pay it again."
  ],
  "ui.rewardOnce": [
    "完成任一有效解法即可推进，同一任务基础奖励只结算一次。",
    "Any valid resolution advances the task. Its base reward is paid only once."
  ],
  "ui.routeCount": [
    "{count}项现场行动 · 线索 {known}/{total}",
    "{count} on-site actions · Clues {known}/{total}"
  ],
  "ui.completedSummary": [
    "处置已记录：{outcome}",
    "Resolution recorded: {outcome}"
  ],
  "ui.choiceHint": [
    "已知影响：{hint}",
    "Known consequence: {hint}"
  ],
  "ui.taskAvailable": [
    "当前任务",
    "Current task"
  ],
  "ui.taskLocked": [
    "前一任务尚未完成，可先查看行动准备。",
    "The preceding task is unfinished. You can review preparations now."
  ],
  "ui.finished": [
    "已完成",
    "Completed"
  ],
  "ui.ready": [
    "条件已满足",
    "Requirements met"
  ],
  "encounter.quarry.title": [
    "矿车下的呼救",
    "Cries beneath the mine cart"
  ],
  "encounter.quarry.summary": [
    "先查制动器，再决定如何救出工匠、保全证据。护送证人或保全货签，会为石梁前哨带来不同的解决办法。",
    "Inspect the brake before rescuing the workers and securing evidence. Escorting a witness or preserving the cargo tags opens different approaches at the ridge post."
  ],
  "encounter.ridge.title": [
    "石梁前哨的封锁",
    "The ridge-post blockade"
  ],
  "encounter.ridge.summary": [
    "可凭证人交涉、凭货签切断警报，或正面战斗。已经取得的线索会影响你能采取的行动。",
    "Negotiate with a witness, use the cargo tags to cut the alarm, or fight directly. Your recorded clues determine the available approaches."
  ],
  "encounter.oath.title": [
    "三誓供能线",
    "The Oathguard power lines"
  ],
  "encounter.oath.summary": [
    "读现场刻线，再逐段断开控制台。顺序错误可以重试，也可以选择与守卫战斗。",
    "Read the markings, then disconnect the consoles in sequence. You may retry a wrong sequence or choose to fight the guards."
  ],
  "outcome.pending": [
    "尚未作出最终处置。已获得的线索会保留。",
    "No final resolution yet. Recorded clues remain available."
  ],
  "outcome.rescueWitness": [
    "工匠已获救，证人愿意在前哨说明情况。可尝试证人交涉。",
    "The workers are safe, and a witness will speak at the post. Witness negotiation is now possible."
  ],
  "outcome.rescueLedger": [
    "工匠已获救，完整货签已保全。可据此查出前哨警报线路。",
    "The workers are safe, and the cargo tags are intact. They can identify the alarm circuit at the post."
  ],
  "outcome.parley": [
    "证人说明了被困工匠与军械的去向，前哨守军解除封锁并撤离。",
    "The witness explained the workers and cargo. The post guards lifted the blockade and withdrew."
  ],
  "outcome.battle": [
    "固定守军已被击败，这处封锁已解除。",
    "The fixed guards were defeated and the blockade was cleared."
  ],
  "outcome.mechanism": [
    "三段供能已依次断开，三誓守卫停机，通路恢复。",
    "All three power lines were disconnected in sequence. The Oathguard shut down and the passage reopened."
  ],
  "clue.quarrySurvey": [
    "侧轨制动器与救援位置",
    "The side-track brake and rescue position"
  ],
  "clue.witness": [
    "获救工匠的证词",
    "The rescued workers’ testimony"
  ],
  "clue.ledger": [
    "完整的军械货签",
    "Intact armament cargo tags"
  ],
  "clue.oathRead": [
    "已读刻线：北 → 西 → 东",
    "Recorded order: north → west → east"
  ],
  "reason.resolved": [
    "这处遭遇已完成，处置与奖励不会重复结算。",
    "This encounter is resolved. Its resolution and rewards cannot be claimed again."
  ],
  "reason.quarrySurvey": [
    "先查验侧轨制动器，确认救援位置。",
    "Inspect the side-track brake to locate the rescue point first."
  ],
  "reason.witness": [
    "需要在采坑救援中护送工匠证人。",
    "Escort a worker witness during the quarry rescue first."
  ],
  "reason.ledger": [
    "需要在采坑救援中保全完整货签。",
    "Preserve the intact cargo tags during the quarry rescue first."
  ],
  "reason.oathRead": [
    "先阅读现场的三剑供能刻线。",
    "Read the three-sword power markings first."
  ],
  "reason.alarmDone": [
    "警报已经切断，固定弓手已撤离；仍需处理剩余守军。",
    "The alarm is cut and the fixed archers have withdrawn. The remaining guards still need to be dealt with."
  ],
  "reason.ready": [
    "可前往现场，确认后执行这项行动。",
    "Visit the scene and confirm before carrying out this action."
  ],
  "reason.unavailable": [
    "这项行动当前不可执行，请查看已有线索与现场条件。",
    "This action is currently unavailable. Review your clues and the scene conditions."
  ],
  "event.survey": [
    "制动卡槽、工匠位置和货签已核对。现在可以选择护送证人或保全货签完成救援。",
    "The brake, trapped workers, and cargo tags have been checked. Choose to escort a witness or preserve the tags to complete the rescue."
  ],
  "event.witness": [
    "工匠获救，证人已准备前往石梁前哨。证人交涉路线已开放。",
    "The workers are safe, and the witness is ready to reach the ridge post. Witness negotiation is available."
  ],
  "event.ledger": [
    "工匠获救，完整货签已保存。可据此辨认前哨警报线路。",
    "The workers are safe, and the intact tags are recorded. They can identify the post’s alarm circuit."
  ],
  "event.parley": [
    "证人当面核对了工役与押运记录。前哨解除封锁，守军撤离。",
    "The witness checked the labor and transport records in person. The post lifted the blockade and its guards withdrew."
  ],
  "event.alarm": [
    "警报线路已切断，固定弓手撤离。剩余守军仍需战斗解决。",
    "The alarm circuit is cut and the fixed archers have withdrawn. The remaining guards still require combat."
  ],
  "event.battleStarted": [
    "战斗开始，处理现场固定守军及其增援即可推进。",
    "Combat has begun. Defeat the fixed guards and their reinforcements to advance."
  ],
  "event.oathRead": [
    "刻线记下断能顺序：北 → 西 → 东。线索已保留，可回旅程查看。",
    "The markings give the shutdown order: north → west → east. The clue is recorded for later review."
  ],
  "event.oathStep": [
    "已断开 {count}/3 段供能；下一台仍需按刻线判断。",
    "Disconnected {count}/3 power lines. Use the markings to choose the next console."
  ],
  "event.oathWrong": [
    "顺序不符，本轮供能线复位。刻线线索保留，可重新尝试，未扣除材料。",
    "The order was wrong and this attempt reset. The markings remain recorded. You may retry without losing materials."
  ],
  "event.oathDone": [
    "北、西、东三段供能已依序断开，三誓守卫停机。",
    "North, west, and east power lines are disconnected in order. The Oathguard shut down."
  ],
  "event.combatDone": [
    "固定守军已被击败，遭遇处置与任务进度已记录。",
    "The fixed guards were defeated. Encounter resolution and task progress are recorded."
  ],
  "choice.confirm": [
    "确认执行",
    "Confirm action"
  ],
  "choice.later": [
    "稍后再来",
    "Come back later"
  ],
  "action.quarry-survey.label": [
    "查验侧轨制动器",
    "Inspect the side-track brake"
  ],
  "action.quarry-survey.description": [
    "查看卡槽、工匠与货签的位置，再决定救援方式。",
    "Check the brake, trapped workers, and tags before choosing a rescue approach."
  ],
  "action.quarry-survey.hint": [
    "只记录救援线索，暂不替你选择证人或货签。",
    "Records the rescue clue without choosing a witness or the tags for you."
  ],
  "action.quarry-witness.label": [
    "护送工匠证人",
    "Escort the worker witness"
  ],
  "action.quarry-witness.description": [
    "完成现场救援，并护送能说明情况的工匠证人。证人可在石梁前哨出面交涉。",
    "Complete the rescue and escort a worker who can speak at the ridge post."
  ],
  "action.quarry-witness.hint": [
    "完成采坑任务，取得后续证人交涉的条件。",
    "Resolves the quarry task and enables witness negotiation at the post."
  ],
  "action.quarry-ledger.label": [
    "保全货签并救援",
    "Preserve the tags and rescue the workers"
  ],
  "action.quarry-ledger.description": [
    "完成现场救援，保全箱板上的完整货签。可用货签辨认石梁前哨的警报线路。",
    "Complete the rescue while preserving the intact tags that identify the post’s alarm circuit."
  ],
  "action.quarry-ledger.hint": [
    "完成采坑任务，取得后续断警报、减少固定弓手的条件。",
    "Resolves the quarry task and enables cutting the alarm to reduce fixed archers."
  ],
  "action.ridge-parley.label": [
    "请证人出面交涉",
    "Negotiate with the witness"
  ],
  "action.ridge-parley.description": [
    "让获救工匠当面核对押运与工役记录，争取解除前哨封锁。",
    "Let the rescued worker verify the transport and labor records to lift the blockade."
  ],
  "action.ridge-parley.hint": [
    "证人路线可让前哨守军撤离；不需要击杀固定守军。",
    "The witness approach lets the fixed guards withdraw without killing them."
  ],
  "action.ridge-alarm.label": [
    "凭货签切断警报",
    "Use the tags to cut the alarm"
  ],
  "action.ridge-alarm.description": [
    "用完整货签核对警报线路，再在现场切断警报。",
    "Use the intact tags to identify and cut the alarm circuit on site."
  ],
  "action.ridge-alarm.hint": [
    "固定弓手会撤离，剩余守军仍要战斗解决。",
    "Fixed archers withdraw, but the remaining guards still require combat."
  ],
  "action.ridge-battle.label": [
    "迎战固定守军",
    "Fight the fixed guards"
  ],
  "action.ridge-battle.description": [
    "正面迎战石梁前哨固定守军。无需先取得证人或货签。",
    "Fight the ridge post’s fixed guards directly, without needing a witness or tags."
  ],
  "action.ridge-battle.hint": [
    "进入真实战斗；击败固定守军后完成同一任务。",
    "Starts real combat. Defeating the guards completes the same task."
  ],
  "action.oath-read.label": [
    "阅读三剑刻线",
    "Read the three-sword markings"
  ],
  "action.oath-read.description": [
    "在现场核对三剑朝向与供能刻线，再决定操作控制台或战斗。",
    "Read the sword directions and power markings before operating consoles or fighting."
  ],
  "action.oath-read.hint": [
    "记录可复查的断能顺序，不自动替你操作控制台。",
    "Records a reviewable shutdown order without operating consoles for you."
  ],
  "action.oath-north.label": [
    "操作北侧控制台",
    "Operate the north console"
  ],
  "action.oath-north.description": [
    "在北侧控制台断开一段供能，按已掌握的刻线判断顺序。",
    "Disconnect a power line at the north console, using the recorded order."
  ],
  "action.oath-north.hint": [
    "顺序正确推进一段；错误会复位本轮，可无材料损失重试。",
    "A correct step advances the sequence. A wrong step resets the attempt without material loss."
  ],
  "action.oath-west.label": [
    "操作西侧控制台",
    "Operate the west console"
  ],
  "action.oath-west.description": [
    "在西侧控制台断开一段供能，按已掌握的刻线判断顺序。",
    "Disconnect a power line at the west console, using the recorded order."
  ],
  "action.oath-west.hint": [
    "顺序正确推进一段；错误会复位本轮，可无材料损失重试。",
    "A correct step advances the sequence. A wrong step resets the attempt without material loss."
  ],
  "action.oath-east.label": [
    "操作东侧控制台",
    "Operate the east console"
  ],
  "action.oath-east.description": [
    "在东侧控制台断开一段供能，按已掌握的刻线判断顺序。",
    "Disconnect a power line at the east console, using the recorded order."
  ],
  "action.oath-east.hint": [
    "顺序正确推进一段；错误会复位本轮，可无材料损失重试。",
    "A correct step advances the sequence. A wrong step resets the attempt without material loss."
  ],
  "action.oath-battle.label": [
    "迎战三誓守卫",
    "Fight the Oathguard"
  ],
  "action.oath-battle.description": [
    "与三誓守卫及其固定增援进行真实战斗。无需先解开机关顺序。",
    "Fight the Oathguard and their fixed reinforcements without solving the console sequence first."
  ],
  "action.oath-battle.hint": [
    "选择战斗后面对固定守卫阵，击败后完成同一任务。",
    "Starts a real fixed-guard encounter. Defeat it to complete the same task."
  ],
  "ui.stepProgress": [
    "现场步骤 {count}/{total}",
    "Field steps {count}/{total}"
  ],
  "ui.routeUnavailable": [
    "尚无已开放的通路；可查看地图并先完成沿途前置。",
    "No open route is available. Check the map and complete the route prerequisites first."
  ],
  "boss.fixedTitle": [
    "主线首领首胜固定装备",
    "Fixed main-boss first-victory equipment"
  ],
  "boss.fixedRules": [
    "首次真实击败本章主线首领时自动掉落固定装备；普通任务只结算材料与经验。再战保留常规材料与经验，不重复固定装备，也不进行随机装备抽取。",
    "The first real victory over this chapter’s main boss drops fixed equipment automatically. Ordinary quests grant materials and XP. Rematches grant regular materials and XP, without repeating the fixed equipment or rolling random equipment."
  ],
  "boss.fixedShort": [
    "首胜固定装备 · 再战仅材料与经验",
    "First win: fixed gear · Rematch: materials & XP"
  ],
  "boss.randomTitle": [
    "支线与野外首领随机装备",
    "Random side and world-boss equipment"
  ],
  "boss.randomRules": [
    "同章支线与野外首领共享随机奖池。接不接任务，首杀与再战的随机掉落规则相同；任务交付另结算材料与经验。",
    "Side and world bosses share a random pool within each chapter. Accepting a quest does not change first-kill or rematch drops. Quest turn-ins separately grant materials and XP."
  ],
  "boss.randomRates": [
    "基础概率：史诗 {epic}% · 传奇 {legendary}% · 神器 {artifact}%",
    "Base rates: Epic {epic}% · Legendary {legendary}% · Artifact {artifact}%"
  ],
  "boss.randomPity": [
    "史诗及以上最迟第 {epic} 次、传奇及以上最迟第 {legendary} 次；神器无保底。",
    "Epic or better by draw {epic}; Legendary or better by draw {legendary}. Artifacts have no guarantee."
  ],
  "boss.randomShort": [
    "同章随机装备 · 接任务不改变掉落",
    "Chapter pool · Quests do not change drops"
  ],
  "boss.previewStyle": [
    "尚未掉落的装备按{style}预览；已结算装备保持原结果。",
    "Unissued gear is previewed for {style}; issued gear retains its original result."
  ],
  "boss.pendingGround": [
    "首胜装备已掉落 · 留在场景待拾取",
    "First-victory gear dropped · Waiting on the ground"
  ],
  "boss.owned": [
    "已拥有",
    "Owned"
  ],
  "boss.awarded": [
    "首胜奖励已结算",
    "First-victory reward already issued"
  ],
  "boss.awaitFirstWin": [
    "首次击败主线首领后自动掉落",
    "Drops after the first main-boss victory"
  ],
  "boss.fixedNoClaim": [
    "此页查看固定掉落，无需领取任务装备。",
    "This page previews fixed drops. There is no quest-equipment claim."
  ],
  "boss.backFixed": [
    "返回固定装备",
    "Back to fixed equipment"
  ],
  "boss.backRewards": [
    "返回装备来源",
    "Back to equipment sources"
  ],
  "boss.taskMaterials": [
    "任务材料与经验：{reward}",
    "Quest materials and XP: {reward}"
  ],
  "boss.stepAlreadyKilled": [
    "此首领已击败，已承认既有进度；继续现场取证即可，不必再杀。",
    "This boss is already defeated and your prior progress counts. Continue with the evidence step; another kill is unnecessary."
  ],
  "boss.stepFight": [
    "需要真实击败 {name} · Lv{level} · {area}",
    "Defeat {name} in real combat · Lv{level} · {area}"
  ],
  "boss.stepEvidence": [
    "击败记录已确认 · 前往现场取证",
    "Defeat recorded · Visit the evidence site"
  ],
  "boss.autoFight": [
    "自动前往战斗地点",
    "Travel to the battle site"
  ],
  "boss.rewardSplit": [
    "Boss装备独立掉落；完成任务不额外领取装备。",
    "Boss equipment drops independently. Completing the quest does not grant extra equipment."
  ],
  "boss.kindMain": [
    "主线首领",
    "Main boss"
  ],
  "boss.kindSide": [
    "支线首领",
    "Side boss"
  ],
  "boss.kindWorld": [
    "野外首领",
    "World boss"
  ],
  "boss.sourcesTitle": [
    "第{chapter}章 · 固定装备与随机奖池",
    "Chapter {chapter} · Fixed gear and random pool"
  ],
  "boss.mainCompletion": [
    "主线首胜固定装备；重复挑战仅材料与经验",
    "First main-boss victory grants fixed gear; rematches grant materials and XP"
  ],
  "boss.state": [
    "首领状态",
    "Boss status"
  ],
  "boss.alive": [
    "首领存活",
    "Boss alive"
  ],
  "boss.unbeaten": [
    "尚未击败",
    "Not defeated yet"
  ]
} as const;
const zh:Record<string,string>={},en:Record<string,string>={};
for(const [key,[chinese,english]]of Object.entries(messages)){zh[key]=chinese;en[key]=english;}
const translate=registerMessages('chapterTwoEncounters',zh,en);
export const encounterText=(key:string,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
