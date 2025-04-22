import json
import os
import pathlib

from crate import client as crate_client
from bs4 import BeautifulSoup, Tag, NavigableString
from openai import OpenAI

# Structure of a parsed section:
# parsed_section = {
#     'ref': '',
#     'main_section_title': '',
#     'title': '',
#     'content': '',
#     'content_html': '',
#     'metadata': {
#         'file_name': '',
#         'root': '',
#         'sub_root': ''
#     }
# }


token = os.getenv('OPENAITOKEN', os.getenv('OPEN_AI_TOKEN'))
client = OpenAI(api_key=token)
connection = crate_client.connect('http://192.168.88.251:4200')


def clean_text(text: str, remove_text: str = ''):
    if remove_text:
        text = text.replace(remove_text, '')
    return text.replace('¶', '')


def get_all_siblings(tag: Tag):
    """
    Get all sibling elements until the next section is reached, for now we also ignore the rubric
    """
    siblings = []
    next_siblings = tag.find_next_siblings()

    for sibling in next_siblings:
        if 'class' in sibling.attrs and (
                'section' in sibling.attrs['class'] or 'rubric' in sibling.attrs['class']):
            break

        sibling.insert(0, NavigableString('\n'))
        siblings.append(sibling)

    return siblings


def get_section(tag: Tag, parent_sections: list, soup):
    if parent_sections is None:
        parent_sections = []

    section_title = clean_text(tag.text)

    siblings = get_all_siblings(tag)

    section_description = soup.new_tag('div')

    for sibling in siblings:
        sibling.wrap(section_description)

    ref = tag.parent.attrs['id']
    return {
        'level': int(tag.name.replace('h', '')),
        'ref': ref,
        'ignore_this_section_hierarchy': "&_&".join(parent_sections),
        'title': clean_text(section_title),
        'content': clean_text(
            (
                section_description
                .text
                .replace('\n' * 3, '\n')
                .replace('\n' * 2, '\n')
                .replace('\n' * 1, ' ')
                .lstrip()
                .rstrip()
            )
        ) if section_description is not None else None,
        'content_html': str(section_description) if section_description is not None else None,
    }


def parse_html(html: str):
    parsed_sections = []
    soup = BeautifulSoup(html, features='html.parser')

    # The main section of the page, without the top bar, footer, left navigation...
    main_section = soup.find('div', attrs={'class': 'wrapper-content-right'}).find('div', attrs={
        'class': 'section'})

    h1 = main_section.find('h1')
    main_section_title = clean_text(h1.text)

    section = get_section(
        h1,
        None,
        soup
    )

    parsed_sections.append(section)

    # All sections under the main section.
    all_sections = main_section.find_all('div', attrs={'class': 'section'})

    level_2_sections = list(filter(lambda el: el.find('h2') is not None, all_sections))

    for level_2_section in level_2_sections:
        h2 = level_2_section.find('h2')
        if h2:
            section = get_section(h2, [main_section_title], soup)
            parsed_sections.append(section)

        level_3_sections = level_2_section.find_all('div', attrs={'class': 'section'})

        for level_3_section in level_3_sections:
            h3 = level_3_section.find('h3')
            if h3:
                section = get_section(h3, [main_section_title, clean_text(h2.text)], soup)
                parsed_sections.append(section)
    return parsed_sections


docs_path = pathlib.Path('/home/surister/doc_builder/html/')
docs_path_len = len(docs_path.parts)

file_generator = docs_path.rglob('*.html')

from embeddings.io import insert_to_cratedb, run_stmt

crate_stmt = """
CREATE TABLE IF NOT EXISTS "doc"."fs_search" (
   "level" BIGINT,
   "hierarchy" TEXT,
   "title_fs" TEXT,
   "content_fs" TEXT,
   "content_html" TEXT,
   "ref_html" TEXT,
   "metadata" OBJECT,
   "xs" FLOAT_VECTOR(2048)
)
"""

run_stmt(connection=connection, stmt=crate_stmt)

if __name__ == '__main__':
    for file in file_generator:
        print(f'Trying to parse "{file}"')
        if 'appendices/release-notes' in str(file):
            continue
        try:
            sections = parse_html(file.read_text())

        except Exception as e:
            print(f'Could not parse "{file}", ignore it or debug it.')
            continue

        parts = list(file.parts[docs_path_len:])
        root = parts[0] if len(parts) > 1 else ''

        parts.remove(file.name)

        metadata = {
            'root': root,
            'sub_root': "/".join(parts),
            'file_name': file.name,
        }

        for i in sections:
            response = client.embeddings.create(
                input=i['content'],
                model="text-embedding-3-large",
                dimensions=2048
            )

            i['metadata'] = json.dumps(metadata)
            i['xs'] = response.data[0].embedding
            i['content'] = i['content'].replace("'", "''")
            i['content_html'] = i['content_html'].replace("'", "''")

            columns = list(i.keys())
            values = list(i.values())

            insert_to_cratedb(
                connection=connection,
                table_name='fs_search',
                columns=columns,
                values=values
            )
