'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../patch/static/pwa/service-worker.js'),'utf8');
function harness(openWindow, windows = []) {
  const events = {};
  const calls = [];
  const clientApis = {
    openWindow: async url => {calls.push(['openWindow',url]);return openWindow(url);},
    matchAll: async opts=>{calls.push(['matchAll',opts]);return windows;},
    claim: async()=>{}
  };
  const sandbox = { URL, Response, caches:{}, self:{location:{origin:'https://www.norsualumni.com'},
    clients:clientApis, addEventListener:(name, callback)=>{events[name]=callback;}} };
  vm.runInNewContext(source, sandbox);
  return {events,calls};
}
async function click(h, url) {
  let task;
  let closed = false;
  h.events.notificationclick({notification:{data:{url},close:()=>{closed=true}},waitUntil:v=>{task=v;}});
  assert(closed);
  await task;
}
async function run(){
 let focused=0;
 let h=harness(async()=>({focus:async()=>{focused++;}}));
 await click(h,'/connections/messages/?conversation=12&tab=unread');
 assert.equal(focused,1);
 let dest=new URL(h.calls[0][1]);
 assert.equal(dest.pathname,'/app/notification/');
 assert.equal(dest.searchParams.get('target'),'/connections/messages/?conversation=12&tab=unread');
 console.log('PASS: push click opens notification gateway and retains original query');

 let redirected=0, fallbackFocus=0;
 h=harness(async()=>{throw Error('unavailable')}, [{url:'https://www.norsualumni.com/alumni/', navigate:async()=>{redirected++;return {focus:async()=>{fallbackFocus++}};}}]);
 await click(h,'/announcements/5/');
 assert.equal(redirected,1); assert.equal(fallbackFocus,1);
 console.log('PASS: existing-tab fallback navigates and focuses');

 h=harness(async()=>{throw Error('should not open')});
 await click(h,'https://phishing.example/login');
 assert.equal(h.calls.length,0);
 console.log('PASS: external origins rejected');

 h=harness(async()=>({focus:async()=>{}}));
 await click(h,'/app/');
 dest=new URL(h.calls[0][1]);
 assert.equal(dest.searchParams.get('target'),'/app/');
 console.log('PASS: fallback navigation uses PWA launch');
}
run().catch(error=>{console.error(error);process.exitCode=1});
