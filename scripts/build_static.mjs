import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const dist = path.join(root, "dist");
const secretPattern =
  /(\bapiKey\b|\bAPI_KEY\b|\bOPENAI_API_KEY\b|\bGEMINI_API_KEY\b|\bANTHROPIC_API_KEY\b|\bAuthorization\b|Bearer\s+[A-Za-z0-9._-]+|\bsecret\b|\btoken\b|sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]+)/i;

function assertConciseJson(jsonText) {
  const data = JSON.parse(jsonText);
  const failures = [];
  for (const disease of data) {
    for (const field of ["essentialsOfDiagnosis", "treatmentManagement"]) {
      const maxItems = field === "essentialsOfDiagnosis" ? 6 : 8;
      const items = disease[field] || [];
      if (items.length > maxItems) {
        failures.push(`${disease.diagnosis} ${field} has ${items.length} bullets`);
      }
      for (const item of items) {
        if (item.length > 180) {
          failures.push(`${disease.diagnosis} ${field} bullet is ${item.length} chars`);
        }
      }
    }
    if ((disease.prescription || "").length > 1800) {
      failures.push(`${disease.diagnosis} prescription is too long`);
    }
  }
  if (failures.length) {
    throw new Error(`Disease JSON is not hosting-safe:\n${failures.slice(0, 20).join("\n")}`);
  }
}

async function assertNoPdfFiles(dir) {
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await assertNoPdfFiles(fullPath);
    } else if (entry.name.toLowerCase().endsWith(".pdf")) {
      throw new Error(`PDF file must not be included in public build: ${fullPath}`);
    }
  }
}

async function assertNoSecretsInDist(dir) {
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await assertNoSecretsInDist(fullPath);
      continue;
    }
    if (!/\.(html|css|js|json|txt|md)$/i.test(entry.name)) continue;
    const text = await readFile(fullPath, "utf8");
    if (secretPattern.test(text)) {
      throw new Error(`Possible secret/API credential found in public build: ${fullPath}`);
    }
  }
}

await rm(dist, { recursive: true, force: true });
await mkdir(path.join(dist, "data"), { recursive: true });
await mkdir(path.join(dist, "icons"), { recursive: true });

for (const file of ["index.html", "styles.css", "app.js", "README.md", "manifest.json", "service-worker.js", "favicon.png"]) {
  if (existsSync(path.join(root, file))) {
    await cp(path.join(root, file), path.join(dist, file));
  }
}

for (const file of ["icon-192.png", "icon-512.png", "apple-touch-icon.png"]) {
  await cp(path.join(root, "icons", file), path.join(dist, "icons", file));
}

const diagnosisJson = await readFile(path.join(root, "data", "diagnoses.json"), "utf8");
assertConciseJson(diagnosisJson);
await writeFile(path.join(dist, "data", "diagnoses.json"), diagnosisJson);

await assertNoPdfFiles(dist);
await assertNoSecretsInDist(dist);

console.log("Static build ready in dist/");
