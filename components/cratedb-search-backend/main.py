import os
import time
from typing import Union, List
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from crate import client

app = FastAPI()

origins = ['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins
)

token = os.getenv('OPEN_AI_TOKEN')


def run_stmt(stmt: str, connection: str = '192.168.88.251:4200') -> list:
    cursor = client.connect(connection).cursor()
    cursor.execute(stmt)
    return cursor.fetchall()


def get_embedding(content: str,
                  token: None | str,
                  model="text-embedding-3-large") -> list[float]:
    client = OpenAI(api_key=token)
    response = client.embeddings.create(
        input=content,
        model=model,
        dimensions=2048
    )
    return response.data[0].embedding


def get_embedding_or_create(search_terms: str) -> (bool, list[float]):
    """Checks if the vector exists in the """
    result = run_stmt(f"select xs from vector_cache where search_terms = '{search_terms}'")

    if result:
        return True, result[0][0]

    vector = get_embedding(search_terms, token=os.getenv('OPENAI_TOKEN'))
    run_stmt(f"insert into vector_cache values ('{search_terms}', {vector})")
    return False, vector

def hybrid_search_query(search_term: str, vector: list[float]) -> list:
    query = f"""
    WITH 
        bm25 as (
      SELECT
        _score,
        RANK() OVER (
          ORDER BY
            _score DESC
        ) as rank,
        *
      FROM
        search3
      WHERE
        metadata['adult'] = false and
        MATCH("title_fs", '{search_term}')
      ORDER BY
        _score DESC
    ),
    vector as (
      SELECT
        _score,
        RANK() OVER (
          ORDER BY
            _score DESC
        ) as rank,
        id
      FROM
        search3
      WHERE
      metadata['adult'] = false and
        KNN_MATCH(
          xs,
          {vector},
          15
        )
    )
    SELECT
      TRUNC((1.0 / (bm25.rank + 60)) + (1.0 / (vector.rank + 60)), 6) as final_rank,
--       bm25.rank as bm25_rank,
--       vector.rank as vector_rank,
      bm25.id,
      bm25.hierarchy,
      bm25.title_fs,
      bm25.content_fs,
      bm25.content_pretty,
      bm25.ref,
      bm25.metadata
    FROM
      bm25,
      vector
    WHERE
      bm25.id = vector.id
    ORDER BY final_rank DESC
    LIMIT 15
        """
    return run_stmt(query)


@app.get("/search/hybrid")
def hybrid_search(search_term: str):
    t = time.time()
    created, vector = get_embedding_or_create(search_term)
    result = hybrid_search_query(search_term, vector)
    return {'result': result, 'query_time': time.time() - t}
