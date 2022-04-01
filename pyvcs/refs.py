import pathlib
import typing as tp


def update_ref(gitdir: pathlib.Path, ref: tp.Union[str, pathlib.Path], new_value: str) -> None:
    pathlib.Path(str(gitdir / ref))
    with pathlib.Path(str(gitdir / ref)).open("w", encoding="utf-8") as f:  # обновляю содержимое HEAD
        f.write(new_value)


def symbolic_ref(gitdir: pathlib.Path, name: str, ref: str) -> None:
    head = gitdir / name
    with head.open("w", encoding='utf-8') as f:  # по аналогии с примером git symbolic-ref HEAD refs/heads/dev
        f.write("ref: " + ref)


def ref_resolve(gitdir: pathlib.Path, refname: str) -> str:  # до меня вообще не доходит, как оно должно работать
    if not is_detached(gitdir):
        ref = get_ref(gitdir)
        with pathlib.Path(str(gitdir / ref)).open("r", encoding="utf-8") as f:
            content = f.read()
        with pathlib.Path(str(gitdir / "HEAD")).open("w", encoding="utf-8") as f:
            f.write(content)
    pathlib.Path(str(gitdir / refname))
    with pathlib.Path(str(gitdir / refname)).open("r", encoding="utf-8") as f:
        content = f.read()
    return content


def resolve_head(gitdir: pathlib.Path) -> tp.Optional[str]:  # вытаскиваю содержимое файла, путь к которому лежит в HEAD
    content = None
    if pathlib.Path(str(gitdir / get_ref(gitdir))).exists():
        with pathlib.Path(str(gitdir / get_ref(gitdir))).open("r", encoding="utf-8") as f:
            content = f.read()
    return content


def is_detached(gitdir: pathlib.Path) -> bool:
    head = gitdir / "HEAD"
    with head.open("r", encoding='utf-8') as f:
        content = f.read()
    if "ref: refs/heads/" not in content:  # если тут хэш - то is detached
        return True
    return False


def get_ref(gitdir: pathlib.Path) -> str:
    head = gitdir / "HEAD"
    with head.open("r", encoding='utf-8') as f:  # содержимое файла HEAD
        content = f.read()
    return content.split()[1]
