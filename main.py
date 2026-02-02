import os
import sys
from typing import NoReturn


def check_windows_environment() -> bool:
    """Проверка что программа запущена в Windows"""
    try:
        import utils
        if not utils.is_windows_os():
            print("=" * 60)
            print("ОШИБКА: Эта программа предназначена только для Windows!")
            print(f"Текущая операционная система: {sys.platform}")
            print("=" * 60)
            return False
        return True
    except ImportError:
        print("=" * 60)
        print("ОШИБКА: Модуль utils не найден!")
        print("=" * 60)
        return False


def display_windows_banner() -> None:
    """Отображение баннера с информацией о Windows"""
    import navigation
    print("=" * 70)
    print(" " * 20 + "WINDOWS ФАЙЛОВЫЙ МЕНЕДЖЕР")
    print("=" * 70)

    # Текущий диск
    current_drive = navigation.get_current_drive()
    print(f"Текущий диск: {current_drive}")

    # Доступные диски
    drives = navigation.list_available_drives()
    print(f"Доступные диски: {', '.join(drives)}")

    # Текущий путь
    current_path = os.getcwd()
    print(f"Текущий путь: {current_path}")

    # Специальные папки Windows
    print("\nСпециальные папки Windows:")
    special_folders = navigation.get_windows_special_folders()
    for name, path in special_folders.items():
        if os.path.exists(path):
            print(f"  {name}: {path}")

    print("=" * 70)
    print()


def display_main_menu(current_path: str) -> None:
    """Отображение главного меню для Windows"""
    print(f"\nТекущая директория: {current_path}")
    print("-" * 70)
    print("Доступные команды:")
    print("  1. Просмотр содержимого текущей директории")
    print("  2. Статистика текущей директории")
    print("  3. Меню поиска файлов")
    print("  4. Анализ типов файлов")
    print("  5. Переход в родительский каталог (..)")
    print("  6. Переход в подкаталог")
    print("  7. Сменить диск")
    print("  8. Переход в специальную папку Windows")
    print("  0. Выход из программы")
    print("-" * 70)


def handle_windows_navigation(command: str, current_path: str) -> str:
    """Обработка команд навигации в Windows"""
    import navigation

    if command == "5":  # Переход в родительский каталог
        new_path = navigation.move_up(current_path)
        print(f"Переход в: {new_path}")
        return new_path

    elif command == "6":  # Переход в подкаталог
        dir_name = input("Введите имя подкаталога: ").strip()
        if dir_name:
            success, new_path = navigation.move_down(current_path, dir_name)
            if success:
                print(f"Переход в: {new_path}")
                return new_path
            else:
                print(f"Не удалось перейти в '{dir_name}'")

    elif command == "7":  # Сменить диск
        drives = navigation.list_available_drives()
        print("Доступные диски:")
        for i, drive in enumerate(drives, 1):
            print(f"  {i}. {drive}")

        try:
            choice = int(input("Выберите номер диска: "))
            if 1 <= choice <= len(drives):
                new_drive = drives[choice - 1]
                new_path = new_drive + "\\"
                import utils
                valid, msg = utils.validate_windows_path(new_path)
                if valid:
                    os.chdir(new_path)
                    print(f"Переход на диск: {new_drive}")
                    return os.getcwd()
                else:
                    print(f"Ошибка: {msg}")
            else:
                print("Некорректный выбор диска")
        except ValueError:
            print("Введите номер диска")

    elif command == "8":  # Специальные папки Windows
        special_folders = navigation.get_windows_special_folders()
        print("Специальные папки Windows:")
        folders_list = list(special_folders.items())
        for i, (name, path) in enumerate(folders_list, 1):
            if os.path.exists(path):
                print(f"  {i}. {name} ({path})")

        try:
            choice = int(input("Выберите номер папки: "))
            if 1 <= choice <= len(folders_list):
                name, path = folders_list[choice - 1]
                if os.path.exists(path):
                    os.chdir(path)
                    print(f"Переход в: {name}")
                    return os.getcwd()
                else:
                    print(f"Папка '{name}' не найдена")
            else:
                print("Некорректный выбор")
        except ValueError:
            print("Введите номер папки")

    return current_path


