require("main")
local startGame=Start
local Chapter=require("Game.Chapter")
local Save=require("Game.Save")
local function click(id)
    local widget=assert(ChapterApp.root:FindById(id),"Missing UI control "..id) --[[@as Button]]
    widget:OnClick()
end
function Start()
    startGame()
    local app=ChapterApp
    -- Exercise UI/rule integration independently of the still-pending art deliveries.
    app.scene3d=nil
    app.game=Chapter.New(902)
    app.store=Save.New("ui_test_"..os.time().."_"..math.floor(os.clock()*100000))
    app:Rebuild()
    click("begin"); assert(app.started and not app.screen)
    app.game.player.x,app.game.player.y=420,420
    click("interact"); app:Rebuild()
    assert(app.game.dialogue=="offer")
    click("choice_ask_letter"); assert(app.game.flags.saw_copy and app.game.player.gold==60)
    click("open_inventory"); assert(app.screen=="inventory")
    click("equip_W07"); assert(app.game.weapon=="W07")
    click("close_inventory"); assert(not app.screen)
    local function key(code) HandleKeyDown(nil,{Key={GetInt=function() return code end}}) end
    key(KEY_ESCAPE); assert(app.screen=="pause")
    key(KEY_ESCAPE); assert(not app.screen,"Escape must resume a paused journey")
    key(KEY_B); assert(app.screen=="inventory")
    key(KEY_B); assert(not app.screen,"B must close inventory")
    app.game.player.x,app.game.player.y=1480,430
    click("interact"); assert(app.game.scene=="road")
    app:SaveNow()
    local restored=assert(Save.New(app.store.prefix):Load())
    assert(restored.scene=="road" and restored.weapon=="W07" and restored.flags.saw_copy)
    app.started=false; app.screen="fixture"; app:Rebuild()
    print("[UiTest] PASS title -> dialogue choice -> inventory equip -> road -> disk restore")
end
