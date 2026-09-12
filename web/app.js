// UI definitions -----------------------------------------------------------
// Each field: key, label, unit/hint, default, tooltip. Values are sent to bridge.py.
const FIELDS = {
  aircraft: [
    ["Airframe", [
      ["name", "Name", "", "Cessna 172S-like", "Free text label for plots."],
      ["mass", "Take-off mass", "kg", 1157, "Maximum take-off mass. Weight W = m·g0 is what the wing must lift."],
      ["S", "Wing area", "m²", 16.17, "Reference (planform) wing area S."],
      ["span", "Wing span", "m", 11.0, "Tip-to-tip span b. Aspect ratio AR = b²/S is computed from it."],
      ["CL_max", "Max lift coefficient", "–", 1.6, "Clean C_Lmax (no flaps). Light aircraft: 1.3–1.7. Sets stall speed."],
    ]],
    ["Drag", [
      ["CD0", "Zero-lift drag coeff. C_D0", "–", 0.033, "Parasite drag at zero lift. Clean sailplane ~0.012, light single ~0.025–0.035, strut-braced ~0.035–0.045."],
      ["e", "Oswald efficiency e", "–", 0.75, "Span efficiency for induced drag, 0.7–0.85 for straight wings."],
    ]],
    ["Propulsion & fuel", [
      ["propulsion", "Engine type", "", "prop", "Piston-propeller uses power; jet uses thrust. Switching changes the fields below.", {select: [["prop", "Piston + propeller"], ["jet", "Jet / turbofan"]]}],
      ["power_kW", "Engine shaft power (sea level)", "kW", 134, "Rated shaft power. 1 hp = 0.7457 kW. Piston lapse with altitude is applied automatically.", {showIf: ["propulsion", "prop"]}],
      ["eta_p", "Propeller efficiency", "–", 0.78, "Assumed constant. Cruise 0.75–0.85; fixed-pitch props do worse in climb (~0.6).", {showIf: ["propulsion", "prop"]}],
      ["sfc_kg_per_kWh", "Specific fuel consumption", "kg/kWh", 0.274, "Brake SFC. 0.45 lb/(hp·h) = 0.274 kg/kWh (typical aviation piston).", {showIf: ["propulsion", "prop"]}],
      ["thrust_kN", "Total sea-level static thrust", "kN", 186, "All engines combined. 1 lbf = 4.448 N, so 1000 lbf = 4.45 kN.", {showIf: ["propulsion", "jet"]}],
      ["lapse_m", "Thrust lapse exponent", "–", 0.8, "Thrust falls as (density ratio)^m with altitude. 1.0 is Anderson's turbojet assumption; 0.7–0.8 suits low-bypass turbofans.", {showIf: ["propulsion", "jet"]}],
      ["tsfc_per_h", "Thrust-specific fuel consumption", "1/h", 0.67, "Quoted as lb of fuel per lbf of thrust per hour. Dry turbofan 0.6–0.8; afterburning 1.9–2.5.", {showIf: ["propulsion", "jet"]}],
      ["fuel_mass", "Usable fuel", "kg", 144, "Avgas 0.72 kg/L, jet fuel 0.80 kg/L. Used for Breguet range/endurance.", {showIf: null}],
      ["h_cruise", "Cruise altitude", "m", 2438, "Altitude for the cruise-altitude results (2438 m = 8000 ft).", {showIf: null}],
    ]],
  ],
  sizing: [
    ["Mission requirements", [
      ["range_km", "Range", "km", 150, "Cruise distance the aircraft must cover (fuel is sized for it plus 6 % reserve)."],
      ["payload", "Payload mass", "kg", 4, "Everything that is not airframe, engine or fuel (sensors, cargo)."],
      ["V_cruise", "Cruise speed", "m/s", 30, "True airspeed in cruise."],
      ["h_cruise", "Cruise altitude", "m", 1000, "Density there sets the cruise constraint."],
      ["V_stall", "Max stall speed", "m/s", 14, "Lower stall speed → bigger wing. This usually sets the wing loading."],
      ["RC", "Climb rate at sea level", "m/s", 4, "Required vertical speed. Often the constraint that sets engine power."],
      ["S_G", "Take-off ground roll", "m", 60, "Distance to lift-off on a paved runway."],
      ["h_ceiling", "Service ceiling", "m", 4000, "Altitude where climb rate falls to 0.5 m/s."],
      ["loiter_min", "Loiter time", "min", 30, "Time on station (0 for none)."],
    ]],
    ["Design assumptions", [
      ["CD0", "Zero-lift drag coeff. C_D0", "–", 0.035, "Estimate for the class of aircraft."],
      ["AR", "Aspect ratio", "–", 9, "Span²/area. Higher → less induced drag, heavier wing."],
      ["e", "Oswald efficiency e", "–", 0.80, "0.7–0.85 for straight wings."],
      ["CL_max", "C_Lmax (clean)", "–", 1.4, "Used for the stall constraint."],
      ["CL_max_TO", "C_Lmax (take-off config)", "–", 1.6, "With flaps, used for the take-off constraint."],
      ["eta_p", "Propeller efficiency (cruise/climb)", "–", 0.70, "Small props: 0.6–0.75."],
      ["eta_p_TO", "Propeller efficiency (take-off)", "–", 0.55, "Low airspeed → lower efficiency."],
      ["sfc_kg_per_kWh", "Specific fuel consumption", "kg/kWh", 0.54, "Small two-stroke ~0.5–0.6; aviation four-stroke ~0.27."],
      ["empty_frac", "Empty mass fraction W_e/W_0", "–", 0.60, "Structure + engine + systems as a fraction of take-off mass. Small UAV 0.55–0.65; GA single ~0.6."],
    ]],
  ],
  rocket: [
    ["Airframe", [
      ["name", "Name", "", "54 mm mid-power rocket", ""],
      ["dry_mass_g", "Dry mass without motor", "g", 600, "Airframe + recovery + payload, motor excluded."],
      ["diameter_mm", "Body diameter", "mm", 54, "Reference area is the body cross-section."],
      ["Cd", "Drag coefficient C_D", "–", 0.45, "Typical model rockets 0.4–0.6 (subsonic, constant)."],
      ["launch_angle", "Launch angle from vertical", "°", 5, "0 = straight up. Small tilt gives a gravity turn."],
      ["rail_length", "Launch rail length", "m", 1.5, "Rocket is guided along the rail direction until it clears it."],
    ]],
    ["Motor (from catalogue data)", [
      ["motor_name", "Motor name", "", "AeroTech G80 (approx.)", ""],
      ["impulse", "Total impulse", "N·s", 136.6, "Area under the thrust curve. Letter classes: C 5–10, D 10–20, E 20–40, F 40–80, G 80–160, H 160–320."],
      ["burn_time", "Burn time", "s", 1.7, ""],
      ["peak_thrust", "Peak thrust", "N", 116, "Must be ≥ average thrust (impulse/burn time)."],
      ["prop_mass_g", "Propellant mass", "g", 62.5, "Sets Isp = impulse / (m_p·g0)."],
      ["casing_mass_g", "Motor casing mass (empty)", "g", 62.5, "Loaded motor mass minus propellant."],
    ]],
  ],
  deltav: [
    ["Inputs", [
      ["mode", "What to compute", "", "dv", "", {select: [["dv", "Δv from masses"], ["mp", "Propellant for a target Δv"]]}],
      ["isp", "Specific impulse Isp", "s", 300, "Solid ~230–280, kerosene/LOX ~300–340, LH2/LOX ~420–450."],
      ["m0", "Initial mass m0", "kg", 500000, "Only for 'Δv from masses'."],
      ["mf", "Final mass mf", "kg", 50000, "Mass after burn (structure + payload)."],
      ["dv", "Target Δv", "m/s", 9400, "Only for 'Propellant for a target Δv'. LEO ≈ 9.4 km/s incl. losses."],
    ]],
  ],
  atmos: [["Altitude", [["h", "Geometric altitude", "m", 11000, "0 to 86 000 m."]]]],
};

