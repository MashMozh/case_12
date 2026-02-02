import os
import ctypes
from datetime import datetime
from typing import List, Dict, Tuple, Any
import utils


def get_current_drive() -> str:
    """Получение текущего диска Windows"""
    # TODO: Вернуть текущий диск (например: "C:")
    # Использовать os.path.splitdrive()
    current_path = os.getcwd()
    drive, _ = os.path.splitdrive(current_path)
    if drive:
        return drive
    # В случае, если не определился, возвращаем диск C:
    return 'C:'


def list_available_drives() -> List[str]:
    """Получение списка доступных дисков Windows с обработкой ошибок"""
    if not utils.is_windows_os():
        return ['/']

    try:
        import ctypes
        from ctypes import wintypes

        # Безопасный вызов GetLogicalDrives
        GetLogicalDrives = ctypes.windll.kernel32.GetLogicalDrives
        GetLogicalDrives.restype = wintypes.DWORD

        drives_bitmask = GetLogicalDrives()

        # Проверка на ошибку
        if drives_bitmask == 0:
            # Получаем код ошибки
            last_error = ctypes.windll.kernel32.GetLastError()
            print(f"Windows API error GetLogicalDrives: код {last_error}")
            return ['C:']  # Запасной вариант

        drives = []
        for i in range(26):
            if drives_bitmask & (1 << i):
                drive_letter = chr(65 + i) + ':'

                # Проверяем, доступен ли диск для чтения
                try:
                    # Пробуем получить информацию о диске
                    drive_path = drive_letter + '\\'
                    if os.path.exists(drive_path):
                        drives.append(drive_letter)
                except (PermissionError, OSError):
                    # Пропускаем диски без доступа
                    continue

        return drives if drives else ['C:']  # Минимум диск C:

    except AttributeError:
        # WinAPI не доступен
        print("Windows API не доступен")
        return ['C:']
    except OSError as e:
        # Ошибка Windows API
        print(f"Windows API error: {e}")
        return ['C:']
    except Exception as e:
        # Любая другая ошибка
        print(f"Unexpected error getting drives: {e}")
        return ['C:']


def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Отображение содержимого каталога в Windows"""
    entries = []
    try:
        items = utils.safe_windows_listdir(path)
        for item in items:
            full_path = os.path.join(path, item)
            is_hidden = utils.is_hidden_windows_file(full_path)
            is_dir = os.path.isdir(full_path)
            size = os.path.getsize(full_path) if not is_dir else 0
            modified_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d')
            entries.append({
                'name': item,
                'type': 'folder' if is_dir else 'file',
                'size': size,
                'modified': modified_time,
                'hidden': is_hidden
            })
        return True, entries
    except Exception:
        return False, []


def format_size(size_bytes: int) -> str:
    # Форматирование размера файла
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def format_directory_output(items: List[Dict[str, Any]]) -> None:
    """Форматированный вывод содержимого каталога для Windows"""
    if not items:
        print("Пустая директория.")
        return
    for item in items:
        name = item['name']
        type_icon = '[D]' if item['type'] == 'folder' else '[F]'
        size_str = format_size(item['size']) if item['type'] == 'file' else ''
        hidden_marker = '(скрыто)' if item['hidden'] else ''
        print(f"{type_icon} {name} {size_str} {hidden_marker}")


def move_up(current_path: str) -> str:
    """Переход в родительский каталог в Windows"""
    parent_path = utils.get_parent_path(current_path)
    valid, msg = utils.validate_windows_path(parent_path)
    if valid:
        return parent_path
    else:
        print(f"Не удалось перейти в родительский каталог: {msg}")
        return current_path


def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    """Переход в указанный подкаталог в Windows"""
    new_path = os.path.join(current_path, target_dir)
    valid, msg = utils.validate_windows_path(new_path)
    if valid:
        return True, new_path
    else:
        print(f"Ошибка при переходе: {msg}")
        return False, current_path


def get_windows_special_folders() -> Dict[str, str]:
    """Получение путей к специальным папкам Windows"""
    # Только для Windows
    if not utils.is_windows_os():
        # Для Mac возвращаем домашнюю директорию
        home_dir = os.path.expanduser('~')
        return {
            'Desktop': os.path.join(home_dir, 'Desktop'),
            'Documents': os.path.join(home_dir, 'Documents'),
            'Downloads': os.path.join(home_dir, 'Downloads')
        }

    # Для Windows
    user_profile = os.environ.get('USERPROFILE', '')
    return {
        'Desktop': os.path.join(user_profile, 'Desktop'),
        'Documents': os.path.join(user_profile, 'Documents'),
        'Downloads': os.path.join(user_profile, 'Downloads')
    }
