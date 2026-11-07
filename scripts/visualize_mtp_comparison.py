
"""
Visualize the effect of min_tissue_proportion on patch selection.
Overlays patch grids from mtp=0 and mtp=0.25 runs onto the slide thumbnail,
color-coding kept vs filtered patches.

Run on SCC with: python visualize_mtp_comparison.py
"""

import h5py
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
BASE = Path("/restricted/projectnb/luadfrp/trident_output")
OUTPUT_DIR = Path("/usr2/collab/onkongho/wsi-processing-pipeline/figures")

runs = {
    "mtp0":   BASE / "comparison_grandqc_penmarkfix",
    "mtp025": BASE / "penmarkfix_mtp025",
}

slides = ["test2"]  # add "test" if it exists in the mtp0 run

PATCH_SIZE_PX = 256   # native patch size in pixels at extraction mag
EXTRACTION_MAG = 20.0 # magnification used during extraction

# ── Helper ──────────────────────────────────────────────────────────────
def load_coords(run_dir, slide_name):
    h5_path = run_dir / "20x_256px_0px_overlap" / "patches" / f"{slide_name}_patches.h5"
    with h5py.File(h5_path, "r") as f:
        coords = f["coords"][:]
    return coords

def load_thumbnail(run_dir, slide_name):
    # try common naming patterns
    for ext in [".jpg", ".png"]:
        for name in [slide_name, f"{slide_name}.svs"]:
            p = run_dir / "thumbnails" / f"{name}{ext}"
            if p.exists():
                return np.array(Image.open(p))
    # fallback: just grab the first image in thumbnails
    thumb_dir = run_dir / "thumbnails"
    if thumb_dir.exists():
        for f in sorted(thumb_dir.iterdir()):
            if f.suffix.lower() in [".jpg", ".png"]:
                return np.array(Image.open(f))
    raise FileNotFoundError(f"No thumbnail found in {run_dir / 'thumbnails'}")

def get_thumbnail_scale(thumbnail_shape, coords, patch_size):
    """Estimate the scale factor between thumbnail pixels and extraction-level pixels."""
    if len(coords) == 0:
        return 1.0
    max_coord_x = coords[:, 0].max() + patch_size
    max_coord_y = coords[:, 1].max() + patch_size
    # thumbnail is (height, width, channels) so shape[1]=width, shape[0]=height
    scale_x = thumbnail_shape[1] / max_coord_x
    scale_y = thumbnail_shape[0] / max_coord_y
    return min(scale_x, scale_y)

# ── Main ────────────────────────────────────────────────────────────────
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for slide in slides:
    # Load coords from both runs
    coords_mtp0 = load_coords(runs["mtp0"], slide)
    coords_mtp025 = load_coords(runs["mtp025"], slide)

    # Load thumbnail (use mtp0 run since it has thumbnails)
    thumbnail = load_thumbnail(runs["mtp0"], slide)

    # Find which patches were filtered
    # Convert coords to sets of tuples for comparison
    set_mtp0 = set(map(tuple, coords_mtp0))
    set_mtp025 = set(map(tuple, coords_mtp025))
    kept = set_mtp0 & set_mtp025       # in both
    filtered = set_mtp0 - set_mtp025   # removed by mtp=0.25

    print(f"{slide}: mtp=0 has {len(coords_mtp0)} patches, mtp=0.25 has {len(coords_mtp025)}")
    print(f"  kept: {len(kept)}, filtered: {len(filtered)}")

    # Calculate scale
    scale = get_thumbnail_scale(thumbnail.shape, coords_mtp0, PATCH_SIZE_PX)
    patch_thumb = PATCH_SIZE_PX * scale

    # ── Plot ────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))

    titles = [
        f"mtp=0 ({len(coords_mtp0)} patches)",
        f"mtp=0.25 ({len(coords_mtp025)} patches)",
        f"Filtered patches ({len(filtered)} removed)",
    ]

    for ax, title in zip(axes, titles):
        ax.imshow(thumbnail)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

    # Panel 1: all mtp=0 patches in blue
    for (x, y) in coords_mtp0:
        rect = plt.Rectangle((x * scale, y * scale), patch_thumb, patch_thumb,
                              linewidth=0.3, edgecolor="blue", facecolor="blue", alpha=0.15)
        axes[0].add_patch(rect)

    # Panel 2: mtp=0.25 patches in green
    for (x, y) in coords_mtp025:
        rect = plt.Rectangle((x * scale, y * scale), patch_thumb, patch_thumb,
                              linewidth=0.3, edgecolor="green", facecolor="green", alpha=0.15)
        axes[1].add_patch(rect)

    # Panel 3: kept in green, filtered in red
    for (x, y) in kept:
        rect = plt.Rectangle((x * scale, y * scale), patch_thumb, patch_thumb,
                              linewidth=0.2, edgecolor="green", facecolor="green", alpha=0.1)
        axes[2].add_patch(rect)
    for (x, y) in filtered:
        rect = plt.Rectangle((x * scale, y * scale), patch_thumb, patch_thumb,
                              linewidth=0.5, edgecolor="red", facecolor="red", alpha=0.4)
        axes[2].add_patch(rect)

    # Legend for panel 3
    legend_handles = [
        mpatches.Patch(facecolor="green", alpha=0.3, edgecolor="green", label="Kept"),
        mpatches.Patch(facecolor="red", alpha=0.5, edgecolor="red", label="Filtered by mtp=0.25"),
    ]
    axes[2].legend(handles=legend_handles, loc="lower right", fontsize=10)

    fig.suptitle(f"{slide}.svs — Effect of min_tissue_proportion=0.25", fontsize=16, fontweight="bold")
    plt.tight_layout()

    out_path = OUTPUT_DIR / f"{slide}_mtp_comparison.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

print("\nDone.")
