"""
analyses.py  —  The experiments we run on the model, and the pictures they make.
===========================================================================

The engine (engine.py) knows how to solve the model once. This file runs it
MANY times to answer the interesting questions:

  * how does the best layout change as transport gets more expensive?
  * how does it change as we cap the largest allowed plant (y_max)?
  * which single number is the credit most sensitive to? (the "tornado")
  * how do the individual plants rank by cost? (the "merit" curve)
  * does optimising actually beat naive plans?

Each function returns its numbers AND draws a figure into the results folder.
You do not need to edit this file to use the model; it is driven by run.py.

The figures use the thesis's own look: a warm cream background, greens and
ochres, clean axes and anonymous node labels.
"""

# `os` lets us join folder and file names in a way that works on any system.
import os
# `glob` finds font files on disk so we can load a nicer typeface if it is there.
import glob
# pandas gives us the little tables we build the node list and the result tables with.
import pandas as pd
# numpy is used for averages and number arrays.
import numpy as np
# matplotlib draws the figures; we import it in "Agg" mode so it writes PNG files
# without needing a screen (important when running on a server or in the cloud).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# We reuse everything the engine already knows how to do.
from engine import (ConcaveScalePWL, LinearModulesScale, solve_stage_A, stage_B,
                    config_centralized, config_decentralized, config_random)

# -- the thesis colour palette (warm, earthy tones that read as "biochar") -----
CREAM = "#FBF8F1"   # the background of every figure.
GREEN = "#33552B"   # the main colour (the optimum, the "good" option).
OCHRE = "#C68A2E"   # the second colour (contrast, the "worse" option).
INK = "#1C1B18"     # near-black, for text, axes and baselines.
GRID = "#E6DFCF"    # a soft sand colour for the gridlines.
GREY = "#9A948A"    # muted grey for closed nodes and secondary marks.

# Pick a clean typeface IF the machine actually has one, otherwise fall back
# silently to a font that always exists. This avoids the "font not found"
# warnings: we only ever ask for a font that is really installed.
# First, try to register Carlito (common on Linux) or Calibri (on Windows).
for _fp in (glob.glob("/usr/share/fonts/**/Carlito*.ttf", recursive=True)
            + glob.glob("C:/Windows/Fonts/calibri*.ttf")
            + glob.glob("C:/Windows/Fonts/Calibri*.ttf")):
    try:
        font_manager.fontManager.addfont(_fp)
    except Exception:
        pass
# Now look at which font names are actually available on this machine.
_available = {f.name for f in font_manager.fontManager.ttflist}
# Choose the first nice font that is really there; DejaVu Sans always is.
_family = next((name for name in ("Carlito", "Calibri", "DejaVu Sans")
                if name in _available), "DejaVu Sans")

# Set the overall look of every figure once, here, so they all match.
plt.rcParams.update({
    "font.family": _family,     # the typeface chosen just above.
    "font.size": 10,            # a comfortable base text size.
    "figure.facecolor": CREAM,  # the cream background behind the whole figure.
    "axes.facecolor": CREAM,    # the same cream inside the plotting area.
    "axes.edgecolor": INK,      # dark axis lines.
    "axes.labelcolor": INK,     # dark axis labels.
    "axes.titlecolor": INK,     # dark titles.
    "axes.titlesize": 11,       # slightly larger titles.
    "xtick.color": INK,         # dark tick labels on the x-axis.
    "ytick.color": INK,         # dark tick labels on the y-axis.
    "axes.grid": True,          # show a light grid by default.
    "grid.color": GRID,         # the soft sand grid colour.
    "grid.linewidth": 0.8,      # thin gridlines.
    "savefig.facecolor": CREAM, # keep the cream background when saving to PNG.
})


# ---------------------------------------------------------------------------
# Small helpers shared by several experiments
# ---------------------------------------------------------------------------
def nodes_dataframe(node_list):
    """Turn the plain list of producer dictionaries (from toy_data.py) into the
    little table the engine expects."""
    # pandas reads a list of dictionaries straight into a table, one row each.
    return pd.DataFrame(node_list)


def make_theoretical(cfg, y_max=None):
    """Build a THEORETICAL plant block from the settings dictionary, optionally
    overriding the largest allowed plant size `y_max`."""
    # Copy the settings so we do not accidentally change the original.
    c = dict(cfg)
    # If the caller asked for a specific y_max, use it instead of the stored one.
    if y_max is not None:
        c["y_max"] = y_max
    # Create the scale block with those settings.
    return ConcaveScalePWL(name="theoretical", **c)


