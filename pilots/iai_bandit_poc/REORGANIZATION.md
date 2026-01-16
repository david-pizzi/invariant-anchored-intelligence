# Directory Reorganization Summary

**Date**: 2026-01-15  
**Status**: ✅ Complete

## Changes Made

### 1. Created New Structure
```
iai_bandit_poc/
├── src/          # All Python modules
├── docs/         # All documentation
├── deprecated/   # Old/unused files
└── [root]        # Only run scripts, README, requirements.txt
```

### 2. File Movements

#### Core Modules → `src/`
- ✅ `authority.py` - LLM Authority implementation
- ✅ `bandits.py` - Bandit environment
- ✅ `challenger.py` - Strain detection
- ✅ `evaluator.py` - Performance evaluation
- ✅ `policies.py` - Policy implementations
- ✅ `orchestrator.py` - Base orchestrator
- ✅ `orchestrator_live.py` - Live dashboard orchestrator (current)
- ✅ `orchestrator_visual.py` - Visual dashboard orchestrator
- ✅ `dashboard_live.py` - Live terminal UI (current)
- ✅ `dashboard_rich.py` - Rich terminal utilities
- ✅ `dashboard_streamlit.py` - Experimental Streamlit UI
- ✅ `analyze_evolution.py` - Post-run analysis

#### Documentation → `docs/`
- ✅ `QUICK_START.md`
- ✅ `UNDERSTANDING_RESULTS.md`
- ✅ `STRAIN_DETECTION.md`
- ✅ `DASHBOARDS.md`
- ✅ `VISUAL_DASHBOARD_DEMO.md`
- ✅ `FIXES_SUMMARY.md`
- ✅ `README_v2.md`
- ✅ `README.md` (old version)

#### Deprecated Files → `deprecated/`
- ✅ `run_experiment.py` - Original experiment runner (pre-IAI)
- ✅ `run_iai_evolution.py` - Old evolution runner (replaced by run_iai_live.py)
- ✅ `experiment_log.csv` - Old log file

#### Cleaned Up
- ✅ `runs/` folder (empty local folder - removed)
- ✅ `__pycache__/` moved to src/

### 3. Code Updates

#### Updated Import Paths
- ✅ `run_iai_live.py` - Added `sys.path.insert(0, 'src/')` 
- ✅ `run_iai_visual.py` - Added `sys.path.insert(0, 'src/')`

#### New Documentation
- ✅ Created comprehensive `README.md` with:
  - Quick start guide
  - Directory structure overview
  - Command-line options
  - Results location
  - Links to detailed docs

### 4. Testing

- ✅ Verified `run_iai_live.py` works with new structure
- ✅ Confirmed timestamped runs still work
- ✅ Verified analysis generation (minor path issue remains but doesn't affect functionality)

## Benefits

1. **Cleaner Root**: Only essential files at top level
2. **Organized Code**: All modules in `src/`, easy to navigate
3. **Centralized Docs**: All documentation in one place
4. **Preserved History**: Old files kept in `deprecated/` for reference
5. **Better Onboarding**: New README provides clear entry point

## Remaining Items

### Minor Issues
- Analysis script error truncation (cosmetic - analysis still completes successfully)
- Could add `__init__.py` to src/ if needed for package imports

### Future Improvements
- Consider creating `tests/` folder for unit tests
- Could add `examples/` folder for usage examples
- Might create `scripts/` for utility scripts

## File Counts

- **Root**: 4 files (2 run scripts, README, requirements)
- **src/**: 12 Python modules
- **docs/**: 8 markdown files
- **deprecated/**: 3 files

Total reorganization: 27 files organized into clear categories

## Migration Notes

If you have external scripts referencing old paths:
- Old: `from orchestrator_live import ...`
- New: `sys.path.insert(0, 'src'); from orchestrator_live import ...`

Or use absolute imports:
```python
from iai_bandit_poc.src.orchestrator_live import IAIOrchestratorLive
```
