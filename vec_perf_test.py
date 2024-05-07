from crate import client as crate

def insert():
    q = "insert into tlb39 values ('data')"
    cursor = connection.cursor()
    cursor.execute(q)
    cursor.close()


def insert_vectors_to_cratedb(connection,
                              table_name: str,
                              vector_column_name: str,
                              data: list) -> None:
    query = f"""INSERT INTO {table_name}({vector_column_name}) VALUES (?)"""
    cursor = connection.cursor()
    cursor.execute(query, bulk_parameters=data)
    cursor.close()


connection = crate.connect('http://192.168.88.251:4200')

for i in range(15000):
    vector = [.1] * 1500
    insert_vectors_to_cratedb(connection, 'vec_jobs_test', 'xs', [(vector,),])
