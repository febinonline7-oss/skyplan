"""
Target catalog.

Everything here is a literature value, not a guess. To add a target, copy a
block and fill it in from the NASA Exoplanet Archive or the Exoplanet Transit
Database. Keep t0 in BJD_TDB where you can; the app applies the barycentric
light-travel correction, which is worth up to ~16 minutes either way.
"""

# Transiting exoplanets.
#   ra_deg, dec_deg : J2000 / ICRS, degrees
#   period_d        : orbital period, days
#   t0_bjd          : reference mid-transit
#   duration_hr     : first-to-fourth contact
#   depth_pct       : transit depth, percent
EXOPLANETS = [
    {
        "planet": "WASP-52 b",
        "host": "WASP-52",
        "spectral_type": "K2V",
        "vmag": 12.0,
        "ra_deg": (23 + 13 / 60 + 58.7576 / 3600) * 15,
        "dec_deg": 8 + 45 / 60 + 40.572 / 3600,
        "period_d": 1.7497835,
        "t0_bjd": 2456862.79776,
        "duration_hr": 1.81,
        "depth_pct": 2.71,
        "source": "Hebrard+ 2013",
        "note": (
            "Inflated hot Jupiter around an active K dwarf. Starspot crossings "
            "and known TTVs mean contact times can drift a few minutes."
        ),
    },
    {
        "planet": "HAT-P-32 b",
        "host": "HAT-P-32",
        "spectral_type": "F/G dwarf",
        "vmag": 11.289,
        "ra_deg": 31.04282310740376,
        "dec_deg": 46.68783621743084,
        "period_d": 2.15000815,
        "t0_bjd": 2458881.71392,
        "duration_hr": 2.9,
        "depth_pct": 1.9,
        "source": "TESS-era ephemeris; duration approximate",
        "note": "Confirm exact ingress/egress on ETD before scheduling.",
    },
    {
        "planet": "HD 189733 b",
        "host": "HD 189733",
        "spectral_type": "K1.5V",
        "vmag": 7.68,
        "ra_deg": (20 + 0 / 60 + 43.71294 / 3600) * 15,
        "dec_deg": 22 + 42 / 60 + 39.0732 / 3600,
        "period_d": 2.21857567,
        "t0_bjd": 2454279.436714,
        "duration_hr": 1.8,
        "depth_pct": 2.4,
        "source": "Agol+ 2010 (Spitzer, 14 transits)",
        "note": (
            "Bright enough for a small scope and one of the best-studied hot "
            "Jupiters. Host is a BY Dra variable, so expect spot activity."
        ),
    },
    {
        "planet": "HD 209458 b",
        "host": "HD 209458",
        "spectral_type": "G0V",
        "vmag": 7.65,
        "ra_deg": (22 + 3 / 60 + 10.77275 / 3600) * 15,
        "dec_deg": 18 + 53 / 60 + 3.5494 / 3600,
        "period_d": 3.52474859,
        "t0_bjd": 2452826.628521,
        "duration_hr": 3.0,
        "depth_pct": 1.7,
        "source": "Knutson+ 2007; t0 originally HJD",
        "note": (
            "The first transiting exoplanet confirmed. t0 is referenced to HJD "
            "rather than BJD_TDB, so treat timing as good to minutes, not seconds."
        ),
    },
]


# Spectral standards spanning A0 through M, for the spectroscopy pipeline.
STANDARDS = [
    {"name": "Vega",       "spectral_type": "A0V",     "vmag": 0.03,
     "ra_deg": (18 + 36 / 60 + 56.3 / 3600) * 15,  "dec_deg": 38 + 47 / 60 + 1 / 3600},
    {"name": "Sirius",     "spectral_type": "A1V",     "vmag": -1.46,
     "ra_deg": (6 + 45 / 60 + 8.9 / 3600) * 15,    "dec_deg": -(16 + 42 / 60 + 58 / 3600)},
    {"name": "Procyon",    "spectral_type": "F5IV-V",  "vmag": 0.34,
     "ra_deg": (7 + 39 / 60 + 18.1 / 3600) * 15,   "dec_deg": 5 + 13 / 60 + 30 / 3600},
    {"name": "Capella",    "spectral_type": "G0III",   "vmag": 0.08,
     "ra_deg": (5 + 16 / 60 + 41.4 / 3600) * 15,   "dec_deg": 45 + 59 / 60 + 53 / 3600},
    {"name": "Arcturus",   "spectral_type": "K1.5III", "vmag": -0.05,
     "ra_deg": (14 + 15 / 60 + 39.7 / 3600) * 15,  "dec_deg": 19 + 10 / 60 + 56 / 3600},
    {"name": "Aldebaran",  "spectral_type": "K5III",   "vmag": 0.87,
     "ra_deg": (4 + 35 / 60 + 55.2 / 3600) * 15,   "dec_deg": 16 + 30 / 60 + 33 / 3600},
    {"name": "Betelgeuse", "spectral_type": "M1-2Ia",  "vmag": 0.50,
     "ra_deg": (5 + 55 / 60 + 10.3 / 3600) * 15,   "dec_deg": 7 + 24 / 60 + 25 / 3600},
]
