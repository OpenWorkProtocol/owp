#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { sha256Id } from './verify-software-work-integrity.mjs';
const dir=resolve(import.meta.dirname,'../test/software-work-integrity-vectors');
const path=n=>resolve(dir,n);
const base=JSON.parse(readFileSync(path('valid.json'),'utf8')).bundle;

function clone(x){ return structuredClone(x); }
function seal(b,{badAttemptAck=false,badContractAck=false,missingValidator=false,badTestSubject=false,uncheckedDelta=false}={}){
  b.agreement.contract_digest=sha256Id(b.agreement.contract_body);
  for(const a of b.agreement.acknowledgements) a.contract_digest=b.agreement.contract_digest;
  b.execution_commitment.contract_digest=b.agreement.contract_digest;
  const exDigest=sha256Id(b.execution_commitment);
  b.execution_commitment_digest=exDigest;
  b.attempt_acceptance.execution_commitment_digest=exDigest;
  for(const a of b.attempt_acceptance.acknowledgements) a.execution_commitment_digest=exDigest;
  b.delivery_claim.contract_digest=b.agreement.contract_digest;
  b.delivery_claim.execution_commitment_digest=exDigest;
  b.validator_attestation.predicate.contract_digest=b.agreement.contract_digest;
  b.validator_attestation.predicate.execution_commitment_digest=exDigest;
  b.validator_attestation.predicate.delivery_claim_digest=sha256Id(b.delivery_claim);
  if(badTestSubject) {
    b.test_result.subject[0].digest.gitCommit='7777777777777777777777777777777777777777';
  }
  const testDigest=sha256Id(b.test_result);
  const byId=new Map(b.validator_attestation.predicate.acceptance_results.map(x=>[x.id,x]));
  for(const item of [...b.agreement.contract_body.definition_of_done,...b.execution_commitment.acceptance_delta]){
    if(item.tier!=='deterministic') continue;
    if(byId.has(item.id)) byId.get(item.id).evidence_digest=testDigest;
  }
  b.validator_attestation_digest=sha256Id(b.validator_attestation);
  b.customer_disposition.validator_attestation_digest=b.validator_attestation_digest;
  b.customer_disposition_digest=sha256Id(b.customer_disposition);
  if(badAttemptAck) b.attempt_acceptance.acknowledgements[0].execution_commitment_digest='sha256:'+'0'.repeat(64);
  if(badContractAck) b.agreement.acknowledgements[1].contract_digest='sha256:'+'0'.repeat(64);
  if(missingValidator) b.agreement.acknowledgements=b.agreement.acknowledgements.filter(x=>x.role!=='owp_validator');
  if(uncheckedDelta) {
    // Deliberately leave the new deterministic delta absent from validator acceptance_results.
  }
  return b;
}
function write(name,bundle,expected){ writeFileSync(path(name),JSON.stringify({expected_valid:expected,bundle},null,2)+'\n'); }

let v=seal(clone(base)); write('valid.json',v,true);
let x;
x=clone(v); x.execution_commitment.source_snapshot.base_commit='111111111111'; x=seal(x); write('invalid-abbreviated-base.json',x,false);
x=seal(clone(v),{badAttemptAck:true}); write('invalid-attempt-consensus.json',x,false);
x=seal(clone(v),{badContractAck:true}); write('invalid-contract-consensus.json',x,false);
x=seal(clone(v),{missingValidator:true}); write('invalid-missing-validator.json',x,false);
x=seal(clone(v),{badTestSubject:true}); write('invalid-test-subject.json',x,false);
x=clone(v); x.execution_commitment.acceptance_delta=[{id:'steer',tier:'deterministic',statement:'Steer check.',command:'node steer.js'}]; x=seal(x,{uncheckedDelta:true}); write('invalid-unchecked-delta.json',x,false);
console.log('refreshed 7 Software Work Integrity vectors');
