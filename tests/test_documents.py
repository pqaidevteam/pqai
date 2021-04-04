import unittest

# Run tests without using GPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TEST'] = "1"

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)


if __name__ == '__main__':
    unittest.main()