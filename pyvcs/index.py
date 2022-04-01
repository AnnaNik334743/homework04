import hashlib
import operator
import os
import pathlib
import struct
import typing as tp

from pyvcs.objects import hash_object


class GitIndexEntry(tp.NamedTuple):
    # @see: https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
    ctime_s: int
    ctime_n: int
    mtime_s: int
    mtime_n: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha1: bytes
    flags: int
    name: str

    def pack(self) -> bytes:
        class_values = list(self._asdict().values())  # получаю все атрибуты класса
        class_values[-1] = class_values[-1].encode()  # имя в байтах, надо превратить в строку
        length = len(class_values[-1])  # длина строки, чтобы вычислить флаг (один из атрибутов)
        packed = struct.pack(f"!10I20sh{length}s{((61+length)//8+1)*8 - 62 - length}x", *class_values) # докинуть пустыми битами, чтоб общее кол-во бит на 8 делилось
        return packed

    @staticmethod
    def unpack(data: bytes) -> "GitIndexEntry":
        length = struct.unpack("!h", data[60:62])[0]  # это флаг, чтобы получилось правильно считать строку (имя файла)
        unpacked = struct.unpack(f"!10I20sh{length}s{((61+length)//8+1)*8 - 62 - length}x", data)
        ctime_s, ctime_n, mtime_s, mtime_n, dev, ino, mode, uid, gid, size, sha1, flags, name = unpacked
        return GitIndexEntry(ctime_s, ctime_n, mtime_s, mtime_n, dev, ino, mode, uid, gid, size, sha1, flags, name.decode())


def read_index(gitdir: pathlib.Path) -> tp.List[GitIndexEntry]:
    spisok = []  # максимально оригинальное название. тут будут лежать экземпляры класса
    if pathlib.Path(str(gitdir) + "/index").exists():  # если файла нет, то и считывать нечего
        with pathlib.Path(str(gitdir) + "/index").open("rb") as f:
            text = f.read()
        rest = text[12:-20]  # это нужное нам содержимое - информация о лежащих в директории файлах
        while len(rest) > 0:
            curr_length = struct.unpack("!h", rest[60:62])[0]
            curr_item = rest[:((61 + curr_length) // 8 + 1) * 8].replace(b"\\", b"/")
            spisok.append(GitIndexEntry.unpack(curr_item))
            rest = rest[((61 + curr_length) // 8 + 1) * 8:]
    return spisok


def write_index(gitdir: pathlib.Path, entries: tp.List[GitIndexEntry]) -> None:
    if not pathlib.Path(str(gitdir) + "/index").exists():
        pathlib.Path(str(gitdir) + "/index")  # если индекса нет - его нужно создать

    with pathlib.Path(str(gitdir) + "/index").open("wb") as f:
        text = struct.pack("!4s2I", b"DIRC", 2, len(entries))
        for item in entries:
            text += GitIndexEntry.pack(item)
        f.write(text + hashlib.sha1(text).digest())  # хэш не от предыдущего содержимого файла, а от того, что я записываю в него сейчас. максимально странно


def ls_files(gitdir: pathlib.Path, details: bool = False) -> None:
    if details:
        for item in read_index(gitdir):
            print(oct(item.mode)[2:], item.sha1.hex(), f"0\t{item.name}")
    else:
        for item in read_index(gitdir):
            print(item.name)


def update_index(gitdir: pathlib.Path, paths: tp.List[pathlib.Path], write: bool = True) -> None:
    entries = []
    for path in paths:  # создаем из файлов то, что можно будет в дальнейшем записать в индекс
        with open(path, "r", encoding='utf-8') as f:
            content = f.read().encode()
        result = os.stat(path)
        name = str(path).replace(r"\\", r"/")  # это приколы с выводом пути, из-за которых есть проблемы с тестами
        hash = hash_object(content, fmt="blob", write=write) # я буквально добавляю файл в объекты. это выглядит неправильно, но тесты...
        entries.append(
            GitIndexEntry(int(result.st_ctime), 0, int(result.st_mtime), 0,
                          result.st_dev, result.st_ino, result.st_mode, result.st_uid, result.st_gid, result.st_size,
                          hash.encode().fromhex(hash), len(name), name))
    entries.sort(key=lambda item: (item.name, item.ctime_s))  # фиг знает, что такое stage, поэтому будем сортировать сначала по имени, а потом по времени изменения
    write_index(gitdir, entries)

