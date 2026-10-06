"""
toy_data.py  —  The numbers you are meant to play with.
===========================================================================

THIS IS THE ONLY FILE YOU NEED TO EDIT.

Everything here is made-up ("toy") data: a small, invented set of wood-chip
producers scattered across northern Italy, plus the economic and environmental
numbers the model uses. None of it is real company data. Change anything you
like and run the model again to see what happens.

HOW TO USE IT
-------------
1. Open this file.
2. Change numbers (see the three blocks below).
3. Save, then run:   python run.py
4. Look in the `results` folder for the tables and figures.

THE TWO MOST INTERESTING KNOBS (start here)
-------------------------------------------
* TRANSPORT_COST  — how expensive it is to move chips. Cheap transport pushes
                    the model to build ONE big central plant; expensive
                    transport pushes it to build MANY small local plants.
* THEORETICAL["y_max"] — the largest plant the model is allowed to build. Lower
                    it and the model is forced to spread production out.

Try changing those two first: they move the result the most.
"""

# ---------------------------------------------------------------------------
# BLOCK 1 — THE PRODUCERS (the map of who supplies chips, and how much)
# ---------------------------------------------------------------------------
# IMPORTANT — WHERE THESE NUMBERS COME FROM, AND WHY THEY ARE SAFE TO SHARE:
# These are the 22 REAL wood-chip producers of the thesis, so the map keeps the
# SAME geography and the SAME mix of large and small suppliers. BUT the data has
# been deliberately PERTURBED to protect the producers' privacy: the company
# names are replaced by letters (A..V), each location is shifted by up to ~25
# random kilometres, and the biomass and prices are nudged by a few percent and
# rounded (the shift is also large enough to keep the map readable).
# The perturbation uses a fixed recipe, so it is reproducible, and it is small
# enough that the model behaves like the real one — but no real producer can be
# identified from these numbers. In short: real shape, anonymised and blurred.
#
# Each line is one producer. The fields are:
#   "node"       a short anonymous label (A, B, C, ...).
#   "lat","lon"  where it is on the map (latitude and longitude in degrees).
#   "S"          how much DRY biomass it offers per year, in tonnes.
#   "prezzo_acq" the price you pay for its chips, in euros per dry tonne.
# You may add, remove or change lines freely; the model adapts to any number.
NODES = [
    {"node": "A", "lat": 45.055, "lon": 10.466, "S": 15700, "prezzo_acq": 81},
    {"node": "B", "lat": 46.014, "lon": 8.673,  "S": 2490,  "prezzo_acq": 122},
    {"node": "C", "lat": 46.038, "lon": 11.349, "S": 2480,  "prezzo_acq": 131},
    {"node": "D", "lat": 44.197, "lon": 7.560,  "S": 2040,  "prezzo_acq": 78},
    {"node": "E", "lat": 44.494, "lon": 9.927,  "S": 688,   "prezzo_acq": 303},
    {"node": "F", "lat": 44.852, "lon": 9.716,  "S": 1530,  "prezzo_acq": 134},
    {"node": "G", "lat": 42.353, "lon": 11.474, "S": 4030,  "prezzo_acq": 127},
    {"node": "H", "lat": 43.325, "lon": 12.094, "S": 1500,  "prezzo_acq": 195},
    {"node": "I", "lat": 41.648, "lon": 13.772, "S": 302,   "prezzo_acq": 156},
    {"node": "J", "lat": 46.059, "lon": 10.209, "S": 94.8,  "prezzo_acq": 150},
    {"node": "K", "lat": 46.190, "lon": 11.002, "S": 12000, "prezzo_acq": 112},
    {"node": "L", "lat": 41.636, "lon": 12.335, "S": 2100,  "prezzo_acq": 107},
    {"node": "M", "lat": 46.223, "lon": 13.184, "S": 463,   "prezzo_acq": 189},
    {"node": "N", "lat": 45.900, "lon": 8.618,  "S": 437,   "prezzo_acq": 129},
    {"node": "O", "lat": 46.210, "lon": 11.286, "S": 45200, "prezzo_acq": 84},
    {"node": "P", "lat": 45.887, "lon": 12.170, "S": 24900, "prezzo_acq": 144},
    {"node": "Q", "lat": 44.322, "lon": 10.887, "S": 3190,  "prezzo_acq": 74},
    {"node": "R", "lat": 44.582, "lon": 7.794,  "S": 6590,  "prezzo_acq": 131},
    {"node": "S", "lat": 46.057, "lon": 9.553,  "S": 8890,  "prezzo_acq": 95},
    {"node": "T", "lat": 46.465, "lon": 11.853, "S": 7580,  "prezzo_acq": 165},
    {"node": "U", "lat": 42.530, "lon": 13.182, "S": 6430,  "prezzo_acq": 71},
    {"node": "V", "lat": 44.028, "lon": 7.704,  "S": 190,   "prezzo_acq": 91},
]

