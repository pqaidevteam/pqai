# PQAI: API Usage Guide

[TOC]

## Introduction

PQAI API enables you to use the data and functionality of PQAI in a programmatic way.

You can use it to obtain patent data (only US patents as of now), run similarity searches, predict CPCs given some technical text, etc. This guide shows all you can do with it.

## Getting started

API access is provided as a part of PQAI+ subscription. Visit this page for more details: [Pricing](https://projectpq.ai/pricing).

Once you have an active subscription, you will see an API access token on your [account page](http://localhost:8555/account).

For academic and non-commercial usage, you can request a free API token by emailing [sam@projectpq.ai](mailto:sam@projectpq.ai). While requesting access, please provide a brief about your use case. We will send you an API token via email.

Once you haven an access token, you can begin using with the API. Some programming experience is needed to make use of this API.

## How to use the API?

### How to formulate requests?

Every request has to go to one of the API routes.

The endpoints are listed in the [next section](#Endpoints). Each route specifies some parameters. They can be of two types:

1. Path parameters
2. Query string parameters

**Path parameters** are part of the URL. In this guide, they are preceded by a colon in the route URL. For example, the route below is one for getting a patent drawing:

`/patents/:pn/drawings/:n`

It contains two parameters, `pn` and `n`. To make a request, we have to replace them (along with the preceding colons) with their values.

To get drawing #4 of patent no. US7654321B2, the route will become: `/patents/US7654321B2/drawings/4`.

By adding this route to the PQAI endpoint, which is `http://api.projectpq.ai`, you get the final URL:

https://api.projectpq.ai/patents/US7654321B2/drawings/4

(if you open the above route in your browser, you should see the drawing returned by the API - try changing the patent and drawing number to get a hang of it)

**Query string parameters** come after the URL and are separated from it with a `?` symbol.

Let's demonstrate with an example. There is another route in PQAI API similar to the one above. It returns thumbnails of drawings:

https://api.projectpq.ai/patents/US7654321B2/thumbnails/4

This route also accepts query string parameters. They are `w` and `h`, which specify the width and height of the thumbnail to be returned.

Let's try sending the `w` parameter with this route.

https://api.projectpq.ai/patents/US7654321B2/thumbnails/4?w=300

Note that query string parameters are sent by specifying their symbol, followed by `=` sign, and then followed by their value, which in this case, was 300.

To send multiple query string parameters, separate them with the `&` symbol, like so:

https://api.projectpq.ai/patents/US7654321B2/thumbnails/4?w=300&h=300

### How to send requests?

Most endpoints accept HTTP GET requests, which you can make by using an appropriate HTTP client in any programming language (e.g., Python, Javascript, etc.).

Since these are GET requests, they can also be made by typing in a URL in your browser. Example:

https://api.projectpq.ai/patents/US10112730B2/thumbnails/2?w=400

### How to use access token?

All requests (except a few, see note below) need to be authenticated with a `token` parameter, like so:

https://api.projectpq.ai/patents/US11154408B2?token=392cd21128f44cc496331c4c9c772b62

(note that the above request won't work because it uses a fake token)

Some requests, such as those for a patent drawing, do not require a token. In the next section, unless specified explicitly, the endpoint requires a valid token to be passed.

### How to process responses?

Most endpoints return JSON responses.

### How to make requests programmatically?

#### Python

Here is an example of making an API request in Python:

    :::python
    import requests
    
    token = "392cd21128f44cc496331c4c9c772b62" # fake; replace with yours
    endpoint = "https://api.projectpq.ai"      # address of the PQAI API
    route = "/search/102"                      # search route
    url = endpoint + route
    
    query = "a fire fighting drone" # search query (can be paragraph long)
    n = 10                          # no. of results to return
    result_type = "patent"          # exclude research papers
    after = "2016-01-01"            # return patents published post-2016
    
    params = {                      # create parameter object
        "q": query,
        "n": n,
        "type": result_type,
        "after": after,
        "token": token
    }
    response = requests.get(url, params=params)  # send the request
    assert response.status_code == 200           # error check
    
    results = response.json().get("results")     # decode response
    print(results)

#### Javascript

Here is the same example in Javascript:

    :::javascript
    var request = require('request');
    
    const endpoint = "https://api.projectpq.ai";
    const route = "/search/102";
    const url = endpoint + route;
    
    const qs = {
        q: "a fire fighting drone", // search query
        n: 10,                      // return 10 results
        type: "patent",             // exclude research papers
        after: "2016-01-01",        // return patents published post-2016
        token: "392cd21128f44cc496331c4c9c772b62" // fake; replace with yours
    }
    
    request({ url, qs }, (err, res, body) => {
        if(err) {
            console.log(err);
            return;
        }
        const results = JSON.parse(body).results;
        console.log(results);
    });

#### Browser

The same request can be made by going to the following URL (put together manually):

```
https://api.projectpq.ai/search/102?q=a%20fire%fighting%20drone&n=10&type=patent&after=2016-01-01&token=392cd21128f44cc496331c4c9c772b62
```

(note that the above URL as such will give you an Invalid Token error. To get it to work, you'd have to replace the fake token in it with a valid one. The [Getting Started](#Getting%20started) section above describes how to get an access token.)

## Routes

###  1. Retrieve prior-art documents with text query

Route: `/search/102/`

Query string parameters

| Parameter | Value   | Meaning                               | Example                              |
| --------- | ------- | ------------------------------------- | ------------------------------------ |
| `q`       | String  | Query                                 | `"fire fighting drone"`              |
| `lq`      | String  | Latent query                          | `{"relevant": [], "irrelevant": []}` |
| `n`       | Integer | No. of results                        | `10`                                 |
| `offset`  | Integer | Pagination offset (0-indexed)         | `10` (for skipping first 10 results) |
| `index`   | String  | CPC subclass                          | `"H04W"` (`"auto"` for auto-select)  |
| `cc`      | String  | Comma-separated list of country codes | `"US,EP,WO"`                         |
| `after`   | String  | Cutoff date 1                         | `"2006-01-01"`                       |
| `before`  | String  | Cutoff date 2                         | `"2019-12-31"`                       |
| `type`    | String  | Document type                         | `"patent"` or `"npl"`                |
| `snip`    | Boolean | Include snippets                      | `1` or `0`                           |
| `maps`    | Boolean | Include element-wise mapping          | `1` or `0`                           |

Latent query parameter `lq` has to be a valid JSON string description of an object with two keys: `relevant` and `irrelevant`, each of which, when present, must be a list of patent numbers. This parameter can be used to influence the search by providing positive or negative feedback.

###  2. Retrieve prior-art combinations with text query

Route: `/search/103/`

Parameters: [Same as for `/search/102/` route]

###  3. Retrieve prior-art for a patent  (documents published before the filing date)

Route: `/prior-art/patent/`

Query string parameters

| Parameter | Value   | Meaning                       | Example                              |
| --------- | ------- | ----------------------------- | ------------------------------------ |
| `pn`      | String  | Publication number            | `"US7654321B2"`                      |
| `n`       | Integer | No. of results                | `10`                                 |
| `offset`  | Integer | Pagination offset (0-indexed) | `10` (for skipping first 10 results) |
| `index`   | String  | CPC subclass                  | `"H04W"` (`"auto"` for auto-select)  |
| `type`    | String  | Document type                 | `"patent"` or `"npl"`                |

###  4. Retrieve similar documents to a patent

Route: `/similar/`

Parameters: [Same as `/prior-art/patent/` route]

###  5. Retrieve snippet for a query-document pair

Route: `/snippets/`

Query string parameters:

| Parameter | Value  | Meaning            | Example          |
| --------- | ------ | ------------------ | ---------------- |
| `q`       | String | Text query         | `"drone"`        |
| `pn`      | String | Publication number | `"US10112730B2"` |

###  6. Retrieve element-wise mapping for a query-document pair

Route: `/mappings/`

Parameters: [Same as `/snippets/` route]

###  7. Retrieve a sample from a dataset

Route: `/datasets/`

Query string parameters

| Parameter | Value   | Meaning       | Example |
| --------- | ------- | ------------- | ------- |
| `n`       | Integer | Sample number | `23`    |
| `dataset` | String  | Dataset name  | `"PoC"` |

###  8. Retrieve a document from PQAI database

Route: `/documents/`

Query string parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `id`      | String  | Document ID   | `US7654321B2` |

###  9. Get a patent drawing

Route: `/patents/:pn/drawings/:n`

Response type: `PNG` image (binary)

NOTE: Authentication token is NOT required for this route.

Path parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `pn`      | String  | Patent Number | `US7654321B2` |
| `n`       | Integer | Drawing index | `3`           |

Query string parameters

| Parameter | Value   | Meaning | Example |
| --------- | ------- | ------- | ------- |
| `w`       | Integer | Width   | `300`   |
| `h`       | Integer | Height  | `300`   |

We suggest you pass *only one* of the parameters `w` and `h` - if you pass both and their values are not appropriately set, the drawing may appear stretched along the horizontal or vertical direction (example: [accurate](https://api.projectpq.ai/patents/US10112730B2/thumbnails/2?w=400), [distorted](https://api.projectpq.ai/patents/US10112730B2/thumbnails/2?w=400&h=200)).

###  10. Get list of drawings for a patent (to tell how many drawings are there)

Route: `/patents/:pn/drawings`

NOTE: Authentication token is NOT required for this route.

Path parameters

| Parameter | Value   | Meaning       | Example       |
| --------- | ------- | ------------- | ------------- |
| `pn`      | String  | Patent Number | `US7654321B2` |

### 11. Get list of thumbnails available for a patent

Route: `/patents/:pn/thumbnails`

NOTE: Authentication token is NOT required for this route.

Path parameters

| Parameter | Value  | Meaning       | Example       |
| --------- | ------ | ------------- | ------------- |
| `pn`      | String | Patent Number | `US7654321B2` |

### 12. Get a thumbnail of a patent's drawing

Route: `/patents/:pn/thumbnails/:n`

NOTE: Authentication token is NOT required for this route.

Response type: `PNG` image (binary) 

Path parameters

| Parameter | Value   | Meaning                                | Example       |
| --------- | ------- | -------------------------------------- | ------------- |
| `pn`      | String  | Patent Number                          | `US7654321B2` |
| `n`       | Integer | Thumbnail (drawing) index              | `3`           |
| `h`       | Integer | Thumbnail height (in pixels, optional) | `300`         |
| `w`       | Integer | Thumbnail width (in pixels, optional)  | `400`         |

We suggest you pass *only one* of the parameters `w` and `h` - if you pass both and their values are not appropriately set, the drawing may appear stretched along the horizontal or vertical direction (example: [accurate](https://api.projectpq.ai/patents/US10112730B2/thumbnails/2?w=400), [distorted](https://api.projectpq.ai/patents/US10112730B2/thumbnails/2?w=400&h=200)).

### 13. Get a patent's data

Route: `/patents/:pn`

Path parameters

| Parameter | Value  | Meaning       | Example       |
| --------- | ------ | ------------- | ------------- |
| `pn`      | String | Patent Number | `US7654321B2` |

### 14. Get a patent's vector

Route: `/patents/:pn/vectors/:field`

Path parameters

| Parameter | Value  | Meaning          | Example              |
| --------- | ------ | ---------------- | -------------------- |
| `pn`      | String | Patent Number    | `US7654321B2`        |
| `field`   | String | Field vectorized | `cpcs` or `abstract` |


### 15. Suggest CPCs for a text excerpt

Route: `/suggest/cpcs`

Query string parameters

| Parameter | Value  | Meaning      | Example                     |
| --------- | ------ | ------------ | --------------------------- |
| `text`    | String | Text Excerpt | `fire fighting drones`      |

### 16. Suggest Group Art Units for a text excerpt

Route: `/predict/gaus`

Query string parameters

| Parameter | Value  | Meaning      | Example                     |
| --------- | ------ | ------------ | --------------------------- |
| `text`    | String | Text Excerpt | `fire fighting drones`      |

### 17. Get definition of a CPC class

Route: `/definitions/cpcs`

Query string parameters

| Parameter | Value  | Meaning    | Example     |
| --------- | ------ | ---------- | ----------- |
| `cpc`     | String | A CPC code | `H04W52/02` |

### 18. Get API documentation

Route: `/docs`

Response type: `HTML` string

Parameters: None required