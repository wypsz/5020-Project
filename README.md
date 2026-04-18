# SEEM5020 Project

This repository studies **frequency estimation under the strict turnstile model with the α-bounded deletion property**.

The project includes:

- four required algorithms:
  - `Double-MG`
  - `Double-SS`
  - `Count-Min Sketch`
  - `Count-Sketch`
- one advanced design candidate:
  - `Integrated SpaceSaving±`
- dataset generators and validators for strict-turnstile streams
- experiment runners for synthetic and real-world data
- a notebook for plotting and comparing the final results

The final write-up is in [report/SEEM5020_Report.md](report/SEEM5020_Report.md).

## Repository Layout

```text
src/seem5020/
  algorithms/   estimator implementations
  stream/       dataset generation and validation
  evaluation/   metrics and experiment runner
experiments/
  configs/      experiment configurations
  *.py          generation, execution, and summarization scripts
scripts/
  *.sh          end-to-end experiment pipelines
notebooks/
  project_required_results.ipynb
report/
  figures/      generated figures
  tables/       experiment outputs
  SEEM5020_Report.md
```

## Main Experiment Pipelines

### 1. Baseline project run

This pipeline generates the final synthetic and Kosarak datasets, runs the main experiments, and builds merged result tables.

```bash
bash scripts/run_project_required_expanded.sh
```

Outputs:

- `report/tables/project_required_expanded_*`
- `report/figures/project_required_expanded/*`

### 2. Epsilon sweep

This supplementary run reuses the materialized datasets and evaluates `epsilon in {0.01, 0.05, 0.1}`.

```bash
bash scripts/run_epsilon_sweep_existing_datasets.sh
```

Outputs:

- `report/tables/epsilon_sweep_*`

### 3. Equal logical space comparison

This supplementary run reuses the materialized datasets and compares all methods under matched logical budgets.

```bash
bash scripts/run_equal_logical_space_existing_datasets.sh
```

Outputs:

- `report/tables/equal_logical_space_*`

## How to Plot the Results

Open:

- [notebooks/project_required_results.ipynb](notebooks/project_required_results.ipynb)

The notebook loads:

- baseline results,
- epsilon-sweep results,
- equal-space results,

and produces:

- `alpha` sweeps,
- `stream-length` sweeps,
- `epsilon` sweeps,
- equal-space comparisons,
- both **normalized absolute error** and **relative error** plots.

## Real-World Data

The final report uses **Kosarak** as the required real-world dataset.

The codebase also contains a CAIDA pipeline, but it is optional and was not used in the final reported figures.

## Notes

- The final experiment protocol uses **unit updates** and the **non-interleaved** deletion mode.
- If the project-required datasets do not already exist, run the baseline pipeline first.
- The notebook reads the merged result files under `report/tables/`.