# ---------------------------------------------------------------------------
# BLOCK 2 — THE TWO KNOBS TO SWEEP (the ones the README tells you to vary)
# ---------------------------------------------------------------------------
# The base price of moving one tonne of chips one kilometre (euros).
TRANSPORT_COST = 0.077
# A few transport prices the model will try in turn, to show the effect.
TRANSPORT_SWEEP = [0.077, 0.300, 1.000]
# A few "largest allowed plant" sizes (tonnes/hour) the model will try in turn.
# With this biomass a single plant would want about 19 t/h, so these caps BITE:
# 30 lets one big plant through, 16 and 8 force the model to open several smaller
# plants, which is exactly the effect worth seeing.
YMAX_SWEEP = [8.0, 16.0, 30.0]

# ---------------------------------------------------------------------------
# BLOCK 3 — THE ECONOMIC AND ENVIRONMENTAL NUMBERS
# ---------------------------------------------------------------------------
# These set the income, the costs and the carbon accounting. You can leave them
# as they are for a first run; each one has a short note saying what it does.
PARAMS = dict(
    # --- how much of each product comes out of one tonne of dry chips ---
    biochar_yield=0.20,       # tonnes of biochar per tonne of chips.
    byproduct_yield=0.40,     # tonnes of by-products (ignored while their price is 0).
    energy_yield=0.27,        # share of the chips that leaves as syngas (for power).
    residue_yield=0.03,       # share that becomes ash and must be disposed of.
    # --- selling prices (the income side) ---
    biochar_price=100.0,      # euros per tonne of biochar (the key price; swept elsewhere).
    energy_price=125.0,       # euros per MWh of electricity sold.
    byproduct_price=0.0,      # euros per tonne of by-product (kept at 0, a cautious choice).
    residue_price=-30.0,      # euros per tonne of ash: NEGATIVE because you PAY to dispose of it.
    # --- turning syngas into sellable electricity ---
    syngas_lhv=3.5,           # energy content of the syngas, MWh per tonne.
    elec_efficiency=0.35,     # how much of that energy becomes electricity.
    sellable_fraction=0.83,   # the share of power actually sold (the rest runs the plant).
    # --- carbon accounting (sets the CO2 removed, the credit's denominator) ---
    carbon_fraction=0.80,     # how much of the biochar is carbon.
    stable_fraction=0.80,     # how much of that carbon stays locked for 100 years.
    transport_emission=1.008e-4,  # tonnes of CO2 per tonne-kilometre of hauling.
    process_emission=0.0,     # CO2 from making the biochar (kept at 0 here).
    grid_emission=0.0,        # CO2 from any grid power used (kept at 0 here).
    capex_emission=0.0,       # CO2 embodied in building the plant (kept at 0 here).
    use_emission=0.0,         # CO2 from using the biochar (kept at 0 here).
    use_distance_km=0.0,      # distance the biochar travels to its use (kept at 0 here).
    # --- finance and availability (to spread the building cost over the years) ---
    rate=0.06,                # yearly interest rate used to annualise the investment.
    life_years=20,            # how many years a plant is assumed to last.
    hours_per_year=0.90 * 8760,  # operating hours per year (90% of all the hours in a year).
)

# ---------------------------------------------------------------------------
# BLOCK 4 — THE TWO PLANT TYPES (usually left as they are)
# ---------------------------------------------------------------------------
# The THEORETICAL plant: one big plant with economies of scale (bigger is cheaper
# per unit). This is the scenario where "y_max" matters.
THEORETICAL = dict(
    capex_ref=26.6e6,   # the building cost of a reference-size plant (euros).
    y_ref=5.0,          # that reference size, in tonnes of chips per hour.
    R=0.6,              # the scale exponent: 0.6 is the engineers' rule of thumb.
    opex_frac=0.02,     # yearly running cost, as a fraction of the building cost.
    y_min=0.5,          # the smallest plant size considered (tonnes/hour).
    y_max=30.0,         # the LARGEST plant allowed (tonnes/hour) — an interesting knob.
    n_seg=10,           # how finely the cost curve is approximated. 10 is fast and
                        # gives the same answer as 15 here; raise it for extra smoothness.
)
# The REALISTIC plant: many identical small modules, no economies of scale.
REALISTIC = dict(
    capex_mod=1.6e6,        # the building cost of one module (euros).
    cap_mod_t_year=401.5,   # how much dry biomass one module processes per year (tonnes).
    opex_frac=0.028,        # yearly running cost of a module, as a fraction of its cost.
    n_max_mod=120,          # a generous cap on modules per site (never really reached).
)
