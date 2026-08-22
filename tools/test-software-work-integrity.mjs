#!/usr/bin/env node
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, cpSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import {
  PROFILE, IN_TOTO_STATEMENT, TEST_RESULT_PREDICATE, VALIDATION_PREDICATE,
  IndeterminateError, sha256Id, verifyBundle, verifyGitReality, computeChangeSetDigest
} from './verify-software-work-integrity.mjs';

function git(cwd,args){ const r=spawnSync('git',args,{cwd,encoding:'utf8'}); if(r.status!==0) throw new Error(`git ${args.join(' ')}: ${r.stderr}`); return r.stdout.trim(); }
function sh(cwd,cmd){ const r=spawnSync(cmd,{cwd,shell:true,encoding:'utf8'}); if(r.status!==0) throw new Error(`${cmd}: ${r.stderr||r.stdout}`); return r.stdout.trim(); }
function clone(x){ return structuredClone(x); }
function mustFail(name,fn,needle){
  try { fn(); throw new Error(`NEGATIVE TEST DID NOT FAIL: ${name}`); }
  catch(e){ if(e.message.startsWith('NEGATIVE TEST DID NOT FAIL')) throw e; if(needle && !e.message.includes(needle)) throw new Error(`${name}: wrong failure: ${e.message}`); }
}

function agreement(workRef='PAY-4'){
  const body={
    profile:PROFILE, work_ref:workRef, outcome:'Implement retry logic without unrelated changes.',
    definition_of_done:[{id:'native-tests',tier:'deterministic',statement:'Native test passes from exact result.',command:'node test.js'}],
    scope:{allowed_paths:['src/**','test.js'],forbidden_paths:['.github/**','.env','secrets/**']},
    evidence_policy:{independent_validation:true,fresh_environment:true,require_exact_result_subject:true,require_diff_review:true}
  };
  const d=sha256Id(body);
  return {contract_body:body,contract_digest:d,acknowledgements:[
    {role:'customer',actor_id:'customer:acme',decision:'ACCEPT',contract_digest:d},
    {role:'provider',actor_id:'provider:alpha',decision:'ACCEPT',contract_digest:d},
    {role:'orchestrator',actor_id:'orchestrator:alpha',decision:'ACCEPT',contract_digest:d},
    {role:'owp_validator',actor_id:'validator:independent',decision:'ACCEPT',contract_digest:d},
  ]};
}

function buildRepo(){
  const dir=mkdtempSync(join(tmpdir(),'owp-swi-repo-'));
  git(dir,['init','-q','-b','main']); git(dir,['config','user.email','test@example.invalid']); git(dir,['config','user.name','OWP Fixture']);
  mkdirSync(join(dir,'src'));
  writeFileSync(join(dir,'src','retry.js'),'export function retry(x){ return x; }\n');
  writeFileSync(join(dir,'test.js'),"import { retry } from './src/retry.js';\nif (retry('ok') !== 'ok') process.exit(1);\n");
  writeFileSync(join(dir,'package.json'),'{"type":"module"}\n');
  git(dir,['add','.']); git(dir,['commit','-q','-m','base']);
  const base=git(dir,['rev-parse','HEAD']), baseTree=git(dir,['rev-parse','HEAD^{tree}']);
  writeFileSync(join(dir,'src','retry.js'),"export function retry(x){ for(let i=0;i<3;i++){ if(x) return x; } return x; }\n");
  git(dir,['add','src/retry.js']); git(dir,['commit','-q','-m','result']);
  const result=git(dir,['rev-parse','HEAD']), resultTree=git(dir,['rev-parse','HEAD^{tree}']);
  return {dir,base,baseTree,result,resultTree,diffDigest:computeChangeSetDigest(dir,base,result)};
}

