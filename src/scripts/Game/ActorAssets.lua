-- Populate only with inspected local model/animation assets, including local authoring.
-- Maker cloud generation, credentials and project binding are not required here.
-- Each entry accepts a verified .prefab, or .mdl + ordered material resource paths.
-- A real skeleton and four verified .ani resources are required to unlock play.
---@class ChapterActorAsset
---@field status string
---@field prefab? string
---@field model? string
---@field materials? string[]
---@field clips? table<string,string>
---@field scale? number
---@field yawOffset? number
---@field sockets? table
---@class ChapterActorAssetSet
---@field hero ChapterActorAsset
---@field mira ChapterActorAsset
---@field raider ChapterActorAsset
---@type ChapterActorAssetSet
local actors={
    hero={status="local_authored",model="model/raphael/Character.mdl",
        materials={"model/raphael/Material-00.xml","model/raphael/Material-01.xml","model/raphael/Material-02.xml","model/raphael/Material-03.xml","model/raphael/Material-04.xml","model/raphael/Material-05.xml","model/raphael/Material-06.xml","model/raphael/Material-07.xml","model/raphael/Material-08.xml","model/raphael/Material-09.xml","model/raphael/Material-10.xml","model/raphael/Material-11.xml"},
        clips={idle="model/raphael/idle.ani",run="model/raphael/run.ani",attack="model/raphael/attack.ani",hit="model/raphael/hit.ani"},
        sockets={sword={rotation={-0.37420061230659485,0.31580090522766113,0.5663303136825562,-0.6629581451416016},position={0,0,-0.075}},bow={rotation={0.13029098510742188,0.47199636697769165,0.839079737663269,0.23704181611537933},position={0,0,-0.075}},staff={rotation={0.08220118284225464,0.4826999604701996,0.8586525321006775,0.15152394771575928},position={0,0,-0.075}}}},
    mira={status="local_authored",model="model/mira/Character.mdl",
        materials={"model/mira/Material-00.xml","model/mira/Material-01.xml","model/mira/Material-02.xml","model/mira/Material-03.xml","model/mira/Material-04.xml","model/mira/Material-05.xml","model/mira/Material-06.xml","model/mira/Material-07.xml","model/mira/Material-08.xml","model/mira/Material-09.xml"},
        clips={idle="model/mira/idle.ani",run="model/mira/run.ani",attack="model/mira/attack.ani",hit="model/mira/hit.ani"},
        sockets={sword={rotation={-0.2913409471511841,0.30958452820777893,0.611498236656189,-0.6673438549041748},position={0,0,-0.075}},bow={rotation={0.1593090146780014,0.3941354751586914,0.8619590997695923,0.27623245120048523},position={0,0,-0.075}},staff={rotation={0.1188964694738388,0.40814921259880066,0.8853542804718018,0.18821708858013153},position={0,0,-0.075}}}},
    raider={status="local_authored",model="model/raider/Character.mdl",
        materials={"model/raider/Material-00.xml","model/raider/Material-01.xml","model/raider/Material-02.xml","model/raider/Material-03.xml","model/raider/Material-04.xml","model/raider/Material-05.xml","model/raider/Material-06.xml","model/raider/Material-07.xml","model/raider/Material-08.xml","model/raider/Material-09.xml","model/raider/Material-10.xml"},
        clips={idle="model/raider/idle.ani",run="model/raider/run.ani",attack="model/raider/attack.ani",hit="model/raider/hit.ani"},
        sockets={sword={rotation={-0.37420061230659485,0.31580090522766113,0.5663303136825562,-0.6629581451416016},position={0,0,-0.075}},bow={rotation={0.13029098510742188,0.47199636697769165,0.839079737663269,0.23704181611537933},position={0,0,-0.075}},staff={rotation={0.08220118284225464,0.4826999604701996,0.8586525321006775,0.15152394771575928},position={0,0,-0.075}}}},
}
return actors
