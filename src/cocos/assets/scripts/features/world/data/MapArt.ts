import type {AreaDef} from '../../../core/Contracts';

/** Painted surface selection only. Geometry, navigation and metre coordinates
 * remain owned by SceneBuilder/Terrain. These scales are art-production targets,
 * not measured dimensions claimed for a scanned source texture. */
export type MapArtFamily='town-stone'|'meadow-earth'|'birch-forest'|'reed-marsh'|'mountain-quarry'|'oath-ruin'|'warm-interior'|'inhabited-undercity'|'drowned-crypt';
export type MapArtTexture='cobble'|'earth'|'meadow'|'forest'|'wet-earth'|'bedrock'|'flagstone'|'wood'|'water';
export interface MapArtSurface {
 readonly key:MapArtTexture;
 readonly resource:string;
 /** Metres covered by one complete square texture. */
 readonly tileMetres:number;
 readonly tint:string;
}
export interface MapArtProfile {
 readonly family:MapArtFamily;
 readonly ground:MapArtSurface;
 readonly road:MapArtSurface;
 readonly grass:MapArtSurface;
 readonly paving:MapArtSurface;
 readonly wood:MapArtSurface;
 readonly water:MapArtSurface;
 readonly propTints:{readonly stone:string;readonly foliage:string;readonly timber:string};
}

export const MAP_ART_TEXTURE_ROOT='flat2d/terrain-v1/';
// Versioned siblings retain the original art for comparison. The existing map
// resource scope and terrain bundle continue to own the same nine textures.
const surface=(key:MapArtTexture,tileMetres:number,tint='#FFFFFF'):MapArtSurface=>({key,resource:MAP_ART_TEXTURE_ROOT+key+'-v2',tileMetres,tint});
export const MAP_ART_SURFACES:Readonly<Record<MapArtTexture,MapArtSurface>>={
 cobble:surface('cobble',2.2),
 earth:surface('earth',5.6),
 meadow:surface('meadow',5.6),
 forest:surface('forest',5.8),
 'wet-earth':surface('wet-earth',5.4),
 bedrock:surface('bedrock',5.8),
 flagstone:surface('flagstone',2.8),
 wood:surface('wood',2.8),
 water:surface('water',6.5),
};
const s=MAP_ART_SURFACES;
const profile=(family:MapArtFamily,ground:MapArtSurface,road:MapArtSurface,stone='#FCF7E7',foliage='#EDFFE0'):MapArtProfile=>({
 family,ground,road,grass:s.meadow,paving:s.flagstone,wood:s.wood,water:s.water,
 propTints:{stone,foliage,timber:'#FFF4DE'},
});

/** Each family retains its material identity. A quarry is bedrock with a worn
 * earth route; masonry paving is reserved for built courts and working floors. */
export const MAP_ART_PROFILES:Readonly<Record<MapArtFamily,MapArtProfile>>={
 'town-stone':profile('town-stone',s.meadow,s.cobble),
 'meadow-earth':profile('meadow-earth',s.meadow,s.earth),
 'birch-forest':profile('birch-forest',s.forest,s.earth,'#F7F2E1','#E5FFD6'),
 'reed-marsh':profile('reed-marsh',s['wet-earth'],s.earth,'#E9F4E1','#DBF2BB'),
 'mountain-quarry':profile('mountain-quarry',s.bedrock,s.earth,'#FAF7EA','#E8F6CE'),
 'oath-ruin':profile('oath-ruin',s.flagstone,s.cobble,'#FCF8EE','#E4F4CE'),
 'warm-interior':profile('warm-interior',s.wood,s.wood,'#F8F1DE','#EFF9D3'),
 'inhabited-undercity':profile('inhabited-undercity',s.bedrock,s.flagstone,'#E8EFE3','#DCEBD0'),
 'drowned-crypt':profile('drowned-crypt',s.flagstone,s.flagstone,'#E0EBE4','#D7EACC'),
};

