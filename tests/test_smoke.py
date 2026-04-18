"""Small smoke test for the project pipeline."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from seem5020.evaluation.runner import AlgorithmConfig, run_experiment_suite
from seem5020.stream.generators import SyntheticStreamSpec, generate_synthetic_stream
from seem5020.stream.validators import validate_stream


def main() -> None:
    spec = SyntheticStreamSpec(
        family="uniform",
        final_f1=10,
        alpha=2.0,
        mode="interleaved",
        seed=7,
        domain_size=32,
    )
    dataset = generate_synthetic_stream(spec)
    report = validate_stream(dataset.updates, expected_final_f1=10, alpha=2.0)
    assert report.strict_turnstile_ok
    assert report.final_f1_ok
    assert report.alpha_ok

    results = run_experiment_suite(
        dataset=dataset,
        algorithm_configs=[
            AlgorithmConfig(name="double_mg", params={"capacity": 8}),
            AlgorithmConfig(name="double_ss", params={"capacity": 8}),
            AlgorithmConfig(name="count_min", params={"width": 32, "depth": 3}),
            AlgorithmConfig(name="count_sketch", params={"width": 32, "depth": 3}),
            AlgorithmConfig(name="integrated_sspm", params={"capacity": 8}),
        ],
        seed=7,
        heavy_k=5,
        sample_k=5,
    )
    assert len(results) == 5
    for row in results:
        assert row["observed_final_f1"] == 10
        assert row["stream_length"] == len(dataset.updates)

    print("smoke test passed")


if __name__ == "__main__":
    main()
