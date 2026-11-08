// Runs the Khronos glTF Validator on .glb files and prints one JSON report per file.
// Usage: node validate-gltf.mjs <file.glb>...
// Exits 1 if any file has errors or warnings, 2 on bad usage.
import { readFile } from "node:fs/promises";
import { basename } from "node:path";
import validator from "gltf-validator";

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error("usage: node validate-gltf.mjs <file.glb>...");
  process.exit(2);
}

let failed = false;
const reports = [];
for (const file of files) {
  const bytes = new Uint8Array(await readFile(file));
  let report;
  try {
    report = await validator.validateBytes(bytes, {
      uri: basename(file),
      maxIssues: 100,
      // Bundles embed nothing external; any external reference is a failure.
      externalResourceFunction: (uri) => Promise.reject(new Error(`external resource not allowed: ${uri}`)),
    });
  } catch (error) {
    // The validator throws instead of reporting when it can't read the file at all.
    failed = true;
    reports.push({ file, errors: 1, warnings: 0, infos: 0, hints: 0, messages: [{ code: "UNREADABLE", severity: 0, message: String(error) }] });
    continue;
  }
  const issues = report.issues;
  if (issues.numErrors > 0 || issues.numWarnings > 0) failed = true;
  reports.push({
    file,
    errors: issues.numErrors,
    warnings: issues.numWarnings,
    infos: issues.numInfos,
    hints: issues.numHints,
    messages: issues.messages.map((m) => ({ code: m.code, severity: m.severity, pointer: m.pointer, message: m.message })),
  });
}
console.log(JSON.stringify(reports, null, 2));
process.exit(failed ? 1 : 0);
