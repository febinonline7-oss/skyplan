"""
Shared core for SkyPlan.

Everything that more than one page needs lives here: the observer settings
(persisted across pages via session state), catalogue loading, and the
astronomy helpers. Pages import from this module rather than duplicating it.
"""

import os

import numpy as np
import pandas as pd
import streamlit as st

import astropy.units as u
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time


# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------

LY_PER_PC = 3.261563

DARK_SUN_ALT = -18.0      # astronomical twilight
USABLE_SUN_ALT = -12.0    # nautical twilight; workable for bright targets
MIN_TARGET_ALT = 30.0     # below this, airmass starts to hurt photometry

HYG_URL = (
    "https://raw.githubusercontent.com/astronexus/HYG-Database/"
    "master/hyg/CURRENT/hygdata_v41.csv"
)
HYG_SKY = "hyg_bright.csv"          # naked-eye, for the sky map and lookup
HYG_NEAR = "hyg_neighbourhood.csv"  # nearby, for the 3D atlas

DEFAULTS = {
    "obs_lat": 8.5241,
    "obs_lon": 76.9366,
    "obs_height": 10.0,
    "obs_tz": 5.5,
    "obs_use_now": True,
}


# --------------------------------------------------------------------------
# observer state, shared across pages
# --------------------------------------------------------------------------

def _init_state():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def observer_sidebar(show_time=True):
    """
    Draw the observer controls and return (location, t_ref, tz_offset).

    Values live in session state keyed by name, so moving between pages
    keeps your site and chosen time rather than resetting to defaults.
    """
    _init_state()

    with st.sidebar:
        st.header("Observer")
        st.number_input("Latitude (deg N)", key="obs_lat", format="%.4f")
        st.number_input("Longitude (deg E)", key="obs_lon", format="%.4f")
        st.number_input("Elevation (m)", key="obs_height", step=10.0)
        st.number_input("UTC offset (hours)", key="obs_tz", step=0.5)

        if show_time:
            st.divider()
            st.header("Time")
            st.checkbox("Use current time", key="obs_use_now")
            if st.session_state.obs_use_now:
                t_ref = Time.now()
            else:
                d = st.date_input("Date (UTC)", key="obs_date")
                h = st.slider("Hour (UTC)", 0, 23, 18, key="obs_hour")
                m = st.slider("Minute (UTC)", 0, 59, 0, key="obs_min")
                t_ref = Time(f"{d} {h:02d}:{m:02d}:00", scale="utc")
        else:
            t_ref = Time.now()

    location = EarthLocation(
        lat=st.session_state.obs_lat * u.deg,
        lon=st.session_state.obs_lon * u.deg,
        height=st.session_state.obs_height * u.m,
    )
    return location, t_ref, st.session_state.obs_tz


def local_str(t, tz, fmt="%Y-%m-%d %H:%M"):
    """Format an astropy Time on the observer's local clock."""
    return (t.utc.datetime + pd.Timedelta(hours=tz)).strftime(fmt)


def altaz_of(coord, t, location):
    return coord.transform_to(AltAz(obstime=t, location=location))


def sky_state(sun_alt_deg):
    if sun_alt_deg > 0:
        return "Daylight"
    if sun_alt_deg > -6:
        return "Civil twilight"
    if sun_alt_deg > -12:
        return "Nautical twilight"
    if sun_alt_deg > -18:
        return "Astronomical twilight"
    return "Fully dark"


def moon_info(t, location):
    """Return (illuminated_fraction, AltAz) for the Moon."""
    # Both bodies geocentric: the phase-angle formula assumes a common origin,
    # and mixing a topocentric Moon with a geocentric Sun makes the separation
    # depend on which way the transform runs.
    sun_geo = get_sun(t)
    moon_geo = get_body("moon", t)
    elong = sun_geo.separation(moon_geo)
    phase_angle = np.arctan2(
        sun_geo.distance * np.sin(elong),
        moon_geo.distance - sun_geo.distance * np.cos(elong),
    )
    illum = float((1 + np.cos(phase_angle)) / 2.0)

    moon_topo = get_body("moon", t, location)
    return illum, altaz_of(moon_topo, t, location)


