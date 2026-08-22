#!/usr/bin/env node
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { resolve, relative } from 'node:path';
const root=resolve(import.meta.dirname,'..');
const skip=new Set(['RELEASE_RECORD.md','tools/test-project-surface.mjs']);
const textExt=/\.(md|json|mjs|yml|yaml|html|txt)$/;
const wrong=[]; const oldCurrent=[];
function walk(dir){ for(const name of readdirSync(dir)){ const p=resolve(dir,name); const rel=relative(root,p).replaceAll('\\','/'); const s=statSync(p); if(s.isDirectory()) walk(p); else if(textExt.test(name)){ const t=readFileSync(p,'utf8'); if(t.includes(['try','openwork','org'].join('.'))) wrong.push(rel); if(!skip.has(rel)&&t.includes('openworkprotocol.io')) oldCurrent.push(rel); } } }
walk(root);
if(wrong.length) throw new Error(`wrong Try hostname in: ${wrong.join(', ')}`);
if(oldCurrent.length) throw new Error(`stale .io candidate namespace in: ${oldCurrent.join(', ')}`);
const readme=readFileSync(resolve(root,'README.md'),'utf8');
for(const token of ['https://openworkprotocol.org/','https://try.openworkprotocol.org/','ACKNOWLEDGMENTS.md']) if(!readme.includes(token)) throw new Error(`README missing ${token}`);
const ack=readFileSync(resolve(root,'ACKNOWLEDGMENTS.md'),'utf8');
if(!ack.includes('https://github.com/grogugo')) throw new Error('missing grogugo acknowledgment');
const hist=readFileSync(resolve(root,'RELEASE_RECORD.md'),'utf8');
if(!hist.includes('historical RC2 publication record') || !hist.includes('openworkprotocol.io')) throw new Error('RC2 legacy URL boundary missing');

for (const rel of ['templates/try-owp/README.md','templates/try-owp/scripts/smoke.sh','scripts/new-try-owp.sh','docs/15-run-your-own-try-owp.md','templates/try-owp/deploy/cloudflared-config.yml.example']) { try { readFileSync(resolve(root,rel),'utf8'); } catch { throw new Error(`missing ${rel}`); } }
const templateServer=readFileSync(resolve(root,'templates/try-owp/owp_field_lab/server.py'),'utf8');
if (!templateServer.includes('path.startswith("/admin")') || !templateServer.includes('path.startswith("/api/admin")')) throw new Error('template must explicitly hide admin HTTP routes');
const templateReadme=readFileSync(resolve(root,'templates/try-owp/README.md'),'utf8');
for (const token of ['greenfield build','58','Software Work Integrity']) if(!templateReadme.includes(token)) throw new Error(`template README missing ${token}`);
const fieldLabProfile=readFileSync(resolve(root,'templates/try-owp/spec/FIELD_LAB_PROFILE.md'),'utf8');
const fieldLabService=readFileSync(resolve(root,'templates/try-owp/owp_field_lab/service.py'),'utf8');
if(fieldLabProfile.includes('1.0-rc2') || fieldLabService.includes('1.0-rc2')) throw new Error('template must not advertise RC2 as its current OWP relationship');
if(!fieldLabProfile.includes('1.0-rc3 development candidate') || !fieldLabService.includes('1.0-rc3 development-candidate concepts')) throw new Error('template missing explicit RC3 development-candidate relationship');
const bootstrap=readFileSync(resolve(root,'scripts/new-try-owp.sh'),'utf8');
for (const token of ['--operator','--hostname','--provider-id','--no-test']) if(!bootstrap.includes(token)) throw new Error(`bootstrap missing ${token}`);

console.log('project surface consistency PASS');
