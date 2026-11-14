import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createAuthService} from './server.mjs';
const appId='taptest123',secret='fixture-secret-not-a-real-credential';
async function start(options={}){const server=createAuthService({appId,secret,dbPath:':memory:',...options});await new Promise(r=>server.listen(0,'127.0.0.1',r));return {url:`http://127.0.0.1:${server.address().port}`,close:()=>new Promise(r=>server.close(r))};}
const login=(url,code='valid')=>fetch(url+'/auth/taptap',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({code,miniAppId:appId})});
test('official exchange, durable opaque sessions, expiry and revocation; no platform secrets exposed',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'taptap-auth-')),dbPath=join(dir,'sessions.sqlite');let time=1000,calls=0;
 const options={dbPath,now:()=>time,ttlSeconds:60,fetcher:async url=>{calls++;assert.equal(url.origin,'https://cloud-miniapp.tapapis.cn');assert.equal(url.pathname,'/auth/v1/jscode2session');assert.equal(url.searchParams.get('appid'),appId);assert.equal(url.searchParams.get('secret'),secret);assert.equal(url.searchParams.get('js_code'),'valid');assert.equal(url.searchParams.get('grant_type'),'authorization_code');return Response.json({openid:'real-openid',unionid:'real-unionid',session_key:'platform-secret-key'});}};
 let service=await start(options);
 try{
  const res=await login(service.url);assert.equal(res.status,200);assert.equal(res.headers.get('cache-control'),'no-store');const text=await res.text();assert.ok(!text.includes(secret)&&!text.includes('session_key')&&!text.includes('platform-secret-key'));const body=JSON.parse(text);assert.equal(body.token.length,64);assert.equal(body.user.openid,'real-openid');assert.equal(calls,1);
  await service.close();service=await start(options);const headers={Authorization:`Bearer ${body.token}`};
  assert.equal((await fetch(service.url+'/auth/session',{headers})).status,200,'session survives server restart');
  assert.equal((await fetch(service.url+'/auth/session',{headers:{Authorization:`Bearer ${'b'.repeat(64)}`}})).status,401);
  time=62000;assert.equal((await fetch(service.url+'/auth/session',{headers})).status,401,'expired token rejected');
  const newer=await(await login(service.url)).json();const newerHeaders={Authorization:`Bearer ${newer.token}`};assert.notEqual(body.token,newer.token);
  assert.equal((await fetch(service.url+'/auth/session',{method:'DELETE',headers:newerHeaders})).status,200);assert.equal((await fetch(service.url+'/auth/session',{headers:newerHeaders})).status,401);
 }finally{await service.close();rmSync(dir,{recursive:true,force:true});}
});
test('invalid request and upstream rejection never create authenticated identity',async()=>{
 let calls=0;const service=await start({fetcher:async()=>{calls++;return Response.json({errcode:1040029,errmsg:'sensitive-upstream-detail'});}});
 try{
  assert.equal((await login(service.url,'')).status,400);assert.equal(calls,0);
  assert.equal((await login(service.url,'x'.repeat(5000))).status,413);assert.equal(calls,0);
  const rejected=await login(service.url);assert.equal(rejected.status,401);assert.deepEqual(await rejected.json(),{error:'INVALID_CODE'});
  assert.equal((await fetch(service.url+'/auth/session')).status,401);
 }finally{await service.close();}
});
test('malformed or unavailable platform response is sanitized',async()=>{
 for(const fetcher of [async()=>Response.json({openid:'fake',session_key:''}),async()=>{throw new Error('secret in upstream URL');},async()=>new Response('',{status:500})]){
  const service=await start({fetcher});try{const res=await login(service.url);assert.equal(res.status,503);assert.ok(!(await res.text()).includes('secret'));}finally{await service.close();}
 }
 assert.throws(()=>createAuthService({appId,secret:''}),/environment/);
});
