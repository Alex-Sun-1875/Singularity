"""Read the actual frozen compiled profile; never changes rules or the bundle."""
from pathlib import Path
import hashlib,json,re


def extract(report,root):
 served=(root/report['buildProvenance']['servedBuild']).resolve()
 mains=[path for path in (served/'assets/main').glob('index*.js') if re.fullmatch(r'index(?:\..+)?\.js',path.name)]
 assert len(mains)==1
 main=mains[0];payload=main.read_bytes();digest=hashlib.sha256(payload).hexdigest()
 assert digest==report['gameHash']
 match=re.search(r'"BUILD_PROFILE",Object\.freeze\((\{[^}]+\})\)',payload.decode('utf8'))
 assert match,'Frozen bundle did not expose an unambiguous BUILD_PROFILE literal'
 literal=match[1];json_text=re.sub(r'([,{])([A-Za-z_][A-Za-z_0-9]*):',r'\1"\2":',literal).replace('!0','true').replace('!1','false')
 profile=json.loads(json_text)
 assert profile['name']=='test' and profile['schemaVersion']==2
 return {'servedMain':str(main.relative_to(root)).replace('\\','/'),'compiledSha256':digest,'compiledLiteral':literal,'actualProfile':profile,
  'qualification':'Read from the frozen served bundle. This task checks training-range VFX and actual casts, not campaign growth/balance acceptance. Concurrent profile flags are recorded as compiled and are never changed to force normal-rule claims.'}
