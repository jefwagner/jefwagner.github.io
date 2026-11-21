// Fixture widget: y = a·sin(x), with a slider for the amplitude a.
// Shows the widget contract (default-exported mount(el)), using the global
// Plotly from [extra] plotly = true, and reading theme colors from the page's
// CSS tokens so the plot matches dark and light mode.

export default function mount(el) {
  const css = getComputedStyle(document.documentElement);
  const token = (name) => css.getPropertyValue(name).trim();

  const controls = document.createElement("label");
  controls.className = "widget-controls";
  controls.textContent = "amplitude a = ";
  const value = document.createElement("output");
  const slider = document.createElement("input");
  Object.assign(slider, { type: "range", min: "0", max: "2", step: "0.05", value: "1" });
  controls.append(value, slider);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  el.append(controls, plot);

  const xs = Array.from({ length: 201 }, (_, i) => (i / 200) * 2 * Math.PI);
  const layout = {
    margin: { l: 40, r: 10, t: 10, b: 30 },
    paper_bgcolor: token("--bg"),
    plot_bgcolor: token("--bg"),
    font: { color: token("--fg") },
    xaxis: { gridcolor: token("--border"), zerolinecolor: token("--border") },
    yaxis: { range: [-2.2, 2.2], gridcolor: token("--border"), zerolinecolor: token("--border") },
  };
  const config = { displayModeBar: false, responsive: true };

  function draw() {
    const a = Number(slider.value);
    value.textContent = a.toFixed(2);
    Plotly.react(plot, [{
      x: xs,
      y: xs.map((x) => a * Math.sin(x)),
      mode: "lines",
      line: { color: token("--accent"), width: 3 },
    }], layout, config);
  }

  slider.addEventListener("input", draw);
  draw();
}
