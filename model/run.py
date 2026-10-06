"""
run.py  —  Press play.  Runs the whole study and fills the `results` folder.
===========================================================================

This is the file you actually launch:

    python run.py

It reads your numbers from toy_data.py, runs BOTH plant scenarios (the
theoretical one with economies of scale, and the realistic one with small
modules) through the experiments you switch on below, and writes all the tables,
figures and a plain-English summary into a folder called `results`.

To change the STUDY, edit toy_data.py.
To make a run FASTER, turn some experiments off just below.
"""

# `os` is used to build the path of the results folder and its files.
import os

# Bring in your editable numbers (the producers and the parameters).
import toy_data as toy
# Bring in the experiments and the two little helpers that build the pieces.
import analyses as A

# ---------------------------------------------------------------------------
# WHICH EXPERIMENTS TO RUN  (set any to False to skip it and finish sooner)
# ---------------------------------------------------------------------------
# The whole suite on the 22 nodes takes a few minutes, because some experiments
# re-solve the optimisation many times. The "(SLOW)" ones below are the reason;
# turn them off for a quick look. The others are fast.
RUN_SITING_MAPS   = True   # best layout + a map at each transport cost (a few solves).
RUN_SENSITIVITY   = True   # (SLOW) the one-at-a-time curves: re-solves at many transport values.
RUN_MERIT_CURVE   = True   # the supply curve ranking the producers (FAST: no re-solving).
RUN_COMPARISON    = True   # optimised vs naive layouts (one solve + a quick random cloud).
RUN_YMAX_SWEEP    = True   # plant-size cap sweep, theoretical only (a few solves).
RUN_TORNADO       = True   # (SLOW) tornado sensitivity, theoretical only: re-solves several times.

# The folder where every output will be written (created next to this file).
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def main():
    """Run the chosen experiments from start to finish."""
    # Make sure the results folder exists (create it if it does not).
    A._ensure(RESULTS)
    # Turn the editable list of producers into the table the engine expects.
    nodes = A.nodes_dataframe(toy.NODES)
    # The base transport price to use wherever a single value is needed.
    base_transport = toy.TRANSPORT_COST

    # Two "scenario makers": each is a short name plus a function that builds a
    # fresh plant block of that type. Running everything twice, once per scenario,
    # is how we compare "big plants with economies of scale" against "small modules".
    scenarios = {
        "theoretical": lambda: A.make_theoretical(toy.THEORETICAL),
        "realistic":   lambda: A.make_realistic(toy.REALISTIC),
    }

    # We collect a few headline lines of text to write into the summary at the end.
    summary = []
    # A title line for the summary file.
    summary.append("BIOCHAR SUPPLY-CHAIN MODEL — TOY RUN SUMMARY")
    summary.append("=" * 60)
    # Record the key settings so the summary is self-explanatory.
    summary.append(f"Producers (real, anonymised & perturbed): {len(toy.NODES)}")
    summary.append(f"Base transport cost:   {base_transport} EUR/(t*km)")
    summary.append(f"Transport prices tried: {toy.TRANSPORT_SWEEP}")
    summary.append(f"Plant-size caps tried:  {toy.YMAX_SWEEP} t/h (theoretical scenario)")
    summary.append("")

    # Run the experiments that make sense for BOTH scenarios.
    for tag, maker in scenarios.items():
        # Tell the user on screen which scenario we are working on.
        print(f"\n=== Scenario: {tag} ===")

        # Experiment 1: best layout at each transport price (+ a siting map each time).
        if RUN_SITING_MAPS:
            print("  - optimal layout by transport cost ...")
            table = A.optimal_by_transport(nodes, toy.PARAMS, maker, toy.TRANSPORT_SWEEP, RESULTS, tag)
            # Add this scenario's transport table to the summary.
            summary.append(f"[{tag}] break-even credit by transport cost:")
            summary.append(table.to_string(index=False))
            summary.append("")

        # Experiment 3: one-at-a-time sensitivity curves (the slow one).
        if RUN_SENSITIVITY:
            print("  - one-at-a-time sensitivity curves (slow) ...")
            A.sensitivity_1d(nodes, toy.PARAMS, maker, base_transport, RESULTS, tag)

        # Experiment 5: the merit curve (ranking the producers).
        if RUN_MERIT_CURVE:
            print("  - merit curve ...")
            A.merit_curve(nodes, toy.PARAMS, maker, base_transport, RESULTS, tag)

        # Experiment 6: optimised vs naive layouts.
        if RUN_COMPARISON:
            print("  - optimised vs naive layouts ...")
            comp = A.optimal_vs_reference(nodes, toy.PARAMS, maker, base_transport, RESULTS, tag)
            # Add that comparison to the summary.
            summary.append(f"[{tag}] optimised vs naive (EUR/tCO2): "
                           + ", ".join(f"{k} {v:.0f}" for k, v in comp.items()))
            summary.append("")

    # Run the experiments that only make sense for the theoretical scenario
    # (the realistic modular plant has no economies of scale and no y_max knob).
    if RUN_YMAX_SWEEP or RUN_TORNADO:
        print("\n=== Theoretical-only experiments ===")
    # Experiment 2: the plant-size cap sweep (one of the two recommended knobs).
    if RUN_YMAX_SWEEP:
        print("  - plant-size cap (y_max) sweep ...")
        ytab = A.ymax_sweep(nodes, toy.PARAMS, toy.THEORETICAL, base_transport, toy.YMAX_SWEEP, RESULTS)
        # Add it to the summary.
        summary.append("[theoretical] break-even credit by plant-size cap (y_max):")
        summary.append(ytab.to_string(index=False))
        summary.append("")

    # Experiment 4: the tornado (the other slow one).
    if RUN_TORNADO:
        print("  - tornado sensitivity (slow) ...")
        A.tornado(nodes, toy.PARAMS, toy.THEORETICAL, base_transport, RESULTS, "theoretical")

    # Write the collected summary lines into a plain-text file in the results folder.
    with open(os.path.join(RESULTS, "summary.txt"), "w") as f:
        f.write("\n".join(summary))

    # Tell the user where to look.
    print(f"\nDone. Tables, figures and summary.txt are in: {RESULTS}")


# This standard line means: only run main() when the file is launched directly
# (python run.py), not when it is imported by another file.
if __name__ == "__main__":
    main()