def make_realistic(cfg):
    """Build a REALISTIC (modular) plant block from its settings dictionary."""
    # Create the scale block straight from the settings.
    return LinearModulesScale(name="realistic", **cfg)


def _ensure(folder):
    """Make sure a folder exists before we write files into it."""
    # Create the folder (and any parent folders); do nothing if it is already there.
    os.makedirs(folder, exist_ok=True)
    # Hand the folder path back so the caller can build file names on it.
    return folder


def _clean(ax):
    """Tidy an axis the way the thesis figures do: drop the top and right borders
    and push the grid behind the data."""
    # Remove the top border line of the plotting box.
    ax.spines["top"].set_visible(False)
    # Remove the right border line of the plotting box.
    ax.spines["right"].set_visible(False)
    # Draw the grid underneath the plotted marks, not on top of them.
    ax.set_axisbelow(True)
    # Return the axis so the caller can keep using it.
    return ax


# ---------------------------------------------------------------------------
# Figure: a siting map (where the plants are, and which chips flow where)
# ---------------------------------------------------------------------------
def draw_siting_map(sol, nodes, title, path):
    """Draw the producers on a map, mark which sites host a plant, and draw an
    arrow for every flow of chips from a producer to its plant."""
    # Start a new figure of a comfortable size.
    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    # A quick lookup from node name to its (longitude, latitude) position.
    pos = {r["node"]: (r["lon"], r["lat"]) for _, r in nodes.iterrows()}
    # The biggest biomass value, used to scale the marker sizes sensibly.
    Smax = max(nodes["S"])
    # Draw every flow first (so the node markers sit on top of the lines).
    for (i, j), frac in sol.z.items():
        # Skip tiny or self flows (a producer feeding its own on-site plant needs no arrow).
        if frac <= 0.01 or i == j:
            continue
        # The start point (producer) and end point (plant).
        x0, y0 = pos[i]
        x1, y1 = pos[j]
        # Draw a soft ochre line from producer to plant, slightly see-through.
        ax.plot([x0, x1], [y0, y1], color=OCHRE, lw=1.1, alpha=0.7, zorder=1)
    # Now draw the nodes themselves.
    for _, r in nodes.iterrows():
        # Whether this node hosts an open plant.
        is_plant = sol.x[r["node"]] > 0.5
        # A marker size that grows with the node's biomass (so big suppliers stand out).
        size = 50 + 240 * (r["S"] / Smax)
        if is_plant:
            # Open plants: a solid green square with a dark edge.
            ax.scatter(r["lon"], r["lat"], s=size, marker="s",
                       color=GREEN, edgecolor=INK, linewidth=0.8, zorder=3)
        else:
            # Served (closed) nodes: a hollow circle with a grey edge.
            ax.scatter(r["lon"], r["lat"], s=size, marker="o",
                       facecolor="white", edgecolor=GREY, linewidth=1.0, zorder=3)
        # Write the node's anonymous label just above-right of the marker.
        ax.annotate(r["node"], (r["lon"], r["lat"]),
                    textcoords="offset points", xytext=(5, 4), fontsize=8, color=INK)
    # Label the axes with what they are.
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    # Put the given title on top.
    ax.set_title(title, fontsize=10.5)
    # Tidy the borders and grid.
    _clean(ax)
    # A small legend explaining the two marker types.
    ax.scatter([], [], marker="s", color=GREEN, edgecolor=INK, label="open plant")
    ax.scatter([], [], marker="o", facecolor="white", edgecolor=GREY, label="served node (closed)")
    ax.legend(loc="lower right", fontsize=8, frameon=True, facecolor=CREAM, edgecolor=GRID)
    # A caption at the very bottom, making the anonymisation explicit.
    fig.text(0.5, 0.005,
             "Real Italian geography, anonymised (A..V) and privacy-perturbed; "
             "marker area ~ node biomass. Flows: chips routed producer -> plant.",
             ha="center", va="bottom", fontsize=7, color=GREY)
    # Leave a little room at the bottom for that caption, then save and close.
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 1: the best layout as transport gets more expensive
# ---------------------------------------------------------------------------
def optimal_by_transport(nodes, p, scale_maker, transports, results_dir, tag):
    """Solve the model at several transport prices and record, for each, how many
    plants open and what the break-even credit is. Also draw a siting map each time.

    `scale_maker` is a function with no arguments that returns a fresh plant block
    (so the theoretical and realistic scenarios can both use this one experiment).
    `tag` is a short label used in file names, e.g. 'theoretical'.
    """
    # A place to collect one summary row per transport price.
    rows = []
    # Try each transport price in turn.
    for tr in transports:
        # Get a fresh plant block for this run.
        scale = scale_maker()
        # Solve Stage A (the location problem) at this transport price.
        sol = solve_stage_A(nodes, p, scale, tr)
        # Score it with Stage B (the money-and-carbon balance).
        kpi = stage_B(sol, nodes, p)
        # Keep the headline numbers for the summary table.
        rows.append(dict(transport_cost=tr, open_plants=kpi["n_plants"],
                         breakeven_credit=round(kpi["breakeven_credit"], 1),
                         fixed_cost=round(kpi["fixed_cost"]), transport_cost_eur=round(sol.transport_cost)))
        # Draw the siting map for this transport price.
        draw_siting_map(
            sol, nodes,
            title=f"Optimal siting — {tag} — transport {tr} EUR/(t*km)\n"
                  f"{kpi['n_plants']} plant(s), break-even credit {kpi['breakeven_credit']:.0f} EUR/tCO2",
            path=os.path.join(results_dir, f"map_{tag}_transport_{tr}.png"))
    # Turn the collected rows into a table.
    table = pd.DataFrame(rows)
    # Save the table as a CSV file.
    table.to_csv(os.path.join(results_dir, f"optimal_by_transport_{tag}.csv"), index=False)
    # Hand the table back so run.py can print it on screen too.
    return table


