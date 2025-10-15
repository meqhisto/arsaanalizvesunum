import { promises as fs } from "fs";
import path from "path";

const repoRoot = path.resolve(process.cwd());
const templatesDir = path.join(repoRoot, "templates");
const outputDir = path.join(repoRoot, "frontend", "src", "legacy", "templates");

function pascalCaseSegments(segments) {
  return segments
    .filter(Boolean)
    .map((segment) =>
      segment
        .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase())
        .replace(/^[a-z]/, (chr) => chr.toUpperCase())
        .replace(/[^a-zA-Z0-9]/g, "")
    )
    .join("");
}

function sanitizeHtml(html) {
  return html.replace(/`/g, "\\`").replace(/\$\{/g, "\\${");
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function convertFile(filePath) {
  const relative = path.relative(templatesDir, filePath);
  const withoutExt = relative.replace(/\.html$/i, "");
  const segments = withoutExt.split(path.sep);
  const componentName = pascalCaseSegments(segments) || "Template";
  const outputPath = path.join(outputDir, `${withoutExt}.tsx`);

  const rawHtml = await fs.readFile(filePath, "utf8");
  const serializedHtml = JSON.stringify(rawHtml);

  const component = `/* Auto-generated from ${relative} */
import React from "react";

export const rawHtml = ${serializedHtml};

export default function ${componentName}(props: { html?: string; wrapperClassName?: string }) {
  const { html = rawHtml, wrapperClassName } = props;
  return (
    <div className={wrapperClassName} dangerouslySetInnerHTML={{ __html: html }} />
  );
}
`;

  await ensureDir(path.dirname(outputPath));
  await fs.writeFile(outputPath, component, "utf8");
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fullPath);
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) {
      await convertFile(fullPath);
    }
  }
}

async function main() {
  await walk(templatesDir);
  console.log("Templates converted to", outputDir);
}

main().catch((err) => {
  console.error("Conversion failed", err);
  process.exit(1);
});
