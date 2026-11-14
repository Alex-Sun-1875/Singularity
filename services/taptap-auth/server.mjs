import {createServer} from 'node:http';
import {randomBytes,createHash} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import {mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const hash=value=>createHash('sha256').update(value).digest('hex');
class HttpError extends Error {constructor(status,code){super(code);this.status=status;this.code=code;}}

/** One instance + persistent SQLite volume. Secrets and upstream bodies are never logged. */
export function createAuthService({appId,secret,dbPath='data/sessions.sqlite',ttlSeconds=86400,fetcher=fetch,now=Date.now}){
 if(!/^tap[a-z0-9]+$/i.test(appId||'')||!secret?.trim())throw new Error('Set TAPTAP_MINIAPP_ID and TAPTAP_MINIAPP_SECRET in the server environment.');
 if(!Number.isSafeInteger(ttlSeconds)||ttlSeconds<60||ttlSeconds>604800)throw new Error('SESSION_TTL_SECONDS must be 60..604800.');
 if(dbPath!==':memory:')mkdirSync(dirname(resolve(dbPath)),{recursive:true,mode:0o700});
 const db=new DatabaseSync(dbPath);
 db.exec('PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, openid TEXT NOT NULL, unionid TEXT, expires_at INTEGER NOT NULL); CREATE INDEX IF NOT EXISTS expiry ON sessions(expires_at);');
 const insert=db.prepare('INSERT INTO sessions VALUES(?,?,?,?)'),lookup=db.prepare('SELECT openid,unionid,expires_at FROM sessions WHERE token_hash=? AND expires_at>?'),prune=db.prepare('DELETE FROM sessions WHERE expires_at<=?');
 prune.run(now());
 const cleanup=setInterval(()=>prune.run(now()),60000);cleanup.unref();
 let windowStart=now(),requests=0,exchanges=0;
 const send=(res,status,body)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(body));};
 const authorization=req=>{const m=/^Bearer ([a-f0-9]{64})$/.exec(req.headers.authorization||'');if(!m)throw new HttpError(401,'SESSION_EXPIRED');return m[1];};
 const server=createServer({maxHeaderSize:8192},async(req,res)=>{
  try{
   if(req.url==='/healthz'&&req.method==='GET'){send(res,200,{ok:true});return;}
   if(now()-windowStart>=60000){windowStart=now();requests=0;exchanges=0;prune.run(now());}
   if(++requests>600)throw new HttpError(429,'RATE_LIMITED');
   if(req.url==='/auth/session'&&req.method==='GET'){
    const token=authorization(req),row=lookup.get(hash(token),now());if(!row)throw new HttpError(401,'SESSION_EXPIRED');
    send(res,200,{token,expiresAt:row.expires_at,user:{openid:row.openid,...(row.unionid?{unionid:row.unionid}:{})}});return;
   }
   if(req.url==='/auth/session'&&req.method==='DELETE'){
    db.prepare('DELETE FROM sessions WHERE token_hash=?').run(hash(authorization(req)));send(res,200,{ok:true});return;
   }
   if(req.url!=='/auth/taptap'||req.method!=='POST')throw new HttpError(404,'NOT_FOUND');
   // Bound upstream calls across all clients; ingress can add per-IP limits without trusting forwarded headers here.
   if(++exchanges>120)throw new HttpError(429,'RATE_LIMITED');
   if(!/^application\/json(?:\s*;|$)/i.test(req.headers['content-type']||''))throw new HttpError(415,'JSON_REQUIRED');
   if(Number(req.headers['content-length'])>4096)throw new HttpError(413,'BODY_TOO_LARGE');
   let text='',bytes=0;
   for await(const part of req){bytes+=part.length;if(bytes>4096)throw new HttpError(413,'BODY_TOO_LARGE');text+=part.toString('utf8');}
   let body;try{body=JSON.parse(text);}catch{throw new HttpError(400,'INVALID_JSON');}
   if(!body||body.miniAppId!==appId||typeof body.code!=='string'||!body.code.trim()||body.code.length>2048)throw new HttpError(400,'INVALID_LOGIN_REQUEST');
   const url=new URL('https://cloud-miniapp.tapapis.cn/auth/v1/jscode2session');
   url.search=new URLSearchParams({appid:appId,secret,js_code:body.code,grant_type:'authorization_code'}).toString();
   let response,identity;
   try{response=await fetcher(url,{signal:AbortSignal.timeout(10000),redirect:'error'});if(!response.ok)throw new Error('upstream');identity=await response.json();}catch{throw new HttpError(503,'TAPTAP_UNAVAILABLE');}
   if(identity?.errcode){if([40029,1040029].includes(Number(identity.errcode)))throw new HttpError(401,'INVALID_CODE');throw new HttpError(503,'TAPTAP_UNAVAILABLE');}
   if(typeof identity?.openid!=='string'||!identity.openid||typeof identity.session_key!=='string'||!identity.session_key)throw new HttpError(503,'INVALID_TAPTAP_RESPONSE');
   const token=randomBytes(32).toString('hex'),expiresAt=now()+ttlSeconds*1000;
   insert.run(hash(token),identity.openid,typeof identity.unionid==='string'?identity.unionid:null,expiresAt);
   // session_key is intentionally discarded: this game does not decrypt platform user data.
   send(res,200,{token,expiresAt,user:{openid:identity.openid,...(typeof identity.unionid==='string'?{unionid:identity.unionid}:{})}});
  }catch(error){if(!res.headersSent)send(res,error instanceof HttpError?error.status:500,{error:error instanceof HttpError?error.code:'INTERNAL_ERROR'});else res.end();}
 });
 server.requestTimeout=15000;server.headersTimeout=10000;server.keepAliveTimeout=5000;
 server.on('close',()=>{clearInterval(cleanup);db.close();});return server;
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const server=createAuthService({appId:process.env.TAPTAP_MINIAPP_ID,secret:process.env.TAPTAP_MINIAPP_SECRET,dbPath:process.env.SESSION_DB_PATH||'data/sessions.sqlite',ttlSeconds:Number(process.env.SESSION_TTL_SECONDS||86400)});
 server.listen(Number(process.env.PORT||8787),process.env.HOST||'127.0.0.1',()=>console.log('TapTap authentication service listening; configure HTTPS ingress before client use.'));
 for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>{server.close();setTimeout(()=>process.exit(0),10000).unref();});
}
