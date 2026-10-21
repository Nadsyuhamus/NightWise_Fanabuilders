"""NightWise dashboard v3.

Run with:  streamlit run app.py
Needs:     pip install streamlit plotly pandas

All data shown here is simulated.
"""
import random
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from environment import load_environment
from impact import (
    compare_energy,
    format_reduction_pct,
    habitat_summary,
    reduction_pct,
)

import json
from dataclasses import asdict

from comparison import run_comparison
from scenarios import get_scenario, get_scenarios

# ------------------------------------------------------------------ palette
SAGE, TAUPE, TANG, FUCH, AMETH = "#c0bda5", "#cc978e", "#f39c6b", "#ff3864", "#261447"
DSAGE = "#8d8a6e"  # darker sage for lines and rings

TICK_S = 0.6  # real seconds per simulated second while playing
SPECIES = ["Monkey", "Wild boar", "Civet", "Bat", "Bird", "Other"]
LAMP_COLOURS = [TANG, TAUPE, DSAGE, AMETH, FUCH]

ZONE_FILL = {
    "walking_path": "rgba(192,189,165,0.40)",
    "habitat_edge": "rgba(204,151,142,0.28)",
    "habitat_corridor": "rgba(38,20,71,0.93)",
}
ZONE_TEXT = {"habitat_corridor": "#e9e6f2"}

MODE_STYLE = {  # mode: (pill background, pill text)
    "idle": (SAGE, AMETH), "occupied": (TANG, AMETH), "fading": (TAUPE, AMETH),
    "fallback": (FUCH, "#ffffff"), "daylight": ("#e7e4d3", AMETH), "protected": (AMETH, "#ffffff"),
}
MODE_LABEL = {
    "idle": "Dim (idle)", "occupied": "Brightened", "fading": "Dimming down",
    "fallback": "Safe mode", "daylight": "Off (daylight)", "protected": "Protected",
}

st.set_page_config(page_title="NightWise", layout="wide", initial_sidebar_state="collapsed")

