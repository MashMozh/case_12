import os
import re
from typing import List, Dict, Any, Tuple
import utils
import navigation
import analysis
import fnmatch


def is_junction_points(path: str) -> bool:
    """Определение junction point через WinAPI."""
    # Используем функцию из analysis модуля
    return analysis.is_junction_points(path)


def find_files_windows(pattern: str, path: str, case_sensitive: bool = False,
                       current_path: str = None, matched_files: List[str] = None) -> List[str]:
    """Поиск файлов по шаблону в Windows"""

    if matched_files is None:
        matched_files = []

    if current_path is None:
        current_path = path

    # Определяем функцию сравнения
    if case_sensitive:
        def match_func(name: str, patrn: str) -> bool:
            return fnmatch.fnmatchcase(name, patrn)
    else:
        def match_func(name: str, patrn: str) -> bool:
            return fnmatch.fnmatchcase(name.lower(), patrn.lower())

    try:
        validity, items = navigation.list_directory(current_path)
        if not validity:
            return matched_files

        for item in items:
            item_path = os.path.join(current_path, item["name"])

            # Проверяем на символические ссылки и junction points
            if os.path.islink(item_path) or is_junction_points(item_path):
                continue

            if item["type"] == "folder":
                # Рекурсивный вызов
                find_files_windows(pattern, path, case_sensitive, item_path, matched_files)
            elif item["type"] == "file":
                if match_func(item["name"], pattern):
                    matched_files.append(item_path)

    except Exception:
        pass  # Игнорируем ошибки при доступе

    return matched_files


def find_by_windows_extension(extensions: List[str], path: str) -> List[str]:
    """
    Поиск файлов по списку расширений Windows с предварительной оптимизацией.
    """
    # Проверка базовых условий
    if not os.path.exists(path):
        return []

    if not os.path.isdir(path):
        return []

    if not extensions:
        return []

    # 1. Нормализация входных расширений
    normalized_exts = []
    for ext in extensions:
        cleaned_ext = ext.strip().lower()
        if not cleaned_ext.startswith('.'):
            cleaned_ext = f".{cleaned_ext}"
        normalized_exts.append(cleaned_ext)

    # 2. Предварительный анализ каталога через analyze_windows_file_types
    success, file_type_stats = analysis.analyze_windows_file_types(path)
    if not success:
        return []

    # Фильтруем только те расширения, которые присутствуют в каталоге
    relevant_exts = [
        ext for ext in normalized_exts
        if ext in file_type_stats and file_type_stats[ext]["count"] > 0
    ]

    if not relevant_exts:
        return []

    # 3. Рекурсивный поиск файлов с нужными расширениями
    matched_files: List[str] = []

    def recursive_scan(current_dir: str) -> None:
        """Внутренняя функция для рекурсивного обхода каталогов"""
        try:
            validity, items = navigation.list_directory(current_dir)
            if not validity:
                return

            for item in items:
                full_path = os.path.join(current_dir, item["name"])

                # Пропускаем символические ссылки и junction points
                if os.path.islink(full_path) or is_junction_points(full_path):
                    continue

                if item["type"] == "folder":
                    # Рекурсивно сканируем подкаталог
                    recursive_scan(full_path)
                elif item["type"] == "file":
                    # Проверяем расширение файла
                    _, file_ext = os.path.splitext(item["name"])
                    if file_ext.lower() in relevant_exts:
                        matched_files.append(full_path)

        except (PermissionError, OSError):
            # Игнорируем недоступные каталоги и ошибки доступа
            pass

    # Запускаем сканирование
    recursive_scan(path)

    return matched_files


def find_large_files_windows(min_size_mb: float, path: str) -> List[Dict[str, Any]]:
    """Поиск крупных файлов в Windows"""
    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024

    def scan_directory(dir_path: str) -> None:
        try:
            validity, items = navigation.list_directory(dir_path)
            if not validity:
                return

            for item in items:
                full_path = os.path.join(dir_path, item["name"])

                # Пропускаем символические ссылки и junction points
                if os.path.islink(full_path) or is_junction_points(full_path):
                    continue

                if item["type"] == "file":
                    try:
                        # Используем функцию из analysis
                        size_success, size_bytes = analysis.count_bytes(full_path)
                        if size_success and size_bytes >= min_size_bytes:
                            large_files.append({
                                'path': full_path,
                                'size_mb': size_bytes / (1024 * 1024),
                                'size_bytes': size_bytes,
                                'name': os.path.basename(full_path),
                                'type': os.path.splitext(full_path)[1]
                            })
                    except Exception:
                        pass

                elif item["type"] == "folder":
                    scan_directory(full_path)

        except Exception:
            pass

    scan_directory(path)
    return large_files