const PRESETS = {
  aircraft: {
    "Cessna 172S-like": {propulsion: "prop", name: "Cessna 172S-like", mass: 1157, S: 16.17, span: 11.0, CL_max: 1.6, CD0: 0.033, e: 0.75, power_kW: 134, eta_p: 0.78, sfc_kg_per_kWh: 0.274, fuel_mass: 144, h_cruise: 2438},
    "Piper PA-28-181 Archer-like": {propulsion: "prop", name: "PA-28 Archer-like", mass: 1157, S: 15.8, span: 10.8, CL_max: 1.5, CD0: 0.034, e: 0.76, power_kW: 134, eta_p: 0.78, sfc_kg_per_kWh: 0.274, fuel_mass: 130, h_cruise: 2438},
    "Motor glider (Stemme-like)": {propulsion: "prop", name: "motor glider", mass: 850, S: 18.7, span: 23.0, CL_max: 1.5, CD0: 0.016, e: 0.85, power_kW: 85, eta_p: 0.8, sfc_kg_per_kWh: 0.29, fuel_mass: 70, h_cruise: 2000},
    "Small gasoline UAV": {propulsion: "prop", name: "survey UAV", mass: 13.2, S: 0.77, span: 2.63, CL_max: 1.4, CD0: 0.035, e: 0.8, power_kW: 1.0, eta_p: 0.7, sfc_kg_per_kWh: 0.54, fuel_mass: 1.3, h_cruise: 1000},
    "F-14A Tomcat — military thrust": {propulsion: "jet", name: "F-14A Tomcat (mil thrust)", mass: 27200, S: 52.49, span: 19.55, CL_max: 1.6, CD0: 0.024, e: 0.75, thrust_kN: 110, lapse_m: 0.8, tsfc_per_h: 0.67, fuel_mass: 7348, h_cruise: 10000},
    "F-14A Tomcat — full afterburner": {propulsion: "jet", name: "F-14A Tomcat (afterburner)", mass: 27200, S: 52.49, span: 19.55, CL_max: 1.6, CD0: 0.024, e: 0.75, thrust_kN: 186, lapse_m: 0.8, tsfc_per_h: 2.5, fuel_mass: 7348, h_cruise: 10000},
    "F-14D Super Tomcat — afterburner": {propulsion: "jet", name: "F-14D Tomcat (F110, AB)", mass: 28000, S: 52.49, span: 19.55, CL_max: 1.6, CD0: 0.024, e: 0.75, thrust_kN: 247, lapse_m: 0.8, tsfc_per_h: 1.9, fuel_mass: 7348, h_cruise: 10000},
    "Airliner-like twin (A320-ish)": {propulsion: "jet", name: "narrow-body twin", mass: 68000, S: 122.6, span: 34.1, CL_max: 1.5, CD0: 0.020, e: 0.80, thrust_kN: 240, lapse_m: 0.8, tsfc_per_h: 0.60, fuel_mass: 15000, h_cruise: 11000},
  },
  sizing: {
    "Survey UAV (4 kg, 150 km)": {range_km: 150, payload: 4, V_cruise: 30, h_cruise: 1000, V_stall: 14, RC: 4, S_G: 60, h_ceiling: 4000, loiter_min: 30, CD0: 0.035, AR: 9, e: 0.8, CL_max: 1.4, CL_max_TO: 1.6, eta_p: 0.7, eta_p_TO: 0.55, sfc_kg_per_kWh: 0.54, empty_frac: 0.6},
    "4-seat light aircraft": {range_km: 1000, payload: 360, V_cruise: 62, h_cruise: 2438, V_stall: 27, RC: 3.8, S_G: 300, h_ceiling: 4300, loiter_min: 45, CD0: 0.033, AR: 7.3, e: 0.75, CL_max: 1.6, CL_max_TO: 2.0, eta_p: 0.78, eta_p_TO: 0.6, sfc_kg_per_kWh: 0.274, empty_frac: 0.62},
    "Long-endurance UAV (12 h)": {range_km: 300, payload: 8, V_cruise: 25, h_cruise: 2000, V_stall: 12, RC: 3, S_G: 80, h_ceiling: 5000, loiter_min: 600, CD0: 0.03, AR: 14, e: 0.8, CL_max: 1.5, CL_max_TO: 1.7, eta_p: 0.72, eta_p_TO: 0.55, sfc_kg_per_kWh: 0.5, empty_frac: 0.55},
  },
  rocket: {
    "54 mm mid-power on G80": {name: "54 mm mid-power rocket", dry_mass_g: 600, diameter_mm: 54, Cd: 0.45, launch_angle: 5, rail_length: 1.5, motor_name: "AeroTech G80 (approx.)", impulse: 136.6, burn_time: 1.7, peak_thrust: 116, prop_mass_g: 62.5, casing_mass_g: 62.5},
    "Small model rocket on Estes C6": {name: "24 mm model rocket", dry_mass_g: 60, diameter_mm: 24, Cd: 0.6, launch_angle: 2, rail_length: 1.0, motor_name: "Estes C6 (approx.)", impulse: 8.8, burn_time: 1.9, peak_thrust: 14, prop_mass_g: 12.5, casing_mass_g: 12, },
    "High-power on H-class (approx.)": {name: "75 mm high-power rocket", dry_mass_g: 1800, diameter_mm: 75, Cd: 0.45, launch_angle: 4, rail_length: 2.4, motor_name: "H-class 38 mm (approx.)", impulse: 280, burn_time: 2.0, peak_thrust: 220, prop_mass_g: 140, casing_mass_g: 150},
  },
  deltav: {
    "Single stage to LEO?": {mode: "mp", isp: 340, m0: 500000, mf: 50000, dv: 9400},
    "Falcon-9-like first stage (rough)": {mode: "dv", isp: 300, m0: 550000, mf: 140000, dv: 9400},
    "Model rocket (G80)": {mode: "dv", isp: 223, m0: 0.725, mf: 0.662, dv: 200},
  },
  atmos: {"Sea level": {h: 0}, "Tropopause 11 km": {h: 11000}, "Airliner cruise 11.9 km": {h: 11900}, "Everest 8849 m": {h: 8849}},
};

