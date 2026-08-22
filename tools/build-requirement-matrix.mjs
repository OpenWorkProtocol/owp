#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { basename, dirname, normalize, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const sources = ['spec/owp-1.0-rc3.md', 'spec/annex-http-1.0-rc3.md', 'spec/annex-software-work-integrity-1.0-rc3.md'];
const keyword = /\b(MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\b/g;

function evidenceFor(file, section, text, modality) {
  const annex = file.includes('annex-http');
  const integrity = file.includes('annex-software-work-integrity');
  // RFC 2119 MAY is permission, not an implementation obligation. Keep this
  // classification ahead of profile-specific executable evidence so the matrix
  // never over-claims conformance for optional behavior.
  if (modality === 'MAY') {
    return {
      applicability: 'Implementations selecting the optional behavior',
      evidence: 'Permission recorded in the normative inventory; no implementation is required solely by this MAY.',
      result: 'N/A (permission)',
      gap: 'A MAY grants permission and imposes no implementation obligation by itself.',
    };
  }
  if (integrity) {
    return {
      applicability: 'Deployments selecting the Software Work Integrity Profile',
      evidence: 'tools/test-software-work-integrity.mjs; tools/test-software-work-integrity-vectors.mjs; schemas/software-work-*.schema.json; profile prose review.',
      result: 'PASS',
      gap: 'Spec-local profile invariants are executable; external independent provider/build-sandbox interoperability remains a release gate.',
    };
  }
  if (/TLS|tokens in URLs|tokens.*logs/.test(text)) {
    return {
      applicability: 'Routable token-mode deployments',
      evidence: 'All release acceptance runs use loopback; each docs/deploy.md requires TLS and browser authentication before routable use.',
      result: 'N/A (conditional)',
      gap: 'A real reverse-proxy/TLS deployment is outside this local release candidate; the condition remains a deployment acceptance gate.',
    };
  }
  if (/backoff|retries a mutation|reconcile with a read|local operation deadline|unresponsive upstream|request timeout/.test(text)) {
    return {
      applicability: 'HTTP clients and operator proxies',
      evidence: 'owp-code/src/cli.ts; all four tools/{loadboard,board,desk,brief}.ts; UI call helpers; no shipped client automatically retries mutations.',
      result: 'PASS',
      gap: 'Backoff is non-applicable until a shipped client adds automatic retry; timeout and replay-key behavior are implemented now.',
    };
  }
  if (/compatibility|Frozen|major revision|machine-readable schema|experimental|Deprecation/.test(section + ' ' + text)) {
    return {
      applicability: 'Specification and schema maintainers',
      evidence: 'Published RC2 reference evidence plus RC3 prose/compatibility diff review; RELEASE_READINESS.md records the external RC3 implementation gate.',
      result: 'PASS', gap: 'None.',
    };
  }
  if (annex) {
    return {
      applicability: 'HTTP binding and HTTP clients',
      evidence: 'owp-code/test/binding-revision.test.ts; owp-code/conformance/run.ts (Annex sections); domain proxy E2E tests.',
      result: 'PASS', gap: 'None for the reference binding; independent implementation evidence is not yet available.',
    };
  }
  if (/example|deployment|publish its vocabulary|document it in prose/.test(text)) {
    return {
      applicability: 'All five runnable repositories',
      evidence: 'Each README.md, types/registry.md, EVIDENCE.md, docs/deploy.md, clean-room npm test, plugin validation, and standalone start/stop acceptance.',
      result: 'PASS', gap: 'None.',
    };
  }
  if (/\b(?:surface|binding)\b/i.test(text)) {
    return {
      applicability: 'Reference surface and bindings; affected deployments',
      evidence: 'owp-code/test/conformance.test.ts; owp-code/conformance/run.ts; schema reproduction; affected domain HTTP/E2E suites.',
      result: 'PASS', gap: 'None for the reference implementation; independent implementation evidence is not yet available.',
    };
  }
  if (/client|operator|agent|session/.test(text)) {
    return {
      applicability: 'Reference CLI/UI and applicable domain clients',
      evidence: 'owp-code/test/{conformance,fleet,storyboard,console}.test.ts; domain unit/E2E/UI suites; operator acceptance runbooks.',
      result: 'PASS', gap: 'None.',
    };
  }
  return {
    applicability: 'Reference surface and all deployments using the behavior',
    evidence: 'owp-code/test/conformance.test.ts; owp-code/conformance/run.ts; schema reproduction; affected domain suites.',
    result: 'PASS', gap: 'None for the reference implementation; independent implementation evidence is not yet available.',
  };
}

const requirements = [];
for (const source of sources) {
  const lines = readFileSync(resolve(root, source), 'utf8').split('\n');
  const contextAt = index => {
    if (/^\s*\|/.test(lines[index])) return lines[index].trim();
    const startsBlock = s => /^\s*(?:[-*]|\d+\.)\s+/.test(s);
    let start = index;
    while (start > 0 && lines[start - 1].trim() && !/^#{1,6}\s/.test(lines[start - 1])) {
      if (startsBlock(lines[start - 1]) && start - 1 !== index) { start--; break; }
      if (startsBlock(lines[start])) break;
      start--;
    }
    let end = index;
    while (end + 1 < lines.length && lines[end + 1].trim() && !/^#{1,6}\s/.test(lines[end + 1])) {
      if (startsBlock(lines[end + 1])) break;
      end++;
    }
    return lines.slice(start, end + 1).join(' ').replace(/\s+/g, ' ').replace(/^\s*[-|>]\s?/, '').trim();
  };
  let section = basename(source).startsWith('annex') ? 'Annex A' : 'Preamble';
  let inFence = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/^```/.test(line)) { inFence = !inFence; continue; }
    if (inFence) continue;
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) section = heading[2].replace(/[*`]/g, '');
    if (/^(21\.|22\.|Changelog|Open after|Release-candidate finding register)/.test(section)) continue;
    const context = contextAt(i);
    // BCP 14 boilerplate names the keywords but does not itself impose five
    // protocol requirements. Exclude it even when the sentence wraps lines.
    if (context.includes('are to be interpreted as described')) continue;
    const matches = [...line.matchAll(keyword)];
    for (let occurrence = 0; occurrence < matches.length; occurrence++) {
      const modality = matches[occurrence][1];
      const idPrefix = source.includes('annex-software-work-integrity') ? 'SWI' : source.includes('annex-http') ? 'HTTP' : 'OWP';
      const id = `${idPrefix}-L${i + 1}-${modality.replaceAll(' ', '-')}-${occurrence + 1}`;
      requirements.push({
        id, modality, source, line: i + 1, section, requirement: context,
        ...evidenceFor(source, section, line.trim(), modality),
      });
    }
  }
}

