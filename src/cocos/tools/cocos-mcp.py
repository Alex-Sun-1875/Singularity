"""Use the installed project-scoped Cocos MCP without changing client settings."""
from pathlib import Path
import argparse,json,re,urllib.request
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--list',action='store_true');p.add_argument('--schema');p.add_argument('--call');p.add_argument('--args');p.add_argument('--script');p.add_argument('--context',default='editor');p.add_argument('--url');a=p.parse_args()
cache=ROOT/'temp/cocos-mcp-endpoint.txt'
try:log=(ROOT/'temp/logs/project.log').read_text(encoding='utf8',errors='replace')
except OSError:log=cache.read_text(encoding='utf8') if cache.exists() else ''
urls=[a.url] if a.url else re.findall(r'http://127\.0\.0\.1:\d+/mcp/project/[a-f0-9]+/',log)
if not urls:raise SystemExit('No project-scoped Cocos MCP endpoint in this project log; open the project in Cocos.')
url=urls[-1];headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def send(method,params,n):
 request=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':n,'method':method,'params':params}).encode(),headers=headers)
 with urllib.request.urlopen(request,timeout=55) as response:
  if response.headers.get('Mcp-Session-Id'):headers['Mcp-Session-Id']=response.headers['Mcp-Session-Id']
  raw=response.read().decode();lines=[line[5:].strip() for line in raw.splitlines() if line.startswith('data:')]
  return json.loads(lines[-1] if lines else raw)
init=send('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'codex-cocos-project','version':'1'}},1)
context=init['result']['funplay']['context']
if Path(context['project_path']).resolve()!=ROOT.resolve():raise SystemExit('Cocos project routing mismatch; refusing operation')
cache.write_text(url,encoding='utf8')
if a.list or a.schema:
 listing=send('tools/list',{},2)['result']['tools'];(ROOT/'temp/cocos-mcp-tools.json').write_text(json.dumps(listing,indent=2),encoding='utf8')
 for t in listing:
  if a.schema==t['name']:print(json.dumps(t,ensure_ascii=False,indent=2))
  elif a.list:print(t['name']+': '+t.get('description','')[:160])
else:
 name=a.call or 'execute_javascript'
 args=json.loads(Path(a.args).read_text(encoding='utf8')) if a.args else {}
 if a.script:args.update({'context':a.context,'code':Path(a.script).read_text(encoding='utf8')})
 args['expected_context']=context['expected_context']
 result=send('tools/call',{'name':name,'arguments':args},3)
 for block in result.get('result',{}).get('content',[]):
  if block.get('type')=='image':print('[image payload omitted; use saved capture file]')
  elif block.get('type')=='text':print(block['text'])
 if 'error' in result:print(json.dumps(result,ensure_ascii=False))
