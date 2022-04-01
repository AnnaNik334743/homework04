import os
import pathlib
import stat
import time
import typing as tp

from pyvcs.index import GitIndexEntry, read_index
from pyvcs.objects import hash_object
from pyvcs.refs import get_ref, is_detached, resolve_head, update_ref


# я не хочу даже думать о том, что написано в следующей функции. оно работает корректно (даже для случаев,
# которые не проверяются в тестере). это стоило мне суток жизни и километров нервов.
# все попытки заставить sha работать можно найти во второй половине файла:
# https://colab.research.google.com/drive/1FnkrxpmJnS6eObg3qGa7uglV6oko1L2J?usp=sharing

def write_tree(gitdir: pathlib.Path, index: tp.Union[tp.List[GitIndexEntry], tp.List[bytes]], dirname: str = "") -> str:
    curr_entries = []
    i = 0
    while i < len(index):
        entry = index[i]
        if len(entry.name.replace(dirname, "").split('/')) == 1:
            curr_entries.append(f"{oct(entry.mode)[2:]} {entry.name.replace(dirname, '')}".encode() + b"\0" + entry.sha1)
            i += 1

        else:
            get_recursively = [entry]
            tree_sha = b""
            dir, the_rest = entry.name.replace(dirname, "").split('/', 1)

            while True:
                i += 1
                if i == len(index):
                    tree_sha = write_tree(gitdir, get_recursively, dirname + dir + '/')
                    tree_sha = tree_sha.encode().fromhex(tree_sha)
                else:
                    entry = index[i]
                    dir_new = "?"
                    if len(entry.name.replace(dirname, "").split('/')) > 1:
                        dir_new, the_rest = entry.name.replace(dirname, "").split('/', 1)
                    else:
                        tree_sha = write_tree(gitdir, get_recursively, dirname + dir + '/')
                        tree_sha = tree_sha.encode().fromhex(tree_sha)
                        break

                    if dir_new == dir:
                        get_recursively.append(entry)
                    else:
                        tree_sha = write_tree(gitdir, get_recursively, dirname + dir + '/')
                        tree_sha = tree_sha.encode().fromhex(tree_sha)
                        break

            curr_entries.append(f"{40000} {dir}".encode() + b"\0" + tree_sha)

    content = b""
    for item in curr_entries:
        content = content + item
    hashed = hash_object(content, "tree", write=True)
    return hashed


def commit_tree(
    gitdir: pathlib.Path,
    tree: str,
    message: str,
    parent: tp.Optional[str] = None,
    author: tp.Optional[str] = None,
) -> str:
    lc_time, tz = int(time.mktime(time.localtime())), time.strftime("%z", time.gmtime())  # https://stackoverflow.com/questions/1111056/get-time-zone-information-of-the-system-in-python
    if parent is None:
        parent = ""
    else:
        parent = f"\nparent {parent}"
    content = f"tree {tree}{parent}\nauthor {author} {lc_time} {tz}\ncommitter {author} {lc_time} {tz}\n\n{message}\n"
    hashed = hash_object(content.encode(), "commit")
    return hashed