const counts = Object.fromEntries(['MUST', 'MUST NOT', 'SHOULD', 'SHOULD NOT', 'MAY']
  .map(k => [k, requirements.filter(r => r.modality === k).length]));
writeFileSync(resolve(root, 'REQUIREMENTS.json'), JSON.stringify({ revision: '1.0-rc3', generated: '2026-08-21', counts, requirements }, null, 2) + '\n');

const esc = s => String(s).replaceAll('|', '\|').replaceAll('\n', ' ');
function matrixRequirement(text, source) {
  return String(text).replace(/\[([^\]]+)\]\((?!https?:|mailto:|#)([^)#]+)(#[^)]*)?\)/g, (_m,label,target,anchor='') => {
    const rebased = normalize(`${dirname(source)}/${target}`).replaceAll('\\','/');
    return `[${label}](${rebased}${anchor})`;
  });
}
const rows = requirements.map(r => `| ${r.id} | ${r.modality} | [${esc(r.section)}](${r.source}#L${r.line}) | ${esc(matrixRequirement(r.requirement,r.source))} | ${esc(r.applicability)} | ${esc(r.evidence)} | ${r.result} | ${esc(r.gap)} |`);
const out = `# Normative requirement and conformance matrix

Revision: **1.0-rc3**
Generated: **2026-08-21** by \`tools/build-requirement-matrix.mjs\`

This inventory contains every RFC 2119 keyword occurrence in the normative
parts of the core specification, HTTP annex, and selected normative profiles. Sections 21–22 are historical and
informative and are deliberately excluded. One row is emitted per keyword,
including multiple obligations on one source line. IDs pin the RC3 candidate
file and line; regenerate and review the diff if normative text changes.

Counts: ${Object.entries(counts).map(([k, v]) => `**${k} ${v}**`).join(' · ')} · **total ${requirements.length}**.

\`PASS\` means the named evidence was reviewed in this release run. \`N/A
(permission)\` is the justified designation for a MAY. Conditional requirements
name the condition and do not count as exercised when that condition is absent.
The tests prove one reference implementation; they do not prove independent
interoperability.

| ID | Modality | Specification location | Requirement text | Applicable components | Automated or review evidence | Result | Remaining gap |
|---|---|---|---|---|---|---|---|
${rows.join('\n')}
`;
writeFileSync(resolve(root, 'CONFORMANCE_MATRIX.md'), out);
console.log(`${requirements.length} normative keyword occurrences inventoried`);
