[TOC]

# API Usage Guide

## Authentication

A `token` parameter is used for authentication, which must be included in every request, except for requests where it is explicitly stated that it isn't need.

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
| `offset`  | Integer | Pagination offset (0-indexed)| `10` (for skipping first 10 results)|
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

Request parameters: [Same as for `/search/102/` route]

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

###  9. Get a patent drawing

Route: `/patents/:pn/drawings/:n`

Request type: `GET`

Response type: `PNG` image (binary)

Path parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `pn`      | String  | Patent Number | `US7654321B2` |
| `n`       | Integer | Drawing index | `3`           |

NOTE: Authentication token is NOT required for this route.

###  10. Get list of drawings for a patent (to tell how many drawings are there)

Route: `/patents/:pn/drawings`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `pn`      | String  | Patent Number | `US7654321B2` |

NOTE: Authentication token is NOT required for this route.

### 11. Get list of thumbnails available for a patent

Route: `/patents/:pn/thumbnails`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning       | Example       |
| --------- | ------ | ------------- | ------------- |
| `pn`      | String | Patent Number | `US7654321B2` |

NOTE: Authentication token is NOT required for this route.

### 12. Get a thumbnail of a patent's drawing

Route: `/patents/:pn/thumbnails/:n`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value   | Meaning                   | Example       |
| --------- | ------- | ------------------------- | ------------- |
| `pn`      | String  | Patent Number             | `US7654321B2` |
| `n`       | Integer | Thumbnail (drawing) index | `3`           |

NOTE: Authentication token is NOT required for this route.

### 13. Get a patent's data

Route: `/patents/:pn`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning       | Example       |
| --------- | ------ | ------------- | ------------- |
| `pn`      | String | Patent Number | `US7654321B2` |

### 14. Get a patent's field (title, abstract, claims, etc.)

Route: `/patents/:pn/:field`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning        | Example                                                   |
| --------- | ------ | -------------- | --------------------------------------------------------- |
| `pn`      | String | Patent Number  | `US7654321B2`                                             |
| `field`   | String | Patent's field | `title`, `abstract`, `claims`, `description`, `citations` |

**NOTES**

* The `/claims` route can also take a suffix path parameter `/n` that can be used to fetch a particular claim. For example, the first claim can be retrieved with `/claims/1`.
* The `/claims` route can also take a suffix path parameter `/independent` to get only independent claims.
* The `/abstract` and `/description` routes can take a suffix path parameter `/concepts` that will return the entities identified by an ML model within these text fields.
* The `/citation` route takes suffix path parameters `/backward` and `/forward` to return only one cited or citing patents.

### 15. Get a patent's CPCs

Route: `/patents/:pn/classification/cpcs`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning       | Example       |
| --------- | ------ | ------------- | ------------- |
| `pn`      | String | Patent Number | `US7654321B2` |

### 16. Get a patent's vector

Route: `/patents/:pn/vectors/:field`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning          | Example              |
| --------- | ------ | ---------------- | -------------------- |
| `pn`      | String | Patent Number    | `US7654321B2`        |
| `field`   | String | Field vectorized | `cpcs` or `abstract` |

### 17. Get a word (concept) vector

Route: `/concepts/:concept/vector`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning    | Example                     |
| --------- | ------ | ---------- | --------------------------- |
| `concept` | String | Given word | `vehicle` or `mobile phone` |

### 18. Get contextually similar words to a given word

Route: `/concepts/:concept/similar`

Request type: `GET`

Response type: `JSON` string

Path parameters

| Parameter | Value  | Meaning    | Example                     |
| --------- | ------ | ---------- | --------------------------- |
| `concept` | String | Given word | `vehicle` or `mobile phone` |

### 19. Get API documentation

Route: `/docs`

Request type: `GET`

Response type: `HTML` string

Parameters: None