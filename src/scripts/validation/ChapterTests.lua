local Tests = {}

function Tests.Run()
    local loaded, Chapter = pcall(require, "Game.Chapter")
    assert(loaded, "RED: local chapter rules are not implemented: " .. tostring(Chapter))
    local count = 0
    local function check(name, fn)
        fn()
        count = count + 1
        print("[ChapterTest] PASS " .. name)
    end
    check("initial free weapons and finite oil", function()
        local g = Chapter.New(123)
        assert(g.owned.W01 and g.owned.W07 and g.owned.W11)
        assert(g.player.oil == 3 and g.scene == "camp")
    end)
    check("diagonal movement is normalized and delta bounded", function()
        local a, b = Chapter.New(1), Chapter.New(1)
        a:Step(0.05, {x = 1})
        b:Step(9, {x = 1, y = 1})
        local ax, ay = a.player.x - 260, a.player.y - 430
        local bx, by = b.player.x - 260, b.player.y - 430
        assert(math.abs(math.sqrt(ax*ax+ay*ay)-math.sqrt(bx*bx+by*by)) < 0.001)
    end)
    check("quest advance cannot skip acceptance", function()
        local g = Chapter.New(2)
        assert(not g:Travel("road"))
        g:Choose("ask_letter")
        assert(g.flags.saw_copy and g.flags.accepted and g.player.gold == 60)
        g:Choose("ask_letter")
        assert(g.player.gold == 60)
        assert(g:Travel("road"))
    end)
    check("normal weapon switching cannot manufacture legendary ownership", function()
        local g = Chapter.New(3)
        assert(not g:Equip("L02"))
        assert(g:Equip("W07"))
        assert(g.weapon == "W07")
    end)
    check("barrel chains and enemy reward receipts settle once", function()
        local g = Chapter.New(4)
        g:Choose("accept")
        g:Travel("road")
        local enemy = g.world.road.enemies[1]
        local x, y = enemy.x, enemy.y
        g.world.road.barrels = {{id="a",x=x,y=y,alive=true},{id="b",x=x+20,y=y,alive=true}}
        enemy.hp = 20
        g:Explode(g.world.road.barrels[1])
        local iron = g.player.iron
        g:Explode(g.world.road.barrels[1])
        g:Kill(enemy)
        assert(enemy.hp == 0 and g.player.iron == iron)
    end)
    check("returning arrow hits once in each leg", function()
        local g = Chapter.New(5)
        g:Choose("accept")
        g:Travel("road")
        g.owned.L02 = true
        g:Equip("L02")
        local e = g.world.road.enemies[1]
        g.player.x, g.player.y = 300, 420
        e.x, e.y, e.hp, e.maxHp = 380,420,500,500
        g.world.road.walls = {}
        g.world.road.enemies = {e}
        g:Attack(0)
        local p = g.projectiles[1]
        assert(p and p.returning)
        p.x, p.y = e.x, e.y
        g:HitProjectile(p, e)
        local afterOut = e.hp
        g:HitProjectile(p, e)
        assert(e.hp == afterOut)
        p.leg = "back"
        g:HitProjectile(p, e)
        assert(e.hp < afterOut)
        local afterBack = e.hp
        g:HitProjectile(p, e)
        assert(e.hp == afterBack)
    end)
    check("snapshot persists choices, loot and random state", function()
        local g = Chapter.New(6)
        g:Choose("ask_letter")
        g:Travel("road")
        g:Loot("road_cache")
        g:RollLegend("test_unique", 1)
        local snapshot = g:Snapshot()
        local restored = assert(Chapter.Restore(snapshot))
        local iron, gold = restored.player.iron, restored.player.gold
        restored:Loot("road_cache")
        restored:RollLegend("test_unique", 1)
        assert(restored.flags.saw_copy and restored.player.iron == iron and restored.player.gold == gold)
        assert(restored.rng == g.rng and restored.receipts.test_unique)
    end)
    check("malformed save is rejected", function()
        assert(not Chapter.Restore({version = 999}))
        local snapshot = Chapter.New(7):Snapshot()
        snapshot.player.hp = 0/0
        assert(not Chapter.Restore(snapshot))
    end)
    check("death restarts without resurrecting defeated world enemies", function()
        local g = Chapter.New(8)
        g:Choose("accept")
        g:Travel("road")
        local e = g.world.road.enemies[1]
        g:Kill(e)
        local iron = g.player.iron
        g.player.hp = 0
        g.status = "dead"
        g:Retry()
        assert(g.player.hp == g.player.maxHp and e.hp == 0 and g.player.iron == iron)
    end)
    print("[ChapterTest] COMPLETE " .. count .. " cases")
end

return Tests
