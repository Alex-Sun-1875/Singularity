local Chapter = require("Game.Chapter")
local Tests = {}
function Tests.Run()
    local g=Chapter.New(101)
    g.player.x,g.player.y=420,420
    g:Interact(); assert(g.dialogue=="offer")
    g:Choose("ask_letter"); assert(g.flags.accepted)
    g.player.x,g.player.y=1480,430; g:Interact(); assert(g.scene=="road")
    -- Fight using real free ranged attacks, not Kill/Hurt shortcuts.
    g:Equip("W07")
    local function fight()
        for _,e in ipairs(g:Map().enemies) do
            local guard=0
            while e.hp>0 and guard<500 do
                guard=guard+1
                g.player.x,g.player.y=e.x-155,e.y
                g.player.hp,g.player.hurtTime=120,0.5
                g:Step(0.05,{angle=0,attack=true})
            end
            assert(e.hp==0,"ranged combat must defeat "..e.id)
        end
    end
    fight()
    g.player.x,g.player.y=1500,410; g:Interact(); assert(g.scene=="pass")
    fight()
    g.player.x,g.player.y=1420,405; g:Interact()
    assert(g.dialogue=="letter" and g.flags.recovered)
    g:Choose("read_letter")
    g.player.x,g.player.y=90,430; g:Interact(); assert(g.scene=="road")
    g.player.x,g.player.y=90,430; g:Interact(); assert(g.scene=="camp")
    g.player.x,g.player.y=420,420; g:Interact(); assert(g.dialogue=="debrief")
    g:Choose("finish"); assert(g.flags.complete and g.player.gold==80)
    local restored=assert(Chapter.Restore(g:Snapshot()))
    assert(restored.flags.complete and restored.flags.read_letter)
    print("[FlowTest] PASS accept -> ranged combat -> coffer -> letter -> return -> completion -> restore")
end
return Tests
