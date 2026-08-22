#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { readFileSync, mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

export const PROFILE = 'https://openworkprotocol.org/profiles/software-work-integrity/v1';
export const VALIDATION_PREDICATE = 'https://openworkprotocol.org/attestation/software-work-validation/v1';
export const IN_TOTO_STATEMENT = 'https://in-toto.io/Statement/v1';
export const TEST_RESULT_PREDICATE = 'https://in-toto.io/attestation/test-result/v0.1';
const ROLES = ['customer','provider','orchestrator','owp_validator'];

export class IndeterminateError extends Error {
  constructor(message){ super(message); this.name='IndeterminateError'; }
}

function assert(cond, message) { if (!cond) throw new Error(message); }

function validateHashDomain(value, path = '$') {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return;
  if (typeof value === 'number') {
    assert(Number.isSafeInteger(value), `${path}: hashed profile objects allow only safe integers, not floats/unsafe integers`);
    return;
  }
  if (Array.isArray(value)) return value.forEach((v,i)=>validateHashDomain(v,`${path}[${i}]`));
  assert(typeof value === 'object', `${path}: unsupported JSON value`);
  for (const [k,v] of Object.entries(value)) {
    assert([...k].every(ch=>ch.codePointAt(0)>=0x20 && ch.codePointAt(0)<=0x7e), `${path}: non-printable/non-ASCII property name ${JSON.stringify(k)}`);
    validateHashDomain(v,`${path}.${k}`);
  }
}

export function canonicalize(value) {
  validateHashDomain(value);
  if (value === null || typeof value === 'boolean' || typeof value === 'number' || typeof value === 'string') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonicalize(value[k])}`).join(',')}}`;
}

export function sha256Id(value) { return `sha256:${createHash('sha256').update(canonicalize(value),'utf8').digest('hex')}`; }
export function sha256Bytes(buf) { return `sha256:${createHash('sha256').update(buf).digest('hex')}`; }
function validSha256Id(v){ return /^sha256:[0-9a-f]{64}$/.test(v ?? ''); }

export function validateOid(oid, objectFormat, label='oid') {
  const re = objectFormat==='sha1' ? /^[0-9a-f]{40}$/ : objectFormat==='sha256' ? /^[0-9a-f]{64}$/ : null;
  assert(re, `unsupported Git object format: ${objectFormat}`);
  assert(re.test(oid ?? ''), `${label} must be a full lowercase ${objectFormat} object id`);
}

function acknowledgementsByRole(entries, digestField, digest, label) {
  const map=new Map();
  for(const ack of entries ?? []){
    assert(ROLES.includes(ack.role), `unknown ${label} role ${ack.role}`);
    assert(!map.has(ack.role), `duplicate ${label} acknowledgement role ${ack.role}`);
    map.set(ack.role,ack);
  }
  for(const role of ROLES){
    const ack=map.get(role); assert(ack,`missing ${role} ${label} acknowledgement`);
    assert(ack.decision==='ACCEPT',`${role} did not ACCEPT ${label}`);
    assert(ack[digestField]===digest,`${role} acknowledged different ${label} digest`);
    assert(typeof ack.actor_id==='string' && ack.actor_id.length>0,`${role} actor_id missing`);
  }
  return map;
}

export function verifyAgreement(agreement) {
  assert(agreement?.contract_body?.profile===PROFILE,'agreement profile mismatch');
  assert(validSha256Id(agreement.contract_digest),'invalid contract_digest syntax');
  assert(sha256Id(agreement.contract_body)===agreement.contract_digest,'contract_digest does not match contract_body');
  const dod=agreement.contract_body.definition_of_done;
  assert(Array.isArray(dod) && dod.length>0,'definition_of_done must be non-empty');
  const ids=new Set();
  for(const item of dod){
    assert(item.id && !ids.has(item.id),`duplicate/missing DoD id ${item.id ?? ''}`); ids.add(item.id);
    assert(['deterministic','evidence','human'].includes(item.tier),`invalid DoD tier for ${item.id}`);
    assert(typeof item.statement==='string' && item.statement.length>0,`missing DoD statement for ${item.id}`);
    if(item.tier==='deterministic') assert(typeof item.command==='string' && item.command.trim(),`deterministic DoD ${item.id} needs command`);
  }
  const roles=acknowledgementsByRole(agreement.acknowledgements,'contract_digest',agreement.contract_digest,'contract');
  if(agreement.contract_body.evidence_policy?.independent_validation){
    const v=roles.get('owp_validator').actor_id;
    assert(v!==roles.get('provider').actor_id,'validator is not independent from provider actor');
    assert(v!==roles.get('orchestrator').actor_id,'validator is not independent from orchestrator actor');
  }
  return roles;
}

