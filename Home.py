"""
SkyPlan — entry page.

Run the whole app with:    streamlit run Home.py
"""

import numpy as np
import pandas as pd
import streamlit as st

import astropy.units as u
from astropy.coordinates import SkyCoord, get_sun

import skyplan_core as core
import targets as tg

st.set_page_config(page_title="SkyPlan", page_icon="*", layout="wide")

location, t_ref, tz = core.observer_sidebar()

st.title("SkyPlan")
st.caption(
    "Observation planning and stellar cartography, on astropy and Gaia. "
    "Your site and chosen time carry across every page."
)

# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------

sun_now = core.altaz_of(get_sun(t_ref), t_ref, location)
illum, moon_now = core.moon_info(t_ref, location)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Local time", core.local_str(t_ref, tz, "%H:%M"))
c2.metric("Sky", core.sky_state(sun_now.alt.deg), f"Sun {sun_now.alt.deg:+.1f}\u00b0")
c3.metric("Moon", f"{illum*100:.0f}% lit", f"alt {moon_now.alt.deg:+.1f}\u00b0")
c4.metric(
    "LST",
    t_ref.sidereal_time("apparent",
                        longitude=st.session_state.obs_lon * u.deg
                        ).to_string(unit=u.hour, sep=":", precision=0),
)

st.divider()

# --------------------------------------------------------------------------
# targets right now
# --------------------------------------------------------------------------

st.subheader("Your targets right now")

rows = []
for t in tg.EXOPLANETS:
    c = SkyCoord(ra=t["ra_deg"] * u.deg, dec=t["dec_deg"] * u.deg)
    p = core.altaz_of(c, t_ref, location)
    if p.alt.deg >= core.MIN_TARGET_ALT and sun_now.alt.deg <= core.USABLE_SUN_ALT:
        status = "observable now"
    elif p.alt.deg >= core.MIN_TARGET_ALT:
        status = "up, but sky too bright"
    elif p.alt.deg > 0:
        status = "up but low"
    else:
        status = "below horizon"
    rows.append({
        "Target": t["planet"],
        "Host": t["host"],
        "V": f"{t['vmag']:.2f}",
        "Altitude": f"{p.alt.deg:+.1f}\u00b0",
        "Azimuth": f"{p.az.deg:.0f}\u00b0",
        "Status": status,
    })

st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

# --------------------------------------------------------------------------
# next observable transit
# --------------------------------------------------------------------------

st.subheader("Next fully observable transit")

best = None
for t in tg.EXOPLANETS:
    for w in core.find_transits(t, t_ref, location, horizon_days=45):
        if w["full"] and (best is None or w["mid"].jd < best["mid"].jd):
            best = w

if best:
    a, b, c = st.columns(3)
    a.metric("Target", best["planet"])
    b.metric("Date", core.local_str(best["mid"], tz, "%d %b"))
    c.metric("Mid-transit", core.local_str(best["mid"], tz, "%H:%M"))
    st.write(
        f"Ingress {core.local_str(best['ingress'], tz, '%H:%M')} "
        f"\u2192 egress {core.local_str(best['egress'], tz, '%H:%M')} local, "
        f"target between {best['tgt_alt'].min():+.0f}\u00b0 and "
        f"{best['tgt_alt'].max():+.0f}\u00b0, depth {best['depth_pct']:.2f}%."
    )
else:
    st.info("No fully observable transit in the next 45 days. "
            "The Transits page will show partial windows.")

st.divider()

st.markdown(
    """
**Where to go from here**

| Page | What it answers |
|---|---|
| **Tonight** | How high is each target through the night, and when is it dark? |
| **Sky map** | Where do I point, right now? |
| **Transits** | Which transits can I actually catch, and at what local time? |
| **Gaia field** | Which comparison stars should I use for differential photometry? |
| **Star lookup** | What are this star's distance, type, and proper motion? |
| **Stellar atlas** | Where are these stars in real 3D space? |

The first five are about the sky as seen from your site. The atlas is a
different projection entirely: parallax turned into real Cartesian positions,
Sol at the origin.
"""
)
