// Mount interactive widgets (loaded on pages with [extra] widgets or plotly = true).
//
// Markup, from the `widget` component in templates/components.html:
//   <div class="widget" data-src="sine.js" style="height:360px"></div>
// data-src is an ES module, resolved relative to the page (so a page bundle's
// own files work), that exports:
//   export default function mount(el) { ... }
// A widget that fails to load or mount shows an error in its own box; the
// others still mount.

for (const el of document.querySelectorAll(".widget[data-src]")) {
  const src = el.dataset.src;
  const url = new URL(src, document.baseURI);
  import(url)
    .then((mod) => {
      if (typeof mod.default !== "function") {
        throw new Error("module has no default export function mount(el)");
      }
      return mod.default(el);
    })
    .catch((err) => {
      console.error(`widget ${src}:`, err);
      el.classList.add("widget-error");
      el.textContent = `Widget failed: ${src}: ${err.message}`;
    });
}
