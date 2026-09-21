"""
Interactive all-sky view.

Drag to pan, scroll to zoom, hover any object to identify it. This is the
planetarium page: constellation figures, planets, the Moon, and every star
down to your chosen magnitude limit, drawn in its true colour.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import astropy.units as u
from astropy.coordinates import AltAz, SkyCoord, get_body

import skyplan_core as core
import targets as tg

st.set_page_config(page_title="Sky map", page_icon="*", layout="wide")

location, t_ref, tz = core.observer_sidebar()

st.title("Sky map")

with st.sidebar:
    st.divider()
    st.header("Chart")
    mag_limit = st.slider("Magnitude limit", 2.0, 6.5, 5.0, 0.5)
    show_con = st.checkbox("Constellation figures", value=True)
    show_planets = st.checkbox("Planets", value=True)
    show_standards = st.checkbox("Spectral standards", value=True)
    show_targets = st.checkbox("Exoplanet hosts", value=True)
    label_bright = st.checkbox("Label bright stars", value=True)

R = 90.0  # horizon radius in projection units
fig = go.Figure()


# --------------------------------------------------------------------------
# horizon, altitude rings, cardinal points
# --------------------------------------------------------------------------

th = np.linspace(0, 2 * np.pi, 240)
for alt_ring, width, colour in [(0, 1.6, "rgba(150,170,205,0.55)"),
                                (30, 1.0, "rgba(120,140,180,0.22)"),
                                (60, 1.0, "rgba(120,140,180,0.22)")]:
    rr = R - alt_ring
    fig.add_trace(go.Scatter(
        x=rr * np.sin(th), y=rr * np.cos(th), mode="lines",
        line=dict(color=colour, width=width),
        hoverinfo="skip", showlegend=False,
    ))

for label, az in [("N", 0), ("E", 90), ("S", 180), ("W", 270)]:
    x, y = core.dome_xy(-7, az)
    fig.add_annotation(x=float(x), y=float(y), text=f"<b>{label}</b>",
                       showarrow=False, font=dict(color="#8d97ab", size=13))


# --------------------------------------------------------------------------
# constellation figures
# --------------------------------------------------------------------------

if show_con:
    cons = core.load_constellations()
    seg_x, seg_y = [], []
    for strips in cons.values():
        for strip in strips:
            ra = np.array([p[0] for p in strip])
            dec = np.array([p[1] for p in strip])
            c = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            aa = c.transform_to(AltAz(obstime=t_ref, location=location))
            alt, az = aa.alt.deg, aa.az.deg
            xs, ys = core.dome_xy(alt, az)
            # break the polyline wherever it dips below the horizon
            for i in range(len(alt) - 1):
                if alt[i] >= 0 and alt[i + 1] >= 0:
                    seg_x += [xs[i], xs[i + 1], None]
                    seg_y += [ys[i], ys[i + 1], None]
    if seg_x:
        fig.add_trace(go.Scatter(
            x=seg_x, y=seg_y, mode="lines",
            line=dict(color="rgba(125,145,190,0.40)", width=1),
            hoverinfo="skip", showlegend=False, name="constellations",
        ))


# --------------------------------------------------------------------------
# stars
# --------------------------------------------------------------------------

stars = core.load_sky_stars()
vis = stars[stars["mag"] <= mag_limit]

sc = SkyCoord(ra=vis["ra_deg"].values * u.deg, dec=vis["dec"].values * u.deg)
aa = sc.transform_to(AltAz(obstime=t_ref, location=location))
up = aa.alt.deg > 0

s_alt, s_az = aa.alt.deg[up], aa.az.deg[up]
sx, sy = core.dome_xy(s_alt, s_az)
s_mag = vis["mag"].values[up]
s_ci = vis["ci"].values[up]
s_lab = vis["label"].values[up]
s_con = vis["con"].values[up]

size = np.clip(11 * 10 ** (-0.19 * s_mag), 1.6, 14)
colours = core.rgb_strings(s_ci)

hover = [
    f"<b>{lab if isinstance(lab, str) and lab else 'unnamed'}</b>"
    f"{f'  ({cn})' if isinstance(cn, str) else ''}"
    f"<br>V {m:.2f}<br>alt {al:+.1f}\u00b0  az {az_:.0f}\u00b0"
    for lab, cn, m, al, az_ in zip(s_lab, s_con, s_mag, s_alt, s_az)
]

fig.add_trace(go.Scatter(
    x=sx, y=sy, mode="markers",
    marker=dict(size=size, color=colours, line=dict(width=0)),
    text=hover, hoverinfo="text", showlegend=False, name="stars",
))

if label_bright:
    bright = s_mag <= 1.8
    named = np.array([isinstance(l, str) and bool(l) for l in s_lab])
    pick = bright & named
    if pick.any():
        fig.add_trace(go.Scatter(
            x=sx[pick], y=sy[pick], mode="text",
            text=s_lab[pick], textposition="top center",
            textfont=dict(color="rgba(232,227,212,0.65)", size=9),
            hoverinfo="skip", showlegend=False,
        ))


# --------------------------------------------------------------------------
# planets, Moon, targets, standards
# --------------------------------------------------------------------------

if show_planets:
    for p in core.planet_positions(t_ref, location):
        if p["alt"] < 0:
            continue
        px, py = core.dome_xy(p["alt"], p["az"])
        fig.add_trace(go.Scatter(
            x=[float(px)], y=[float(py)], mode="markers+text",
            marker=dict(size=p["size"], color=p["colour"],
                        line=dict(width=1, color="rgba(255,255,255,0.5)")),
            text=[p["name"]], textposition="bottom center",
            textfont=dict(color=p["colour"], size=10),
            hovertext=[f"<b>{p['name']}</b><br>{p['au']:.3f} AU"
                       f"<br>alt {p['alt']:+.1f}\u00b0  az {p['az']:.0f}\u00b0"],
            hoverinfo="text", showlegend=False,
        ))

illum, moon_aa = core.moon_info(t_ref, location)
if moon_aa.alt.deg > 0:
    mx, my = core.dome_xy(moon_aa.alt.deg, moon_aa.az.deg)
    fig.add_trace(go.Scatter(
        x=[float(mx)], y=[float(my)], mode="markers+text",
        marker=dict(size=17, color="#ded7bd",
                    line=dict(width=1, color="#9aa0ac")),
        text=["Moon"], textposition="bottom center",
        textfont=dict(color="#ded7bd", size=10),
        hovertext=[f"<b>Moon</b><br>{illum*100:.0f}% illuminated"
                   f"<br>alt {moon_aa.alt.deg:+.1f}\u00b0  "
                   f"az {moon_aa.az.deg:.0f}\u00b0"],
        hoverinfo="text", showlegend=False,
    ))

if show_standards:
    for s in tg.STANDARDS:
        c = SkyCoord(ra=s["ra_deg"] * u.deg, dec=s["dec_deg"] * u.deg)
        p = core.altaz_of(c, t_ref, location)
        if p.alt.deg <= 0:
            continue
        x, y = core.dome_xy(p.alt.deg, p.az.deg)
        fig.add_trace(go.Scatter(
            x=[float(x)], y=[float(y)], mode="markers",
            marker=dict(size=13, color="rgba(0,0,0,0)",
                        line=dict(width=1.6, color="#8fb4db")),
            hovertext=[f"<b>{s['name']}</b><br>spectral standard "
                       f"{s['spectral_type']}<br>V {s['vmag']:.2f}"
                       f"<br>alt {p.alt.deg:+.1f}\u00b0  az {p.az.deg:.0f}\u00b0"],
            hoverinfo="text", showlegend=False,
        ))

if show_targets:
    for t in tg.EXOPLANETS:
        c = SkyCoord(ra=t["ra_deg"] * u.deg, dec=t["dec_deg"] * u.deg)
        p = core.altaz_of(c, t_ref, location)
        if p.alt.deg <= 0:
            continue
        x, y = core.dome_xy(p.alt.deg, p.az.deg)
        fig.add_trace(go.Scatter(
            x=[float(x)], y=[float(y)], mode="markers+text",
            marker=dict(size=16, color="rgba(0,0,0,0)", symbol="circle",
                        line=dict(width=2, color="#c99a45")),
            text=[t["planet"]], textposition="top center",
            textfont=dict(color="#c99a45", size=9.5),
            hovertext=[f"<b>{t['planet']}</b><br>host {t['host']} "
                       f"({t['spectral_type']})<br>V {t['vmag']:.2f} \u00b7 "
                       f"depth {t['depth_pct']:.2f}%"
                       f"<br>alt {p.alt.deg:+.1f}\u00b0  az {p.az.deg:.0f}\u00b0"],
            hoverinfo="text", showlegend=False,
        ))


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------

hidden_axis = dict(showgrid=False, zeroline=False, showticklabels=False,
                   showline=False, range=[-R * 1.13, R * 1.13])

fig.update_layout(
    height=760,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgb(11,15,28)",
    plot_bgcolor="rgb(13,18,32)",
    xaxis=hidden_axis,
    yaxis=dict(**hidden_axis, scaleanchor="x", scaleratio=1),
    hoverlabel=dict(bgcolor="rgb(23,31,53)", bordercolor="#3a4460",
                    font=dict(color="#e8e3d4", size=12)),
    dragmode="pan",
)

st.plotly_chart(fig, width="stretch",
                config={"scrollZoom": True, "displaylogo": False})

st.caption(
    f"{int(up.sum())} stars above the horizon at magnitude \u2264 {mag_limit:.1f}. "
    f"{core.local_str(t_ref, tz)} local. "
    "Zenith at centre, horizon at the rim. Drag to pan, scroll to zoom, "
    "hover anything to identify it."
)
