# Set up a fresh instance of PQAI
#
# This includes setting up:
#     1. Python environment
#     2. Mongo DB bibliography database
#     3. Downloading assets (models, etc.) from S3
#     4. A sample index (for testing)
#
# Run this with `bash scripts/setup.sh` from the `pqai/` directory
# You might need to give this executable permission prior to running:
# `sudo chmod +x scripts/setup.sh`
#
# After this script executes successfully, configure `.env` (using `pqai/env`
# as a template) and then run `python server.py` (or build docker image - for
# that, see `pqai/README.md`)

conda create --name pqai python=3.8
conda activate pqai
sudo apt-get update && apt-get install gcc g++ -y
sudo apt-get install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 -y
pip install -r requirements.txt

curl -o assets.zip "https://s3.amazonaws.com/pqai.s3/public/pqai-assets-latest.zip"
unzip assets.zip -d models/
rm assets.zip

curl -o mongodump.tar.gz "https://s3.amazonaws.com/pqai.s3/public/pqai-mongo-dump.tar.gz"
tar -x --use-compress-program=pigz -f mongodump.tar.gz
mongorestore

curl -o index.zip "https://s3.amazonaws.com/pqai.s3/public/sample-index.zip"
unzip index.zip -d indexes/
rm index.zip
