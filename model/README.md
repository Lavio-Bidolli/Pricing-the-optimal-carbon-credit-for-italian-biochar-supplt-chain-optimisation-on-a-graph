# Biochar supply-chain model — toy, runnable version

A small, self-contained, heavily commented version of the two-stage optimisation
model from the thesis *"Pricing an optimal carbon credit for a competitive Italian
biochar supply chain"*. It runs on the thesis's **real geography, anonymised and
privacy-perturbed** (see the note below), so anyone can launch it, read it, and
experiment, without exposing any real producer.

The model adapts the two-stage framework of **Grimm, Niazmand & Runge (2026)** to a
set of wood-chip producers. It decides where to build biochar plants and how to
route each producer's chips, then computes the **break-even carbon credit** — the
price per tonne of CO₂ that makes the chain's income match its costs.

## What it does

It runs **two scenarios**:
- **theoretical** — one big plant with economies of scale (the "0.6 power" cost
  rule, linearised so a solver can handle it);
- **realistic** — many identical small modules, with no economies of scale.

and, for each, several experiments: the best layout at different transport costs,
one-at-a-time sensitivity curves, a merit curve ranking the plants, and a
comparison of the optimum against naive layouts. For the theoretical scenario it
also sweeps the plant-size cap and draws a tornado chart of what the credit
depends on most.

## How to run

1. Install the dependencies (once):
   ```
   pip install -r requirements.txt
   ```
2. Launch:
   ```
   python run.py
   ```
3. Open the **`results`** folder it creates. You will find CSV tables, PNG figures
   and a plain-English `summary.txt`.

## What to change (and where)

**You only edit `toy_data.py`.** Everything else just uses it. The two most
interesting knobs, as recommended in the thesis, are:

- **`TRANSPORT_COST`** — how expensive it is to move chips. Cheap transport makes
  the model build **one big central plant**; expensive transport makes it build
  **many small local plants**.
- **`THEORETICAL["y_max"]`** — the largest plant the model is allowed to build.
  Lower it and the model is forced to spread production out.

`toy_data.py` also lets you change the producers (the `NODES` list) and every
economic and environmental number (`PARAMS`). Each line has a short note saying
what it does. The model adapts to however many producers you list.

## The files

| File | What it is |
|---|---|
| `toy_data.py` | The toy producers and all the numbers — **the only file to edit**. |
| `engine.py` | The model itself: distances, the two plant types, Stage A (the optimisation), Stage B (the carbon credit). |
| `analyses.py` | The experiments and the figures they draw. |
| `run.py` | Press play: runs everything and fills `results/`. |
| `requirements.txt` | The libraries needed. |

Every line of code carries a plain-language comment, so the files can be read
top to bottom as an explanation of how the model works.

## Notes

- **About the producers (important).** The 22 producers are the *real* nodes of
  the thesis, so the map keeps the same geography and the same mix of large and
  small suppliers. They are **anonymised and perturbed on purpose**: the company
  names are replaced by letters (A..V), each location is shifted by a few random
  kilometres, and the biomass and prices are nudged by a few percent and rounded.
  The perturbation is small enough that the model behaves like the real one, but
  no real producer can be identified from these numbers. This is what makes the
  folder safe to share. (The confidential, exact dataset lives elsewhere and is
  not part of this folder.)
- Several environmental terms (process, grid, end-use emissions) are intentionally
  left at zero, exactly as in the thesis base case; the code shows where they enter
  so real values can be slotted in later.
- The solver is **HiGHS**, driven through **Pyomo**. Results of a mixed-integer
  problem can vary slightly between solver versions when several layouts tie on cost.
- Method credit: the two-stage approach is adapted from Grimm, Niazmand & Runge (2026).
