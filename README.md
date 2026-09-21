# SkyPlan

A planetarium and observation planner in one app, built on astropy and the
ESA Gaia archive.

The first five pages treat the sky as a dome over your head: where to point,
and when. The sixth drops that projection and places stars at their real
positions in space.

---

## Getting it running

**Read this bit first.** The usual advice is to install Python and run
`streamlit run Home.py` on your own machine. That will not work on Windows 7 —
Python 3.9's installer actively blocks installation there, and 3.8 was the last
version that supported it, now long past end-of-life. Streamlit needs 3.9 or
newer.

So don't fight your laptop. Put the code on GitHub and let Streamlit run it in
the cloud. This is free, and your laptop only ever needs a browser.

### Deploying, step by step

1. **Make a GitHub account** at github.com, if you don't already have one.

2. **Make a new repository.** Click the `+` at the top right, then "New
   repository". Name it `skyplan`. Leave it public. Click "Create repository".

3. **Upload these files.** On the new repo's page, click "uploading an existing
   file". Drag in `Home.py`, `skyplan_core.py`, `targets.py`,
   `constellations.json`, `requirements.txt` and `README.md`. Click "Commit
   changes".

4. **Upload the pages folder.** Click "Add file", then "Upload files" again,
   and drag in the whole `pages` folder. GitHub keeps the folder structure.
   Commit again.

5. **Go to share.streamlit.io** and sign in with your GitHub account.

6. **Click "Create app"**, then choose to deploy from GitHub. Pick your
   `skyplan` repository, set the main file path to `Home.py`, and click
   "Deploy".

Give it a few minutes on the first run while it installs everything. After
that you get a permanent link you can open from any browser, including your
phone at the telescope.

To change something later, edit the file on GitHub and the app updates by
itself.

### If you get access to a machine with Python 3.9 or newer

```bash
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows
pip install -r requirements.txt
streamlit run Home.py
```

---

## Layout

```
skyplan/
├── Home.py                  entry point
├── skyplan_core.py          shared observer state, catalogues, astronomy
├── targets.py               your target list — edit this one
├── constellations.json      88 constellation figures
├── requirements.txt
└── pages/
    ├── 1_Tonight.py         altitude curves with twilight shading
    ├── 2_Sky_Map.py         interactive planetarium view
    ├── 3_Transits.py        transit predictions
    ├── 4_Gaia_Field.py      live Gaia comparison-star search
    ├── 5_Star_Lookup.py     catalogue search
    └── 6_Stellar_Atlas.py   3D neighbourhood map
```

Streamlit turns anything in `pages/` into navigation automatically, and the
number prefixes set the order. Keep the structure as it is.

**Why pages and not tabs.** Streamlit reruns the whole script on every
interaction, and tabs render whether or not you are looking at them. With the
3D atlas as a tab, nudging a slider on the Transits page would rebuild a plot
of several thousand points every time. Only the active page runs in a multipage
app.

Your site and chosen time live in `st.session_state`, so they follow you from
page to page instead of resetting.

---

## How close is this to Stellarium?

Fairly close for planning, not close at all for free-look navigation. The
honest breakdown:

| Stellarium feature | Here |
|---|---|
| Stars in true colour | yes, from each star's measured B−V index |
| Constellation figures | yes, all 88 |
| Planets and Moon | yes, from astropy's solar system ephemeris |
| Identify any object | yes, hover it |
| Pan and zoom | yes, drag and scroll |
| Smooth 60fps free-look | no |
| Constellation artwork | no |
| Deep sky objects | no |
| Horizon panorama | no |
| Telescope control | no |

The missing row that matters is the smooth free-look. Streamlit reruns a Python
script for each interaction, which is fine for a chart but is not a game loop.
Real-time navigation needs WebGL running in the browser — which is exactly what
Stellarium Web is built on. That is a different project in a different
language, not an extension of this one.

What this does instead, and Stellarium does not, is the planning: transit
predictions with proper barycentric timing, Gaia comparison-star selection, and
the 3D neighbourhood map.

---

## The pages

**Tonight** — altitude for every target across 24 hours. Amber is daylight,
blue is twilight, and the dashed line is the 30° working floor below which
airmass starts to hurt your photometry.

**Sky map** — the planetarium view. Zenith at centre, horizon at the rim, north
at top. Drag to pan, scroll to zoom, hover anything to identify it.

East is on the **left**, which is correct rather than a mistake. A star chart
shows the dome from the inside, looking up, so it mirrors a ground map. Hold it
overhead with the N edge pointing north and it matches the sky, the same way a
planisphere does.

**Transits** — upcoming transits in local time. The default filter shows only
fully observable events: target above 30° and Sun below −12° for the *entire*
transit, which is what a usable light curve needs.

**Gaia field** — live cone search for comparison stars, filtered on brightness
and colour so differential extinction cancels. Exports CSV for your
ccdproc/photutils pipeline.

**Star lookup** — search by proper name or Bayer/Flamsteed designation.

**Stellar atlas** — the 3D neighbourhood. Rotate, zoom, hover, with
relativistic travel times at a chosen fraction of *c*.

---

## Changing things

**Your site** — the sidebar on any page. Defaults to Thiruvananthapuram.

**Adding a target** — open `targets.py` and copy one of the blocks in
`EXOPLANETS`. You need RA/Dec in degrees, period, a reference mid-transit
epoch, duration and depth, from the NASA Exoplanet Archive or ETD.

**Thresholds** — `MIN_TARGET_ALT` and `USABLE_SUN_ALT` at the top of
`skyplan_core.py`. Raise the altitude floor if you have trees or buildings on
your horizon.

---

## Two things worth knowing

**Transit timing.** Published `t0` values are normally BJD_TDB, referenced to
the solar system barycentre. Converting to your clock needs a light-travel
correction worth up to about 16 minutes; for WASP-52 b it currently runs to
about 9 minutes, enough to miss an ingress if ignored. The app applies it via
`Time.light_travel_time()`. Ephemerides also drift, and WASP-52 b has
documented transit-timing variations from its active host, so confirm against
ETD before committing a night.

**Why the atlas is not pure Gaia.** Gaia DR3 saturates above roughly G = 3, so
Sirius, Alpha Centauri and Vega have missing or unreliable Gaia astrometry — a
Gaia-only local map omits exactly the stars you would look for first. HYG
merges Hipparcos, the Yale Bright Star Catalogue, and Gliese, the last built
specifically for the solar neighbourhood. If you extend this with your own Gaia
queries, require `parallax_over_error > 10` rather than inverting noisy
parallaxes, and apply the Lindegren et al. (2021) zero-point offset.

---

## Sources

- **Star catalogues** — [HYG Database](https://github.com/astronexus/HYG-Database)
  v41 (Hipparcos + Yale Bright Star + Gliese), CC BY-SA 4.0.
- **Constellation figures** — [d3-celestial](https://github.com/ofrohn/d3-celestial),
  BSD 3-Clause.
- **Gaia** — ESA Gaia DR3 via `astroquery.gaia`, queried live.
- **Ephemerides** — per-target literature values, cited in `targets.py`.
- **Colour** — B−V to temperature via Ballesteros (2012); temperature to RGB
  via the Planckian locus.
- **All coordinate transforms, planets and solar system positions** — astropy.
