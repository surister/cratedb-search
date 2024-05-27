import pathlib

import polars
from docutils.core import publish_doctree

CRATE_URI = 'crate://192.168.88.251:4200'


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
            continue

        if sub_node_type == 'title':
            if 'blocks.read_only_allow_delete' in sub_node.astext():
                print()
            current_section['title'] = sub_node.astext()

        elif sub_node_type == 'section':
            r = parse_section(sub_node, None, None, depth=depth + 1)
            if r:
                result.extend(r)
        elif sub_node_type == 'bullet_list':
            for bullet_item in sub_node.children:
                current_section['content'] += f'\n* {getattr(bullet_item, "rawsource", None)}'
        else:
            current_section['content'] += f'{getattr(sub_node, "rawsource", None)}'
    result.append(current_section)
    return result


def traverse_nodes(node, result=None):
    # Traverse nodes with
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
            result['sections'].extend(r)

    else:
        for node in node.children:
            traverse_nodes(node, result)

    return result


if __name__ == '__main__':
    TABLE_NAME = 'fs_search3'
    # Change this path to the location of the crate docs.
    docs_path = pathlib.Path('/home/surister/PycharmProjects/crate/crate/docs/')
    docs_path_len = len(docs_path.parts)

    files = docs_path.rglob('*.rst')
    IGNORED_DIRECTORIES = 'release-notes'

    for file in files:
        if IGNORED_DIRECTORIES not in file.parts:
            parts = list(file.parts[docs_path_len:])
            root = parts[0]
            file_name = file.name
            parts.remove(file_name)

            metadata = {
                'root': root,
                'sub_root': "/".join(parts),
                'file_name': file_name
            }

            t = publish_doctree(file.read_text())
            res = traverse_nodes(t)
            res['metadata'] = metadata

            for section in res['sections']:
                section['metadata'] = metadata
                df = polars.DataFrame(section, schema_overrides={'metadata': polars.Object})
                df.write_database(TABLE_NAME, CRATE_URI, if_table_exists='append')

    # Use this to debug one single page.
    # t = publish_doctree(pathlib.Path(
    #     '/home/surister/PycharmProjects/crate/crate/docs/sql/statements/create-table.rst'
    # ).read_text())
    #
    # res = traverse_nodes(t)
