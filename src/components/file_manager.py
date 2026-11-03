import os
import re
import shutil

import yaml


def is_exists(path: str, ignore_extension: bool = False) -> bool:
    if not ignore_extension:
        return os.path.exists(path)
    else:
        all_file = [
            get_only_filename(p, True)
            for p in list_files(path if is_folder(path) else get_parent_folder(path))
        ]
        return get_only_filename(path, True) in all_file


def validate_file(_f: str) -> str:
    if is_file(_f):
        return _f
    else:
        raise FileNotFoundError(_f)


def is_file(_f: str) -> bool:
    return os.path.isfile(_f)


def list_images(path: str, is_order_by_time: bool = False) -> list[str]:
    return list_files(
        path,
        file_extension=["jpg", "jpeg", "png", "gif", "webp"],
        is_order_by_time=is_order_by_time,
    )


def list_files(
    path: str, file_extension: list = [".*"], is_order_by_time: bool = False
) -> list[str]:
    """list files in a given path

    Args:
        path:
        file_extension: list of file extension e.g. ['yaml', 'yml']

    """
    if not is_exists(path):
        return []
    if not is_folder(path):
        raise ValueError(f"{path} is not a folder.")
    files = [
        os.path.join(path, d)
        for d in os.listdir(path)
        if re.findall(r"\.(" + "|".join(file_extension) + r")$", d, re.IGNORECASE)
    ]
    if is_order_by_time:
        return sorted(files, key=lambda e: os.path.getmtime(e), reverse=False)
    else:
        return files


def split_extension(filename: str) -> tuple[str, str]:
    """
    Split a file path to be a path with filename and its extension

    Args:
        filename (str): a filepath

    Returns:
        tuple[str, str]: a filename and an extension in a form ".xxx"
    """
    return os.path.splitext(filename)


def get_filesize(_f: str) -> int:
    """
    Get size of the filepath

    Args:
        _f (str): filepath

    Returns:
        int: File size in bytes. None if file not found
    """

    if not is_exists(_f):
        return None
    if not is_file(_f):
        return None
    return os.path.getsize(_f)


def move_file(src: str, dst: str) -> None:
    shutil.move(src, dst)


def validate_folder(_f: str) -> str:
    if is_folder(_f):
        return _f
    else:
        raise NotADirectoryError(_f)


def is_folder(_f: str) -> bool:
    return os.path.isdir(_f)


def list_folders(path: str) -> list[str]:
    return [d for d in os.listdir(path) if is_folder(os.path.join(path, d))]


def get_only_filename(path: str, exclude_extension: bool = False) -> str:
    if exclude_extension:
        return split_extension(os.path.basename(path))[0]
    else:
        return os.path.basename(path)


def get_parent_folder(path: str) -> str:
    return os.path.dirname(path)


def make_folder(folder_name: str) -> None:
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def remove_folder(folder_name: str) -> None:
    if not is_folder(folder_name):
        raise ValueError(f"{folder_name} is not a folder")
    if not is_exists(folder_name):
        raise ValueError(f"{folder_name} does not exist")
    shutil.rmtree(folder_name)


def read_all_lines(filepath: str) -> list[str]:
    with open(filepath) as fptr:
        lines = fptr.readlines()
    return lines


def read_yaml(yaml_filepath: str) -> list[dict]:
    with open(yaml_filepath) as fptr:
        content = yaml.safe_load(fptr)
    return content or []


def write_yaml(yaml_filepath: str, content: dict) -> None:
    with open(yaml_filepath, "w") as fptr:
        yaml.dump(content, fptr)