// build forms ---------------------------------------------------------------
function buildForm(tab) {
  const form = document.getElementById("form-" + tab);
  form.innerHTML = "";
  for (const [group, fields] of FIELDS[tab]) {
    const fs = document.createElement("fieldset");
    fs.innerHTML = `<legend>${group}</legend>`;
    for (const [key, label, unit, def, tip, extra] of fields) {
      const row = document.createElement("div");
      row.className = "row";
      row.title = tip || "";
      let input;
      if (extra && extra.select) {
        input = `<select name="${key}">${extra.select.map(([v, t]) => `<option value="${v}" ${v === def ? "selected" : ""}>${t}</option>`).join("")}</select>`;
      } else if (typeof def === "string") {
        input = `<input name="${key}" type="text" value="${def}">`;
      } else {
        input = `<input name="${key}" type="number" step="any" value="${def}">`;
      }
      const short = tip ? tip.split(". ")[0].replace(/\.$/, "") : "";
      const u = unit && unit !== "–" ? unit : "";
      row.innerHTML = `<label>${label}<small>${[u, short].filter(Boolean).join(" · ")}</small></label>${input}`;
      if (extra && extra.showIf) { row.dataset.showIf = extra.showIf[0]; row.dataset.showVal = extra.showIf[1]; }
      fs.appendChild(row);
    }
    form.appendChild(fs);
  }
  form.addEventListener("change", () => applyVisibility(tab));
  applyVisibility(tab);
  const box = document.querySelector(`.presets[data-for="${tab}"]`);
  box.innerHTML = "";
  for (const name of Object.keys(PRESETS[tab])) {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = name;
    b.onclick = () => applyPreset(tab, PRESETS[tab][name]);
    box.appendChild(b);
  }
}
function applyVisibility(tab) {
  const form = document.getElementById("form-" + tab);
  for (const row of form.querySelectorAll(".row[data-show-if]")) {
    const ctrl = form.elements[row.dataset.showIf];
    row.hidden = !ctrl || ctrl.value !== row.dataset.showVal;
  }
}
function applyPreset(tab, values) {
  const form = document.getElementById("form-" + tab);
  for (const [k, v] of Object.entries(values)) { const el = form.elements[k]; if (el) el.value = v; }
  applyVisibility(tab);
}
function readForm(tab) {
  const form = document.getElementById("form-" + tab);
  const out = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    out[el.name] = el.type === "number" ? parseFloat(el.value) : el.value;
    if (el.type === "number" && !isFinite(out[el.name])) throw new Error(`"${el.name}" is not a number`);
  }
  return out;
}