function makeBundle(repo, {revision=0, provider='provider:alpha', orchestrator='orchestrator:alpha', parent=null, delta=[]}={}){
  const a=agreement();
  // A new provider/orchestrator on a revision must also be the actors that accepted this agreement.
  a.acknowledgements.find(x=>x.role==='provider').actor_id=provider;
  a.acknowledgements.find(x=>x.role==='orchestrator').actor_id=orchestrator;
  const ex={profile:PROFILE,work_ref:'PAY-4',attempt_id:`attempt-${revision+1}`,revision,contract_digest:a.contract_digest,provider_id:provider,orchestrator_id:orchestrator,
    source_snapshot:{repository_uri:'file://fixture/repo',object_format:git(repo.dir,['rev-parse','--show-object-format']),base_commit:repo.base,base_tree:repo.baseTree},
    acceptance_delta:delta,parent};
  const exd=sha256Id(ex);
  const attempt_acceptance={execution_commitment_digest:exd,acknowledgements:[
    {role:'customer',actor_id:'customer:acme',decision:'ACCEPT',execution_commitment_digest:exd},
    {role:'provider',actor_id:provider,decision:'ACCEPT',execution_commitment_digest:exd},
    {role:'orchestrator',actor_id:orchestrator,decision:'ACCEPT',execution_commitment_digest:exd},
    {role:'owp_validator',actor_id:'validator:independent',decision:'ACCEPT',execution_commitment_digest:exd},
  ]};
  const delivery={work_ref:'PAY-4',attempt_id:ex.attempt_id,contract_digest:a.contract_digest,execution_commitment_digest:exd,provider_id:provider,repository_uri:'file://fixture/repo',claimed_base_commit:repo.base,result_commit:repo.result,result_tree:repo.resultTree,diff_digest:repo.diffDigest,evidence_refs:[]};
  const tr={_type:IN_TOTO_STATEMENT,subject:[{name:'fixture/repo',digest:{gitCommit:repo.result,gitTree:repo.resultTree}}],predicateType:TEST_RESULT_PREDICATE,predicate:{result:'PASSED',configuration:[{name:'node test.js'}],passedTests:['native-tests'],warnedTests:[],failedTests:[]}};
  const trd=sha256Id(tr);
  const acceptanceResults=[...a.contract_body.definition_of_done,...delta].filter(x=>x.tier!=='human').map(x=>({id:x.id,outcome:'PASS',evidence_digest:x.tier==='deterministic'?trd:'sha256:'+'1'.repeat(64)}));
  const att={_type:IN_TOTO_STATEMENT,subject:[{name:'fixture/repo',digest:{gitCommit:repo.result,gitTree:repo.resultTree}}],predicateType:VALIDATION_PREDICATE,predicate:{work_ref:'PAY-4',attempt_id:ex.attempt_id,contract_digest:a.contract_digest,execution_commitment_digest:exd,expected_source:{base_commit:repo.base,base_tree:repo.baseTree},observed_result:{result_commit:repo.result,result_tree:repo.resultTree},delivery_claim_digest:sha256Id(delivery),validator:'validator:independent',policy_version:'owp-swi-v1',acceptance_results:acceptanceResults,outcome:'VALID'}};
  const attd=sha256Id(att);
  const disp={work_ref:'PAY-4',attempt_id:ex.attempt_id,validator_attestation_digest:attd,decision:'APPROVE',feedback:{}};
  return {agreement:a,execution_commitment:ex,execution_commitment_digest:exd,attempt_acceptance,delivery_claim:delivery,validator_attestation:att,validator_attestation_digest:attd,test_result:tr,customer_disposition:disp,customer_disposition_digest:sha256Id(disp)};
}

