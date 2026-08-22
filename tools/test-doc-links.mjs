#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const markdown = [];
const skipDirs = new Set(['.git', '__pycache__', 'node_modules']);

function walk(dir) {
  for (const name of readdirSync(dir)) {
    if (skipDirs.has(name)) continue;
    const path = resolve(dir, name);
    const stat = statSync(path);
    if (stat.isDirectory()) walk(path);
    else if (name.endsWith('.md')) markdown.push(path);
  }
}
walk(root);

// Intentionally checks ordinary inline Markdown links. It does not try to
// implement a full Markdown parser; repository docs use this portable subset.
const link = /(?<!!)\[[^\]]*\]\(([^)]+)\)/g;
let checked = 0;
const failures = [];
for (const file of markdown.sort()) {
  const text = readFileSync(file, 'utf8');
  for (const match of text.matchAll(link)) {
    let target = match[1].trim();
    if (target.startsWith('<') && target.includes('>')) target = target.slice(1, target.indexOf('>'));
    else target = target.split(/\s+/)[0]; // strip an optional Markdown title
    if (!target || /^(?:#|https?:|mailto:|urn:)/i.test(target)) continue;
    if (target.includes('__OWP_')) continue; // unrendered template source
    target = decodeURIComponent(target.split('#', 1)[0].split('?', 1)[0]);
    if (!target) continue;
    const absolute = resolve(dirname(file), target);
    checked += 1;
    if (!(absolute === root || absolute.startsWith(`${root}/`))) {
      failures.push(`${relative(root, file)} -> ${match[1]} (escapes repository)`);
    } else if (!existsSync(absolute)) {
      failures.push(`${relative(root, file)} -> ${match[1]} (missing)`);
    }
  }
}
if (failures.length) {
  console.error(`documentation link validation FAIL (${failures.length}/${checked})`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log(`documentation local-link validation PASS (${checked} links)`);