// tabs ----------------------------------------------------------------------
document.getElementById("nav").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  document.querySelectorAll("nav button").forEach(x => x.classList.toggle("active", x === b));
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.id === "tab-" + b.dataset.tab));
});
for (const tab of Object.keys(FIELDS)) buildForm(tab);

// pyodide -------------------------------------------------------------------
const PKG_FILES = ["__init__", "atmosphere", "aerodynamics", "aircraft_performance", "sizing", "rocket", "numerics", "trajectory", "plots"];
let pyodide = null, ready = false;
const statusEl = document.getElementById("status"), statusText = document.getElementById("status-text");
function setStatus(t) { statusText.textContent = t; statusEl.classList.remove("hidden"); }

async function boot() {
  try {
    setStatus("Loading Python runtime — about 10–20 s on first visit…");
    pyodide = await loadPyodide();
    setStatus("Loading numpy, scipy, matplotlib…");
    await pyodide.loadPackage(["numpy", "scipy", "matplotlib"]);
    setStatus("Loading the aerosizing package…");
    pyodide.FS.mkdirTree("/home/pyodide/aerosizing");
    for (const f of PKG_FILES) {
      const src = await (await fetch(`aerosizing/${f}.py`, {cache: "no-cache"})).text();
      pyodide.FS.writeFile(`/home/pyodide/aerosizing/${f}.py`, src);
    }
    const bridge = await (await fetch("web/bridge.py", {cache: "no-cache"})).text();
    await pyodide.runPythonAsync(bridge);
    ready = true;
    statusEl.classList.add("hidden");
    document.querySelectorAll(".run").forEach(b => b.disabled = false);
  } catch (err) {
    setStatus("Failed to load Python runtime: " + err);
  }
}
document.querySelectorAll(".run").forEach(b => b.disabled = true);
boot();

