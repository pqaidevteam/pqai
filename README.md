# PQAI: Patent Quality through AI

An AI-powered tool for running prior-art checks.

PQAI takes plain language invention description as input and finds similar prior work within patents and research articles. It uses a number of ML models to parse the input, find similar prior-art, and present the results. The models have been trained on publicly available patent examination records of USPTO.

## Web-app

Use [projectPQ.AI](https://projectpq.ai/search) to run prior-art searches.

## API Access

PQAI can be plugged into other apps easily through API integration. Refer to the [API Usage Guide](docs/README-API.md) for details.

## Create your own PQAI server

You would need the following:

1. PQAI code: clone this repository
2. ML models: download and extract the [models](https://s3.amazonaws.com/pqai.s3/public/pqai-models-2020-12-10.zip) to the `./models/` directory in the cloned repository.
3. A database of prior-art documents
4. Searchable indexes: create using `indexes` module.

## License

The project is licensed under the MIT license.

## Support

Please create an issue if you need help.

## Contribute

We welcome contributions. Please take a look at our contributions guide.

## Contact

Write to [sam@projectpq.ai](sam@projectpq.ai)