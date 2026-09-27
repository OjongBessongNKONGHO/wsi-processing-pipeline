"""
WSI Processing Pipeline — Entry Point.

Two modes:
  1. Single config:  python run_pipeline.py single <config.csv> <wsi_dir> <job_dir>
  2. Batch config:   python run_pipeline.py batch <run_config.csv>

Single mode: each row in the CSV is a slide with its own parameters.
Batch mode:  one config defines parameters for all slides in a zip or directory.
"""

import sys

from src.validator import validate_config
from src.runner import run_pipeline
from src.batch_processor import run_batch_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_pipeline.py single <config.csv> <wsi_dir> <job_dir>")
        print("  python run_pipeline.py batch <run_config.csv>")
        print()
        print("Modes:")
        print("  single  Each row in CSV is one slide with its parameters")
        print("  batch   One config for all slides in a zip or directory")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "single":
        if len(sys.argv) != 5:
            print("Usage: python run_pipeline.py single <config.csv> <wsi_dir> <job_dir>")
            sys.exit(1)

        config_path = sys.argv[2]
        wsi_dir = sys.argv[3]
        job_dir = sys.argv[4]

        print("Validating config...")
        errors = validate_config(config_path, wsi_dir)

        if errors:
            print(f"\nValidation failed with {len(errors)} error(s):\n")
            for error in errors:
                print(f"  {error}")
            print("\nFix the errors above and try again.")
            sys.exit(1)

        print("Config valid.\n")
        summary = run_pipeline(config_path, wsi_dir, job_dir)

        if summary["failed"] > 0:
            sys.exit(1)

    elif mode == "batch":
        if len(sys.argv) != 3:
            print("Usage: python run_pipeline.py batch <run_config.csv>")
            sys.exit(1)

        config_path = sys.argv[2]
        run_batch_pipeline(config_path)

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'single' or 'batch'")
        sys.exit(1)


if __name__ == "__main__":
    main()
