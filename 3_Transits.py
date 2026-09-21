"""Upcoming transits, with observability judged at all three contact points."""

import pandas as pd
import streamlit as st

import skyplan_core as core
import targets as tg

st.set_page_config(page_title="Transits", page_icon="*", layout="wide")

location, t_ref, tz = core.observer_sidebar()

st.title("Transits")

c1, c2 = st.columns([2, 1])
with c1:
    horizon_days = st.slider("Search window (days)", 3, 90, 21)
with c2:
    quality = st.radio("Show", ["Fully observable", "Partial too", "Everything"])

rows = []
for t in tg.EXOPLANETS:
    for w in core.find_transits(t, t_ref, location, horizon_days=horizon_days):
        if quality == "Fully observable" and not w["full"]:
            continue
        if quality == "Partial too" and not (w["full"] or w["partial"]):
            continue
        rows.append({
            "Planet": w["planet"],
            "Ingress (local)": core.local_str(w["ingress"], tz, "%d %b %H:%M"),
            "Mid": core.local_str(w["mid"], tz, "%H:%M"),
            "Egress": core.local_str(w["egress"], tz, "%H:%M"),
            "Alt at mid": f"{w['tgt_alt'][1]:+.0f}\u00b0",
            "Min alt": f"{w['tgt_alt'].min():+.0f}\u00b0",
            "Sun at mid": f"{w['sun_alt'][1]:+.0f}\u00b0",
            "Depth": f"{w['depth_pct']:.2f}%",
            "Quality": "full" if w["full"] else ("partial" if w["partial"] else "no"),
            "_sort": w["mid"].jd,
        })

if rows:
    df = pd.DataFrame(rows).sort_values("_sort").drop(columns="_sort")
    st.dataframe(df, width="stretch", hide_index=True)
    st.success(f"{sum(r['Quality'] == 'full' for r in rows)} fully observable "
               f"of {len(rows)} shown.")
else:
    st.info("Nothing matches in this window. Widen it, or loosen the filter.")

st.caption(
    f"'Full' means the target stays above {core.MIN_TARGET_ALT:.0f}\u00b0 and the "
    f"Sun below {core.USABLE_SUN_ALT:.0f}\u00b0 from ingress through egress \u2014 "
    "you need the whole event, plus out-of-transit baseline either side, for a "
    "usable light curve."
)

with st.expander("Timing method, and why it matters"):
    st.markdown(
        """
Published `t0` values are normally in **BJD_TDB**, a timescale referenced to
the solar system barycentre rather than to Earth. Turning that into a time on
your clock requires correcting for light travel across Earth's orbit, which is
worth up to about **16 minutes** depending on where the target sits relative to
the Sun.

This page applies that correction via `Time.light_travel_time()`. Skipping it
is a common way to arrive at the telescope and find the ingress already over.

Ephemerides also drift as the reference epoch recedes, and WASP-52 b in
particular has documented transit-timing variations from its active host.
Treat these as planning numbers and confirm against the Exoplanet Transit
Database before committing a night.
        """
    )

with st.expander("Ephemerides in use"):
    st.dataframe(
        pd.DataFrame(tg.EXOPLANETS)[
            ["planet", "host", "vmag", "period_d", "t0_bjd",
             "duration_hr", "depth_pct", "source"]
        ],
        width="stretch", hide_index=True,
    )