export function verifyExecution(agreement, execution, claimedDigest) {
  assert(execution?.profile===PROFILE,'execution profile mismatch');
  assert(execution.work_ref===agreement.contract_body.work_ref,'execution work_ref mismatch');
  assert(execution.contract_digest===agreement.contract_digest,'execution contract_digest mismatch');
  assert(Number.isSafeInteger(execution.revision) && execution.revision>=0,'invalid revision');
  assert(Array.isArray(execution.acceptance_delta),'acceptance_delta must be an array');
  const seen=new Set(agreement.contract_body.definition_of_done.map(x=>x.id));
  for(const item of execution.acceptance_delta){
    assert(item.id && !seen.has(item.id),`duplicate/missing acceptance_delta id ${item.id ?? ''}`); seen.add(item.id);
    assert(['deterministic','evidence','human'].includes(item.tier),`invalid acceptance_delta tier for ${item.id}`);
    assert(typeof item.statement==='string' && item.statement.length>0,`missing acceptance_delta statement for ${item.id}`);
    if(item.tier==='deterministic') assert(typeof item.command==='string' && item.command.trim(),`deterministic delta ${item.id} needs command`);
  }
  const ss=execution.source_snapshot ?? {};
  assert(typeof ss.repository_uri==='string' && ss.repository_uri,'source repository_uri missing');
  validateOid(ss.base_commit,ss.object_format,'source base_commit');
  validateOid(ss.base_tree,ss.object_format,'source base_tree');
  if(execution.revision===0) assert(execution.parent===null,'revision zero parent must be null');
  else{
    assert(execution.parent && typeof execution.parent==='object','revision >0 requires parent');
    assert(execution.parent.attempt_id,'parent attempt_id missing');
    assert(validSha256Id(execution.parent.validator_attestation_digest),'invalid parent validator attestation digest');
    assert(validSha256Id(execution.parent.customer_disposition_digest),'invalid parent customer disposition digest');
  }
  assert(validSha256Id(claimedDigest),'invalid execution_commitment_digest syntax');
  assert(sha256Id(execution)===claimedDigest,'execution_commitment_digest mismatch');
}

export function verifyAttemptAcceptance(agreement, execution, executionDigest, attemptAcceptance) {
  assert(attemptAcceptance?.execution_commitment_digest===executionDigest,'Attempt acceptance execution_commitment_digest mismatch');
  const contractRoles=new Map((agreement.acknowledgements ?? []).map(x=>[x.role,x]));
  const attemptRoles=acknowledgementsByRole(attemptAcceptance.acknowledgements,'execution_commitment_digest',executionDigest,'Attempt');
  for(const role of ROLES){
    assert(attemptRoles.get(role).actor_id===contractRoles.get(role)?.actor_id,`${role} Attempt actor differs from current Work Agreement actor`);
  }
  assert(attemptRoles.get('provider').actor_id===execution.provider_id,'Attempt provider acknowledgement != execution provider');
  assert(attemptRoles.get('orchestrator').actor_id===execution.orchestrator_id,'Attempt orchestrator acknowledgement != execution orchestrator');
  return attemptRoles;
}

