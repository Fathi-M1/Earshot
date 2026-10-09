# design/_src — regenerate the brand kit
Run from this folder's parent repo copy (needs Python 3 + Pillow/numpy/scipy/fontTools/potracer + Chrome):
1. `python trace.py` — traces `flat.png` (the source logo) into `paths.json` (potrace, smooth beziers).
2. `python wordmark.py <name>` — outlines the wordmark in Host Grotesk 500 → `wordmark.json`.
3. `BRAND_NAME=<name> python build.py` — writes logo/lockup/icon SVGs, tile HTML, tokens.json (brand.name).
4. `python sheet.py`, `python mock.py`, then render with `shot.sh` (headless Chrome).
Rename to Kinig: `python wordmark.py kinig && BRAND_NAME=kinig python build.py && python sheet.py && python mock.py` and re-render.
Paths in the scripts assume they're run from a sibling build folder (`../earshot-docs/design`); adjust `D=` if needed.