# --------------------------------------------------------------------------
# catalogues
# --------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading star catalogue...")
def load_sky_stars(mag_limit=6.5):
    """
    Naked-eye catalogue for the sky map and lookup. Cached to disk on first
    run, so the app works offline in the field afterwards.
    """
    if os.path.exists(HYG_SKY):
        return pd.read_csv(HYG_SKY)

    cols = ["proper", "bf", "con", "ra", "dec", "dist", "pmra", "pmdec",
            "mag", "absmag", "spect", "ci"]
    df = pd.read_csv(HYG_URL, usecols=cols, low_memory=False)

    # HYG ships the Sun as a row (mag -26.7 parked at RA 0, Dec 0). Drop it,
    # or it renders as a huge artifact on the chart.
    df = df[df["proper"] != "Sol"]

    df = df[df["mag"] <= mag_limit].copy()
    df = df[df["ra"].notna() & df["dec"].notna()]

    # HYG uses 100000 pc as its "no reliable parallax" placeholder.
    df.loc[df["dist"] >= 100000, "dist"] = np.nan

    df["ra_deg"] = df["ra"] * 15.0        # HYG stores RA in hours
    df["label"] = (df["proper"].fillna("").replace("", np.nan)
                   .fillna(df["bf"]).fillna(""))
    df.to_csv(HYG_SKY, index=False)
    return df


@st.cache_data(show_spinner="Loading the neighbourhood...")
def load_neighbourhood(max_pc=50.0):
    """
    Nearby stars with real 3D positions, for the atlas.

    Gliese matters here. Gaia DR3 saturates above roughly G=3, so a
    Gaia-only local map is missing or unreliable for exactly the stars
    people look for first: Sirius, Alpha Centauri, Vega. Gliese is a
    dedicated nearby-star catalogue, so it covers both those and the
    faint red dwarfs that dominate the volume by number.
    """
    if os.path.exists(HYG_NEAR):
        return pd.read_csv(HYG_NEAR)

    cols = ["proper", "bf", "gl", "hip", "con", "ra", "dec", "dist",
            "mag", "absmag", "spect", "ci"]
    df = pd.read_csv(HYG_URL, usecols=cols, low_memory=False)

    df = df[df["proper"] != "Sol"]
    df = df[(df["dist"] > 0) & (df["dist"] <= max_pc)]
    df = df[df["ra"].notna() & df["dec"].notna()].copy()

    # Real Cartesian positions. HYG's own x/y/z columns are equatorial;
    # galactic is the physically meaningful frame for a neighbourhood map,
    # so both are computed here from scratch.
    c = SkyCoord(ra=df["ra"].values * 15 * u.deg,
                 dec=df["dec"].values * u.deg,
                 distance=df["dist"].values * u.pc)

    eq = c.cartesian
    df["x_eq"], df["y_eq"], df["z_eq"] = eq.x.value, eq.y.value, eq.z.value

    gal = c.galactic.cartesian
    df["x_gal"], df["y_gal"], df["z_gal"] = gal.x.value, gal.y.value, gal.z.value

    df["ly"] = df["dist"] * LY_PER_PC
    df["label"] = (
        df["proper"].fillna("").replace("", np.nan)
        .fillna(df["bf"])
        .fillna(df["gl"])
        .fillna("HIP " + df["hip"].astype("Int64").astype(str))
    )
    df["teff"] = bv_to_teff(df["ci"].fillna(0.65).values)

    df.to_csv(HYG_NEAR, index=False)
    return df


# --------------------------------------------------------------------------
# stellar colour: B-V index -> effective temperature -> approximate RGB
# --------------------------------------------------------------------------

def bv_to_teff(bv):
    """
    Ballesteros (2012), EPL 97, 34008. Treats the star as a blackbody seen
    through the B and V bands. Good to a few per cent on the main sequence,
    though it underestimates the hottest stars because B-V saturates there.
    """
    bv = np.clip(bv, -0.4, 2.0)
    return 4600.0 * (1.0 / (0.92 * bv + 1.7) + 1.0 / (0.92 * bv + 0.62))


def teff_to_rgb(t):
    """Planckian locus approximation (Tanner Helland's piecewise fit)."""
    t = np.clip(t, 1000.0, 40000.0) / 100.0

    r = np.where(t <= 66, 255.0,
                 329.698727446 * np.power(np.maximum(t - 60, 1e-9), -0.1332047592))
    g = np.where(
        t <= 66,
        99.4708025861 * np.log(np.maximum(t, 1e-9)) - 161.1195681661,
        288.1221695283 * np.power(np.maximum(t - 60, 1e-9), -0.0755148492),
    )
    b = np.where(
        t >= 66, 255.0,
        np.where(t <= 19, 0.0,
                 138.5177312231 * np.log(np.maximum(t - 10, 1e-9)) - 305.0447927307),
    )
    return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(int)