// Stable IDs follow the 97-location art catalog. A narrative family describes
// the location's character; the current AreaDef and overrides below determine
// its actual outdoor/indoor walking material. No geometry or exits change here.
const FAMILY_IDS:Readonly<Record<MapArtFamily,readonly string[]>>={
 'town-stone':['S01','S10','S01-T4','S01-T6','H02','H03','H08','H09','H11','H12','B03','B06','B09','B10','B11','B16','B18','F01','F02','F03','F05','F06','F07','F08','F09','F10','F12','F13'],
 'meadow-earth':['S03','S09','S18','B02','B07','B15','F16'],
 'birch-forest':['S05','S07','S19'],
 'reed-marsh':['S02','S06','S14','B12','B13','B14'],
 'mountain-quarry':['S04','S08','S11','S13','S16','S17','S20','H01','H04','H05','H07','H14','H15','H16','H17','B01','F17','U1-02'],
 'oath-ruin':['S12','S15','H10','H13','B08','B17','F11','U1-06'],
 'warm-interior':['S01-T1','S01-T2','S01-T3','S01-T5','H06','B04','B05','F04','F14','F15','U2-04'],
 'inhabited-undercity':['U1-01','U1-03','U1-04','U1-05','U1-07','U1-08','U1-09','U1-10'],
 'drowned-crypt':['U2-01','U2-02','U2-03','U2-05','U2-06','U2-07','U2-08','U2-09'],
};
const AREA_FAMILIES=new Map<string,MapArtFamily>();
for(const family of Object.keys(FAMILY_IDS)as MapArtFamily[])for(const id of FAMILY_IDS[family])AREA_FAMILIES.set(id,family);

const OVERRIDES:Readonly<Record<string,Partial<MapArtProfile>>>={
 // Fortifications, warehouses and small paved shelters need built floors,
 // unlike the grassy outer streets of S01 and the larger living settlements.
 S10:{ground:s.bedrock,road:s.cobble},
 'S01-T3':{ground:s.flagstone,road:s.flagstone},
 'S01-T4':{ground:s.cobble,road:s.cobble},
 'S01-T5':{ground:s.flagstone,road:s.flagstone},
 'S01-T6':{ground:s.flagstone,road:s.flagstone},
 S11:{road:s.flagstone},
 S14:{road:s.cobble},
 S15:{ground:s['wet-earth'],road:s.flagstone},
 // A real inhabited floor must not inherit the generic underground rock tint.
 // The existing ResidenceStoneFloor uses paving; tables/woodwork use wood.
 'U1-02':{road:s.flagstone},
 'U1-04':{ground:s.flagstone,road:s.flagstone},
 'U1-05':{ground:s.flagstone,road:s.flagstone},
 'U1-07':{ground:s.flagstone,road:s.flagstone},
 'U1-08':{ground:s.flagstone,road:s.flagstone},
 'U2-01':{ground:{...s.flagstone,tint:'#E1E6E4'}},
 // R2: stone streets and working courts are distinct from the natural rock
 // cuts. The injured workers' street and army camp remain compacted earth;
 // their grey timber benches/tents do not turn the entire outdoor area to wood.
 H01:{ground:s.bedrock,road:s.cobble},
 H02:{ground:s.cobble,road:s.cobble},
 H03:{ground:s.flagstone,road:s.flagstone},
 H05:{ground:s.bedrock,road:s.flagstone},
 H06:{ground:s.earth,road:s.cobble},
 H07:{ground:s.bedrock,road:s.flagstone},
 H08:{ground:s.flagstone,road:s.cobble},
 H09:{ground:s.flagstone,road:s.flagstone},
 H11:{ground:s.cobble,road:s.flagstone},
 H12:{ground:s.earth,road:s.earth},
 H13:{ground:s.flagstone,road:s.flagstone},
 H15:{ground:s.bedrock,road:s.flagstone},
 H17:{ground:s.earth,road:s.flagstone},
 // R3: only actual decks/platforms use the separate wood surface. The ground
 // around dockyards, river inns and lamp workshops is dry or damp earth/stone,
 // while Terrain's real bridge slabs retain their own wood/paving selection.
 B03:{ground:s.cobble,road:s.cobble},
 B04:{ground:s['wet-earth'],road:s.flagstone},
 B05:{ground:s.earth,road:s.cobble},
 B06:{ground:s.cobble,road:s.cobble},
 B08:{ground:s.flagstone,road:s.flagstone},
 B09:{ground:s['wet-earth'],road:s.cobble},
 B10:{ground:s['wet-earth'],road:s.cobble},
 B11:{ground:s.bedrock,road:s.flagstone},
 B12:{ground:s['wet-earth'],road:s.flagstone},
 B13:{ground:s['wet-earth'],road:s.bedrock},
 B16:{ground:s['wet-earth'],road:s.flagstone},
 B18:{ground:s.cobble,road:s.flagstone},
 // R4: built streets, gate courts, artillery platforms and the quiet large
 // battle floor use masonry. The old camp and drained moat retain worn earth.
 F01:{ground:s.cobble,road:s.cobble},
 F02:{ground:s.cobble,road:s.cobble},
 F03:{ground:s.flagstone,road:s.cobble},
 F04:{ground:s.flagstone,road:s.flagstone},
 F05:{ground:s.earth,road:s.cobble},
 F06:{ground:s.flagstone,road:s.flagstone},
 F07:{ground:s.cobble,road:s.cobble},
 F08:{ground:s.flagstone,road:s.flagstone},
 F09:{ground:s.flagstone,road:s.flagstone},
 F10:{ground:s.flagstone,road:s.flagstone},
 F11:{ground:s.flagstone,road:s.flagstone},
 F12:{ground:s.flagstone,road:s.cobble},
 F13:{ground:s.flagstone,road:s.flagstone},
 F14:{ground:s.flagstone,road:s.flagstone},
 F15:{ground:s.flagstone,road:s.cobble},
 F16:{ground:s.earth,road:s.earth},
 F17:{ground:s.bedrock,road:s.flagstone},
 // Underground circulation remains built grey stone in the former residence
 // and the daylight corridor; mining cuts still use the bedrock family above.
 'U1-06':{ground:s.flagstone,road:s.flagstone},
 'U1-10':{ground:s.flagstone,road:s.flagstone},
 'U2-04':{ground:s.flagstone,road:s.flagstone},
};

