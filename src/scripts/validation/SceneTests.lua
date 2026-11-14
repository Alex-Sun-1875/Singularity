function Start()
    local Chapter=require("Game.Chapter")
    local Scene3D=require("Game.Scene3D")
    local app={game=Chapter.New(17)}
    local scene=Scene3D.New(app)
    scene:Update(0)
    local p=require("Game.Environment").ToWorld(600,420)
    local screen=scene.camera:WorldToScreenPoint(p)
    local x,y=scene:GroundPoint(screen.x,screen.y)
    assert(math.abs(x-600)<0.01 and math.abs(y-420)<0.01,"camera projection/ray must roundtrip into game coordinates")
    local playerActor=scene.actors.player
    scene.actors.player=nil
    assert(not scene:CharactersReady(),"an absent model must not be faked by portrait tokens")
    scene.actors.player=playerActor
    -- Native format API probe, never a production actor or visual fallback.
    local imported=assert(scene:CreateActor("native_format_probe",{model="Models/Box.mdl"}),"engine MDL deliveries must import without a prefab")
    assert(imported.mesh.model.numGeometries>0)
    assert(not imported.ready,"a mesh with no skeleton/motion must never unlock gameplay")
    imported.node:Remove()
    if scene:CharactersReady() then
        app.game:Attack(0); scene:Update(.016)
        assert(scene.actors.player.state=="attack")
        assert(scene.actors.player.weapons and scene.actors.player.weapons.current=="W01")
    end
    app.game:Choose("accept"); app.game:Travel("road"); scene:Update(0)
    assert(scene.name=="road" and scene.environment.root:GetChild("Road"))
    print("[SceneTest] PASS 3D camera aiming, map transition and explicit pending character assets")
end
