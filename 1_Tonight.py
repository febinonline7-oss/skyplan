"""Altitude curves across the night, with twilight shading."""

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

import skyplan_core as core
import targets as tg

st.set_page_config(page_title="Tonight", page_icon="*", layout="wide")

location, t_ref, tz = core.observer_sidebar()

st.title("Tonight")
st.caption("A 24-hour window centred on your chosen time.")


@st.cache_data(show_spinner=False)
def sun_alt_series(jd_grid, lat, lon, height):
    """Sun altitude on a grid of JDs. Cached: this is the slow part."""
    loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=height * u.m)
    times = Time(np.array(jd_grid), format="jd")
    return get_sun(times).transform_to(AltAz(obstime=times, location=loc)).alt.deg


jd_grid = t_ref.jd + np.linspace(-0.5, 0.5, 145)
times = Time(jd_grid, format="jd")
sun_alts = sun_alt_series(
    tuple(jd_grid),
    st.session_state.obs_lat,
    st.session_state.obs_lon,
    st.session_state.obs_height,
)

fig, ax = plt.subplots(figsize=(12, 4.6))

ax.fill_between(jd_grid, -90, 90, where=(sun_alts > 0),
                color="#f5c77e", alpha=0.25, label="Daylight")
ax.fill_between(jd_grid, -90, 90, where=(sun_alts <= 0) & (sun_alts > -18),
                color="#9fb3d1", alpha=0.20, label="Twilight")

peaks = []
for t in tg.EXOPLANETS:
    c = SkyCoord(ra=t["ra_deg"] * u.deg, dec=t["dec_deg"] * u.deg)
    alts = c.transform_to(AltAz(obstime=times, location=location)).alt.deg
    ax.plot(jd_grid, alts, lw=1.8, label=t["planet"])
    peaks.append((t["planet"], alts.max()))

ax.axhline(core.MIN_TARGET_ALT, color="#b06a52", ls="--", lw=1,
           label=f"{core.MIN_TARGET_ALT:.0f}\u00b0 working floor")
ax.axhline(0, color="#555", lw=1)
ax.set_ylim(-20, 90)
ax.set_xlim(jd_grid[0], jd_grid[-1])
ax.set_ylabel("Altitude (deg)")

tick_jds = np.linspace(jd_grid[0], jd_grid[-1], 9)
ax.set_xticks(tick_jds)
ax.set_xticklabels([core.local_str(Time(j, format="jd"), tz, "%H:%M")
                    for j in tick_jds])
ax.set_xlabel(f"Local time (UTC{tz:+g})")
ax.legend(loc="upper right", fontsize=8, ncol=3)
ax.grid(alpha=0.2)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

st.subheader("Peak altitude in this window")
cols = st.columns(len(peaks))
for col, (name, pk) in zip(cols, peaks):
    col.metric(name, f"{pk:+.0f}\u00b0")

dark = (sun_alts <= core.DARK_SUN_ALT).sum() * (24 / 144)
st.caption(
    f"About {dark:.1f} hours below astronomical twilight in this window. "
    "Amber is daylight, blue is twilight."
)