CSS = """
<style>
:root{--sage:#c0bda5;--taupe:#cc978e;--tang:#f39c6b;--fuchsia:#ff3864;--amethyst:#261447;
--bg:#faf8f3;--line:#e8e3d4;--soft:#5d5573;}
[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--amethyst);}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none;}
#MainMenu,footer{visibility:hidden;}
.block-container{max-width:1560px;padding:1.2rem 2.4rem 3rem;}
@media (max-width:820px){.block-container{padding:1rem 1rem 3rem;}}

/* force readable text even if the browser or Streamlit is in dark mode */
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label,[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,
[data-testid="stExpander"] summary p,[data-testid="stExpander"] summary span,
[data-testid="stTickBarMin"],[data-testid="stTickBarMax"],
[data-testid="stSliderThumbValue"],[data-testid="stSlider"] p,
[data-testid="stToggle"] p,[data-testid="stForm"] p,h1,h2,h3{color:var(--amethyst)!important;}
[data-testid="stExpander"]{background:#fff;border:1px solid var(--line);border-radius:14px;}

/* header */
.hero{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:6px 4px 10px;}
.brand{font-size:2rem;font-weight:800;color:var(--amethyst);line-height:1.1;}
.tagline{font-size:1rem;color:var(--soft);margin-top:3px;}
.badge{font-size:.74rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap;
color:var(--fuchsia);border:1.5px solid var(--fuchsia);border-radius:999px;padding:5px 14px;}
.accent{height:4px;border-radius:99px;margin-bottom:16px;
background:linear-gradient(90deg,#c0bda5,#cc978e,#f39c6b,#ff3864);}

/* top navigation tabs */
div[data-baseweb="tab-list"]{gap:8px;background:#fff;padding:7px;border-radius:16px;
border:1px solid var(--line);box-shadow:0 1px 3px rgba(38,20,71,.06);margin-bottom:14px;}
button[data-baseweb="tab"]{border-radius:11px;padding:9px 22px;height:auto;background:transparent;}
button[data-baseweb="tab"] p{font-weight:700;color:var(--soft)!important;font-size:1rem;}
button[data-baseweb="tab"][aria-selected="true"]{background:var(--amethyst);}
button[data-baseweb="tab"][aria-selected="true"] p{color:#fff!important;}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none;}

/* cards */
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:16px;}
.card-title{font-size:1.05rem;font-weight:700;margin:2px 4px 2px;color:var(--amethyst);}
.card-sub{font-size:.85rem;color:var(--soft);margin:0 4px 10px;}

/* guided steps */
.steps{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 12px;}
.step{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid var(--line);
border-radius:999px;padding:6px 16px 6px 8px;font-size:.88rem;font-weight:600;color:var(--amethyst);}
.step b{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;
border-radius:50%;background:var(--tang);color:var(--amethyst);font-size:.8rem;}

/* KPI tiles */
.kpi-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:2px 0 12px;}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px;
box-shadow:0 1px 2px rgba(38,20,71,.04);border-top:4px solid var(--tang);}
.kpi:nth-child(2){border-top-color:var(--taupe);}
.kpi:nth-child(3){border-top-color:var(--sage);}
.kpi:nth-child(4){border-top-color:var(--amethyst);}
.kpi-label{font-size:.72rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--soft);}
.kpi-value{font-size:1.6rem;font-weight:800;line-height:1.2;margin-top:2px;color:var(--amethyst);}
.kpi-sub{font-size:.8rem;color:var(--soft);margin-top:2px;}
.kpi-grid.wide{grid-template-columns:repeat(4,1fr);}
@media (max-width:820px){.kpi-grid.wide{grid-template-columns:repeat(2,1fr);}}

/* status + legend */
.status{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--line);
border-radius:999px;padding:5px 16px;font-size:.88rem;font-weight:600;color:var(--amethyst);}
.dot{width:10px;height:10px;border-radius:50%;background:var(--amethyst);}
.dot.day{background:var(--tang);} .dot.run{background:var(--fuchsia);}
.legend{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:.8rem;color:var(--soft);margin:8px 6px 4px;}
.legend span{display:inline-flex;align-items:center;gap:7px;}
.legend svg{flex:none;}

/* lamp cards */
.lamp-grid{display:grid;grid-template-columns:1fr;gap:10px;margin:6px 0 10px;}
.lamp{background:#fff;border:1px solid var(--line);border-radius:14px;padding:11px 14px;}
.lamp-top{display:flex;justify-content:space-between;align-items:center;}
.lamp-top b{font-size:1.05rem;color:var(--amethyst);}
.pill{font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:999px;}
.lamp-zone{font-size:.78rem;color:var(--soft);}
.bar{height:8px;border-radius:999px;background:#efece0;margin:8px 0 6px;overflow:hidden;}
.bar-fill{height:100%;background:linear-gradient(90deg,#f6b793,#f39c6b);}
.lamp-meta{display:flex;justify-content:space-between;font-size:.8rem;color:var(--soft);}
.lamp-reason{font-size:.8rem;margin-top:4px;color:var(--amethyst);}
.alert{background:rgba(255,56,100,.08);border:1px solid rgba(255,56,100,.35);color:#9b1236;
border-radius:12px;padding:9px 13px;font-size:.86rem;margin-bottom:8px;}
.note{background:rgba(192,189,165,.25);border:1px solid var(--sage);border-radius:12px;
padding:9px 13px;font-size:.86rem;margin:4px 0 10px;color:var(--amethyst);}

/* buttons */
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{
border-radius:12px;font-weight:700;border:1px solid var(--line);background:#fff;color:var(--amethyst);}
.stButton>button p,.stDownloadButton>button p,[data-testid="stFormSubmitButton"]>button p{color:var(--amethyst)!important;}
button[kind="primary"],button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"]{
background:var(--tang)!important;border-color:var(--tang)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------- simulation

@st.cache_data
def run(scenario_name):
    """Use the same scenario and comparison runner as the exporter."""
    comparison = run_comparison(scenario_name)

    frames = comparison["nightwise"]
    env = comparison["environment"]
    baseline_frames = comparison["fixed_baseline"]

    baseline_w = [
        frame["total_power_w"]
        for frame in baseline_frames
    ]

    return frames, env, baseline_w, baseline_frames

# ---------------------------------------------------------------- helpers
def kpi_grid(items, wide=False):
    cells = "".join(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>'
        for label, value, sub in items)
    st.markdown(f'<div class="kpi-grid{" wide" if wide else ""}">{cells}</div>', unsafe_allow_html=True)


def card_title(title, sub=""):
    st.markdown(f'<div class="card-title">{title}</div><div class="card-sub">{sub}</div>',
                unsafe_allow_html=True)


def lamp_card(row, zone_label):
    bg, fg = MODE_STYLE.get(row["mode"], (SAGE, AMETH))
    label = MODE_LABEL.get(row["mode"], row["mode"])
    warn = ""
    if row["sensor_status"] != "healthy":
        warn = f'<div class="lamp-reason" style="color:#9b1236">Sensor {row["sensor_status"]}</div>'
    return (
        f'<div class="lamp"><div class="lamp-top"><b>{row["lamp_id"]}</b>'
        f'<span class="pill" style="background:{bg};color:{fg}">{label}</span></div>'
        f'<div class="lamp-zone">{zone_label}</div>'
        f'<div class="bar"><div class="bar-fill" style="width:{row["brightness_pct"]}%"></div></div>'
        f'<div class="lamp-meta"><span>{row["brightness_pct"]:.2f}% brightness</span>'
        f'<span>{row["power_w"]:.2f} W</span></div>'
        f'<div class="lamp-reason">{row["reason"]}</div>{warn}</div>')


def style_fig(fig, height=320):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=28, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=AMETH), legend=dict(orientation="h", y=1.14, x=0),
        hoverlabel=dict(bgcolor="white", font_color=AMETH))
    fig.update_xaxes(gridcolor="#ece8d9", zeroline=False)
    fig.update_yaxes(gridcolor="#ece8d9", zeroline=False)
    return fig


def show(fig):
    try:  # newer Streamlit
        st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch")
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def wide_button(col, label, **kwargs):
    try:  # newer Streamlit
        return col.button(label, width="stretch", **kwargs)
    except TypeError:  # older Streamlit
        return col.button(label, use_container_width=True, **kwargs)


def svg(inner):
    return f'<svg width="16" height="16" viewBox="0 0 16 16">{inner}</svg>'


LEGEND = (
    '<div class="legend">'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6 fill={TANG} stroke=white stroke-width=2 />")}Lamp, lit (glow grows with brightness)</span>'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6 fill={SAGE} stroke=white stroke-width=2 />")}Lamp, off</span>'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6 fill={FUCH} stroke=white stroke-width=2 />")}Lamp in safe mode (sensor problem)</span>'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6.5 fill=none stroke={DSAGE} stroke-width=1.4 stroke-dasharray=2,2 />")}Motion sensor range</span>'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6 fill={AMETH} stroke=white stroke-width=2 />")}Resident</span>'
    f'<span>{svg(f"<polygon points=8,1 10,6 15,6.3 11,9.6 12.3,15 8,12 3.7,15 5,9.6 1,6.3 6,6 fill={FUCH} />")}Wild animal</span>'
    f'<span>{svg(f"<polygon points=8,2 14,8 8,14 2,8 fill={AMETH} />")}Light measuring point</span>'
    f'<span>{svg(f"<circle cx=8 cy=8 r=6 fill=none stroke={FUCH} stroke-width=2.5 />")}Resident ping</span>'
    '</div>'
    '<div class="legend">'
    f'<span><svg width="16" height="16"><rect width="16" height="16" rx="4" fill="rgba(192,189,165,0.7)"/></svg>Walking path</span>'
    f'<span><svg width="16" height="16"><rect width="16" height="16" rx="4" fill="rgba(204,151,142,0.5)"/></svg>Habitat edge</span>'
    f'<span><svg width="16" height="16"><rect width="16" height="16" rx="4" fill="{AMETH}"/></svg>Habitat corridor (no lamps, kept dark)</span>'
    '</div>'
)


def make_map(env, frame, day, pings):
    """Township map: zones, path, trees, glowing lamps, agents, pings and lux points."""
    width, height = env.get("width_m", 60), env.get("height_m", 40)
    zones = env.get("zones", [])
    lamp_cfg = {lamp["lamp_id"]: lamp for lamp in env["lamps"]}
    lux_by_point = {r["point_id"]: r["artificial_lux"] for r in frame["lux_readings"]}
    fig = go.Figure()
    shapes, notes = [], []

    for zone in zones:
        x0, y0, x1, y1 = zone["bounds_m"]
        shapes.append(dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, layer="below", line=dict(width=0),
                           fillcolor=ZONE_FILL.get(zone["zone_id"], "rgba(200,200,200,0.3)")))
        notes.append(dict(x=x0 + 2, y=y1 - 1.2, text=zone["label"].upper(), showarrow=False,
                          xanchor="left", yanchor="top",
                          font=dict(size=11, color=ZONE_TEXT.get(zone["zone_id"], AMETH))))
    if day:
        shapes.append(dict(type="rect", x0=0, y0=0, x1=width, y1=height, layer="below", line=dict(width=0),
                           fillcolor="rgba(243,156,107,0.10)"))
        notes.append(dict(x=width - 2, y=height - 1.2, text="DAYLIGHT: LAMPS OFF", showarrow=False,
                          xanchor="right", yanchor="top", font=dict(size=11, color="#b4541a")))

    shapes.append(dict(type="line", x0=0, x1=width, y0=10, y1=10, layer="below",
                       line=dict(color="rgba(255,255,255,0.8)", width=22)))
    shapes.append(dict(type="line", x0=0, x1=width, y0=10, y1=10, layer="below",
                       line=dict(color="rgba(192,189,165,0.9)", width=1, dash="dash")))

    rng = random.Random(7)
    bounds = {z["zone_id"]: z["bounds_m"] for z in zones}
    if "habitat_corridor" in bounds:
        _, cy0, _, cy1 = bounds["habitat_corridor"]
        tx = [rng.uniform(2.5, width - 2.5) for _ in range(18)]
        ty = [rng.uniform(cy0 + 3, cy1 - 2) for _ in range(18)]
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(symbol="triangle-up", color="rgba(192,189,165,0.5)",
                                             size=[rng.randint(10, 17) for _ in tx])))
    if "habitat_edge" in bounds:
        _, ey0, _, ey1 = bounds["habitat_edge"]
        bx = [rng.uniform(2.5, width - 2.5) for _ in range(10)]
        by = [rng.uniform(ey0 + 1, ey1 - 3) for _ in range(10)]
        fig.add_trace(go.Scatter(x=bx, y=by, mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(symbol="circle", color="rgba(192,189,165,0.75)", size=9)))

    for row in frame["lamps"]:
        lamp = lamp_cfg[row["lamp_id"]]
        x, y, b = lamp["x_m"], lamp["y_m"], row["brightness_pct"]
        rr = lamp["sensor_radius_m"]
        shapes.append(dict(type="circle", x0=x - rr, x1=x + rr, y0=y - rr, y1=y + rr, layer="below",
                           line=dict(color=DSAGE, width=1, dash="dot"), fillcolor="rgba(0,0,0,0)"))
        if b > 0:
            for scale, alpha in ((1.0, 0.10), (0.66, 0.16), (0.36, 0.30)):
                r = (2.0 + 0.10 * b) * scale
                shapes.append(dict(type="circle", x0=x - r, x1=x + r, y0=y - r, y1=y + r, layer="below",
                                   line=dict(width=0), fillcolor=f"rgba(243,156,107,{alpha})"))

    for point in env["measurement_points"]:
        in_corridor = point["zone"] == "habitat_corridor"
        lux = lux_by_point.get(point["point_id"], 0.0)
        fig.add_trace(go.Scatter(
            x=[point["x_m"]], y=[point["y_m"]], mode="markers+text" if in_corridor else "markers",
            text=[f"{lux:.2f} lx"] if in_corridor else None, textposition="top center",
            textfont=dict(size=10, color="#e9e6f2"),
            marker=dict(symbol="diamond", size=9, color="#ffffff" if in_corridor else AMETH,
                        line=dict(color=AMETH, width=1)),
            hovertext=f"{point['point_id']}<br>{lux:.3f} lux (modelled)", hoverinfo="text", showlegend=False))

    fig.add_trace(go.Scatter(
        x=[lamp_cfg[r["lamp_id"]]["x_m"] for r in frame["lamps"]],
        y=[lamp_cfg[r["lamp_id"]]["y_m"] for r in frame["lamps"]],
        mode="markers+text",
        text=[f"{r['lamp_id']}  {r['brightness_pct']:.2f}%" for r in frame["lamps"]],
        textposition="bottom center", textfont=dict(size=11, color=AMETH),
        marker=dict(size=18, line=dict(color="white", width=2.5),
                    color=[FUCH if r["mode"] == "fallback" else (TANG if r["brightness_pct"] > 0 else SAGE)
                           for r in frame["lamps"]]),
        hovertext=[f"<b>{r['lamp_id']}</b><br>{MODE_LABEL.get(r['mode'], r['mode'])}: {r['reason']}"
                   f"<br>{r['brightness_pct']:.2f}% brightness, {r['power_w']:.2f} W" for r in frame["lamps"]],
        hoverinfo="text", showlegend=False))

    if pings:
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in pings], y=[p["y"] for p in pings], mode="markers+text",
            text=[p["species"] for p in pings], textposition="top center",
            textfont=dict(size=10, color=FUCH),
            marker=dict(symbol="circle-open", size=22, color=FUCH, line=dict(width=3)),
            hovertext=[f"Resident ping: {p['species']}<br>{p['reported_at']}" for p in pings],
            hoverinfo="text", showlegend=False))

    for agent in frame["agents"]:
        person = agent["agent_type"] == "person"
        fig.add_trace(go.Scatter(
            x=[agent["x_m"]], y=[agent["y_m"]], mode="markers", showlegend=False,
            marker=dict(symbol="circle" if person else "star", size=15 if person else 20,
                        color=AMETH if person else FUCH, line=dict(color="white", width=2)),
            hovertext=agent["agent_id"].replace("_", " ").title(), hoverinfo="text"))

    shapes.append(dict(type="line", x0=3, x1=13, y0=2.5, y1=2.5, line=dict(color=AMETH, width=3)))
    notes.append(dict(x=8, y=4.2, text="10 m", showarrow=False, font=dict(size=10, color=AMETH)))

    fig.update_layout(shapes=shapes, annotations=notes, height=470, showlegend=False,
                      margin=dict(l=4, r=4, t=4, b=4), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(bgcolor="white", font_color=AMETH))
    fig.update_xaxes(range=[-3, width + 3], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-1.5, height + 1.5], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    return fig


def lamp_timeline(frames, t, lamp_ids, day):
    """Brightness of every lamp across the run, with the resident's walk shaded."""
    fig = go.Figure()
    xs = list(range(len(frames)))
    shapes, notes = [], []
    if day:
        shapes.append(dict(type="rect", x0=0, x1=len(frames) - 1, y0=0, y1=118, layer="below",
                           line=dict(width=0), fillcolor="rgba(243,156,107,0.14)"))
        notes.append(dict(x=len(frames) / 2, y=108, text="Scheduled daytime: lamps off; motion faults remain reportable", showarrow=False,
                          font=dict(size=11, color="#b4541a")))
    for agent_id, label, fill, ypos in (
            ("PERSON_1", "Resident walks", "rgba(38,20,71,0.08)", 112),
            ("ANIMAL_1", "Wild animal in zone", "rgba(255,56,100,0.10)", 102)):
        times = [f["time_s"] for f in frames if any(a["agent_id"] == agent_id for a in f["agents"])]
        if times:
            shapes.append(dict(type="rect", x0=min(times), x1=max(times), y0=0, y1=118, layer="below",
                               line=dict(width=0), fillcolor=fill))
            notes.append(dict(x=min(times) + 1, y=ypos, text=label, showarrow=False, xanchor="left",
                              font=dict(size=10, color=AMETH if agent_id == "PERSON_1" else "#b3153b")))
    shapes.append(dict(type="line", x0=t, x1=t, y0=0, y1=118, line=dict(color=FUCH, width=2, dash="dot")))
    for i, lid in enumerate(lamp_ids):
        ys = [next(r["brightness_pct"] for r in f["lamps"] if r["lamp_id"] == lid) for f in frames]
        fig.add_trace(go.Scatter(x=xs, y=ys, name=lid, mode="lines",
                                 line=dict(color=LAMP_COLOURS[i % len(LAMP_COLOURS)], width=3)))
    fig.update_layout(shapes=shapes, annotations=notes)
    fig.update_xaxes(title="Simulated seconds")
    fig.update_yaxes(title="Brightness %", range=[0, 118])
    return style_fig(fig, 270)


