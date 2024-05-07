def insert_vectors_to_cratedb(connection,
                              table_name: str,
                              id_column_name: str,
                              vector_column_name: str,
                              data: list) -> None:
    query = f"""INSERT INTO {table_name}({id_column_name},{vector_column_name}) VALUES (?, ?)"""
    cursor = connection.cursor()
    cursor.execute(query, bulk_parameters=data)
    cursor.close()


def get_indexes(connection, table_name: str):
    query = f"SELECT uuid, content FROM {table_name}"
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def knn_search(connection, table_name, vec_column_name, vec, n_results=10):
    query = f"""
        SELECT source_id, _score FROM {table_name} WHERE knn_match({vec_column_name}, {vec}, {n_results}) ORDER BY _score DESC;
    """
    # 189k tokens
    # $0.02 / 1M tokens
    # 0.0004€ -> 189k tokens
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()
