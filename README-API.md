# API Usage Guide

## Authentication

A `token` parameter is used for authentication, which must be included in
every request.

## API Routes

###  1. Retrieve prior-art documents with text query

Route: `/search/102/`

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

Route: `/search/103/`

Request type: `GET`

Response type: `JSON` string

Request parameters: [Same as for `/document/` route]

###  3. Retrieve prior-art for a patent  (documents published before the filing date)

Route: `/prior-art/patent/`

Request type: `GET`

Response type: `JSON` string

Request parameters

| Parameter | Value  | Meaning            | Example         |
| --------- | ------ | ------------------ | --------------- |
| `pn`      | String | Publication number | `"US7654321B2"` |

###  4. Retrieve similar documents to a patent

Route: `/similar/`

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

###  8. Retrieve a document from PQAI database

Route: `/documents/`

Request type: `GET`

Response type: `JSON` string

Request parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `id`      | String  | Document ID   | `US7654321B2` |