# ------------------------------------------------- live map + properties
def dashboard_energy(frames, baseline_w):
    """Calculate energy savings using matched simulation intervals."""
    if len(frames) != len(baseline_w):
        raise ValueError(
            "Baseline power count differs from frame count"
        )

    baseline_frames = [
        {
            "time_s": frame["time_s"],
            "dt_s": frame["dt_s"],
            "total_power_w": power_w,
        }
        for frame, power_w in zip(frames, baseline_w)
    ]

    return compare_energy(frames, baseline_frames)

def render_live(frames, env, baseline_w, zone_labels, lamp_ids):
    """Map and properties panel. A fragment, so Play only refreshes this part."""
    ss = st.session_state
    last = len(frames) - 1
    if ss.playing:
        ss.t = min(ss.t + 1, last)

    top_l, top_r = st.columns([4, 1])
    with top_r:
        show_props = st.toggle("Show properties", value=True, key="show_props")
    t = ss.t
    state_dot, state_text = "", "Ready. Press Start simulation"
    if ss.playing:
        state_dot, state_text = " run", "Running"
    elif t >= last:
        state_text = "Finished. Press Replay or drag the timeline"
    elif t > 0:
        state_text = "Paused"
    st.slider(
        "Timeline: drag to jump to any moment",
        0,
        last,
        key="t",
    )

    t = ss.t
    frame = frames[t]

    day = not frame["lamps"][0]["is_night"]
    daylight_ok = frame["lamps"][0]["daylight_ok"]

    seconds = int(frame["time_s"])
    clock = f"{seconds // 60:02d}:{seconds % 60:02d}"

    time_of_day = (
        ("Daylight" if day else "Night")
        if daylight_ok
        else "Day/night input unavailable"
    )

    top_l.markdown(
        f'<div class="status">'
        f'<span class="dot{state_dot}"></span>{state_text} &nbsp;|&nbsp; '
        f'{time_of_day} &nbsp;|&nbsp; Simulation clock {clock}</div>',
        unsafe_allow_html=True,
    )

    if show_props:
        col_map, col_props = st.columns([5, 3], gap="large")
    else:
        col_map, col_props = st.container(), None

    with col_map:
        with st.container(border=True):
            card_title("Township map", "Hover over a lamp or point for details")
            show(
                make_map(
                    env,
                    frame,
                    day and daylight_ok,
                    ss.get("sightings", []),
                )
            )
            st.markdown(LEGEND, unsafe_allow_html=True)

    if col_props is not None:
        with col_props:
            with st.container(border=True):
                card_title("Properties", "Live numbers for this moment")
                live_impact = dashboard_energy(
                    frames[: t + 1],
                    baseline_w[: t + 1],
                )
                saved = live_impact["savings_pct"]
                lit = sum(1 for r in frame["lamps"] if r["brightness_pct"] > 0)
                raised = sum(1 for r in frame["lamps"] if r["mode"] == "occupied")
                n = len(frame["lamps"])
                kpi_grid([
                    (
                        "Power used",
                        f"{frame['total_power_w']:.2f} W",
                        f"fixed baseline: {baseline_w[t]:.2f} W",
                    ),
                    (
                        "Energy reduction",
                        format_reduction_pct(saved),
                        (
                            f"fixed − adaptive: "
                            f"{live_impact['saved_kwh'] * 1000:+.4f} Wh; "
                            "+ saved, − extra use"
                        ),
                    ),
                    (
                        "Lights lit",
                        f"{lit} of {n}",
                        f"{raised} brightened for movement",
                    ),
                    (
                        "Resident pings",
                        str(len(ss.get("sightings", []))),
                        "wild animal reports",
                    ),
                ])

                if not daylight_ok:
                    st.warning(
                        "Day/night input unavailable: lamps use "
                        "configured zone fallback."
                    )

                for r in frame["lamps"]:
                    if r["sensor_status"] != "healthy":
                        st.markdown(
                            f'<div class="alert">'
                            f'<b>{r["lamp_id"]}</b>: motion sensor '
                            f'{r["sensor_status"]}; mode: {r["mode"]}; '
                            f'brightness: {r["brightness_pct"]:.2f}%; '
                            f'power: {r["power_w"]:.2f} W.'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                for r in frame["lamps"]:
                    if r["sensor_status"] != "healthy":
                        st.markdown(
                            f'<div class="alert">'
                            f'<b>{r["lamp_id"]}</b>: motion sensor '
                            f'{r["sensor_status"]}; mode: {r["mode"]}; '
                            f'brightness: {r["brightness_pct"]:.2f}%; '
                            f'power: {r["power_w"]:.2f} W.'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                with st.expander("Lights lit: which lamps and how bright"):
                    if day:
                        lit_count = sum(
                            r["brightness_pct"] > 0
                            for r in frame["lamps"]
                        )
                        unhealthy_count = sum(
                            r["sensor_status"] != "healthy"
                            for r in frame["lamps"]
                        )

                        st.markdown(
                            '<div class="note">'
                            f'Scheduled daytime: {lit_count} lamp(s) lit; '
                            f'modelled lamp power: '
                            f'{frame["total_power_w"]:.2f} W. '
                            f'Motion sensors requiring attention: '
                            f'{unhealthy_count}.'
                            '</div>',
                            unsafe_allow_html=True,
                        )

                pings = ss.get("sightings", [])
                with st.expander("Resident pings"):
                    if not pings:
                        st.markdown('<div class="note">No pings yet. Residents can report an animal '
                                    'in the Community tab.</div>', unsafe_allow_html=True)
                    for p in reversed(pings[-5:]):
                        st.markdown(f'<div class="note"><b>{p["species"]}</b> at {zone_labels.get(p["zone"], p["zone"])}'
                                    f' &nbsp;|&nbsp; {p["reported_at"]}</div>', unsafe_allow_html=True)

    if ss.playing and ss.t >= last:
        ss.playing = False
        st.rerun()


# ------------------------------------------------------------------- page
st.markdown(
    '<div class="hero"><div><div class="brand">NightWise</div>'
    '<div class="tagline">Smart township lighting that protects nature</div></div>'
    '<div class="badge">Simulated data</div></div><div class="accent"></div>',
    unsafe_allow_html=True)

ss = st.session_state
lamp_ids = [lamp["lamp_id"] for lamp in load_environment()["lamps"]]

scenario_name = st.selectbox(
    "Scenario",
    options=list(get_scenarios()),
    index=list(get_scenarios()).index("one_pedestrian"),
    key="scenario_name",
)

scenario = get_scenario(scenario_name)
st.caption(scenario.description)

st.download_button(
    "Download scenario definition",
    data=json.dumps(asdict(scenario), indent=2),
    file_name=f"{scenario_name}_scenario.json",
    mime="application/json",
)

ss.setdefault("t", 0)
ss.setdefault("playing", False)
ss.setdefault("sightings", [])
ss.setdefault("feedback", [])

if ss.get("cfg_applied") != scenario_name:
    ss.cfg_applied = scenario_name
    ss.t = 0
    ss.playing = False

frames, env, baseline_w, baseline_frames = run(scenario_name)
zone_labels = {z["zone_id"]: z["label"] for z in env.get("zones", [])}

tab_map, tab_comm, tab_more = st.tabs(["Live map", "Community", "Analysis"])

# ---- Live map (main page)
with tab_map:
    st.markdown(
        '<div class="steps"><div class="step"><b>1</b>Choose what happens tonight</div>'
        '<div class="step"><b>2</b>Press Start simulation</div>'
        '<div class="step"><b>3</b>Watch the map and the properties panel</div></div>',
        unsafe_allow_html=True)

    with st.container(border=True):
        card_title(
            "Scenario replay",
            "Choose a scenario above, then start the replay.",
        )
        c4, c5 = st.columns(2)
        last = len(frames) - 1
        if ss.playing:
            label = "Pause"
        elif ss.t >= last:
            label = "Replay"
        elif ss.t > 0:
            label = "Resume"
        else:
            label = "Start simulation"
        if wide_button(c4, label, type="primary", key="btn_start"):
            if ss.playing:
                ss.playing = False
            else:
                if ss.t >= last:
                    ss.t = 0
                ss.playing = True
            st.rerun()
        if wide_button(c5, "Restart", key="btn_restart"):
            ss.t = 0
            ss.playing = False
            st.rerun()

    live = st.fragment(
        render_live,
        run_every=TICK_S if ss.playing else None,
    )
    live(frames, env, baseline_w, zone_labels, lamp_ids)

# ---- Community
with tab_comm:
    kpi_grid([
        ("Wildlife pings", str(len(ss.sightings)), "shown on the Live map"),
        ("Lighting feedback", str(len(ss.feedback)), "too dark or too bright"),
        ("Reviewed by", "Operator", "reports never control lamps"),
        ("Data", "Simulated", "demo entries only"),
    ], wide=True)
    col_a, col_b = st.columns(2, gap="large")
    labels = {label: zid for zid, label in zone_labels.items()}
    centres = {z["zone_id"]: (z["bounds_m"][1] + z["bounds_m"][3]) / 2 for z in env.get("zones", [])}
    with col_a:
        with st.container(border=True):
            card_title("Ping a wild animal", "Tell the team where you saw it. It appears on the Live map.")
            with st.form("sighting_form", clear_on_submit=True):
                species = st.selectbox("What did you see?", SPECIES)
                where = st.selectbox("In which zone?", list(labels))
                along = st.slider("Where along the zone? (metres from the left edge)", 0, 60, 30)
                detail = st.text_input("Note (optional)")
                if st.form_submit_button("Send ping", type="primary"):
                    zid = labels[where]
                    n = len(ss.sightings)
                    ss.sightings.append({
                        "reported_at": datetime.now().strftime("%H:%M:%S"), "species": species,
                        "zone": zid, "x": float(along), "y": centres.get(zid, 20) + ((n % 3) - 1) * 2.0,
                        "note": detail})
            if ss.sightings:
                sdf = pd.DataFrame(ss.sightings)[["reported_at", "species", "zone", "note"]]
                st.dataframe(sdf, hide_index=True)
                st.download_button("Download pings CSV", sdf.to_csv(index=False), "pings.csv", "text/csv")
    with col_b:
        with st.container(border=True):
            card_title("Lighting feedback", "Tell us if an area feels too dark or too bright")
            with st.form("feedback_form", clear_on_submit=True):
                lamp = st.selectbox("Nearest lamp", lamp_ids)
                issue = st.radio("How does it feel?", ["Too dark", "Too bright"], horizontal=True)
                note = st.text_input("Comment (optional)")
                if st.form_submit_button("Send feedback", type="primary"):
                    ss.feedback.append({"reported_at": datetime.now().strftime("%H:%M:%S"),
                                        "lamp_id": lamp, "issue": issue, "comment": note})
            if ss.feedback:
                fdf = pd.DataFrame(ss.feedback)
                st.dataframe(fdf, hide_index=True)
                st.download_button("Download feedback CSV", fdf.to_csv(index=False), "feedback.csv", "text/csv")

# ---- Analysis (everything else)
with tab_more:
    impact = dashboard_energy(frames, baseline_w)

    adaptive_wh = impact["adaptive_kwh"] * 1000
    baseline_wh = impact["baseline_kwh"] * 1000
    saved_all = impact["savings_pct"]
    kpi_grid([
    (
        "Energy reduction",
        format_reduction_pct(saved_all),
        "whole replay; N/A when baseline energy is zero",
    ),
    (
        "Energy difference",
        f"{impact['saved_kwh'] * 1000:+.4f} Wh",
        "fixed − adaptive; + saved, − extra use",
    ),
    (
        "Smart lamps used",
        f"{adaptive_wh:.2f} Wh",
        "adaptive system",
    ),
    (
        "Fixed baseline",
        f"{baseline_wh:.2f} Wh",
        "walking path 70%; habitat edge 30%; daytime off",
    ),
    (
        "Peak power",
        f"{max(f['total_power_w'] for f in frames):.2f} W",
        "highest moment, adaptive",
    ),
    ], wide=True)

    st.caption(
    "Energy difference = fixed baseline − adaptive energy. "
    "Positive values mean savings; negative values mean extra consumption. "
    "Percentage reduction is N/A when baseline energy is zero."
)

    with st.container(border=True):
        card_title("Power over time", "Smart lamps compared with fixed lighting.")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(frames))), y=baseline_w, name="Fixed baseline",
                                 line=dict(color=DSAGE, width=2), fill="tozeroy",
                                 fillcolor="rgba(192,189,165,0.30)"))
        fig.add_trace(go.Scatter(x=list(range(len(frames))), y=[f["total_power_w"] for f in frames],
                                 name="Smart lamps", line=dict(color=TANG, width=3), fill="tozeroy",
                                 fillcolor="rgba(243,156,107,0.35)"))
        fig.update_xaxes(title="Simulated seconds")
        fig.update_yaxes(title="Watts")
        show(style_fig(fig, 330))
        st.caption(
            "Fixed baseline: walking-path lamps at 70% and the habitat-edge "
            "lamp at 30% throughout nighttime; off during scheduled daytime. "
            "Both policies use identical fixtures and shielding. "
            "Energy and savings apply only to this simulated replay."
        )

    points = [
        point
        for point in env["measurement_points"]
        if point["zone"] == "habitat_corridor"
    ]

    with st.container(border=True):
        card_title(
            "Light reaching the habitat corridor",
            "Modelled artificial illuminance and exposure",
        )

        scope_label = st.selectbox(
            "Habitat averaging period",
            ["Nighttime only", "Full run"],
            key="habitat_averaging_scope",
        )

        night_only = scope_label == "Nighttime only"

        if not points:
            st.info("No habitat-corridor measurement points are configured.")

        else:
            point_ids = [point["point_id"] for point in points]

            adaptive_habitat = habitat_summary(
                frames,
                point_ids,
                night_only=night_only,
            )

            baseline_habitat = habitat_summary(
                baseline_frames,
                point_ids,
                night_only=night_only,
            )

            if (
                adaptive_habitat["duration_s"]
                != baseline_habitat["duration_s"]
            ):
                raise ValueError("Habitat comparison durations differ")

            if adaptive_habitat["duration_s"] == 0:
                st.info(
                    "No eligible readings for this period. "
                    "Choose Full run or a scenario containing nighttime."
                )

            else:
                cut = reduction_pct(
                    baseline_habitat["mean_lux"],
                    adaptive_habitat["mean_lux"],
                )

                kpi_grid([
                    (
                        "Mean light reduction",
                        format_reduction_pct(cut),
                        scope_label,
                    ),
                    (
                        "Smart lamps",
                        f"{adaptive_habitat['mean_lux']:.3f} lux",
                        "duration-weighted mean; equal point weights",
                    ),
                    (
                        "Fixed baseline",
                        f"{baseline_habitat['mean_lux']:.3f} lux",
                        "same period and measurement points",
                    ),
                    (
                        "Smart exposure",
                        (
                            f"{adaptive_habitat['mean_point_exposure_lux_h']:.4f}"
                            " lux·h"
                        ),
                        "mean integrated exposure per point",
                    ),
                    (
                        "Baseline exposure",
                        (
                            f"{baseline_habitat['mean_point_exposure_lux_h']:.4f}"
                            " lux·h"
                        ),
                        "mean integrated exposure per point",
                    ),
                ], wide=True)

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=point_ids,
                    y=[
                        point["mean_lux"]
                        for point in baseline_habitat["points"]
                    ],
                    name="Fixed baseline",
                    marker_color=SAGE,
                ))

                fig.add_trace(go.Bar(
                    x=point_ids,
                    y=[
                        point["mean_lux"]
                        for point in adaptive_habitat["points"]
                    ],
                    name="Smart lamps",
                    marker_color=TANG,
                ))

                fig.update_layout(barmode="group")
                fig.update_yaxes(
                    title=f"Mean artificial lux — {scope_label}"
                )

                show(style_fig(fig, 300))

                st.caption(
                    f"Period: {scope_label}. "
                    f"Included duration: {adaptive_habitat['duration_s']:g} s. "
                    f"Measurement points: {adaptive_habitat['point_count']}. "
                    "Means are weighted by interval duration, with equal "
                    "weight per measurement point. Exposure integrates "
                    "lux over time. These selected points do not represent "
                    "an area-weighted habitat survey. Modelled artificial "
                    "light only; not measured data or proof of ecological "
                    "recovery."
                )

    with st.container(border=True):
        df = pd.DataFrame([
            {
                **row,
                "interval_wh": row["power_w"] * frame["dt_s"] / 3600,
                "brightness_seconds": (
                    row["brightness_pct"] * frame["dt_s"]
                ),
                "dt_s": frame["dt_s"],
                "occupied_seconds": (
                    frame["dt_s"] if row["mode"] == "occupied" else 0.0
                ),
                "fallback_seconds": (
                    frame["dt_s"] if row["mode"] == "fallback" else 0.0
                ),
            }
            for frame in frames
            for row in frame["lamps"]
        ])

        summary = df.groupby("lamp_id").agg(
            zone=("zone", "first"),
            brightness_seconds=("brightness_seconds", "sum"),
            duration_s=("dt_s", "sum"),
            peak=("brightness_pct", "max"),
            wh=("interval_wh", "sum"),
            active=("occupied_seconds", "sum"),
            safe=("fallback_seconds", "sum"),
        ).reindex(lamp_ids)

        summary["avg"] = (
            summary.pop("brightness_seconds")
            / summary.pop("duration_s")
        )

        summary = summary[
            ["zone", "avg", "peak", "wh", "active", "safe"]
        ]
        summary.insert(0, "Lamp", summary.index)
        summary["zone"] = summary["zone"].map(lambda z: zone_labels.get(z, z))
        st.dataframe(
            summary.rename(columns={"zone": "Zone", "avg": "Average brightness", "peak": "Peak brightness",
                                    "wh": "Energy (Wh)", "active": "Seconds brightened",
                                    "safe": "Seconds in safe mode"}),
            hide_index=True,
            column_config={
                "Average brightness": st.column_config.ProgressColumn(
                    "Average brightness", min_value=0, max_value=100, format="%.0f%%"),
                "Peak brightness": st.column_config.NumberColumn("Peak brightness", format="%.0f%%"),
                "Energy (Wh)": st.column_config.NumberColumn("Energy (Wh)", format="%.2f"),
            })

    st.info(
        "Use sensor_fault or stale_sensor in the scenario selector "
        "to test motion-input problems."
    )

st.caption("Simulated data. Illustrative settings, not real-world lighting standards.")
