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

## How to Obtain the Datasets

The project uses:

- `uniform` synthetic streams
- `zipf` synthetic streams with `s = 1.2`
- `Kosarak` as the real-world dataset

### 1. Generate the synthetic datasets

The final synthetic datasets are generated from:

- `experiments/configs/synthetic_project_required_expanded.json`

Run:

```bash
python3 -m experiments.generate_datasets \
  --synthetic-config experiments/configs/synthetic_project_required_expanded.json \
  --output-dir data/generated_project_required_synthetic
```

This materializes the required strict-turnstile streams under the final project setting:

- families: `uniform`, `zipf`
- `domain_size = 100000`
- `F1* in {5e4, 1e5, 2e5, 5e5}`
- `alpha in {1.5, 2, 3, 4, 6, 8}`
- stream mode: `non-interleaved`
- Zipf parameter: `s = 1.2`

The generated datasets are written under:

- `data/generated_project_required_synthetic/`

Each dataset directory contains:

- `stream.jsonl`
- `metadata.json`

### 2. Generate the Kosarak datasets

The final real-world datasets are generated from:

- `experiments/configs/real_kosarak_project_required_expanded.json`

Run:

```bash
python3 -m experiments.generate_kosarak \
  --config experiments/configs/real_kosarak_project_required_expanded.json \
  --output-dir data/generated_project_required_kosarak
```

The generator will automatically download `kosarak.dat` if it is not already present, and cache it under:

- `data/raw/skmine_data/kosarak.dat`

It then:

- parses the transaction file,
- expands transactions into item occurrences,
- takes a prefix long enough for the required insertion budget,
- constructs strict-turnstile streams using the same non-interleaved random-deletion policy,
- validates each generated stream.

The generated datasets are written under:

- `data/generated_project_required_kosarak/`

### 3. Generate everything with one command

If you do not want to run the two generators separately, the main baseline pipeline will generate both synthetic and Kosarak datasets automatically before running the experiments:

```bash
bash scripts/run_project_required_expanded.sh
```

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
