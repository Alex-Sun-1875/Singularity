"""Verify delivered FBX bytes and the Blender roundtrip report, without Blender."""
from pathlib import Path
import json,struct,zlib,unittest,hashlib,os
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))
SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'))
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
CLIPS={'idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact'}
def fbx_nodes(data):
    """Read binary FBX 7.4 nodes, including compressed cluster weight arrays."""
    if data[:23]!=b'Kaydara FBX Binary  \x00\x1a\x00':raise ValueError('Not binary FBX')
    if struct.unpack_from('<I',data,23)[0]!=7400:raise ValueError('Expected FBX 7400')
    def prop(offset):
        kind=chr(data[offset]);offset+=1
        simple={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}
        if kind in simple:
            fmt='<'+simple[kind];return struct.unpack_from(fmt,data,offset)[0],offset+struct.calcsize(fmt)
        if kind in 'SR':
            length=struct.unpack_from('<I',data,offset)[0];offset+=4
            value=data[offset:offset+length]
            return (value.decode('utf-8','replace') if kind=='S' else value),offset+length
        if kind in 'fdlibc':
            length,encoding,size=struct.unpack_from('<III',data,offset);offset+=12
            raw=data[offset:offset+size]
            if encoding:raw=zlib.decompress(raw)
            fmt={'f':'f','d':'d','l':'q','i':'i','b':'?','c':'B'}[kind]
            return struct.unpack('<'+str(length)+fmt,raw),offset+size
        raise ValueError('Unknown FBX property '+kind)
    def node(offset):
        end,count,length,nlen=struct.unpack_from('<IIIB',data,offset)
        if end==0:return None,offset+13
        offset+=13;name=data[offset:offset+nlen].decode();offset+=nlen;properties=[]
        for _ in range(count):value,offset=prop(offset);properties.append(value)
        children=[]
        while offset<end:
            child,next_offset=node(offset)
            if child:children.append(child)
            offset=next_offset
            if child is None:break
        return {'name':name,'properties':properties,'children':children},end
    result=[];offset=27
    while offset<len(data)-13:
        value,offset=node(offset)
        if not value:break
        result.append(value)
    return result
