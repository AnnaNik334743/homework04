import os
import pathlib
import typing as tp


def repo_find(workdir: tp.Union[str, pathlib.Path] = ".") -> pathlib.Path:  # через os не работает ничего, надо через pathlib
    try:
        type_dir = str(os.environ["GIT_DIR"])  # если имя не ./git - надо использовать его, не хардкодим
    except KeyError:
        type_dir = ".pyvcs"
    workdir = str(workdir)

    if not pathlib.Path(workdir).exists():
        raise Exception("Directory does not exist")  # если передали путь к несуществующей директории - пусть идут лесом

    found = workdir.find(type_dir)
    if found == -1 and not pathlib.Path(workdir + "/" + type_dir).exists():  # директория есть, а гитовская ли это репа?
        raise Exception("Not a git repository")

    the_path = workdir[:found] + '/' + type_dir  # если всё ок - возвращаем найденную репу
    return pathlib.Path(the_path)


def repo_create(workdir: tp.Union[str, pathlib.Path]) -> pathlib.Path:
    if pathlib.Path(workdir).is_file():
        raise Exception(f"{workdir} is not a directory")  # если передали файл вместо директории - пусть идут лесом
    try:
        type_dir = os.environ["GIT_DIR"]  # если имя не ./git - надо использовать его, не хардкодим
    except KeyError:
        type_dir = pathlib.Path(".pyvcs")

    pathlib.Path(workdir / type_dir).mkdir(parents=True, exist_ok=True)  # создаем всякие нужные для репы директории
    pathlib.Path(str(workdir / type_dir) + "/refs/heads").mkdir(parents=True, exist_ok=True)
    pathlib.Path(str(workdir / type_dir) + "/refs/tags").mkdir(parents=True, exist_ok=True)
    pathlib.Path(str(workdir / type_dir) + "/objects").mkdir(parents=True, exist_ok=True)

    pathlib.Path(str(workdir / type_dir) + "/HEAD")  # и файлы. если файл просто создать, ничего с ним не сделав, то он не создастся
    with pathlib.Path(str(workdir / type_dir) + "/HEAD").open("w", encoding="utf-8") as f:
        f.write("ref: refs/heads/master\n")

    pathlib.Path(str(workdir / type_dir) + "/config")
    with pathlib.Path(str(workdir / type_dir) + "/config").open("w", encoding="utf-8") as f:
        f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n")
    pathlib.Path(str(workdir / type_dir) + "/description")

    with pathlib.Path(str(workdir / type_dir) + "/description").open("w", encoding="utf-8") as f:
        f.write("Unnamed pyvcs repository.\n")
    return workdir / type_dir

