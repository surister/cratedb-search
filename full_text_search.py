import pathlib

import polars
from docutils.core import publish_doctree

CRATE_URI = 'crate://192.168.88.251:4200'
CONTAINER_NODES = ['section', 'note', 'bullet_list', 'rubric', 'topic']
IGNORED_NODES = ['system_message', 'target', 'rubric', 'topic']
DOC_PATH_BLACKLIST = ['appendices']


class Node:
    def __init__(self, type: str):
        self.type = type
        self.children = []

    def append_child(self, child) -> None:
        self.children.append(child)

    def is_container(self):
        return self.type in CONTAINER_NODES

    def __iter__(self):
        return iter(self.children)

    def __repr__(self):
        return f'Node<{self.type}>{self.children if self.children else ""}'


def traverse(node, parent_node, container_nodes, ignored_nodes) -> None:
    """
    Traverses a docutils doctree and creates a flatter graph.

    `container_nodes` is used to specify which nodes will be used to contain other nodes.

    """
    node_type = node.__class__.__name__

    if node_type not in ignored_nodes:
        if node_type != 'document':
            new_node = Node(node_type)
            new_node.content = getattr(node, 'rawsource', None)
            parent_node.append_child(new_node)

        if node_type in container_nodes or node_type == 'document':
            new_parent_node = parent_node

            if node_type in container_nodes:
                new_parent_node = new_node

            for sub_node in node:
                traverse(sub_node, new_parent_node, container_nodes, ignored_nodes)


def node_to_index(node, result=None, extra_attrs: dict = None) -> tuple:
    """
    Iterates a Node and returns a flat tuple representation of all the nodes.

    `extra_attrs` will be added to every tuple.

    Return example:
    [
        ('title', 'Aggregation'), ('paragraph', 'When selecting data you should do...')
    ]

    Note:
    This return format is prime for being used in `INSERT INTO tbl VALUES (?)`
    """
    if result is None:
        result = []

    for child_node in node:
        if child_node.is_container():
            node_to_index(child_node, result, extra_attrs)

        else:
            result.append(
                (child_node.type, child_node.content, *extra_attrs.values())
            )

    return result


def create_indexes(doc_path, final_url: str = ''):
    if doc_path.is_dir() and not doc_path.name.startswith(
            '_') and doc_path.name not in DOC_PATH_BLACKLIST:

        for dir in doc_path.iterdir():
            create_indexes(doc_path / dir.name, final_url + '/' + dir.name)

    if doc_path.suffix == '.rst' and doc_path.name != 'index':
        node = Node('document')

        traverse(
            publish_doctree(pathlib.Path(doc_path).read_text()),
            node,
            CONTAINER_NODES,
            IGNORED_NODES
        )

        tuples = node_to_index(
            node,
            extra_attrs={
                'root': final_url.replace(".rst", "").split('/')[1],
                'sub_root': final_url.replace(".rst", "")
            })
        df = polars.DataFrame(tuples, schema=['type', 'content', 'root', 'sub_root'], orient='row')

        df.write_database('test_search2', CRATE_URI, if_table_exists='append')


if __name__ == '__main__':
    # Change this path to the location of the crate docs.
    path_iter = pathlib.Path('/home/surister/PycharmProjects/crate/crate/docs')
    create_indexes(path_iter)