# ---------------------------------------------------------------------------
# Experiment 2: the effect of the largest-allowed-plant knob (y_max)
# ---------------------------------------------------------------------------
def ymax_sweep(nodes, p, theoretical_cfg, transport, ymax_list, results_dir):
    """For the theoretical scenario, try several caps on the largest plant and see
    how the number of plants and the credit respond."""
    # Collect one row per y_max value.
    rows = []
    # Try each cap in turn.
    for ym in ymax_list:
        # Build a theoretical plant block with this particular y_max.
        scale = make_theoretical(theoretical_cfg, y_max=ym)
        # Solve and score.
        sol = solve_stage_A(nodes, p, scale, transport)
        kpi = stage_B(sol, nodes, p)
        # Record the headline numbers.
        rows.append(dict(y_max=ym, open_plants=kpi["n_plants"],
                         breakeven_credit=round(kpi["breakeven_credit"], 1)))
    # Make a table from the rows.
    table = pd.DataFrame(rows)
    # Save it as a CSV.
    table.to_csv(os.path.join(results_dir, "ymax_sweep.csv"), index=False)
    # Draw a simple bar chart of credit versus y_max.
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    # One green bar per y_max value, with a dark edge.
    ax.bar([str(r["y_max"]) for r in rows], [r["breakeven_credit"] for r in rows],
           color=GREEN, edgecolor=INK, width=0.6)
    # Annotate each bar with how many plants opened at that cap.
    for k, r in enumerate(rows):
        ax.text(k, r["breakeven_credit"], f"{r['open_plants']} plants",
                ha="center", va="bottom", fontsize=8.5, color=INK)
    # Label the axes and title.
    ax.set_xlabel("Largest allowed plant  y_max  [t/h]")
    ax.set_ylabel("Break-even credit [EUR/tCO2]")
    ax.set_title("Effect of the plant-size cap (theoretical scenario)")
    # Tidy, save, close.
    _clean(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, "ymax_sweep.png"), dpi=140)
    plt.close(fig)
    # Return the table for printing.
    return table


