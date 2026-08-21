#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { resolve, dirname, normalize } from 'node:path';
const root=resolve(import.meta.dirname,'..');
const site=resolve(root,'site');
const required=['index.html','security.html','try.html','404.html','styles.css','app.js','favicon.svg','og-card.png','robots.txt','sitemap.xml','site.webmanifest','CNAME','.nojekyll'];
for (const f of required) { if (!existsSync(resolve(site,f))) throw new Error(`missing site/${f}`); }
const allHtml=readdirSync(site).filter(x=>x.endsWith('.html'));
for (const f of allHtml) {
  const text=readFileSync(resolve(site,f),'utf8');
  if (!/<!doctype html>/i.test(text)) throw new Error(`${f}: missing doctype`);
  if (!/<meta[^>]+name="viewport"/i.test(text)) throw new Error(`${f}: missing viewport`);
  if (text.includes(['try','openwork','org'].join('.'))) throw new Error(`${f}: wrong Try OWP hostname`);
}
const index=readFileSync(resolve(site,'index.html'),'utf8');
const tryPage=readFileSync(resolve(site,'try.html'),'utf8');
const css=readFileSync(resolve(site,'styles.css'),'utf8');
for (const token of ['.tag{','.card pre{']) if(!css.includes(token)) throw new Error(`styles missing ${token}`);
for (const token of ['Run your own','scripts/new-try-owp.sh','Field Lab results are not conformance certification','greenfield build idea','58-test']) if(!tryPage.includes(token)) throw new Error(`try page missing ${token}`);
for (const token of ['https://try.openworkprotocol.org/','21/21','256','grogugo','development candidate','Experiment ≠ conformance','Spin up your own Try OWP','id="try-your-own"','class="section-head"']) {
  if (!index.includes(token)) throw new Error(`index missing ${token}`);
}
const href=/href="([^"]+)"/g;
for (const f of allHtml) {
  const text=readFileSync(resolve(site,f),'utf8');
  for (const m of text.matchAll(href)) {
    const h=m[1];
    if (h.startsWith('http:')||h.startsWith('https:')||h.startsWith('mailto:')||h.startsWith('#')) continue;
    const clean=h.split('#')[0].split('?')[0];
    if (!clean || clean==='/') continue;
    const target=clean.startsWith('/') ? resolve(site,clean.slice(1)) : resolve(dirname(resolve(site,f)),clean);
    if (!existsSync(target)) throw new Error(`${f}: broken local href ${h}`);
  }
}
if (readFileSync(resolve(site,'CNAME'),'utf8').trim()!=='openworkprotocol.org') throw new Error('wrong CNAME');
console.log(`site smoke PASS (${allHtml.length} HTML pages)`);