def rgb_strings(bv):
    """Vectorised B-V to 'rgb(r,g,b)' strings, with a solar fallback."""
    bv = np.asarray(bv, dtype=float)
    filled = np.where(np.isfinite(bv), bv, 0.65)     # 0.65 ~ solar
    arr = teff_to_rgb(bv_to_teff(filled))
    return [f"rgb({r},{g},{b})" for r, g, b in arr]


# --------------------------------------------------------------------------
# transit prediction
# --------------------------------------------------------------------------

def find_transits(target, t_ref, location, horizon_days=21,
                  min_alt=MIN_TARGET_ALT, max_sun=USABLE_SUN_ALT):
    """
    Upcoming transits of one target, with observability assessed at all three
    contact points.

    Published t0 values are normally BJD_TDB, referenced to the solar system
    barycentre. Converting to the observer's clock needs a light-travel
    correction worth up to about 16 minutes, applied here.
    """
    coord = SkyCoord(ra=target["ra_deg"] * u.deg, dec=target["dec_deg"] * u.deg)
    half = (target["duration_hr"] / 2.0) / 24.0

    n0 = int(np.ceil((t_ref.tdb.jd - target["t0_bjd"]) / target["period_d"]))
    n_max = int(np.ceil(horizon_days / target["period_d"])) + 1

    out = []
    for k in range(n_max):
        mid_bjd = target["t0_bjd"] + (n0 + k) * target["period_d"]

        t_bary = Time(mid_bjd, format="jd", scale="tdb", location=location)
        ltt = t_bary.light_travel_time(coord, kind="barycentric")
        mid = (t_bary - ltt).utc

        if (mid.jd - t_ref.jd) > horizon_days:
            break

        ingress = mid - half * u.day
        egress = mid + half * u.day

        checks = Time([ingress.jd, mid.jd, egress.jd], format="jd")
        frame = AltAz(obstime=checks, location=location)
        tgt_alt = coord.transform_to(frame).alt.deg
        sun_alt = get_sun(checks).transform_to(frame).alt.deg

        full = bool((tgt_alt >= min_alt).all() and (sun_alt <= max_sun).all())
        partial = bool((tgt_alt >= min_alt).any() and (sun_alt <= max_sun).any())

        out.append({
            "planet": target["planet"],
            "ingress": ingress, "mid": mid, "egress": egress,
            "tgt_alt": tgt_alt, "sun_alt": sun_alt,
            "full": full, "partial": partial,
            "depth_pct": target["depth_pct"],
        })
    return out


# --------------------------------------------------------------------------
# constellations and planets
# --------------------------------------------------------------------------

CONSTELLATIONS_FILE = os.path.join(os.path.dirname(__file__), "constellations.json")

PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]

PLANET_STYLE = {
    "mercury": ("#b8b0a4", 7),
    "venus":   ("#f0e2c0", 11),
    "mars":    ("#c9603f", 9),
    "jupiter": ("#d9c49a", 13),
    "saturn":  ("#e0cf9e", 12),
    "uranus":  ("#9fd4d9", 8),
    "neptune": ("#7a9fd4", 8),
}


@st.cache_data(show_spinner=False)
def load_constellations():
    """Stick-figure lines for all 88 constellations, as [[ra_deg, dec_deg], ...]."""
    import json
    if not os.path.exists(CONSTELLATIONS_FILE):
        return {}
    with open(CONSTELLATIONS_FILE) as f:
        return json.load(f)


def planet_positions(t, location):
    """Alt/az for the seven naked-eye planets. Returns a list of dicts."""
    out = []
    for name in PLANETS:
        try:
            c = get_body(name, t, location)
            aa = altaz_of(c, t, location)
            colour, size = PLANET_STYLE[name]
            out.append({
                "name": name.capitalize(),
                "alt": float(aa.alt.deg),
                "az": float(aa.az.deg),
                "au": float(c.distance.to(u.au).value),
                "colour": colour,
                "size": size,
            })
        except Exception:
            continue
    return out


def dome_xy(alt, az):
    """
    Project alt/az onto a flat disc: zenith at the centre, horizon at
    radius 90, north at the top.

    East ends up on the LEFT, which is correct and is not a typo. A star
    chart shows the sky dome from the inside, looking up. For a viewer
    looking along +up with north at the top of the image, image-right works
    out to west (right = forward x up = U x N = -E). This is the planisphere
    convention: hold the chart overhead, point its N edge north, and it
    matches the sky. A map, drawn looking down at the ground, puts east on
    the right instead; using that convention here would mirror the sky.
    """
    alt = np.asarray(alt, dtype=float)
    az = np.asarray(az, dtype=float)
    r = 90.0 - alt
    th = np.radians(az)
    return -r * np.sin(th), r * np.cos(th)