const tests=[]; const t=(name,fn)=>tests.push([name,fn]);
let repo;
t('positive bundle and real Git validation',()=>{ repo=buildRepo(); const b=makeBundle(repo); verifyBundle(b); verifyGitReality(b,repo.dir,{allowExec:true}); });
t('wrong provider-claimed base is rejected',()=>{const b=makeBundle(repo); b.delivery_claim.claimed_base_commit='0'.repeat(40); mustFail('wrong base',()=>verifyBundle(b),null);});
t('abbreviated Git OID is rejected',()=>{const b=makeBundle(repo); b.execution_commitment.source_snapshot.base_commit=b.execution_commitment.source_snapshot.base_commit.slice(0,12); b.execution_commitment_digest=sha256Id(b.execution_commitment); b.attempt_acceptance.execution_commitment_digest=b.execution_commitment_digest; for(const a of b.attempt_acceptance.acknowledgements)a.execution_commitment_digest=b.execution_commitment_digest; b.delivery_claim.execution_commitment_digest=b.execution_commitment_digest; mustFail('abbrev',()=>verifyBundle(b),'full lowercase');});
t('wrong base tree is rejected by real Git validation',()=>{const b=makeBundle(repo); b.execution_commitment.source_snapshot.base_tree='0'.repeat(40); b.execution_commitment_digest=sha256Id(b.execution_commitment); b.attempt_acceptance.execution_commitment_digest=b.execution_commitment_digest; for(const a of b.attempt_acceptance.acknowledgements)a.execution_commitment_digest=b.execution_commitment_digest; b.delivery_claim.execution_commitment_digest=b.execution_commitment_digest; b.validator_attestation.predicate.execution_commitment_digest=b.execution_commitment_digest; b.validator_attestation.predicate.expected_source.base_tree='0'.repeat(40); b.validator_attestation.predicate.delivery_claim_digest=sha256Id(b.delivery_claim); b.validator_attestation_digest=sha256Id(b.validator_attestation); b.customer_disposition.validator_attestation_digest=b.validator_attestation_digest; b.customer_disposition_digest=sha256Id(b.customer_disposition); verifyBundle(b); mustFail('tree',()=>verifyGitReality(b,repo.dir,{allowExec:true}),'base_tree');});
t('result tree substitution is rejected',()=>{const b=makeBundle(repo); b.delivery_claim.result_tree='0'.repeat(40); mustFail('tree substitution',()=>verifyBundle(b),'gitTree');});
t('test result on different commit is rejected',()=>{const b=makeBundle(repo); b.test_result.subject[0].digest.gitCommit=repo.base; mustFail('test substitution',()=>verifyBundle(b),'exact delivered');});
t('missing deterministic test evidence is rejected',()=>{const b=makeBundle(repo); delete b.test_result; mustFail('missing test',()=>verifyBundle(b),'requires exact-subject');});
t('deterministic acceptance evidence digest must name the exact test statement',()=>{const b=makeBundle(repo); b.test_result.predicate.configuration=[{name:'different command'}]; mustFail('test evidence digest',()=>verifyBundle(b),'not bound to the exact test-result');});
t('four-party agreement requires all roles',()=>{const b=makeBundle(repo); b.agreement.acknowledgements=b.agreement.acknowledgements.filter(x=>x.role!=='owp_validator'); mustFail('missing role',()=>verifyBundle(b),'missing owp_validator');});
t('validator must be independent from provider',()=>{const b=makeBundle(repo); b.agreement.acknowledgements.find(x=>x.role==='owp_validator').actor_id='provider:alpha'; mustFail('independence',()=>verifyBundle(b),'not independent');});
t('different contract digest acknowledgement is rejected',()=>{const b=makeBundle(repo); b.agreement.acknowledgements.find(x=>x.role==='orchestrator').contract_digest='sha256:'+'0'.repeat(64); mustFail('digest agreement',()=>verifyBundle(b),'different contract');});
t('Attempt acceptance requires all four roles on exact execution digest',()=>{const b=makeBundle(repo); b.attempt_acceptance.acknowledgements=b.attempt_acceptance.acknowledgements.filter(x=>x.role!=='customer'); mustFail('attempt role',()=>verifyBundle(b),'missing customer Attempt');});
t('Attempt acknowledgement cannot accept a different execution digest',()=>{const b=makeBundle(repo); b.attempt_acceptance.acknowledgements.find(x=>x.role==='owp_validator').execution_commitment_digest='sha256:'+'0'.repeat(64); mustFail('attempt digest',()=>verifyBundle(b),'different Attempt digest');});
t('delivery cannot bind wrong Attempt',()=>{const b=makeBundle(repo); b.delivery_claim.attempt_id='attempt-other'; mustFail('attempt mismatch',()=>verifyBundle(b),'attempt_id mismatch');});
t('acceptance delta must be evaluated',()=>{const delta=[{id:'extra-check',tier:'deterministic',statement:'Extra check',command:'node test.js'}]; const b=makeBundle(repo,{delta}); b.validator_attestation.predicate.acceptance_results=b.validator_attestation.predicate.acceptance_results.filter(x=>x.id!=='extra-check'); b.validator_attestation_digest=sha256Id(b.validator_attestation); b.customer_disposition.validator_attestation_digest=b.validator_attestation_digest; b.customer_disposition_digest=sha256Id(b.customer_disposition); mustFail('delta missing',()=>verifyBundle(b),'extra-check');});
t('real validator requires explicit permission to execute commands',()=>{const b=makeBundle(repo); mustFail('exec gate',()=>verifyGitReality(b,repo.dir,{allowExec:false}),'explicitly enabled');});
t('unavailable required command execution is classified INDETERMINATE',()=>{const b=makeBundle(repo); try{verifyGitReality(b,repo.dir,{allowExec:false}); throw new Error('expected INDETERMINATE');}catch(e){if(!(e instanceof IndeterminateError)) throw e;}});
t('reference verifier refuses to fake a hardened production sandbox',()=>{const b=makeBundle(repo); b.agreement.contract_body.evidence_policy.hardened_sandbox=true; b.agreement.contract_digest=sha256Id(b.agreement.contract_body); for(const a of b.agreement.acknowledgements)a.contract_digest=b.agreement.contract_digest; b.execution_commitment.contract_digest=b.agreement.contract_digest; b.execution_commitment_digest=sha256Id(b.execution_commitment); b.attempt_acceptance.execution_commitment_digest=b.execution_commitment_digest; for(const a of b.attempt_acceptance.acknowledgements)a.execution_commitment_digest=b.execution_commitment_digest; b.delivery_claim.contract_digest=b.agreement.contract_digest; b.delivery_claim.execution_commitment_digest=b.execution_commitment_digest; b.validator_attestation.predicate.contract_digest=b.agreement.contract_digest; b.validator_attestation.predicate.execution_commitment_digest=b.execution_commitment_digest; b.validator_attestation.predicate.delivery_claim_digest=sha256Id(b.delivery_claim); b.validator_attestation_digest=sha256Id(b.validator_attestation); b.customer_disposition.validator_attestation_digest=b.validator_attestation_digest; b.customer_disposition_digest=sha256Id(b.customer_disposition); verifyBundle(b); try{verifyGitReality(b,repo.dir,{allowExec:true}); throw new Error('expected INDETERMINATE');}catch(e){if(!(e instanceof IndeterminateError)) throw e;}});
t('forbidden changed path is rejected',()=>{const evil=mkdtempSync(join(tmpdir(),'owp-swi-evil-')); cpSync(repo.dir,evil,{recursive:true}); git(evil,['config','user.email','test@example.invalid']); git(evil,['config','user.name','OWP Fixture']); mkdirSync(join(evil,'.github'),{recursive:true}); writeFileSync(join(evil,'.github','pwn.yml'),'name: pwn\n'); git(evil,['add','.github/pwn.yml']); git(evil,['commit','-q','-m','forbidden']); const r={dir:evil,base:repo.base,baseTree:repo.baseTree,result:git(evil,['rev-parse','HEAD']),resultTree:git(evil,['rev-parse','HEAD^{tree}'])}; r.diffDigest=computeChangeSetDigest(evil,r.base,r.result); const b=makeBundle(r); verifyBundle(b); mustFail('forbidden',()=>verifyGitReality(b,evil,{allowExec:true}),'outside allowed scope'); rmSync(evil,{recursive:true,force:true});});
t('unrelated history is rejected',()=>{const other=mkdtempSync(join(tmpdir(),'owp-swi-other-')); git(other,['init','-q','-b','main']); git(other,['config','user.email','test@example.invalid']);git(other,['config','user.name','OWP Fixture']); mkdirSync(join(other,'src')); writeFileSync(join(other,'src','retry.js'),'x\n'); writeFileSync(join(other,'test.js'),'process.exit(0)\n'); writeFileSync(join(other,'package.json'),'{"type":"module"}\n'); git(other,['add','.']);git(other,['commit','-q','-m','other']); const b=makeBundle(repo); const newResult=git(other,['rev-parse','HEAD']); const newTree=git(other,['rev-parse','HEAD^{tree}']); git(repo.dir,['fetch','-q',other,newResult]); b.delivery_claim.result_commit=newResult; b.delivery_claim.result_tree=newTree; b.delivery_claim.diff_digest=computeChangeSetDigest(repo.dir,repo.base,newResult); b.validator_attestation.subject[0].digest={gitCommit:newResult,gitTree:newTree}; b.validator_attestation.predicate.observed_result={result_commit:newResult,result_tree:newTree}; b.validator_attestation.predicate.delivery_claim_digest=sha256Id(b.delivery_claim); b.test_result.subject[0].digest={gitCommit:newResult,gitTree:newTree}; const trd=sha256Id(b.test_result); for(const r of b.validator_attestation.predicate.acceptance_results) if(r.id==='native-tests') r.evidence_digest=trd; b.validator_attestation_digest=sha256Id(b.validator_attestation); b.customer_disposition.validator_attestation_digest=b.validator_attestation_digest;b.customer_disposition_digest=sha256Id(b.customer_disposition); verifyBundle(b); mustFail('unrelated',()=>verifyGitReality(b,repo.dir,{allowExec:true}),'not descended'); rmSync(other,{recursive:true,force:true});});
t('revision handoff must start from validator-attested prior result',()=>{const first=makeBundle(repo); first.customer_disposition.decision='STEER'; first.customer_disposition.feedback={requested_change:'one more check'}; first.customer_disposition_digest=sha256Id(first.customer_disposition); // make next commit
 writeFileSync(join(repo.dir,'src','retry.js'),readFileSync(join(repo.dir,'src','retry.js'),'utf8')+'// revision\n');git(repo.dir,['add','src/retry.js']);git(repo.dir,['commit','-q','-m','revision']); const r2={dir:repo.dir,base:first.delivery_claim.result_commit,baseTree:first.delivery_claim.result_tree,result:git(repo.dir,['rev-parse','HEAD']),resultTree:git(repo.dir,['rev-parse','HEAD^{tree}'])};r2.diffDigest=computeChangeSetDigest(repo.dir,r2.base,r2.result); const parent={attempt_id:first.execution_commitment.attempt_id,validator_attestation_digest:first.validator_attestation_digest,customer_disposition_digest:first.customer_disposition_digest}; const second=makeBundle(r2,{revision:1,provider:'provider:beta',orchestrator:'orchestrator:beta',parent,delta:[{id:'steer-check',tier:'deterministic',statement:'Steered result still tests',command:'node test.js'}]}); second.customer_disposition.decision='APPROVE'; second.customer_disposition_digest=sha256Id(second.customer_disposition); verifyBundle(first); verifyBundle(second,first); verifyGitReality(second,repo.dir,{allowExec:true}); const bad=clone(second); bad.execution_commitment.source_snapshot.base_commit=repo.base; bad.execution_commitment.source_snapshot.base_tree=repo.baseTree; bad.execution_commitment_digest=sha256Id(bad.execution_commitment); bad.attempt_acceptance.execution_commitment_digest=bad.execution_commitment_digest; for(const a of bad.attempt_acceptance.acknowledgements)a.execution_commitment_digest=bad.execution_commitment_digest; bad.delivery_claim.execution_commitment_digest=bad.execution_commitment_digest; bad.delivery_claim.claimed_base_commit=repo.base; bad.validator_attestation.predicate.execution_commitment_digest=bad.execution_commitment_digest; bad.validator_attestation.predicate.expected_source={base_commit:repo.base,base_tree:repo.baseTree}; bad.validator_attestation.predicate.delivery_claim_digest=sha256Id(bad.delivery_claim); bad.validator_attestation_digest=sha256Id(bad.validator_attestation); bad.customer_disposition.validator_attestation_digest=bad.validator_attestation_digest;bad.customer_disposition_digest=sha256Id(bad.customer_disposition); mustFail('bad handoff',()=>verifyBundle(bad,first),'not prior validator-attested');});

let passed=0;
try {
 for (const [name,fn] of tests){ try{fn(); passed++; console.log(`ok ${passed} - ${name}`);} catch(e){console.error(`not ok ${passed+1} - ${name}\n  ${e.stack||e.message}`);process.exitCode=1;break;} }
} finally { if(repo?.dir) rmSync(repo.dir,{recursive:true,force:true}); }
if (!process.exitCode) console.log(`# ${passed}/${tests.length} software-work-integrity tests passed`);
