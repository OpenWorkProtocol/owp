#!/usr/bin/env node
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { verifyBundle } from './verify-software-work-integrity.mjs';
const dir=new URL('../test/software-work-integrity-vectors/',import.meta.url);
let n=0;
for(const name of readdirSync(dir).filter(x=>x.endsWith('.json')).sort()){
 const v=JSON.parse(readFileSync(new URL(name,dir),'utf8')); let ok=true, err='';
 try{verifyBundle(v.bundle)}catch(e){ok=false;err=e.message}
 if(ok!==v.expected_valid){console.error(`not ok - ${name}: expected ${v.expected_valid}, got ${ok}: ${err}`);process.exit(1)}
 n++; console.log(`ok ${n} - ${name}`);
}
console.log(`# ${n} static vectors passed`);
