import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TEST'] = "1"

import sys
from pathlib import Path
from dotenv import load_dotenv

TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_PATH = "{}/.env".format(BASE_DIR)

load_dotenv(ENV_PATH)

sys.path.append(BASE_DIR)
