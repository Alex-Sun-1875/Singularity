require("main")
local startGame=Start
function Start()
    startGame()
    -- Read-only deterministic screenshot fixture. Never touches the user's save.
    ChapterApp.started=false
    ChapterApp.game=require("Game.Chapter").New(997)
    ChapterApp.game:Choose("ask_letter")
    ChapterApp.game:Travel("road")
    ChapterApp.game.player.x,ChapterApp.game.player.y=440,430
    ChapterApp.screen="fixture"
    ChapterApp:Rebuild()
    local UI=require("urhox-libs/UI")
    print("[ViewportTest] fixture dimensions",graphics.width,graphics.height,UI.GetViewportSize(),UI.GetScale())
end
