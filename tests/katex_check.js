// Render every math expression in built pages with KaTeX, failing on errors.
//
//   node tests/katex_check.js KATEX_JS FILE.html [FILE.html ...]
//
// Finds math the same way static/math.js does in the browser:
//   display: <pre ...><code data-lang="math">...</code></pre>
//   inline:  <code>$...$</code> (a bare <code>; code blocks carry data-lang)
// and renders each with throwOnError, catching LaTeX that KaTeX rejects
// (Zola itself never validates math).
//
// Exit: 0 all rendered; 1 some failed; 2 usage error or a file with no math.

"use strict";

const fs = require("fs");
const path = require("path");

function decode(html) {
  return html
    .replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, "&");
}

function extract(html) {
  const display = [...html.matchAll(
    /<pre\b[^>]*>\s*<code\b[^>]*data-lang="math"[^>]*>([\s\S]*?)<\/code>/g,
  )].map((m) => decode(m[1]).trim());
  const inline = [...html.matchAll(/<code>([\s\S]*?)<\/code>/g)]
    .map((m) => decode(m[1]))
    .filter((t) => t.length >= 3 && t.startsWith("$") && t.endsWith("$"))
    .map((t) => t.slice(1, -1));
  return { display, inline };
}

function main(argv) {
  if (argv.length < 2) {
    console.error("usage: node katex_check.js KATEX_JS FILE.html [FILE.html ...]");
    return 2;
  }
  const katex = require(path.resolve(argv[0]));
  let status = 0;
  for (const file of argv.slice(1)) {
    const { display, inline } = extract(fs.readFileSync(file, "utf8"));
    if (display.length + inline.length === 0) {
      console.error(`no math found: ${file}`);
      return 2;
    }
    let failed = 0;
    for (const [kind, list, displayMode] of [
      ["display", display, true],
      ["inline", inline, false],
    ]) {
      for (const tex of list) {
        try {
          katex.renderToString(tex, { displayMode, throwOnError: true });
        } catch (err) {
          failed += 1;
          const snippet = JSON.stringify(tex.slice(0, 60));
          console.log(`FAIL ${file}: ${kind}: ${snippet}: ${err.message}`);
        }
      }
    }
    if (failed) {
      status = 1;
    } else {
      console.log(`ok ${file}: ${display.length} display, ${inline.length} inline`);
    }
  }
  return status;
}

process.exit(main(process.argv.slice(2)));