# ---------------------------------------------------------------------------
# Experiment 3: one-at-a-time sensitivity curves
# ---------------------------------------------------------------------------
def sensitivity_1d(nodes, p, scale_maker, transport, results_dir, tag):
    """Draw how the credit changes as we move, one at a time, the biochar price,
    the biomass price and the transport cost."""
    # Solve once at the base settings; we reuse this layout for the price curves
    # (changing a downstream PRICE does not change the optimal map, only the money).
    base_sol = solve_stage_A(nodes, p, scale_maker(), transport)

    # --- curve 1: credit versus the biochar selling price ---
    # A range of biochar prices to try (euros per tonne).
    biochar_prices = np.linspace(0, 1500, 25)
    # For each price, re-score the SAME layout with that price.
    credit_vs_biochar = [stage_B(base_sol, nodes, p, biochar_price=pbc)["breakeven_credit"]
                         for pbc in biochar_prices]

    # --- curve 2: credit versus the biomass purchase price (scaled up and down) ---
    # Scaling factors applied to every producer's chip price.
    biomass_scales = np.linspace(0.5, 1.5, 21)
    # A place to collect the credit at each scale.
    credit_vs_biomass = []
    # For each scale, make a copy of the node table with scaled prices, re-score.
    for s in biomass_scales:
        nodes_scaled = nodes.copy()
        nodes_scaled["prezzo_acq"] = nodes["prezzo_acq"] * s
        credit_vs_biomass.append(stage_B(base_sol, nodes_scaled, p)["breakeven_credit"])

    # --- curve 3: credit versus the transport cost (this one DOES change the map) ---
    # A range of transport prices to try (kept short because each one re-solves the model).
    transport_values = np.linspace(0.05, 1.0, 7)
    # For each transport price we must RE-SOLVE, because transport changes the best layout.
    credit_vs_transport = []
    for tr in transport_values:
        sol = solve_stage_A(nodes, p, scale_maker(), tr)
        credit_vs_transport.append(stage_B(sol, nodes, p)["breakeven_credit"])

    # Draw the three curves side by side.
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 4.0))
    # Curve 1: biochar price (green).
    axs[0].plot(biochar_prices, credit_vs_biochar, color=GREEN, lw=2)
    axs[0].set_xlabel("Biochar price [EUR/t]"); axs[0].set_ylabel("Break-even credit [EUR/tCO2]")
    axs[0].set_title("vs biochar price", fontsize=10)
    # Curve 2: biomass price (ochre).
    axs[1].plot(biomass_scales, credit_vs_biomass, color=OCHRE, lw=2)
    axs[1].set_xlabel("Biomass price (scale factor)")
    axs[1].set_title("vs biomass price", fontsize=10)
    # Curve 3: transport cost (ink).
    axs[2].plot(transport_values, credit_vs_transport, color=INK, lw=2)
    axs[2].set_xlabel("Transport cost [EUR/(t*km)]")
    axs[2].set_title("vs transport cost", fontsize=10)
    # Tidy each of the three panels.
    for ax in axs:
        _clean(ax)
    # A shared title for the three.
    fig.suptitle(f"One-at-a-time sensitivity of the break-even credit — {tag}", fontsize=11)
    # Save and close.
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, f"sensitivity_1d_{tag}.png"), dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 4: the tornado (which single number matters most)
# ---------------------------------------------------------------------------
def tornado(nodes, p, theoretical_cfg, transport, results_dir, tag):
    """Move each of several inputs to a LOW and a HIGH value, one at a time, and
    see how far the credit swings. The parameter with the longest bar is the one
    the result depends on most. (We use the theoretical scenario here.)"""
    # Helper: solve + score with a given set of parameters, node prices and transport.
    def credit(params, node_table, tr, y_max):
        scale = make_theoretical(theoretical_cfg, y_max=y_max)
        sol = solve_stage_A(node_table, params, scale, tr)
        return stage_B(sol, node_table, params)["breakeven_credit"]

    # The baseline credit, with everything at its base value.
    base = credit(p, nodes, transport, theoretical_cfg["y_max"])

    # Small helpers to change exactly one thing at a time.
    def with_param(key, value):
        # Return a copy of the parameters with one value changed.
        q = dict(p); q[key] = value; return q
    def with_biomass(scale_factor):
        # Return a copy of the node table with all chip prices scaled.
        nt = nodes.copy(); nt["prezzo_acq"] = nodes["prezzo_acq"] * scale_factor; return nt

    # The list of things to test, each with a low and a high setting.
    tests = [
        ("Biochar price",  credit(with_param("biochar_price", 50),  nodes, transport, theoretical_cfg["y_max"]),
                           credit(with_param("biochar_price", 200), nodes, transport, theoretical_cfg["y_max"])),
        ("Biomass price",  credit(p, with_biomass(0.7), transport, theoretical_cfg["y_max"]),
                           credit(p, with_biomass(1.3), transport, theoretical_cfg["y_max"])),
        ("Transport cost", credit(p, nodes, 0.05, theoretical_cfg["y_max"]),
                           credit(p, nodes, 0.5,  theoretical_cfg["y_max"])),
        ("Energy price",   credit(with_param("energy_price", 90),  nodes, transport, theoretical_cfg["y_max"]),
                           credit(with_param("energy_price", 160), nodes, transport, theoretical_cfg["y_max"])),
        ("Discount rate",  credit(with_param("rate", 0.04), nodes, transport, theoretical_cfg["y_max"]),
                           credit(with_param("rate", 0.08), nodes, transport, theoretical_cfg["y_max"])),
        ("Plant-size cap", credit(p, nodes, transport, 8.0),
                           credit(p, nodes, transport, 30.0)),
    ]
    # Sort the tests so the widest swing is at the top (classic tornado look).
    tests.sort(key=lambda t: abs(t[2] - t[1]))
    # Save the numbers as a table too.
    pd.DataFrame([dict(parameter=t[0], low=round(t[1], 1), high=round(t[2], 1),
                       base=round(base, 1)) for t in tests]
                 ).to_csv(os.path.join(results_dir, f"tornado_{tag}.csv"), index=False)
    # Draw the tornado.
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    # One horizontal ochre bar per parameter, from its low value to its high value.
    for k, (name, lo, hi) in enumerate(tests):
        # The left and right ends of the bar.
        left, right = min(lo, hi), max(lo, hi)
        # Draw the bar spanning from left to right at row k.
        ax.barh(k, right - left, left=left, color=OCHRE, edgecolor=INK, height=0.62)
        # Put the parameter name just to the left of the bar.
        ax.text(left, k, f"{name}  ", va="center", ha="right", fontsize=9, color=INK)
    # Draw a dashed green vertical line at the baseline credit.
    ax.axvline(base, color=GREEN, ls="--", lw=1.4)
    # Note the baseline value next to the line.
    ax.text(base, len(tests) - 0.4, f" base {base:.0f}", color=GREEN, fontsize=9)
    # Hide the y-axis ticks (the names are already written on the bars).
    ax.set_yticks([])
    # Give the names room on the left so they are not clipped.
    ax.margins(x=0.18)
    # Label the x-axis and title.
    ax.set_xlabel("Break-even credit [EUR/tCO2]")
    ax.set_title(f"Tornado: what the credit depends on most — {tag}")
    # Keep only a vertical grid (horizontal gridlines add nothing here).
    ax.grid(axis="x"); ax.grid(axis="y", visible=False)
    _clean(ax)
    # Save and close.
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, f"tornado_{tag}.png"), dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 5: the merit curve (ranking the individual plants)
# ---------------------------------------------------------------------------
def merit_curve(nodes, p, scale_maker, transport, results_dir, tag):
    """Solve once, then work out each open plant's OWN break-even credit (its own
    costs over its own CO2), and draw them ranked from cheapest to dearest."""
    # Build the DECENTRALISED layout — every producer runs its own on-site plant —
    # and rank those plants by their own credit. This is a "supply curve" of the
    # whole fleet and gives one step per producer. (Ranking the OPTIMUM instead
    # would often be a single step, because the optimum opens just one plant.)
    from engine import distance_matrix_km, config_decentralized
    dist = distance_matrix_km(nodes["lat"].to_numpy(), nodes["lon"].to_numpy())
    idx = {i: k for k, i in enumerate(nodes["node"].tolist())}
    sol = config_decentralized(nodes, p, scale_maker(), dist, idx, transport)
    # The purchase price of chips at each producer.
    price = dict(zip(nodes["node"], nodes["prezzo_acq"]))
    # A place to collect (plant name, its biomass, its own credit).
    plants = []
    # Look at every site.
    for j in sol.ids:
        # Skip sites with no plant open.
        if sol.x[j] <= 0.5:
            continue
        # The biomass this plant processes.
        proc_j = sol.proc[j]
        # Skip empty plants just in case.
        if proc_j <= 0:
            continue
        # The biochar this plant makes.
        bc_j = p["biochar_yield"] * proc_j
        # Its fixed cost (already computed by the engine).
        cf_j = sol.C[j]
        # Its transport cost: the chips flowing INTO this plant times distance times the tariff
        # (zero for an on-site plant, where every producer sits on its own plant).
        ct_j = sum(sol.z[i, j] * sol.S[i] * sol.dist[sol.idx[i], sol.idx[j]] * transport for i in sol.ids)
        # Its material cost: the chips flowing into it, each at its producer's price, plus ash disposal.
        mat_j = (sum(sol.z[i, j] * sol.S[i] * price[i] for i in sol.ids)
                 + proc_j * p["residue_yield"] * (-p["residue_price"]))
        # Its electricity income.
        energy_MWh = p["energy_yield"] * proc_j * p["syngas_lhv"] * p["elec_efficiency"] * p["sellable_fraction"]
        # Its total income (biochar + electricity; by-products are zero).
        income_j = p["biochar_yield"] * proc_j * p["biochar_price"] + energy_MWh * p["energy_price"]
        # Its net CO2 removed (storage minus its own transport emissions).
        co2_j = (bc_j * p["carbon_fraction"] * p["stable_fraction"] * (44 / 12)
                 - (ct_j / transport) * p["transport_emission"])
        # Its own break-even credit.
        cc_j = (cf_j + ct_j + mat_j - income_j) / co2_j if co2_j else float("nan")
        # Record it.
        plants.append((j, proc_j, cc_j))
    # Sort the plants from the cheapest credit to the dearest.
    plants.sort(key=lambda t: t[2])
    # Save the ranking as a table.
    pd.DataFrame([dict(plant=t[0], biomass_t_year=round(t[1]), own_credit=round(t[2], 1))
                  for t in plants]).to_csv(os.path.join(results_dir, f"merit_order_{tag}.csv"), index=False)
    # Draw the merit curve as a step chart: cumulative biomass on x, each plant's credit on y.
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    # Running total of biomass as we add plants from cheapest to dearest.
    cum = 0
    # Draw one thick green step per plant, labelled with its letter.
    for name, proc_j, cc_j in plants:
        # Draw a flat line at the plant's credit, spanning its slice of biomass.
        ax.hlines(cc_j, cum, cum + proc_j, color=GREEN, lw=4)
        # Write the plant's letter above the middle of its step.
        ax.text(cum + proc_j / 2, cc_j, name, ha="center", va="bottom", fontsize=8, color=INK)
        # Move the running total along.
        cum += proc_j
    # A baseline at zero for reference.
    ax.axhline(0, color=INK, lw=0.8)
    # Label the axes and title.
    ax.set_xlabel("Cumulative biomass [t/year]")
    ax.set_ylabel("Each plant's own credit [EUR/tCO2]")
    ax.set_title(f"Merit curve — plants ranked cheapest to dearest — {tag}")
    # Tidy, save, close.
    _clean(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, f"merit_{tag}.png"), dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 6: does optimising beat naive plans?
