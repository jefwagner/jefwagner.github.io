+++
title = "Fixture: math, code, and widgets"
date = 2026-01-01
draft = true
description = "Test fixture for KaTeX math, code highlighting, and the widget component. Never published."

[extra]
math = true
plotly = true
+++
Fixture placeholder text. Inline math: `$U_{\text{tot}}$` and `$\Phi = -\mathcal{F}/T$`.
Inline code that is not math: `zola build`.

Display math, including the cases that markdown mangles (`|_{`, `\,`, `\\`):

```math
\left.\frac{\partial S_{\text{res}}}{\partial U_{\text{res}}}
\right|_{U_{\text{res}}=U_{\text{tot}}} \, U
```

```math
\begin{aligned}
\mathcal{F} &= U - TS \\
\Phi &= S - \frac{U}{T}
\end{aligned}
```

Code block:

```rust
fn main() {
    let x: u32 = 42;
    println!("{x}");
}
```

Widget:

{{ <widget src="sine.js" height={360} /> }}
