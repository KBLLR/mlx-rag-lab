# Code Cleanup Audit

**Date**: 2025-11-12
**Agent**: Rhyme (LabCustodian)

## Directories to Review

### benchmarks/ (135M) 🔴 **Archive Candidate**
- **Size**: 135M (mostly output files)
- **Contents**: Flux benchmark scripts and outputs
- **Decision**: Archive unless actively used for MLX performance measurement
- **Reasoning**: The `bench-cli` exists, but 135M of outputs suggests this is historical data

**Action**: Move to `archive/benchmarks/` or delete output files, keep scripts if valuable

### segment_anything/ (708K) 🟢 **Keep**
- **Purpose**: SAM (Segment Anything Model) in MLX (Meta AI's model, MLX implementation)
- **MLX-native**: ✅ Yes (confirmed by David)
- **Usage**: Not in CLI yet, but valuable MLX vision model

**Action**: Keep and consider promoting to CLI or documenting in examples

### musicgen/ (40K) ⚠️ **Review Needed**
- **Purpose**: MusicGen experiments
- **Status**: Model exists in `mlx-models/musicgen-small/`
- **CLI**: Mentioned in `COMMANDS_MANIFEST.md` but no `musicgen-cli` in `apps/`

**Action**: Either promote to first-class CLI (`apps/musicgen_cli.py`) or archive

### experiments/ (32K) 🟡 **Selective Keep**
- **Purpose**: Experimental ingestion/data workflows
- **MLX-data**: Some scripts use mlx-data, others don't

**Action**: Keep mlx-data experiments, archive non-MLX code

### speechcommands/ (24K) 🔴 **Archive Candidate**
- **Purpose**: Speech recognition experiments
- **Usage**: Not documented or referenced

**Action**: Archive to `archive/audio/speechcommands/`

### utils/ (4K) 🟢 **Consolidate**
- **Purpose**: Utility scripts
- **Action**: Migrate to `libs/mlx_core/` or `scripts/`, then delete directory

## Files to Review

### third_party/ ⚠️ **Document or Remove**
- **Action**: Either document why vendored code is needed, or remove entirely
- **Reasoning**: MLX projects should use standard pip/uv dependencies

### archive/tui/ ✅ **Keep**
- Already archived, documented as historical reference

## Proposed Cleanup Commands

```bash
# Phase 1: Archive non-MLX experiments
mkdir -p archive/audio
mv speechcommands/ archive/audio/
# NOTE: segment_anything/ is MLX-native, KEEP IT

# Phase 2: Clean benchmark outputs (keep scripts)
mkdir -p archive/benchmarks
find benchmarks/ -name "*.png" -o -name "*.jpg" -o -name "*.json" | xargs -I {} mv {} archive/benchmarks/

# Phase 3: Consolidate utils
mv utils/* scripts/  # or libs/mlx_core/ if they're modules
rmdir utils/

# Phase 4: Review experiments (manual)
# Keep: experiments/ingestion/mlx_data_*.py
# Archive: experiments/ingestion/*_numpy.py, *_pandas.py

# Phase 5: Decide on musicgen
# Option A: Promote to CLI
# Option B: Archive
```

## Decision Matrix

| Directory | MLX-Native? | Used by CLI? | Documented? | Decision |
|-----------|-------------|--------------|-------------|----------|
| benchmarks/ | Yes | bench-cli | Yes | Keep scripts, clean outputs |
| segment_anything/ | Yes | No | No | Keep (MLX-native SAM) |
| musicgen/ | Yes | Partial | Yes | Promote to CLI or archive |
| experiments/ | Mixed | No | No | Keep mlx-data, archive rest |
| speechcommands/ | Unknown | No | No | Archive |
| utils/ | N/A | No | No | Consolidate into scripts/ |
| third_party/ | N/A | Unknown | No | Document or remove |

## Next Steps

1. Get David's approval on archive decisions
2. Create `archive/` structure if not exists
3. Run cleanup commands
4. Update `pyproject.toml` to remove unused dependencies (textual, etc.)
5. Update `.gitignore` to exclude `archive/`
6. Document remaining code in `docs/ARCHITECTURE.md`

## Questions for David

1. Is the `benchmarks/` output data valuable? (135M is a lot)
2. Should MusicGen be promoted to first-class CLI or archived?
3. Is `segment_anything/` MLX-based or PyTorch? (determines keep vs archive)
4. Any specific experiments in `experiments/` you want to preserve?