export function getMapArt(area:Pick<AreaDef,'id'|'kind'|'palette'>):MapArtProfile {
 const family=AREA_FAMILIES.get(area.id)??(area.kind==='interior'?'warm-interior':area.kind==='underground'||area.palette==='cave'?'inhabited-undercity':area.palette==='stone'?'mountain-quarry':area.palette==='marsh'?'reed-marsh':area.palette==='forest'?'birch-forest':area.kind==='town'?'town-stone':'meadow-earth');
 const base=MAP_ART_PROFILES[family],override=OVERRIDES[area.id];
 // "Warm interior" is also an art-catalog label for an inhabited workshop,
 // inn exterior or underground home. Actual interior floors are the only
 // places where that label can select wood across the whole area's ground.
 const context:Partial<MapArtProfile>=family==='warm-interior'&&area.kind!=='interior'
  ?{ground:area.kind==='underground'||area.palette==='stone'?s.flagstone:s.earth,road:area.kind==='underground'||area.palette==='stone'?s.flagstone:s.cobble}
  :family==='town-stone'&&area.kind!=='interior'&&area.palette==='stone'
   ?{ground:s.cobble,road:s.cobble}
   :family==='town-stone'&&area.kind!=='interior'&&area.palette==='marsh'
    ?{ground:s['wet-earth'],road:s.cobble}:{};
 return {...base,...context,...override};
}

/** Names of the already constructed walk surfaces. Other surfaces such as
 * woven rugs retain their own material; a rug is not recolored paving. */
export function mapArtSurface(profile:MapArtProfile,name:string):MapArtSurface|undefined {
 if(name==='Ground')return profile.ground;
 if(name==='Road')return profile.road;
 if(name==='GrassCover')return profile.grass;
 if(name==='ResidenceStoneFloor'||name==='HearthStone'||name==='Flagstone')return profile.paving;
 return undefined;
}
