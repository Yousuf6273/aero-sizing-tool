"""Run every example (used by CI and as a quick demo)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import cessna172_performance, model_rocket_trajectory, trade_studies, uav_sizing  # noqa: E402

if __name__ == "__main__":
    cessna172_performance.main()
    uav_sizing.main()
    model_rocket_trajectory.main()
    trade_studies.main()
    print("\nAll examples ran; figures written to figures/")
