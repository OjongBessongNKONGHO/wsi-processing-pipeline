# Config Options Reference

## Columns

| Column | Required | Valid Values |
|--------|----------|-------------|
| wsi | yes | filename of the slide (.svs) in wsi_dir |
| segmenter | yes | hest, grandqc, otsu |
| remove_artifacts | yes | true, false |
| remove_penmarks | yes | true, false |
| patch_encoder | yes | uni_v1 (256/20), uni_v2 (256/20), conch_v15 (512/20), virchow (224/20), virchow2 (224/20), phikon (224/20), gigapath (256/20), and 26 more in encoder_registry.py |
| patch_size | yes | must match encoder requirement |
| mag | yes | must match encoder requirement |
| overlap | yes | 0 or positive integer less than patch_size |
| slide_encoder | optional | titan (needs conch_v15), gigapath (needs gigapath), prism (needs virchow2), or leave empty |
