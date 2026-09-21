"""3D map of the solar neighbourhood, with interstellar travel times."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import skyplan_core as core

st.set_page_config(page_title="Stellar atlas", page_icon="*", layout="wide")

core.observer_sidebar(show_time=False)

st.title("Stellar atlas")
st.caption(
    "The other pages show the sky as a dome over your head. This one drops "
    "that projection: parallax gives distance, and distance plus sky position "
    "gives a real position in space. Sol sits at the origin."
)

with st.sidebar:
    st.divider()
    st.header("Atlas")
    radius_ly = st.slider("Radius (light years)", 5, 160, 40, 5)
    frame = st.radio("Reference frame", ["Galactic", "Equatorial"], index=0)
    mag_cut = st.slider("Faintest absolute magnitude", 0.0, 20.0, 16.0, 0.5,
                        help="Lower values keep only intrinsically bright stars.")
    named_only = st.checkbox("Named stars only", value=False)
    show_plane = st.checkbox("Show galactic plane", value=True)
    frac_c = st.slider("Travel speed (fraction of c)", 0.01, 0.99, 0.10, 0.01)

radius_pc = radius_ly / core.LY_PER_PC
stars = core.load_neighbourhood()

sel = stars[(stars["dist"] <= radius_pc) & (stars["absmag"] <= mag_cut)].copy()
if named_only:
    sel = sel[sel["proper"].notna()]

if sel.empty:
    st.warning("Nothing left after those cuts. Widen the radius or the "
               "magnitude limit.")
    st.stop()

if frame == "Galactic":
    xs, ys, zs = sel["x_gal"], sel["y_gal"], sel["z_gal"]
    axis_titles = ("toward galactic centre (pc)",
                   "galactic rotation (pc)",
                   "galactic north (pc)")
else:
    xs, ys, zs = sel["x_eq"], sel["y_eq"], sel["z_eq"]
    axis_titles = ("x (pc)", "y (pc)", "z (pc)")

# Brighter intrinsic luminosity draws larger, floored so the red dwarfs that
# dominate the volume by number stay visible.
size = np.clip(14 - 0.7 * sel["absmag"].values, 2.2, 15)

hover = [
    f"<b>{lab}</b><br>{ly:.2f} ly ({d:.2f} pc)"
    f"<br>{sp if isinstance(sp, str) else 'type unknown'}"
    f"<br>V {m:.2f} \u00b7 M<sub>V</sub> {am:.2f}<br>~{t:.0f} K"
    for lab, ly, d, sp, m, am, t in zip(
        sel["label"], sel["ly"], sel["dist"], sel["spect"],
        sel["mag"], sel["absmag"], sel["teff"])
]

fig = go.Figure()

fig.add_trace(go.Scatter3d(
    x=xs, y=ys, z=zs, mode="markers",
    marker=dict(size=size, color=core.rgb_strings(sel["ci"].values),
                opacity=0.92, line=dict(width=0)),
    text=hover, hoverinfo="text", name="stars",
))

fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0], mode="markers+text",
    marker=dict(size=9, color="rgb(255,244,214)",
                line=dict(width=2, color="#c99a45")),
    text=["Sol"], textposition="top center",
    textfont=dict(color="#c99a45", size=12),
    hovertext=["<b>Sol</b><br>G2V \u00b7 5772 K<br>you are here"],
    hoverinfo="text", name="Sol",
))

notable = sel[sel["proper"].notna()].nsmallest(28, "dist")
if len(notable):
    nx, ny, nz = ((notable["x_gal"], notable["y_gal"], notable["z_gal"])
                  if frame == "Galactic"
                  else (notable["x_eq"], notable["y_eq"], notable["z_eq"]))
    fig.add_trace(go.Scatter3d(
        x=nx, y=ny, z=nz, mode="text", text=notable["proper"],
        textposition="top center",
        textfont=dict(color="rgba(232,227,212,0.75)", size=9),
        hoverinfo="skip", showlegend=False,
    ))

if show_plane and frame == "Galactic":
    th = np.linspace(0, 2 * np.pi, 120)
    for rr in np.linspace(radius_pc / 4, radius_pc, 4):
        fig.add_trace(go.Scatter3d(
            x=rr * np.cos(th), y=rr * np.sin(th), z=np.zeros_like(th),
            mode="lines", line=dict(color="rgba(120,140,180,0.22)", width=1),
            hoverinfo="skip", showlegend=False,
        ))

axis_style = dict(backgroundcolor="rgb(11,15,28)",
                  gridcolor="rgba(120,140,180,0.15)",
                  zerolinecolor="rgba(120,140,180,0.3)",
                  showbackground=True, color="#7c8494")

fig.update_layout(
    height=720, margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgb(11,15,28)",
    scene=dict(xaxis=dict(title=axis_titles[0], **axis_style),
               yaxis=dict(title=axis_titles[1], **axis_style),
               zaxis=dict(title=axis_titles[2], **axis_style),
               aspectmode="cube"),
    showlegend=False,
)

st.plotly_chart(fig, width="stretch")

c1, c2, c3 = st.columns(3)
c1.metric("Stars shown", f"{len(sel):,}")
c2.metric("Radius", f"{radius_ly} ly")
c3.metric("Nearest", f"{sel['ly'].min():.2f} ly")

st.subheader("Travel times")
gamma = 1.0 / np.sqrt(1.0 - frac_c ** 2)
st.write(
    f"At **{frac_c:.0%} c**, ignoring acceleration and deceleration. "
    f"Ship-board time is shorter by the Lorentz factor, \u03b3 = {gamma:.3f}."
)

near = sel.nsmallest(18, "dist")[["label", "ly", "dist", "spect", "mag", "absmag"]].copy()
near["Earth years"] = (near["ly"] / frac_c).round(1)
near["Ship years"] = (near["ly"] / frac_c / gamma).round(1)
near["ly"] = near["ly"].round(2)
near["dist"] = near["dist"].round(2)
near = near.rename(columns={"label": "Star", "ly": "Light years",
                            "dist": "Parsecs", "spect": "Type",
                            "mag": "V", "absmag": "M_V"})
st.dataframe(near, width="stretch", hide_index=True)

with st.expander("Why this map is not built from Gaia alone"):
    st.markdown(
        """
Gaia DR3 has about 1.8 billion sources, but it **saturates above roughly
G = 3**. The brightest and most famous nearby stars — Sirius, Alpha Centauri,
Vega — therefore have missing or unreliable Gaia astrometry. A local map built
purely from Gaia is missing exactly the stars you would look for first.

So this uses HYG, which merges Hipparcos (bright stars), the Yale Bright Star
Catalogue, and **Gliese** — a catalogue built specifically for the solar
neighbourhood, covering both those bright stars and the faint red dwarfs that
dominate the volume by number.

Two further cautions if you extend this with your own Gaia queries:

- **Do not invert a low-significance parallax.** Distance from `1/parallax` is
  badly biased at low signal-to-noise. Require `parallax_over_error > 10`, or
  use a proper distance estimator such as Bailer-Jones.
- **Apply the parallax zero point.** Gaia DR3 parallaxes carry an offset of
  roughly \u221217 \u00b5as (Lindegren et al. 2021); the full correction depends on
  magnitude, colour and sky position.
        """
    )
