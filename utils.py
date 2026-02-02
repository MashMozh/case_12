import os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import ctypesimport os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import re

PathString = Union[str, Path]


def is_windows_os() -> bool:
    """Проверка что программа запущена на Windows"""
    return platform.system() == "Windows"


def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Проверка корректности Windows пути"""
    symbols = ['/', '*', '?', '"', '<', '>', '|']
    p_str = str(path)
    p_obj = Path(p_str)

    disk_prefix = ''
    remaining_path = p_str

    m = re.match(r'^[A-Za-z]:', p_str)
    if m:
        disk_prefix = m.group(0)
        remaining_path = p_str[len(disk_prefix):]

    match remaining_path:
        case x if any(smbl in symbols for smbl in x):
            return False, "Путь содержит недопустимые символы."
        case x if len(remaining_path) > 260:
            return False, "Путь содержит более 260 символов."
        case x if not p_obj.exists():
            return False, "Путь не существует."
        case _:
            return True, "Путь валиден."


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемом виде для Windows"""
    # TODO: Преобразовать байты в удобочитаемый формат
    # Пример: 1024 -> "1.0 KB", 1500000 -> "1.4 MB"
    # Учесть что в Windows используются единицы: KB, MB, GB (не KiB, MiB)
    if size_bytes < 1024:
        return f"{size_bytes} B"

    KB = 1024
    MB = KB * 1024
    GB = MB * 1024
    TB = GB * 1024

    if size_bytes < MB:
        return f"{size_bytes / KB:.1f} KB"
    elif size_bytes < GB:
        return f"{size_bytes / MB:.1f} MB"
    elif size_bytes < TB:
        return f"{size_bytes / GB:.1f} GB"
    else:
        return f"{size_bytes / TB:.1f} TB"


def get_parent_path(path: PathString) -> str:
    """Получение родительского каталога с учетом Windows путей"""
    p_str = str(path)
    parent = os.path.dirname(p_str)
    if os.path.splitdrive(parent)[1] == "":
        parent = os.path.join(parent, "")
    return parent


def safe_windows_listdir(path: PathString) -> List[str]:
    """Безопасное получение содержимого каталога в Windows"""
    try:
        p_str = str(path)
        return os.listdir(p_str)
    except (PermissionError, FileNotFoundError, OSError):
        return []


def is_hidden_windows_file(path: PathString) -> bool:
    """Проверка является ли файл скрытым в Windows с обработкой ошибок"""
    p_str = str(path)

    if not Path(p_str).exists():
        return False

    try:
        import ctypes
        from ctypes import wintypes

        file_attribute_hidden = 0x02

        # Более безопасный вызов WinAPI
        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
        GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        GetFileAttributesW.restype = wintypes.DWORD

        attrs = GetFileAttributesW(p_str)

        # Проверка на ошибку (INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF)
        if attrs == 0xFFFFFFFF:
            # Получаем код ошибки
            last_error = ctypes.windll.kernel32.GetLastError()

            # Обработка специфичных Windows ошибок
            ERROR_FILE_NOT_FOUND = 2
            ERROR_PATH_NOT_FOUND = 3
            ERROR_ACCESS_DENIED = 5

            if last_error in [ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND]:
                return False
            elif last_error == ERROR_ACCESS_DENIED:
                # Если доступ запрещен, возможно это системный файл
                return True
            else:
                return False

        return bool(attrs & file_attribute_hidden)

    except AttributeError:
        # ctypes.windll.kernel32 не доступен (не Windows)
        return False
    except OSError as e:
        # Windows-специфичные OSError
        print(f"Windows API error checking hidden attribute: {e}")
        return False
    except Exception as e:
        # Любая другая ошибка
        print(f"Unexpected error checking hidden file: {e}")
        return False
import re
from unittest import case

PathString = Union[str, Path]

def is_windows_os() -> bool:
    """Проверка что программа запущена на Windows"""
    return platform.system() == "Windows"


def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Проверка корректности Windows пути"""
    symbols = ['/', '*', '?', '"', '<', '>', '|']
    p_str = str(path)
    p_obj = Path(p_str)

    disk_prefix = ''
    remaining_path = p_str

    m = re.match(r'^[A-Za-z]:', p_str)
    if m:
        disk_prefix = m.group(0)
        remaining_path = p_str[len(disk_prefix):]

    match remaining_path:
        case x if any(smbl in symbols for smbl in x):
            return False, "Путь содержит недопустимые символы."
        case x if len(remaining_path) > 260:
            return False, "Путь содержит более 260 символов."
        case x if not p_obj.exists():
            return False, "Путь не существует."
        case _:
            return True, "Путь валиден."


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемом виде для Windows"""
    # TODO: Преобразовать байты в удобочитаемый формат
    # Пример: 1024 -> "1.0 KB", 1500000 -> "1.4 MB"
    # Учесть что в Windows используются единицы: KB, MB, GB (не KiB, MiB)
    if size_bytes < 1024:
        return f"{size_bytes} B"
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024
    TB = GB * 1024

    match size_bytes:
        case size if size < KB:
            return f"{size_bytes} B"
        case size if KB <= size < MB:
            return f"{round(size_bytes / KB, 1)} KB"
        case size if MB <= size < GB:
            return f"{round(size_bytes / MB, 1)} MB"
        case size if GB <= size < TB:
            return f"{round(size_bytes / GB, 1)} GB"
    pass

def get_parent_path(path: PathString) -> str:
    """Получение родительского каталога с учетом Windows путей"""
    p_str = str(path)
    parent = os.path.dirname(p_str)
    if os.path.splitdrive(parent)[1] == "":
        parent = os.path.join(parent, "")
    return parent


def safe_windows_listdir(path: PathString) -> List[str]:
    """Безопасное получение содержимого каталога в Windows"""
    try:
        p_str = str(path)
        return os.listdir(p_str)
    except (PermissionError, FileNotFoundError, OSError):
        return []

def is_hidden_windows_file(path: PathString) -> bool:
    """Проверка является ли файл скрытым в Windows"""
    p_str = str(path)

    if not Path(p_str).exists():
        return False

    file_attribute_hidden = 0x02

    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p_str))
        if attrs == -1:
            return False
        return bool(attrs & file_attribute_hidden)
    except Exception:
        return False
      
