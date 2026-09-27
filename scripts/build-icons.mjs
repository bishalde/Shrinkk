// Builds public/static/icons.svg: a sprite containing only the icons the app references.
// Lucide icons are referenced by name (icon('link')); brand icons as 'brand-<simple-icons slug>'.
import { existsSync, readFileSync, writeFileSync, readdirSync, statSync, mkdirSync } from "node:fs";
import { join, extname } from "node:path";

const ROOTS = ["templates", "services", "public/static/js"];
const PATTERNS = [
  /icon\(\s*['"]([a-z0-9-]+)['"]/g,          // Jinja macro calls
  /icons\.svg#i-([a-z0-9-]+)/g,              // raw <use> references
  /data-icon=["']([a-z0-9-]+)["']/g,
  /["']icon["']\s*:\s*["']([a-z0-9-]+)["']/g, // python/JS dicts: "icon": "brand-x"
];
// Icons chosen at runtime (e.g. from data) that no pattern can see.
const EXTRA = ["check", "x", "copy", "loader-circle", "circle-alert", "info", "circle-check"];

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return walk(path);
    return [".html", ".py", ".js"].includes(extname(path)) ? [path] : [];
  });
}

const names = new Set(EXTRA);
const isLucide = (n) => existsSync(`node_modules/lucide-static/icons/${n}.svg`);
for (const file of ROOTS.flatMap(walk)) {
  const text = readFileSync(file, "utf8");
  for (const re of PATTERNS) for (const m of text.matchAll(re)) names.add(m[1]);
  // Names passed through variables, e.g. {% for label, icon_name in [("Links", "link")] %}
  for (const m of text.matchAll(/["']([a-z0-9]+(?:-[a-z0-9]+)*)["']/g)) {
    if (m[1].length > 1 && isLucide(m[1])) names.add(m[1]);
  }
}

const symbols = [];
const missing = [];
for (const name of [...names].sort()) {
  if (name.startsWith("brand-")) {
    const slug = name.slice(6);
    try {
      const svg = readFileSync(`node_modules/simple-icons/icons/${slug}.svg`, "utf8");
      const path = svg.match(/<path d="([^"]+)"/)[1];
      symbols.push(`<symbol id="i-${name}" viewBox="0 0 24 24" fill="currentColor"><path d="${path}"/></symbol>`);
    } catch {
      missing.push(name);
    }
    continue;
  }
  try {
    const svg = readFileSync(`node_modules/lucide-static/icons/${name}.svg`, "utf8");
    const body = svg.slice(svg.indexOf(">", svg.indexOf("<svg")) + 1, svg.lastIndexOf("</svg>")).trim();
    symbols.push(
      `<symbol id="i-${name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ` +
        `stroke-linecap="round" stroke-linejoin="round">${body.replace(/\s*\n\s*/g, "")}</symbol>`
    );
  } catch {
    missing.push(name);
  }
}

mkdirSync("public/static", { recursive: true });
writeFileSync(
  "public/static/icons.svg",
  `<svg xmlns="http://www.w3.org/2000/svg" style="display:none">${symbols.join("")}</svg>\n`
);
console.log(`icons.svg: ${symbols.length} icons`);
if (missing.length) {
  console.error(`Unknown icons: ${missing.join(", ")}`);
  process.exit(1);
}