export function verifyDelivery(agreement, execution, executionDigest, delivery) {
  const ss=execution.source_snapshot;
  assert(delivery.work_ref===execution.work_ref,'delivery work_ref mismatch');
  assert(delivery.attempt_id===execution.attempt_id,'delivery attempt_id mismatch');
  assert(delivery.contract_digest===agreement.contract_digest,'delivery contract mismatch');
  assert(delivery.execution_commitment_digest===executionDigest,'delivery execution commitment mismatch');
  assert(delivery.provider_id===execution.provider_id,'delivery provider mismatch');
  assert(delivery.repository_uri===ss.repository_uri,'delivery repository mismatch');
  validateOid(delivery.claimed_base_commit,ss.object_format,'delivery claimed_base_commit');
  validateOid(delivery.result_commit,ss.object_format,'delivery result_commit');
  validateOid(delivery.result_tree,ss.object_format,'delivery result_tree');
  assert(delivery.claimed_base_commit===ss.base_commit,'provider claimed a different base commit');
  assert(validSha256Id(delivery.diff_digest),'invalid diff_digest syntax');
}

function resultSubject(attestation){
  assert(attestation?._type===IN_TOTO_STATEMENT,'validator attestation must be in-toto Statement v1');
  assert(attestation.predicateType===VALIDATION_PREDICATE,'validator predicateType mismatch');
  assert(Array.isArray(attestation.subject) && attestation.subject.length===1,'validator attestation requires exactly one result subject');
  const d=attestation.subject[0].digest ?? {}; return {commit:d.gitCommit,tree:d.gitTree};
}
function allAcceptanceItems(agreement,execution){ return [...agreement.contract_body.definition_of_done,...execution.acceptance_delta]; }

export function verifyAttestation(agreement, execution, executionDigest, delivery, attestation) {
  const roles=new Map((agreement.acknowledgements ?? []).map(x=>[x.role,x]));
  const subject=resultSubject(attestation);
  assert(subject.commit===delivery.result_commit,'validator attestation gitCommit subject != delivered result');
  assert(subject.tree===delivery.result_tree,'validator attestation gitTree subject != delivered result tree');
  const p=attestation.predicate ?? {};
  assert(p.work_ref===execution.work_ref,'attestation work_ref mismatch');
  assert(p.attempt_id===execution.attempt_id,'attestation attempt_id mismatch');
  assert(p.contract_digest===agreement.contract_digest,'attestation contract mismatch');
  assert(p.execution_commitment_digest===executionDigest,'attestation execution commitment mismatch');
  assert(p.delivery_claim_digest===sha256Id(delivery),'attestation delivery_claim_digest mismatch');
  assert(p.validator===roles.get('owp_validator')?.actor_id,'attestation validator differs from agreed independent validator');
  assert(p.expected_source?.base_commit===execution.source_snapshot.base_commit,'attestation expected base commit mismatch');
  assert(p.expected_source?.base_tree===execution.source_snapshot.base_tree,'attestation expected base tree mismatch');
  assert(p.observed_result?.result_commit===delivery.result_commit,'attestation observed result commit mismatch');
  assert(p.observed_result?.result_tree===delivery.result_tree,'attestation observed result tree mismatch');
  assert(['VALID','INVALID','INDETERMINATE'].includes(p.outcome),'invalid validator outcome');
  const byId=new Map((p.acceptance_results ?? []).map(x=>[x.id,x]));
  for(const item of allAcceptanceItems(agreement,execution)){
    if(item.tier==='human') continue;
    const r=byId.get(item.id); assert(r,`missing validator result for acceptance item ${item.id}`);
    assert(r.outcome==='PASS',`acceptance item ${item.id} is not PASS`);
    assert(validSha256Id(r.evidence_digest),`acceptance item ${item.id} missing/invalid evidence_digest`);
  }
  assert(p.outcome==='VALID',`bundle is not valid: validator outcome ${p.outcome}`);
}

export function verifyTestResult(testResult, delivery) {
  assert(testResult?._type===IN_TOTO_STATEMENT,'test result must be in-toto Statement v1');
  assert(testResult.predicateType===TEST_RESULT_PREDICATE,'test result predicateType mismatch');
  assert(Array.isArray(testResult.subject) && testResult.subject.length>=1,'test result subject missing');
  assert(testResult.subject.some(s=>s?.digest?.gitCommit===delivery.result_commit && s?.digest?.gitTree===delivery.result_tree),'test result subject is not the exact delivered commit/tree');
  assert(['PASSED','WARNED','FAILED'].includes(testResult.predicate?.result),'invalid test result outcome');
  assert(testResult.predicate.result==='PASSED','test result did not pass');
}