def child(node,name):return next((n for n in node['children'] if n['name']==name),None)
class CharacterAssets(unittest.TestCase):
    def test_texture_budget_and_preserved_authoring_maps(self):
        actor_root=OUT
        native_manifests=[json.loads((actor_root/i/'manifest.json').read_text())for i in IDS if(actor_root/i/'manifest.json').is_file()]
        if any(m.get('runtimeProfile')=='native-kit-v1'for m in native_manifests):
            # Native kit uses shared original PBR maps at512, with principal
            # heads1024. Root approved these explicit mobile import budgets;
            # the old6.5MB budget belonged to256px procedural MPFB maps.
            maps=list((actor_root/'native-shared/textures').glob('*.png'))
            self.assertLessEqual(sum(p.stat().st_size for p in maps),16000000)
            base=0;mip=0
            for p in maps:
                w,h=struct.unpack_from('>II',p.read_bytes(),16);base+=w*h*4
                while True:
                    mip+=w*h*4
                    if w==1 and h==1:break
                    w=max(1,w//2);h=max(1,h//2)
            self.assertLessEqual(base,64*1024*1024)
            self.assertLessEqual(mip,86*1024*1024)
        else:self.assertLess(sum(p.stat().st_size for p in actor_root.glob('*/textures/*.png')),6500000)
        for identity in IDS:
            manifest=json.loads((actor_root/identity/'manifest.json').read_text())
            if manifest.get('runtimeProfile')=='native-kit-v1':
                for record in manifest['textureProvenance']:
                    original=ROOT/record['source'];png=original.read_bytes()
                    self.assertEqual(hashlib.sha256(png).hexdigest(),record['sourceSHA256'])
                    self.assertGreaterEqual(max(struct.unpack_from('>II',png,16)),max(record['size']))
            else:
                png=(SOURCE/'textures'/identity/'skin.png').read_bytes()
                self.assertGreaterEqual(max(struct.unpack_from('>II',png,16)),2048)
    def test_modular_weapon_meshes(self):
        folder=OUT/'props'
        if not(folder/'manifest.json').is_file()and(OUT.parent/'props/manifest.json').is_file():folder=OUT.parent/'props'
        manifest=json.loads((folder/'manifest.json').read_text())
        native=manifest.get('pipeline')=='tools/model-pipeline/cocos_native_props.py'
        if not native:self.assertEqual(manifest['gripOrigin'],[0,0,0]);self.assertEqual(manifest['cocosLongAxis'],'+Y')
        for name in ['sword','bow','staff']:
            objects=next(n for n in fbx_nodes((folder/f'{name}.fbx').read_bytes()) if n['name']=='Objects')['children']
            geometries=[n for n in objects if n['name']=='Geometry'and n['properties'][2]=='Mesh']
            self.assertGreater(sum(len(child(n,'PolygonVertexIndex')['properties'][0]) for n in geometries),60)
            if native:
                prop=manifest['props'][name]
                self.assertEqual(prop['exportGripOrigin'],[0,0,0]);self.assertEqual(prop['cocosLongAxis'],'+Y')
                triangles=sum(len(child(n,'PolygonVertexIndex')['properties'][0])-2*sum(i<0 for i in child(n,'PolygonVertexIndex')['properties'][0])for n in geometries)
                self.assertEqual(triangles,prop['topology']['sourceTriangles'])
                self.assertEqual(hashlib.sha256((folder/f'{name}.fbx').read_bytes()).hexdigest(),prop['exportSHA256'])
                self.assertTrue(prop['fbxRoundtrip']['passed'])
                if name=='bow':self.assertIn('Draw',prop['fbxRoundtrip']['shapeNamesAfterFBXImport'])
            for texture in [n for n in objects if n['name']=='Texture']:
                relative=child(texture,'RelativeFilename')['properties'][0].replace('\\','/')
                self.assertTrue(relative.startswith('textures/'));self.assertTrue((folder/relative).is_file())
    def test_actual_fbx_and_roundtrip(self):
        for identity in IDS:
            with self.subTest(character=identity):
                folder=OUT/identity
                manifest=json.loads((folder/'manifest.json').read_text())
                native=manifest.get('runtimeProfile')=='native-kit-v1'
                if native:self.assertFalse(any((folder/'textures').glob('*.png')),'Native bundle must not retain unused legacy MPFB PNGs')
                fbx=folder/f'{identity}.fbx'
                self.assertTrue(fbx.is_file(),f'Missing animated FBX: {fbx}')
                data=fbx.read_bytes()
                self.assertEqual(data[:23],b'Kaydara FBX Binary  \x00\x1a\x00')
                self.assertGreater(len(data),100000)
                nodes=fbx_nodes(data);objects=next(n for n in nodes if n['name']=='Objects')['children']
                self.assertEqual(sum(n['name']=='Model' and n['properties'][2]=='LimbNode' for n in objects),manifest['skeletonJointCount'] if native else 53)
                if native:self.assertEqual(manifest['skinJointCount'],65)
                actual_clips={n['properties'][1].split('\x00')[0].split('|')[-1] for n in objects if n['name']=='AnimationStack'}
                self.assertTrue(CLIPS.issubset(actual_clips))
                geometries=[n for n in objects if n['name']=='Geometry' and n['properties'][2]=='Mesh']
                self.assertGreater(sum(sum(index<0 for index in child(n,'PolygonVertexIndex')['properties'][0]) for n in geometries),10000)
                runtime_triangles=sum(len(child(n,'PolygonVertexIndex')['properties'][0])-2*sum(i<0 for i in child(n,'PolygonVertexIndex')['properties'][0]) for n in geometries)
                self.assertLessEqual(runtime_triangles,65000 if identity=='raphael' else (60000 if identity=='mira' else 45000))
                textures=[n for n in objects if n['name']=='Texture']
                self.assertGreater(len(textures),5)
                for texture in textures:
                    relative=child(texture,'RelativeFilename')['properties'][0].replace('\\','/')
                    self.assertTrue(relative.startswith('../native-shared/textures/') if native else relative.startswith('textures/'),'FBX must reference runtime textures: '+relative)
                    self.assertTrue((folder/relative).is_file(),relative)
                    self.assertTrue((folder/relative).resolve().is_relative_to(OUT.resolve()))
                connections=next(n for n in nodes if n['name']=='Connections')['children']
                parents={n['properties'][1]:n['properties'][2] for n in connections if n['properties'][0]=='OO'}
                influences=defaultdict(int)
                for cluster in [n for n in objects if n['name']=='Deformer' and n['properties'][2]=='Cluster']:
                    indices=child(cluster,'Indexes');weights=child(cluster,'Weights')
                    if indices and weights:
                        for index,weight in zip(indices['properties'][0],weights['properties'][0]):
                            if weight>1e-6:influences[(parents[cluster['properties'][0]],index)]+=1
                self.assertLessEqual(max(influences.values()),4)
                self.assertTrue(CLIPS.issubset(set(manifest['clips'])))
                self.assertEqual(manifest['axis'],{'forward':'Z','up':'Y','meters':True})
                self.assertLessEqual(manifest['maxInfluences'],4)
                self.assertGreater(manifest['triangles'],15000)
                self.assertEqual(manifest['triangles'],runtime_triangles)
                self.assertIn('hand_r',manifest['bones'])
                for name,grip in manifest['sockets']['grips'].items():
                    self.assertTrue(grip['path'].endswith('/'+name))
                    self.assertLess(abs(sum(q*q for q in grip['uprightIdleRotationXYZW'])-1),.001)
                self.assertTrue(all((folder/p).is_file() for p in manifest['textures']))
                for relative in manifest['textures']:
                    png=(folder/relative).read_bytes();width,height=struct.unpack_from('>II',png,16)
                    limit=(1024 if identity in ['raphael','mira'] else 512) if native else (1024 if relative.endswith('/skin.png') else (512 if relative.endswith(('/eyes.png','/brows.png')) else 256))
                    self.assertLessEqual(max(width,height),limit)
                self.assertTrue(all(name.encode() in data for name in CLIPS))
                check=json.loads((folder/'inspection.json').read_text())
                self.assertEqual(check['fbxSha256'],hashlib.sha256(data).hexdigest(),'Stale Blender roundtrip report')
                self.assertGreaterEqual(check['boneCount'],53)
                self.assertTrue(CLIPS.issubset(set(check['actions'])))
                self.assertGreater(check['animatedVertexDelta'],.05)
                self.assertLess(check['deathFinalDelta'],.001)
                self.assertGreater(min(check['motionGroundMinimum'].values()),-.008)
                self.assertTrue(check['allImagesResolved'])
                if native:
                    self.assertEqual(check['meshCount'],sum(len(p['nodes'])for p in manifest['parts'].values()))
                    self.assertTrue({'body','arms','legs','feet','head','hair'}.issubset(manifest['parts']))
                else:self.assertGreater(check['meshCount'],8)
                self.assertLess(abs(check['idleGround']),.035)
                self.assertGreater(check['height'],1.5)
                self.assertLess(check['height'],2.2)
                self.assertLess(abs(check['height']-manifest.get('geometry',{}).get('idleHeightMetres',manifest['profile']['height'])),.035)
                self.assertGreater(check['distinctMotionSignatures'],8)
if __name__=='__main__': unittest.main()
