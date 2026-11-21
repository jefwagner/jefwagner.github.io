// Render math with KaTeX (loaded before this script on pages with [extra] math = true).
//
// Math is written as code so Zola's markdown never touches it:
//   display:  ```math fenced blocks  -> <pre><code data-lang="math">
//   inline:   `$...$` inline code    -> <code>$...$</code> (outside <pre>)
// Anything else in backticks stays code.

(function () {
  "use strict";

  const options = { throwOnError: false };

  function renderDisplay() {
    for (const code of document.querySelectorAll('pre > code[data-lang="math"]')) {
      const out = document.createElement("div");
      out.className = "math-display";
      katex.render(code.textContent.trim(), out, { ...options, displayMode: true });
      code.parentElement.replaceWith(out);
    }
  }

  function renderInline() {
    for (const code of document.querySelectorAll("code")) {
      if (code.closest("pre")) continue;
      const text = code.textContent;
      if (text.length < 3 || !text.startsWith("$") || !text.endsWith("$")) continue;
      const out = document.createElement("span");
      out.className = "math-inline";
      katex.render(text.slice(1, -1), out, options);
      code.replaceWith(out);
    }
  }

  function render() {
    if (typeof katex === "undefined") {
      console.error("math.js: KaTeX is not loaded");
      return;
    }
    renderDisplay();
    renderInline();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
