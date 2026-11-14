-- Standalone UrhoX validation entry; deliberately has no UI or cloud dependency.
function Start()
    local loaded, Tests = pcall(require, "validation.ChapterTests")
    assert(loaded, "Could not load chapter tests: " .. tostring(Tests))
    Tests.Run()
    require("validation.FlowTests").Run()
    require("validation.SaveTests").Run()
    require("validation.ViewportTests").Run()
end
