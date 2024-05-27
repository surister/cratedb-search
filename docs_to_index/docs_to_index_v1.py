import pathlib

import polars

CRATE_URI = 'crate://192.168.88.251:4200'


def create_index(path: str, root: str, sub_root: str):
    lines = pathlib.Path(path).read_text().splitlines()
    index = []
    for (i, line) in enumerate(lines):
        before = i - 1
        after = i + 1

        if before >= 0 and after <= len(lines) - 1:
            if '=' in lines[after] and '=' in lines[before]:
                index.append(
                    {'type': 'title', 'index': i, 'text': line, 'root': root, 'sub_root': sub_root}
                )

            if ('=======' in lines[after] or '-------' in lines[after]) and '=' not in lines[
                before]:
                if len(index) > 1 and index[len(index) - 1]['type'] == 'subtitle':
                    before_subtitle = index[len(index) - 1]
                    before_subtitle_index = before_subtitle['index'] + 2
                    after_subtitle_index = i - 1

                    index.append(
                        {
                            'type': 'content',
                            'before_subtitle': before_subtitle,
                            'text': "\n".join(lines[before_subtitle_index: after_subtitle_index]),
                            'index': -1,
                            'root': root,
                            'sub_root': sub_root
                        }
                    )

                index.append(
                    {'type': 'subtitle', 'index': i, 'text': line, 'root': root,
                     'sub_root': sub_root}
                )
    return index


blacklist = ['appendices']


def iter_dir(path: pathlib.Path, final_url: str = ''):
    if path.is_dir() and not path.name.startswith('_') and path.name not in blacklist:
        for dir in path.iterdir():
            iter_dir(path / dir.name, final_url + '/' + dir.name)

    if path.suffix == '.rst' and path.name != 'index':
        df = polars.from_dicts(
            create_index(path=path, root=final_url.replace(".rst", "").split('/')[1],
                         sub_root=final_url.replace(".rst", "")))
        df = df.rename({'index': 'content_line'})
        df.write_database('test_search', CRATE_URI, if_table_exists='append')


iter_dir(pathlib.Path('/home/surister/PycharmProjects/crate/crate/docs'))