// run -----------------------------------------------------------------------
async function run(tab) {
  const out = document.getElementById("out-" + tab);
  const btn = document.querySelector(`.run[data-run="${tab}"]`);
  if (!ready) { out.innerHTML = `<div class="empty">Python runtime still loading…</div>`; return; }
  let params;
  try { params = readForm(tab); } catch (e) { out.innerHTML = `<div class="err">${e.message}</div>`; return; }
  btn.disabled = true; out.innerHTML = `<div class="empty">Computing…</div>`;
  await new Promise(r => setTimeout(r, 30));
  try {
    const fn = pyodide.globals.get("run_" + tab);
    const res = JSON.parse(fn(JSON.stringify(params)));
    fn.destroy && fn.destroy();
    let html = `<h2>Results</h2><table>${res.rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2] || ""}</td></tr>`).join("")}</table>`;
    if (res.meta) html += `<div class="meta">${res.meta}</div>`;
    for (const w of (res.warnings || [])) html += `<div class="warn">⚠︎ ${w}</div>`;
    html += `<div class="figs">${res.figs.map(f => `<img src="${f}" alt="plot">`).join("")}</div>`;
    out.innerHTML = html;
  } catch (e) {
    const msg = String(e).split("\n").filter(l => l.trim()).slice(-3).join("\n");
    out.innerHTML = `<div class="err">Calculation failed:\n${msg}\n\nCheck the inputs (e.g. peak thrust ≥ average thrust, enough engine power for level flight).</div>`;
  }
  btn.disabled = false;
}
document.querySelectorAll(".run").forEach(b => b.addEventListener("click", () => run(b.dataset.run)));
