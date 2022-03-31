# PQAI: Patent Quality Artificial Intelligence

An AI-powered tool for running prior-art checks.

PQAI takes plain language invention description as input and finds similar prior work within patents and other technical literature. It uses a number of machine learning (ML) models to parse the input, find similar prior-art, and present the results. The ML models of PQAI have been trained on past patent examination records.

![PQAI Architecture](docs/architecture.png)

## Web-app

Use [search.projectpq.ai](https://search.projectpq.ai) to run prior-art searches.

## API Access

PQAI can be plugged into other apps easily through API integration. Refer to the [API Usage Guide](docs/README-API.md) for details.

## Create your own PQAI server

You would need the following:

1. PQAI code: clone this repository
2. ML models: download and extract the [models](https://s3.amazonaws.com/pqai.s3/public/pqai-assets-latest.zip) to the `./models/` directory in the cloned repository.
3. A database of prior-art documents
4. Searchable indexes: create using `indexes` module.

## License

The project is open-source under the MIT license.

## Support

Please create an issue if you need help.

## Contribute

We welcome contributions. Please take a look at our [guidelines](./CONTRIBUTING.md) to understand how you can contribute to PQAI.

## Contact

Write to [sam@projectpq.ai](sam@projectpq.ai)
