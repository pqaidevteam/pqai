# Core Modules

## API

Handles the API requests by composition of and orchestrating functionality of other core modules.

## Classifiers

Models that assign labels to inputs, e.g., assigning a CPC subclass to a piece of text.

## Datasets

Wrappers over datasets, modeled as collection of samples.

## DB, Storage

Contains methods for obtaining documents (e.g., patents) from the underlying storage (e.g., database or a flat directory of JSON documents).

## Documents

Defines classes for modeling and interacting with documents, e.g., patents.

## Encoders

Encoders transform a piece of information from one format to another, e.g., a text query into a query vector.

## Filters

Wrappers for search filters, e.g., date filters.

## Highlighter

Decides and highlights certain keywords in a search result snippet.

## Index Selection

Selects indexes to search for a given query adaptively on the basis of the query's content.

## Indexer, Indexes

Unified wrappers for interacting with indexes, e.g., vector indexes.

## Obvious

Handles 103 combinations of documents

## Remote

Handles retrieval and collation of results from other PQAI servers (extensions).

## Representations

Wrappers over various representations of information, e.g., vectors, bag of words, etc.

## Reranking

Models for reranking, that take as input a set of documents and ranks them on the basis of their extent of similarity to a query.

## Results

Models search results

## Search

Runs a query through specified indexes

## Utils

General purpose utility functions

## Vectorizers

A special type of encoders that embed entities (e.g, query, text, or CPC class) into a vector space