def find_windows_system_files(path: str) -> List[str]:
    """
    Ищет системные файлы Windows (.exe, .dll, .sys) в специальных папках,
    а также в указанном пути.
    """
    system_files = []  # сюда будем складывать найденные файлы

    # Получаем пути к папкам Desktop, Documents, Downloads
    special_dirs = navigation.get_windows_special_folders()

    # Пути, в которых будем искать системные файлы
    search_dirs = [
        special_dirs.get('Desktop', ''),
        special_dirs.get('Documents', ''),
        special_dirs.get('Downloads', ''),
        path  # добавляем основной путь, чтобы расширить поиск
    ]

    # Расширения файлов, которые считаем системными
    sys_extensions = ['.exe', '.dll', '.sys']

    for dir_path in search_dirs:
        if not dir_path or not os.path.exists(dir_path):
            continue  # пропускаем, если папки нет
        try:
            # Обходим содержимое папки
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in sys_extensions:
                            full_path = os.path.join(dir_path, entry.name)
                            system_files.append(full_path)
        except Exception:
            # В случае ошибок (например, доступа) просто пропускаем
            pass

    return system_files


def search_menu_handler(current_path: str) -> bool:
    """
    Обработчик меню поиска для Windows.
    Включает интерактивное меню с выбором действий.
    Возвращает True, если пользователь хочет продолжить, иначе False.
    """
    while True:
        print("\n" + "=" * 70)
        print(f"{' ' * 20}Меню поиска в Windows")
        print("=" * 70)
        print("Пожалуйста, выберите действие:")
        print("  1. Найти крупные файлы")
        print("  2. Найти системные файлы Windows")
        print("  3. Показать статистику текущей директории")
        print("  4. Найти файлы по расширению")
        print("  5. Найти файлы по шаблону")
        print("  6. Выйти из меню")
        print("-" * 70)

        choice = input("Введите номер пункта: ").strip()

        match choice:
            case '1':
                try:
                    size_mb = float(input("Введите минимальный размер файла в МБ: "))
                except ValueError:
                    print("Пожалуйста, введите корректное число.")
                    continue

                files = find_large_files_windows(size_mb, current_path)
                print(f"\nНайдено {len(files)} файлов(а) больше {size_mb} МБ:")
                if files:
                    print(f"{'Имя файла':<40} {'Размер (МБ)':<12} {'Тип':<10}")
                    print("-" * 70)
                    for f in files:
                        print(f"{f['name']:<40} {f['size_mb']:<12.2f} {f['type']:<10}")
                else:
                    print("Файлы не найдены.")

            case '2':
                sys_files = find_windows_system_files(current_path)
                print(f"\nОбнаружено системных файлов: {len(sys_files)}")
                for f in sys_files:
                    print(f"  {os.path.basename(f)} - {f}")

            case '3':
                print("\nПоказ статистики текущей папки:")
                analysis.show_windows_directory_stats(current_path)

            case '4':
                exts_input = input("Введите расширения через запятую (например: txt, pdf, exe): ").strip()
                if exts_input:
                    extensions = [ext.strip() for ext in exts_input.split(',')]
                    files = find_by_windows_extension(extensions, current_path)
                    print(f"\nНайдено {len(files)} файлов с расширениями {extensions}:")
                    for f in files:
                        print(f"  {os.path.basename(f)} - {f}")
                else:
                    print("Не указаны расширения для поиска.")

            case '5':
                pattern = input("Введите шаблон для поиска (например: *.txt, test*.doc): ").strip()
                if pattern:
                    case_sensitive = input("Чувствительность к регистру? (да/нет): ").strip().lower()
                    is_case_sensitive = case_sensitive in ['да', 'д', 'yes', 'y']
                    files = find_files_windows(pattern, current_path, is_case_sensitive)
                    print(f"\nНайдено {len(files)} файлов по шаблону '{pattern}':")
                    for f in files:
                        print(f"  {os.path.basename(f)} - {f}")
                else:
                    print("Не указан шаблон для поиска.")

            case '6':
                print("\nВыход из меню поиска. Возвращаюсь в основное меню.")
                return False  # завершение меню

            case _:
                print("Некорректный выбор. Пожалуйста, попробуйте снова.")

        # Спрашиваем, хочет ли пользователь продолжить
        cont = input("\nХотите продолжить поиск? (да/нет): ").strip().lower()
        if cont not in ['да', 'д', 'yes', 'y']:
            print("Спасибо за использование меню поиска. До свидания!")
            return False
        # иначе цикл повторяется, меню выводится снова

    return True


def format_windows_search_results(results: List[Dict[str, Any]], search_type: str) -> None:
    """Форматированный вывод результатов поиска для Windows."""
    print("\n" + "=" * 80)
    print(f"Результаты для поиска по типу: {search_type}")
    print("=" * 80)

    if not results:
        print("Нет результатов для отображения.")
        return

    # Заголовки таблицы
    print(f"{'Имя файла':<40} {'Размер':<15} {'Путь':<30}")
    print("-" * 80)

    for item in results:
        name = item.get('name', 'Нет имени')
        size_bytes = item.get('size_bytes', item.get('size', 0))
        path = item.get('path', '')

        size_str = utils.format_size(size_bytes)  # форматируем размер через utils

        # Выводим строку
        print(f"{name:<40} {size_str:<15} {path:<30}")

    print("=" * 80)
    print(f"Всего найдено: {len(results)} файлов\n")
