import os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import re

PathString = Union[str, Path]


def is_windows_os() -> bool:
    """Проверка что программа запущена на Windows"""
    return platform.system() == "Windows"


def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Проверка корректности Windows пути с учетом всех особенностей"""
    p_str = str(path)
    p_obj = Path(p_str)

    # 1. Проверка формата диска (если есть)
    disk_match = re.match(r'^([A-Za-z]):', p_str)
    disk_prefix = ''
    remaining_path = p_str

    if disk_match:
        disk_prefix = disk_match.group(0)  # "C:"
        remaining_path = p_str[len(disk_prefix):]  # Остаток пути

        # Проверка что буква диска корректная
        if not re.match(r'^[A-Za-z]:$', disk_prefix):
            return False, f"Некорректный формат диска: {disk_prefix}"

    # 2. Проверка запрещенных символов (полный список)
    # В Windows запрещены: < > : " | ? * и / (кроме как разделителя)
    forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']

    # Проверяем двоеточия вне формата диска
    if ':' in remaining_path:
        return False, "Двоеточие разрешено только в формате диска (C:)"

    # Проверяем другие запрещенные символы
    for char in forbidden_chars:
        if char in remaining_path:
            return False, f"Путь содержит запрещенный символ: '{char}'"

    # 3. Проверка зарезервированных имен Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    # Разбиваем путь на компоненты
    path_parts = [part for part in remaining_path.split('\\') if part]

    for part in path_parts:
        # Проверяем без учета расширения
        name_without_ext = os.path.splitext(part)[0].upper()
        if name_without_ext in reserved_names:
            return False, f"Использовано зарезервированное имя: {part}"

        # Проверка точек в конце
        if part.endswith('.') or part.endswith(' '):
            return False, "Имя файла не может заканчиваться точкой или пробелом"

    # 4. Проверка максимальной длины пути
    # Обычные пути: 260 символов, длинные пути с \\?\: 32767 символов
    if p_str.startswith('\\\\?\\'):
        # Длинный путь Windows
        if len(p_str) > 32767:
            return False, "Путь содержит более 32767 символов"
    else:
        # Обычный путь
        if len(p_str) > 260:
            return False, "Путь содержит более 260 символов"

    # 5. Проверка существования пути (опционально)
    if not p_obj.exists():
        # Не возвращаем ошибку, так как путь может быть создан позже
        # return False, "Путь не существует"
        pass

    # 6. Проверка корректности обратных слешей
    # Не должно быть двойных слешей, кроме как после диска
    normalized_path = re.sub(r'\\\\+', '\\\\', p_str)
    if '\\\\' in normalized_path.replace(disk_prefix + '\\\\', ''):
        return False, "Некорректное использование обратных слешей"

    return True, "Путь валиден"


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемом виде для Windows"""
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

    # Для Windows: если родительский каталог - это только диск, добавляем \
    if platform.system() == "Windows":
        if re.match(r'^[A-Za-z]:$', parent):
            parent = parent + '\\'
        elif re.match(r'^[A-Za-z]:\\$', parent):
            # Уже корректный формат
            pass
    elif os.path.splitdrive(parent)[1] == "":
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

    # Для Windows используем WinAPI
    if platform.system() == "Windows":
        try:
            import ctypes
            from ctypes import wintypes

            file_attribute_hidden = 0x02

            GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
            GetFileAttributesW.restype = wintypes.DWORD

            attrs = GetFileAttributesW(p_str)

            if attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                last_error = ctypes.windll.kernel32.GetLastError()
                ERROR_ACCESS_DENIED = 5

                if last_error == ERROR_ACCESS_DENIED:
                    return True  # Если доступ запрещен - считаем скрытым
                return False

            return bool(attrs & file_attribute_hidden)

        except Exception:
            # Если WinAPI недоступен, пробуем другие методы
            pass

    # Для Unix/Linux/Mac или при ошибке WinAPI
    # В Unix скрытые файлы начинаются с точки
    return os.path.basename(p_str).startswith('.')


# Дополнительные полезные функции для Windows
def get_windows_reserved_names() -> List[str]:
    """Получение списка зарезервированных имен в Windows"""
    return [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]


def normalize_windows_path(path: str) -> str:
    """Нормализация Windows пути"""
    # Заменяем прямые слеши на обратные
    path = path.replace('/', '\\')

    # Убираем двойные слеши
    path = re.sub(r'\\\\+', '\\', path)

    # Убираем слеш в конце, если это не корень диска
    if path.endswith('\\') and not re.match(r'^[A-Za-z]:\\$', path):
        path = path.rstrip('\\')

    return path
