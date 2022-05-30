"""Unit test package for ipyrun."""

import pathlib
import sys

FDIR_ROOT = pathlib.Path(__file__).parents[1]
FDIR_SRC = FDIR_ROOT / "src"
sys.path.append(str(FDIR_SRC)) # append ipyautoui source
# ^ for DEV only. comment out at build time.