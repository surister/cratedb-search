# CrateDB Hybrid Search specification.

Version = {PENDING}

This specification outlines a defined way of storing data in CrateDB for hybrid-search (vector + bm25).

If you follow the specification, you will automatically get full-text search, vector-search and
hybrid-search queries to work out of the box, as well as to be able to reuse components,
libraries and tooling based on the specification.

# Definitions.

* Implementor: The developer(s) that uses this specification to create a hybrid search application
with CrateDB.
* Specification: This document.
* vector-search: Search based on vectors, using the `KNN_MATCH` statement.
* full-text search: Search based on bm25, using `MATCH` statement.
* hybrid-search: vector-search + full-text search with re-ranking.

# Getting started

Data has to be conformed in a table that looks like this:

| column_name    | type               | nullable | note                       |
|----------------|--------------------|----------|----------------------------|
| hierarchy      | TEXT               | True     | optional                   |
| title_fs       | TEXT               | False    | has full-text index        |
| content_fs     | TEXT               | False    | has full-text index        |
| content_pretty | TEXT               | True     | optional                   |
| ref            | TEXT               | True     | optional                   |
| xs             | FLOAT_VECTOR(SIZE) | False    | max size is 2048           |   
| metadata       | OBJECT             | False    | optional, empty by default |
 

The DDL statement for the table is:

```sql
CREATE TABLE IF NOT EXISTS "doc"."search"
(
    "hierarchy"    TEXT NULL,
    "title_fs"     TEXT,
    "content_fs"   TEXT,
    "content_html" TEXT NULL,
    "ref_html"     TEXT,
    "metadata"     OBJECT,
    "xs"           FLOAT_VECTOR(2048)
)
```

# Fields

## hierarchy

The position of the content within the context of all the data. It will depend on the data.

Examples:

* A file 'myfile.parquet', hierarchy=`/data/production/products/sample/myfile.parquet`
* A html section 'PHONE 16GB RAM - 400€', hierarchy=`/offers/phones/newphones/phone-400`
* A district 'Leopoldstadt', hierarchy=`Europe-Austria-Vienna`

It is composed of elements joined by a character, it is recommended to use either `/` or `-`, but it
is
left to the implementor, as the end client can take care of any character by splitting the string.

## title_fs

The title of the content. It has a full-text index, the type of full-text index will depend on
the implementor use case.

The full-text search part of the hybrid search might be done in two different fields (title_fs and
content_fs)
to give more weight to title matches, if it makes sense for the implementor use case.

Examples:

* A file 'summer_products_2025.parquet', title=`Summer Products 2025`
* A html section 'PHONE 16GB RAM - 400€', title=`PHONE 16GB RAM - 400€`
* A district 'Leopoldstadt', title=`District of Leopoldstadt` or `Leopoldstadt`

## content_fs

The main content. It has a full-text index. It is the main data point to perform
full-text search against, the full-text part of the hybrid-search might be done
with this table and another one, like `title_fs`.

## content_pretty

The main content prettified for the end application. If the user is never meant to see the content, 
it must be null. 

Examples:
* Code that is formatted, where in `content_fs` is not formatted properly.
* HTML, where in `content_fs` is pure text, without html tags.

## ref

The reference to point the content

## xs

The vector representation of the content.



## More columns are needed

If more columns are needed, first consider using the `metadata` object if it is not enough, e.g.
new column with a full-text index is needed, consider opening an issue to improve the specification;
perhaps the use case was not taken into account. If the use case is too unique to be generalized,
it is ok to extend the specification.



NOTES:
Make hierarchy array(text)?