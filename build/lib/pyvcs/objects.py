import hashlib
import os
import pathlib
import re
import stat
import typing as tp
import zlib

from pyvcs.refs import update_ref
from pyvcs.repo import repo_find


# вот эти штуки буквально меня спасли:
# https://stackoverflow.com/questions/35430584/how-is-the-git-hash-calculated
# https://stackoverflow.com/questions/14790681/what-is-the-internal-format-of-a-git-tree-object#21599232

def hash_object(data: bytes, fmt: str = 'blob', write: bool = False) -> str:
    header = f"{fmt} {len(data)}\0"  # заголовок создаваемого файла
    store = header.encode() + data  # будущее содержимое файла
    hashed = hashlib.sha1(store).hexdigest()  # захэшированное содержимое файла

    if write:
        dir = hashed[:2]  # имя директории
        name = hashed[2:]  # имя файла
        initial = str(repo_find())  # ищем репу, где создавать директорию с файлом, если она еще не создана
        if not pathlib.Path(f"{initial}/objects/{dir}/{name}").exists():

            pathlib.Path(f"{initial}/objects/{dir}").mkdir(parents=True, exist_ok=True)  # директория
            pathlib.Path(f"{initial}/objects/{dir}/{name}")  # файл

            with pathlib.Path(f"{initial}/objects/{dir}/{name}").open("wb") as f:
                to_store = zlib.compress(store)  # записываем в файл содержимое (заголовок + текст)
                f.write(to_store)

    return hashed


def resolve_object(obj_name: str, gitdir: pathlib.Path) -> tp.List[str]:

    if len(obj_name) < 4 or len(obj_name) > 40:
        raise Exception(f"Not a valid object name {obj_name}")  # методом тыка выяснено, какая длина является корректной

    dir_name = obj_name[:2]  # имя директории
    start_of_file_name = obj_name[2:]  # то, с чего НАЧИНАЮТСЯ нужные нам файлы

    all_objects = pathlib.Path(f"{str(gitdir)}/objects/{dir_name}").glob(f"{start_of_file_name}*")  # с помощью регулярок ищем все нужные файлы
    all_objects = list(map(lambda elem: re.search(f"{dir_name}{start_of_file_name}.*",
                                                  re.sub(r"\\+", "", str(elem)))[0], all_objects))

    if len(all_objects) == 0:
        raise Exception(f"Not a valid object name {obj_name}")  # если ни одного файла не нашли - видимо, нам неправильные данные передали

    return all_objects


def find_object(obj_name: str, gitdir: pathlib.Path) -> str:
    dir_name = obj_name[:2]
    file_name = obj_name[2:]

    path = f"{str(gitdir)}/objects/{dir_name}/{file_name}"  # объект однозначно определяется именем директории, файла и путем к репе
    if not pathlib.Path(path).exists():
        raise Exception(f"Invalid path {path}")  # я конечно не врач, но у вас путь к файлу - инвалид

    return path


def read_object(sha: str, gitdir: pathlib.Path) -> tp.Tuple[str, bytes]:
    path = pathlib.Path(find_object(sha, gitdir))  # сначала ищем по хэшу нужный файл
    with open(path, mode="rb") as f:
        obj_data = zlib.decompress(f.read())  # читаем его содержимое

    header = obj_data[:obj_data.find(b"\x00")]  # заголовок
    fmt = header[:header.find(b" ")].decode()  # формат файла
    content = obj_data[obj_data.find(b"\x00")+1:]  # содержимое файла

    return fmt, content


def read_tree(data: bytes) -> tp.List[tp.Tuple[int, str, str]]:
    data = data.replace(b"40000", b"040000")  # у гитхаба какие-то траблы с хэшированием чисел с нулем в начале
    spisok = list(data.split(b" "))
    for i in range(1, len(spisok)):
        spisok[i] = spisok[i - 1][-6:] + b" " + spisok[i]
    del spisok[0]
    for i in range(len(spisok)):
        if i == len(spisok) - 1:
            spisok[i] = spisok[i].replace(b"\x00", b" ")
        else:
            spisok[i] = spisok[i][:-6].replace(b"\x00", b" ")
    notes = []
    for item in spisok:
        mode, name, sha = item.split(b" ")
        notes.append((mode.decode(), name.decode(), sha.hex()))
    return notes


def cat_file(obj_name: str, pretty: bool = True) -> None:
    gitdir = repo_find()  # ищем репу и читаем содержимое файла, который нас попросили прочитать
    fmt, content = read_object(obj_name, gitdir)
    if fmt == "blob":  # у блоба есть только содержимое
        print(content.decode() if pretty else content)
    elif fmt == "tree":  # содержимое дерева надо расшифровывать
        notes = read_tree(content)
        answers = ""
        for note in notes:
            fmt = read_object(note[2], gitdir)[0]
            answers += str(note[0]) + " " + fmt + " " + note[2] + "\t" + note[1] + "\n"
        print(answers)
    elif fmt == "commit":  # в коммите содержимое лежит в нормальном виде
        print(content.decode())


# а оно зачем надо?..
def find_tree_files(tree_sha: str, gitdir: pathlib.Path) -> tp.List[tp.Tuple[str, str]]:
    # PUT YOUR CODE HERE
    ...


# и это тоже - зачем?..
def commit_parse(raw: bytes, start: int = 0, dct=None):
    # PUT YOUR CODE HERE
    ...