def handle_windows_analysis(command: str, current_path: str) -> None:
    """Обработка команд анализа Windows файловой системы"""
    import analysis

    if command == "2":  # Статистика текущей директории
        print(f"\nАнализ директории: {current_path}")
        analysis.show_windows_directory_stats(current_path)

    elif command == "4":  # Анализ типов файлов
        print(f"\nАнализ типов файлов в: {current_path}")
        success, stats = analysis.analyze_windows_file_types(current_path)
        if success:
            print("\nСтатистика по расширениям файлов:")
            print("-" * 50)
            for ext, data in sorted(stats.items(), key=lambda x: -x[1]["size"]):
                if ext:  # Пропускаем файлы без расширения
                    import utils
                    print(f"{ext:10} : {data['count']:4} файлов, {utils.format_size(data['size'])}")
            print("-" * 50)
        else:
            print("Ошибка при анализе типов файлов")


def handle_windows_search(command: str, current_path: str) -> None:
    """Обработка команд поиска в Windows"""
    import search

    if command == "3":
        search.search_menu_handler(current_path)


def run_windows_command(command: str, current_path: str) -> str:
    """Главный обработчик команд с использованием match case"""
    new_path = current_path

    match command:
        case "1":  # Просмотр содержимого текущей директории
            import navigation
            print(f"\nСодержимое директории: {current_path}")
            success, items = navigation.list_directory(current_path)
            if success:
                navigation.format_directory_output(items)
            else:
                print("Ошибка при получении содержимого директории")

        case "2" | "4":  # Анализ и статистика
            handle_windows_analysis(command, current_path)

        case "3":  # Поиск
            handle_windows_search(command, current_path)

        case "5" | "6" | "7" | "8":  # Навигация
            new_path = handle_windows_navigation(command, current_path)

        case "0":  # Выход
            print("Выход из программы...")
            sys.exit(0)

        case _:
            print("Неизвестная команда. Пожалуйста, выберите команду из меню.")

    return new_path


def main() -> NoReturn:
    """Главная функция программы для Windows"""

    # 1. Проверить Windows окружение
    if not check_windows_environment():
        print("\nПрограмма будет завершена.")
        sys.exit(1)

    try:
        # Импортируем Windows-специфичные модули только после проверки
        import navigation
        import analysis
        import search

    except ImportError as e:
        print(f"ОШИБКА: Не удалось импортировать модуль: {e}")
        print("Убедитесь, что все модули находятся в той же папке.")
        sys.exit(1)
    except OSError as e:
        # Windows-специфичные ошибки импорта
        print(f"ОШИБКА Windows: {e}")
        print("Возможно, не хватает системных библиотек.")
        sys.exit(1)

    # 2. Показать баннер
    display_windows_banner()

    # 3. Основной цикл с использованием ВСЕХ модулей
    current_path = os.getcwd()

    while True:
        try:
            display_main_menu(current_path)
            command = input("\nВведите команду: ").strip()
            current_path = run_windows_command(command, current_path)

        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем.")
            break

        except PermissionError:
            print("\nОШИБКА: Отказано в доступе!")
            print("Запустите программу от имени администратора или выберите другой путь.")

        except OSError as e:
            # Обработка Windows-specific OSError
            if hasattr(e, 'winerror'):  # Windows error code
                winerror = e.winerror

                ERROR_ACCESS_DENIED = 5
                ERROR_PATH_NOT_FOUND = 3
                ERROR_INVALID_NAME = 123

                if winerror == ERROR_ACCESS_DENIED:
                    print("\nОШИБКА: Отказано в доступе (код 5)")
                    print("Возможно, у вас нет прав на доступ к этому файлу/папке.")
                elif winerror == ERROR_PATH_NOT_FOUND:
                    print("\nОШИБКА: Путь не найден (код 3)")
                    print("Убедитесь, что путь указан правильно.")
                elif winerror == ERROR_INVALID_NAME:
                    print("\nОШИБКА: Неверное имя файла (код 123)")
                    print("Имя содержит недопустимые символы.")
                else:
                    print(f"\nОШИБКА Windows (код {winerror}): {e}")
            else:
                print(f"\nОШИБКА ОС: {e}")

        except SystemExit:
            raise

        except Exception as e:
            print(f"\nНеожиданная ошибка: {e}")
            print("Тип ошибки:", type(e).__name__)
            print("Продолжаем работу...")

    print("\nСпасибо за использование Windows файлового менеджера!")
    sys.exit(0)


if __name__ == "__main__":
    main()
