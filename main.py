import os

from openai import OpenAI
from crate import client as crate
from embeddings.openai import get_embedding
from embeddings.io import insert_vectors_to_cratedb, get_indexes, knn_search

token = os.getenv('OPENAITOKEN')
client = OpenAI(api_key=token)

connection = crate.connect('http://192.168.88.251:4200')
indexes = get_indexes(connection, 'fs_search5')

query = 'knn search vectors'
embedding = get_embedding(query, token=token)

# Should probably bulk create.
for i in indexes:
    print(f'Creating indexes for {i}')
    response = client.embeddings.create(
        input=i[1],
        model="text-embedding-3-large",
        dimensions=2048
    )
    print('Got')
    print(response.data)

    print('Inserting to CrateDB')
    insert_vectors_to_cratedb(
        connection,
        'fs_vec_big2',
        'fs_search_id',
        'xs',
        [
            (i[0], response.data[0].embedding),
        ]
    )
