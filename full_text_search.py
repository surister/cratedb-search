import pathlib

import uuid

import polars
from docutils.core import publish_doctree

CRATE_URI = 'crate://192.168.88.251:4200'
CONTAINER_NODES = ['section', 'note', 'bullet_list', 'rubric', 'topic']
IGNORED_NODES = ['system_message', 'target', 'rubric', 'topic', 'figure']
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


def create_indexes(table_name: str, doc_path: pathlib.Path, final_url: str = ''):
    if doc_path.is_dir() and not doc_path.name.startswith(
            '_') and doc_path.name not in DOC_PATH_BLACKLIST:

        for dir in doc_path.iterdir():
            create_indexes(table_name, doc_path / dir.name, final_url + '/' + dir.name)

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
        uuids = [str(uuid.uuid4()) for _ in range(len(df))]
        df = df.with_columns(polars.Series('uuid', uuids))
        df.write_database(table_name, CRATE_URI, if_table_exists='append')


def parse_section(section, result=None, current_section=None, depth=1):
    if not result:
        result = []

    if not current_section:
        current_section = {
            'section_depth': depth,
            'title': None,
            'ref': None,
            'content': ''
        }
    if hasattr(section, 'expect_referenced_by_id'):
        current_section['ref'] = tuple(section.expect_referenced_by_id.keys())[0]

    for sub_node in section.children:
        sub_node_type = sub_node.__class__.__name__

        if sub_node_type in ['system_message']:
            return

        if sub_node_type == 'title':
            current_section['title'] = sub_node.astext()

        elif sub_node_type == 'section':
            r = parse_section(sub_node, None, None, depth=depth + 1)
            if r:
                result.extend(r)

        else:
            current_section['content'] += sub_node.astext()

    result.append(current_section)
    return result


def traverse_nodes(node, result=None):
    if not result:
        result = {
            'title': None,
            'ref': None,
            'sections': []
        }

    node_type = node.__class__.__name__
    if node_type in ['system_message']:
        return

    if hasattr(node, 'expect_referenced_by_id'):
        result['ref'] = tuple(node.expect_referenced_by_id.keys())[0]

    if not result['title'] and node_type == 'title':
        result['title'] = node.astext()

    if node_type == 'section':
        r = parse_section(node)
        if r:
            result['sections'].extend(parse_section(node))

    else:
        for node in node.children:
            traverse_nodes(node, result)

    return result


if __name__ == '__main__':
    # Change this path to the location of the crate docs.
    path_iter = pathlib.Path('/home/surister/PycharmProjects/crate/crate/docs/')
    t = publish_doctree(pathlib.Path(
        '/home/surister/PycharmProjects/crate/crate/docs/general/builtins/scalar-functions.rst'
    ).read_text())
