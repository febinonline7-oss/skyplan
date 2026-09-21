"""Search the catalogue by name or designation."""

import numpy as np
import pandas as pd
import streamlit as st

import astropy.units as u
from astropy.coordinates import SkyCoord

import skyplan_core as core

st.set_page_config(page_title="Star lookup", page_icon="*", layout="wide")

location, t_ref, tz = core.observer_sidebar()

st.title("Star lookup")

stars = core.load_sky_stars()
q = st.text_input("Search by name or designation",
                  placeholder="Vega, Alp Lyr, Bet Ori, ...")

if not q:
    st.caption(f"{len(stars):,} stars in the catalogue, down to magnitude 6.5.")
else:
    ql = q.strip().lower()
    hit = stars[
        stars["proper"].fillna("").str.lower().str.contains(ql, regex=False)
        | stars["bf"].fillna("").str.lower().str.contains(ql, regex=False)
    ].sort_values("mag")

    if hit.empty:
        st.warning("Nothing in the catalogue matches that.")
    else:
        st.caption(f"{len(hit)} match(es); showing the brightest few.")
        for _, s in hit.head(6).iterrows():
            c = SkyCoord(ra=s["ra_deg"] * u.deg, dec=s["dec"] * u.deg)
            p = core.altaz_of(c, t_ref, location)
            label = s["proper"] if isinstance(s["proper"], str) and s["proper"] else s["bf"]

            st.subheader(label)
            a, b, cc, d = st.columns(4)
            a.metric("Magnitude", f"V {s['mag']:.2f}")
            b.metric("Distance",
                     f"{s['dist'] * core.LY_PER_PC:.1f} ly"
                     if pd.notna(s["dist"]) else "\u2014")
            cc.metric("Altitude now", f"{p.alt.deg:+.1f}\u00b0")
            d.metric("Azimuth", f"{p.az.deg:.0f}\u00b0")

            pm = np.hypot(s["pmra"], s["pmdec"]) if pd.notna(s["pmra"]) else np.nan
            bits = [
                f"**{s['spect']}**" if isinstance(s["spect"], str) else "",
                f"in {s['con']}" if isinstance(s["con"], str) else "",
                f"RA {c.ra.to_string(unit=u.hour, sep='hms', precision=1)}",
                f"Dec {c.dec.to_string(unit=u.deg, sep='dms', precision=0)}",
            ]
            if np.isfinite(pm):
                bits.append(f"proper motion {pm:.0f} mas/yr")
            if pd.notna(s["ci"]):
                bits.append(f"~{core.bv_to_teff(np.array([s['ci']]))[0]:.0f} K")

            st.write(" \u00b7 ".join(b for b in bits if b))

            if p.alt.deg < 0:
                st.caption("Below your horizon at the selected time.")
            st.divider()