# ---------------------------------------------------------------------------
def optimal_vs_reference(nodes, p, scale_maker, transport, results_dir, tag):
    """Compare the optimised layout against three naive ones: everything in one
    central plant, everything processed on the spot, and a cloud of random plans."""
    # A fresh plant block and the distance table we need for the reference plans.
    scale = scale_maker()
    # Solve the real optimum.
    opt = solve_stage_A(nodes, p, scale, transport)
    opt_credit = stage_B(opt, nodes, p)["breakeven_credit"]
    # Build the distance table and index lookup once (the reference helpers need them).
    from engine import distance_matrix_km
    dist = distance_matrix_km(nodes["lat"].to_numpy(), nodes["lon"].to_numpy())
    idx = {i: k for k, i in enumerate(nodes["node"].tolist())}
    # The fully centralised plan and its credit.
    cen = stage_B(config_centralized(nodes, p, scale_maker(), dist, idx, transport), nodes, p)["breakeven_credit"]
    # The fully decentralised plan and its credit.
    dec = stage_B(config_decentralized(nodes, p, scale_maker(), dist, idx, transport), nodes, p)["breakeven_credit"]
    # The random cloud: take its average credit.
    rnd = float(np.nanmean(config_random(nodes, p, scale_maker(), dist, idx, transport)))
    # Collect the four numbers.
    labels = ["Optimised", "Centralised", "Decentralised", "Random (mean)"]
    values = [opt_credit, cen, dec, rnd]
    # Save them as a table.
    pd.DataFrame(dict(configuration=labels, breakeven_credit=[round(v, 1) for v in values])
                 ).to_csv(os.path.join(results_dir, f"optimal_vs_reference_{tag}.csv"), index=False)
    # Draw a bar chart; the optimum is green, the rest ochre, so the gap is obvious.
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.bar(labels, values, color=[GREEN, OCHRE, OCHRE, OCHRE], edgecolor=INK, width=0.62)
    # Write the value on top of each bar.
    for k, v in enumerate(values):
        ax.text(k, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9, color=INK)
    # Label the y-axis and title; tilt the x labels so they fit.
    ax.set_ylabel("Break-even credit [EUR/tCO2]")
    ax.set_title(f"Optimised vs naive layouts — {tag}")
    plt.xticks(rotation=12)
    # Tidy, save, close.
    _clean(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, f"optimal_vs_reference_{tag}.png"), dpi=140)
    plt.close(fig)
    # Return the four numbers for printing.
    return dict(zip(labels, values))