export function verifyDisposition(disposition, claimedDigest, execution, attestationDigest) {
  assert(disposition.work_ref===execution.work_ref,'disposition work_ref mismatch');
  assert(disposition.attempt_id===execution.attempt_id,'disposition attempt mismatch');
  assert(disposition.validator_attestation_digest===attestationDigest,'disposition validator attestation mismatch');
  assert(['APPROVE','STEER','REJECT'].includes(disposition.decision),'invalid customer disposition');
  assert(sha256Id(disposition)===claimedDigest,'customer_disposition_digest mismatch');
}

export function verifyBundle(bundle, priorBundle=null) {
  const roles=verifyAgreement(bundle.agreement);
  verifyExecution(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest);
  verifyAttemptAcceptance(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest,bundle.attempt_acceptance);
  verifyDelivery(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest,bundle.delivery_claim);
  verifyAttestation(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest,bundle.delivery_claim,bundle.validator_attestation);
  const attDigest=sha256Id(bundle.validator_attestation);
  assert(bundle.validator_attestation_digest===attDigest,'validator_attestation_digest mismatch');
  const deterministic=allAcceptanceItems(bundle.agreement,bundle.execution_commitment).filter(x=>x.tier==='deterministic');
  if(deterministic.length){
    assert(bundle.test_result,'deterministic acceptance requires exact-subject test result evidence');
    verifyTestResult(bundle.test_result,bundle.delivery_claim);
    const testDigest=sha256Id(bundle.test_result);
    const byId=new Map((bundle.validator_attestation.predicate.acceptance_results ?? []).map(x=>[x.id,x]));
    for(const item of deterministic) assert(byId.get(item.id)?.evidence_digest===testDigest,`deterministic acceptance ${item.id} is not bound to the exact test-result attestation`);
  }
  verifyDisposition(bundle.customer_disposition,bundle.customer_disposition_digest,bundle.execution_commitment,attDigest);
  if(priorBundle){
    const ex=bundle.execution_commitment;
    assert(ex.revision>0,'chained bundle must be revision > 0');
    assert(ex.parent?.attempt_id===priorBundle.execution_commitment.attempt_id,'parent attempt mismatch');
    assert(ex.parent?.validator_attestation_digest===priorBundle.validator_attestation_digest,'parent validator attestation mismatch');
    assert(ex.parent?.customer_disposition_digest===priorBundle.customer_disposition_digest,'parent customer disposition mismatch');
    assert(priorBundle.customer_disposition.decision==='STEER','new revision requires prior STEER disposition');
    const prev=resultSubject(priorBundle.validator_attestation);
    assert(ex.source_snapshot.base_commit===prev.commit,'revision/handoff base commit is not prior validator-attested result');
    assert(ex.source_snapshot.base_tree===prev.tree,'revision/handoff base tree is not prior validator-attested result');
  }
  return {ok:true,roles:Object.fromEntries([...roles].map(([k,v])=>[k,v.actor_id]))};
}

