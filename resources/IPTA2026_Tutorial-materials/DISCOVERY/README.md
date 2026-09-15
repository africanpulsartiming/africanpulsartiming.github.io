# Single-pulsar noise analysis with Discovery — student workshop

A short series of Jupyter notebooks taking you from raw pulsar timing data to
single-pulsar noise models and, as a bonus, population-level (hierarchical)
inference. Built on [Discovery](https://github.com/nanograv/discovery).

**This folder is fully self-contained** — the MPTA-DR2 dataset and the bonus
hierarchical data/scripts are bundled under `data/` and `bonus_hierarchical/`, and
the notebooks use only standard Discovery + numpyro + corner (no fork-specific
sampler helpers), so you can zip it up and run it anywhere the requirements are
installed. No `/fred` access needed.

## Notebooks (run in order)

| # | notebook | what you do |
|---|----------|-------------|
| 1 | [`01_make_feathers.ipynb`](01_make_feathers.ipynb) | Turn `.par` + `.tim` into fast-loading **feather** files (uses `make_feather.py`). |
| 2 | [`02_basic_noise_model.ipynb`](02_basic_noise_model.ipynb) | Fit a basic **red + DM** model, sample with NUTS, **save the chain**, get **maximum-likelihood** parameters, make a **corner plot**. |
| 3 | [`03_custom_noise_model.ipynb`](03_custom_noise_model.ipynb) | Load **your** favourite pulsar and toggle **ECORR / red / DM / chromatic** noise on top of the measurement noise; use the corner plot to judge which terms are **significant**. |
| 4 | [`04_bonus_hierarchical.ipynb`](04_bonus_hierarchical.ipynb) | **Bonus:** run the hierarchical population analyses bundled in `bonus_hierarchical/example_1` and `example_2`. |

## Helper script

* `make_feather.py` — batch-convert a directory of `.par`/`.tim` pairs to `.feather`.
  ```bash
  python make_feather.py [indir] [outdir] [--ephem DE440]   # default indir: data/mpta-dr2
  ```

## Data

* `data/mpta-dr2/` — the **MeerKAT Pulsar Timing Array DR2** dataset: 83 millisecond
  pulsars, each with `.par`, `.tim`, and a pre-built `.feather`. Notebooks 1–3 load
  the feathers via a `DATADIR = "./data/mpta-dr2"` variable at the top of each.
* `bonus_hierarchical/` — everything notebook 4 needs (see below).

## How the noise model is built (notebooks 2 & 3)

The model is assembled directly from Discovery's `signals` tools as a list of
components wrapped in a `PulsarLikelihood` — always the data + timing model +
measurement (EFAC/EQUAD) noise, plus any of these optional terms, built as
**Fourier Gaussian processes** (the `fftint=False` path, matching the older
`enterprise` model definitions):

| term | constructor |
|------|-------------|
| ECORR | `signals.makegp_ecorr` |
| red (spin) noise | `signals.makegp_fourier(..., powerlaw, name="red_noise")` |
| DM noise | `signals.makegp_fourier(..., powerlaw, fourierbasis=signals.fourierbasis_dm, name="dm_gp")` |
| chromatic noise | `signals.makegp_fourier(..., powerlaw, fourierbasis=signals.fourierbasis_chrom, name="chrom_gp")` |

Sampling uses `discovery.samplers.numpyro.makemodel_transformed` + `makesampler_nuts`.
The chain is read back with `sampler.to_df()`, the log-likelihood is recomputed for
each sample with `jax.vmap(model.logL)`, and corner plots are built with the `corner`
package — no project-specific plotting helpers, so this is portable to the main
NANOGrav branch of Discovery.

## Bonus: hierarchical inference (notebook 4)

`bonus_hierarchical/` contains two worked examples (`example_1`, `example_2`), each a
self-contained `HyperParInf.ipynb` plus the small inputs it reads:

* `chains/HamSampler/<psr>_chain/*.pickle` — per-pulsar single-pulsar posterior chains,
* `chains/NestSampler/<psr>_chain/*.json` — per-pulsar nested-sampling evidences,
* `Noise_par/` — the injected (true) noise values for the simulation,
* `hyper_utilis.py` and the shared `psrToyModel.py` — helper code.

All paths in the bundled notebooks are relative, so launch them from inside the
example folder. The original notebooks' final **GWB-search** section (which needs
~220 MB of raw feathers) has been trimmed from these copies to keep the bundle light.

> **The bonus requires [Bilby](https://lscsoft.docs.ligo.org/bilby/)** (+ `dynesty`):
> `pip install bilby dynesty`. The hierarchical step uses
> `bilby.hyper.HyperparameterLikelihood` with the `dynesty` nested sampler.

## Requirements

* Core (notebooks 1–3): `discovery`, `enterprise`, `jax`/`numpyro`, `corner`,
  `pandas`, `matplotlib`. Importing `discovery` automatically enables 64-bit
  precision in JAX.
* Bonus (notebook 4): additionally `bilby` and `dynesty`.

Outputs (chains, corner PNGs, feathers you build) are written next to the notebooks
under `results/`, `my_feathers/`, and the bonus `results_*/` folders.
