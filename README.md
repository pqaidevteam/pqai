# PQAI: Patent Quality through AI

An open-source AI-powered search engine for running prior-art checks.

PQAI takes plain language invention description as input and finds similar prior work within patents and research articles. It uses machine learning models trained on patent examination data of the USPTO.

## Website

Use the web-app [projectPQ.ai](https://projectpq.ai/search) if you want to run prior-art searches.

## API Access

###  1. Retrieve prior-art documents with text query

     Route: `/documents/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters

     | Parameter | Value   | Meaning                      | Example                             |
     | --------- | ------- | ---------------------------- | ----------------------------------- |
     | `q`       | String  | Query                        | `"fire fighting drone"`             |
     | `lq`      | String  | Latent query                 | `"unmanned"`                        |
     | `n`       | Integer | No. of results               | `10`                                |
     | `index`   | String  | CPC subclass                 | `"H04W"` (`"auto"` for auto-select) |
     | `after`   | String  | Cutoff date 1                | `"2006-01-01"`                      |
     | `before`  | String  | Cutoff date 2                | `"2019-12-31"`                      |
     | `type`    | String  | Document type                | `"patent"` or `"npl"`               |
     | `snip`    | Boolean | Include snippets             | `1` or `0`                          |
     | `maps`    | Boolean | Include element-wise mapping | `1` or `0`                          |

###  2. Retrieve prior-art combinations with text query

     Route: `/combinations/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters: [Same as for `/document/` route]

###  3. Retrieve prior-art for a patent  (documents published before the filing date)

     Route: `/prior-art/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters

     | Parameter | Value  | Meaning            | Example         |
     | --------- | ------ | ------------------ | --------------- |
     | `pn`      | String | Publication number | `"US7654321B2"` |

###  4. Retrieve similar documents to a patent

     Route: `/combinations/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters: [Same as `/prior-art/` route]

###  5. Retrieve snippet for a query-document pair

     Route: `/snippets/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters:

     | Parameter | Value  | Meaning            | Example          |
     | --------- | ------ | ------------------ | ---------------- |
     | `q`       | String | Text query         | `"drone"`        |
     | `pn`      | String | Publication number | `"US10112730B2"` |

###  6. Retrieve element-wise mapping for a query-document pair

     Route: `/mappings/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters: [Same as `/snippets/` route]

###  7. Retrieve a sample from a dataset

     Route: `/datasets/`

     Request type: `GET`

     Response type: `JSON` string

     Request parameters

     | Parameter | Value   | Meaning       | Example |
     | --------- | ------- | ------------- | ------- |
     | `n`       | Integer | Sample number | `23`    |
     | `dataset` | String  | Dataset name  | `"PoC"` |

## License

The project is licensed under the [TBD] license.

## Support

Please create an issue if you need help.

## Contribute

We welcome your contributions.

## Contact

Please send your queries to [samzellner@gmail.com](samzellner@gmail.com)