function safeGitEnv(home){ return {...process.env,HOME:home,GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null',GIT_NO_REPLACE_OBJECTS:'1'}; }
function git(cwd,args,{env,encoding='utf8'}={}){
  const r=spawnSync('git',args,{cwd,encoding,env:env ?? safeGitEnv(cwd)});
  if(r.status!==0) throw new Error(`git ${args.join(' ')} failed: ${String(r.stderr||r.stdout||'').trim()}`);
  return encoding ? String(r.stdout ?? '').trim() : r.stdout;
}
function globToRegExp(glob){
  let out='^'; for(let i=0;i<glob.length;i++){const c=glob[i]; if(c==='*'&&glob[i+1]==='*'){out+='.*';i++;} else if(c==='*')out+='[^/]*'; else if(c==='?')out+='[^/]'; else out+=c.replace(/[\\^$+?.()|{}\[\]]/g,'\\$&');} return new RegExp(out+'$');
}
function matchesAny(path,globs){ return (globs ?? []).some(g=>globToRegExp(g).test(path)); }
function treeEntry(cwd,commit,path,env){
  const raw=git(cwd,['ls-tree','-z',commit,'--',path],{env,encoding:'utf8'});
  if(!raw) return {mode:null,object:null};
  const head=raw.split('\t',1)[0]; const [mode,_type,object]=head.split(' '); return {mode,object};
}
function splitNulBuffer(buf){
  const out=[]; let start=0;
  for(let i=0;i<buf.length;i++) if(buf[i]===0){ out.push(buf.subarray(start,i)); start=i+1; }
  if(start<buf.length) out.push(buf.subarray(start));
  return out.filter(x=>x.length>0);
}
function strictUtf8(buf,label){
  const text=buf.toString('utf8');
  assert(Buffer.from(text,'utf8').equals(buf),`${label} is not valid UTF-8`);
  return text;
}
export function computeChangeSet(cwd,base,result,{env=safeGitEnv(cwd)}={}){
  const r=spawnSync('git',['diff','--name-status','-z','--no-renames',base,result],{cwd,encoding:null,env});
  if(r.status!==0) throw new Error(`git diff --name-status failed: ${String(r.stderr||'').trim()}`);
  const toks=splitNulBuffer(r.stdout ?? Buffer.alloc(0)); const entries=[];
  for(let i=0;i<toks.length;){
    const statusBuf=toks[i++], pathBuf=toks[i++]; assert(pathBuf!==undefined,'malformed NUL-delimited git diff output');
    const status=strictUtf8(statusBuf,'change status');
    const path=strictUtf8(pathBuf,'changed path');
    const oldE=treeEntry(cwd,base,path,env), newE=treeEntry(cwd,result,path,env);
    entries.push({path,status,old_mode:oldE.mode,old_object:oldE.object,new_mode:newE.mode,new_object:newE.object});
  }
  return entries.sort((a,b)=>Buffer.compare(Buffer.from(a.path,'utf8'),Buffer.from(b.path,'utf8')));
}
export function computeChangeSetDigest(cwd,base,result,opts={}){ return sha256Id(computeChangeSet(cwd,base,result,opts)); }

export function verifyGitReality(bundle, repoPath, {allowExec=false, commandTimeoutMs=120000}={}) {
  verifyAgreement(bundle.agreement);
  verifyExecution(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest);
  verifyAttemptAcceptance(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest,bundle.attempt_acceptance);
  verifyDelivery(bundle.agreement,bundle.execution_commitment,bundle.execution_commitment_digest,bundle.delivery_claim);
  const ex=bundle.execution_commitment,d=bundle.delivery_claim,ss=ex.source_snapshot;
  const temp=mkdtempSync(join(tmpdir(),'owp-swi-validator-')); const home=join(temp,'home'); mkdirSync(home);
  const env=safeGitEnv(home); const checkout=join(temp,'checkout');
  try{
    try {
      git(temp,['clone','--no-local','--quiet',repoPath,checkout],{env});
      // Explicit fetch makes base/result availability independent of the clone's checked-out branch.
      git(checkout,['fetch','--quiet','--no-tags',repoPath,ss.base_commit,d.result_commit],{env});
    } catch(e) {
      throw new IndeterminateError(`validator could not independently obtain required Git source/objects: ${e.message}`);
    }
    const actualFormat=git(checkout,['rev-parse','--show-object-format'],{env});
    assert(actualFormat===ss.object_format,`repository object format ${actualFormat} != commitment ${ss.object_format}`);
    git(checkout,['cat-file','-e',`${ss.base_commit}^{commit}`],{env}); git(checkout,['cat-file','-e',`${d.result_commit}^{commit}`],{env});
    const baseTree=git(checkout,['rev-parse',`${ss.base_commit}^{tree}`],{env}); const resultTree=git(checkout,['rev-parse',`${d.result_commit}^{tree}`],{env});
    assert(baseTree===ss.base_tree,'contracted base_tree does not match actual base commit');
    assert(resultTree===d.result_tree,'delivered result_tree does not match actual result commit');
    const anc=spawnSync('git',['merge-base','--is-ancestor',ss.base_commit,d.result_commit],{cwd:checkout,env});
    assert(anc.status===0,'delivered result is not descended from expected base');
    const changeSet=computeChangeSet(checkout,ss.base_commit,d.result_commit,{env});
    assert(sha256Id(changeSet)===d.diff_digest,'diff_digest does not match canonical base-to-result change set');
    const paths=changeSet.map(x=>x.path), scope=bundle.agreement.contract_body.scope ?? {};
    for(const path of paths){
      if((scope.allowed_paths ?? []).length) assert(matchesAny(path,scope.allowed_paths),`changed path outside allowed scope: ${path}`);
      assert(!matchesAny(path,scope.forbidden_paths),`forbidden path changed: ${path}`);
    }
    git(checkout,['checkout','--detach','--quiet',d.result_commit],{env});
    assert(git(checkout,['rev-parse','HEAD'],{env})===d.result_commit,'fresh checkout HEAD mismatch');
    assert(git(checkout,['rev-parse','HEAD^{tree}'],{env})===d.result_tree,'fresh checkout tree mismatch');
    const deterministic=allAcceptanceItems(bundle.agreement,ex).filter(x=>x.tier==='deterministic');
    if(deterministic.length){
      if(!allowExec) throw new IndeterminateError('deterministic acceptance exists but command execution was not explicitly enabled');
      if(bundle.agreement.contract_body.evidence_policy?.hardened_sandbox===true)
        throw new IndeterminateError('contract requires a hardened sandbox; the dependency-free reference verifier only proves fresh-clone isolation');
      const execEnv={PATH:process.env.PATH ?? '/usr/bin:/bin',HOME:home,LANG:'C.UTF-8',LC_ALL:'C.UTF-8',OWP_VALIDATED_COMMIT:d.result_commit,OWP_VALIDATED_TREE:d.result_tree};
      for(const item of deterministic){
        const r=spawnSync(item.command,{cwd:checkout,shell:true,encoding:'utf8',env:execEnv,timeout:commandTimeoutMs,maxBuffer:16*1024*1024});
        if(r.error || r.status===null || r.signal)
          throw new IndeterminateError(`deterministic acceptance ${item.id} could not be completed: ${String(r.error?.message||r.signal||'unknown execution failure')}`);
        assert(r.status===0,`deterministic acceptance ${item.id} failed: ${String(r.stderr||r.stdout||'').trim()}`);
      }
    }
    return {ok:true,base_commit:ss.base_commit,result_commit:d.result_commit,result_tree:d.result_tree,changed_paths:paths,change_set_digest:d.diff_digest};
  } finally { rmSync(temp,{recursive:true,force:true}); }
}

function usage(){ console.error('Usage: node tools/verify-software-work-integrity.mjs --bundle FILE [--prior FILE] [--git-repo PATH --allow-exec]'); }
if(import.meta.url===`file://${process.argv[1]}`){
  const args=process.argv.slice(2),get=n=>{const i=args.indexOf(n);return i>=0?args[i+1]:null}; const file=get('--bundle'); if(!file){usage();process.exit(2)}
  try{
    const bundle=JSON.parse(readFileSync(file,'utf8')),priorFile=get('--prior'),prior=priorFile?JSON.parse(readFileSync(priorFile,'utf8')):null;
    verifyBundle(bundle,prior); const repo=get('--git-repo'); const reality=repo?verifyGitReality(bundle,repo,{allowExec:args.includes('--allow-exec')}):null;
    console.log(JSON.stringify({outcome:'VALID',bundle:true,git_reality:reality},null,2));
  }catch(e){
    const outcome=e instanceof IndeterminateError ? 'INDETERMINATE' : 'INVALID';
    console.error(JSON.stringify({outcome,error:e.message},null,2));
    process.exit(outcome==='INDETERMINATE'?3:1);
  }
}
