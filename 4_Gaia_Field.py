"""Live Gaia cone search, aimed at comparison-star selection."""

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

import astropy.units as u
from astropy.coordinates import SkyCoord

import skyplan_core as core
import targets as tg

st.set_page_config(page_title="Gaia field", page_icon="*", layout="wide")

core.observer_sidebar(show_time=False)

st.title("Gaia field")
st.write(
    "Live cone search against the ESA Gaia archive. The point here is "
    "comparison-star selection: for differential photometry you want stars "
    "close to the target in both brightness and colour, so that differential "
    "extinction and colour terms largely cancel in the ratio."
)

names = [t["planet"] for t in tg.EXOPLANETS]
c1, c2, c3 = st.columns(3)
with c1:
    pick = st.selectbox("Centre on", names)
with c2:
    radius_arcmin = st.slider("Radius (arcmin)", 2, 30, 12)
with c3:
    dmag = st.slider("Magnitude window (\u00b1)", 0.5, 4.0, 1.5, 0.5)

target = next(t for t in tg.EXOPLANETS if t["planet"] == pick)

if st.button("Query Gaia archive"):
    with st.spinner("Querying ESA Gaia archive..."):
        try:
            from astroquery.gaia import Gaia

            Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
            Gaia.ROW_LIMIT = 2000

            c = SkyCoord(ra=target["ra_deg"] * u.deg,
                         dec=target["dec_deg"] * u.deg)
            res = (Gaia.cone_search_async(c, radius=radius_arcmin * u.arcmin)
                   .get_results().to_pandas())
            res = res[res["phot_g_mean_mag"].notna()]

            lo, hi = target["vmag"] - dmag, target["vmag"] + dmag
            comps = res[(res["phot_g_mean_mag"] >= lo)
                        & (res["phot_g_mean_mag"] <= hi)].copy()

            st.success(f"{len(res)} sources in the field; "
                       f"{len(comps)} inside the magnitude window.")

            if len(comps):
                comps["sep_arcmin"] = comps["dist"] * 60.0
                show = comps[["source_id", "ra", "dec", "phot_g_mean_mag",
                              "bp_rp", "parallax", "sep_arcmin"]] \
                    .sort_values("sep_arcmin")
                show.columns = ["Gaia source_id", "RA", "Dec", "G", "BP-RP",
                                "Parallax (mas)", "Sep (')"]
                st.dataframe(show.head(40), width="stretch", hide_index=True)
                st.download_button(
                    "Download as CSV",
                    show.to_csv(index=False).encode(),
                    f"{pick.replace(' ', '_')}_comparison_stars.csv",
                    "text/csv",
                )

            fig, ax = plt.subplots(figsize=(6.6, 6.6))
            cosd = np.cos(np.radians(target["dec_deg"]))
            dra = (res["ra"] - target["ra_deg"]) * cosd * 60
            ddec = (res["dec"] - target["dec_deg"]) * 60
            sz = np.clip(200 * 10 ** (-0.3 * (res["phot_g_mean_mag"] - 10)), 1, 250)
            ax.scatter(dra, ddec, s=sz, c="#444", alpha=0.6, edgecolors="none")

            if len(comps):
                ax.scatter((comps["ra"] - target["ra_deg"]) * cosd * 60,
                           (comps["dec"] - target["dec_deg"]) * 60,
                           s=60, facecolors="none", edgecolors="#2a7fb8",
                           linewidths=1.2, label="comparison candidates")

            ax.scatter([0], [0], s=150, facecolors="none",
                       edgecolors="#c99a45", linewidths=2, label=pick)
            ax.invert_xaxis()          # east to the left, as at the eyepiece
            ax.set_xlabel("\u0394RA (arcmin, E left)")
            ax.set_ylabel("\u0394Dec (arcmin)")
            ax.set_aspect("equal")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.2)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        except Exception as e:
            st.error(f"Gaia query failed: {e}")
            st.info("The archive goes down for maintenance periodically, and "
                    "some networks block it. Nothing else in the app depends "
                    "on this page.")

with st.expander("Choosing comparison stars well"):
    st.markdown(
        """
- **Brightness** close to the target, so both sit in the same linear part of
  your detector's response and neither saturates.
- **Colour** close to the target (`BP-RP`), because the atmosphere dims blue
  light more than red. A red comparison against a blue target leaves a
  colour-dependent trend that looks like a shallow transit.
- **Several** comparisons, not one. Averaging beats any single star, and it
  lets you catch a comparison that is itself variable.
- **Check parallax and proper motion** before trusting a star: a high-proper-motion
  nearby dwarf is more likely to be flare-active than a distant giant.
        """
    )
