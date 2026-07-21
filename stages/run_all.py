"""
Run the whole UraLex -> BEAST2 curation pipeline in order.

    python3 stages/run_all.py

Each stage is independently re-runnable and writes its own artifacts; this
orchestrator just calls them in dependency order and prints a compact summary.
No phylogenetic inference is performed anywhere in this pipeline.
"""
import importlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STAGES = [
    "stage1_load",
    "stage2_gaps",
    "stage3_loans",
    "stage4_matrix",
    "stage5_calibration",
]


def main():
    for name in STAGES:
        print(f"\n===== {name} =====")
        mod = importlib.import_module(name)
        mod.run()
    print("\n===== pipeline complete =====")


if __name__ == "__main__":
    main()
