from __future__ import annotations

import json
import os
import getpass
import sys
from hashlib import md5
from dataclasses import dataclass
from sys import platform
from pathlib import Path, WindowsPath

import argparse
import requests
from requests.exceptions import ConnectionError, HTTPError
from bs4 import BeautifulSoup
from typing import Tuple, Dict
from loguru import logger as log


# Имя последнего использованного пользователем файла расписания
cache = Path("cache_timetable.json")
user = getpass.getuser()


@dataclass(init=False, frozen=False)
class Timetable:
    def __init__(self, path, url):
        self.path = path
        self.url = url
        if self.path.name != self.url.name:
            raise ValueError("path и url должны вести к файлу с одинаковым названием")

        with open(cache, 'w') as file:
            json.dump({'path': str(self.path), 'url': str(self.url)}, file)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def is_exists(self) -> bool:
        return self.path.exists()

    @property
    def hash(self) -> str:
        if not self.is_exists:
            raise Exception(f"Невозможно вычислить хэш-сумму, т.к. файл {self.path.absolute()} не существует")

        hash_md5 = md5()
        with open(self.path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    @log.catch()
    def download(self) -> None:
        with open(self.path, "wb") as file:
            file.write(get(rf"https://mtuci.ru{self.url}").content)

    def delete(self) -> None:
        if not self.is_exists:
            raise Exception(f"Файл {self.path} невозможно удалить, т.к. он не существует")
        os.remove(self.path)

    def update_and_check(self):
        old_hash = self.hash
        self.delete()
        self.download()
        new_hash = self.hash
        return new_hash == old_hash


@log.catch()
def configure_flags() -> argparse.Namespace:
    flags_parser = argparse.ArgumentParser()
    flags_parser.add_argument(
        '-n', '--notification',
        action='store_true',
        help="отправлять всплывающие уведомления о выполнении (Только для Linux)",
        required=False,
    )
    flags_parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help="режим для разработчика",
        required=False,
    )
    # TODO: add autorun flag

    return flags_parser.parse_args()


def get(url: str) -> requests.Response:
    """
    "Обертка" для метода `requests.get`
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except (ConnectionError, HTTPError) as err:
        log.error("[x] Не удалось получить доступ к сайту:")
        exit(err)
    else:
        return response


@log.catch()
def parse_timetables() -> Tuple[Path]:
    """
    Получает кортеж файлов расписаний, доступных в момент запроса на сайте.
    """
    # Забираем полную html страницу
    response = get(r"https://mtuci.ru/time-table/").content
    # Подключаем BeautifulSoup, чтобы спарсить нужные ссылки
    soup = BeautifulSoup(response, 'lxml')
    # Перебрав руками, берем именно тот диапазон, в котором находятся только расписания
    soup = soup.find_all('li')[7:-160]
    # Забираем только ссылки на файлы и сохраняем в список
    result = tuple(Path(x.a.attrs['href']) for x in soup)
    return result


@log.catch()
def choose_timetable_url() -> Path | Timetable:
    """
    Предлагаем выбрать нужную таблицу.
    По умолчанию выбор из файла `cache_timetable`
    Общий выбор по индексу выведенного списка всех расписаний с сайта
    """
    # Берем все ссылки доступных расписаний с сайта
    timetables_tuple = parse_timetables()

    print("[i] Введите индекс нужного файла из списка.\n")
    # Сначала отображаем последний использованный пользователем файл расписания
    if cache.exists():
        with open('cache_timetable.json', 'r') as file:
            try:
                cache_data: Dict[str, str] = json.load(file)
            except json.decoder.JSONDecodeError:
                log.debug("Файл `cache_timetable.json` пустой или неверный")
            else:
                cache_timetable = Timetable(Path(cache_data['path']), Path(cache_data['url']))
                print(f"[ ] Как в прошлый раз, проверим файл по url {cache_timetable.url}"
                      f"и сравним с файлом {cache_timetable.path}")
    for i, url in enumerate(timetables_tuple):
        print(f"[{i}] {url.name}")
    choice = input("\n[?] Введите номер: ")

    if (not choice or choice == ' ') and cache.exists():
        return cache_timetable
    elif choice.isdigit():
        choice = int(choice)
        if int(choice) < len(timetables_tuple):
            return timetables_tuple[choice]
    print("[x] Вы ошиблись, попробуйте снова")
    return choose_timetable_url()


@log.catch()
def create_timetable_path(filename: str) -> Path | WindowsPath | False:
    """
    Создает дефолтный путь к сохраняемому файлу, опираясь на ОС пользователя.
    """
    if "linux" in platform:
        print('[+] Система определена как Linux')
        return Path('/home/' + user + '/Downloads/' + filename)
    elif platform == "darwin":
        print('[+] Система определена как MacOS')
        return Path('/Users/' + user + '/Downloads/' + filename)
    elif platform == "win32":
        print('[+] Система определена как Windows')
        return WindowsPath("C:\\Users\\" + user + "\\Desktop\\" + filename)
    else:
        return False


@log.catch()
def choose_path(timetable_url: Path) -> Path:
    """
    Позволяет пользователю выбрать, куда сохранить файл.
    """
    default_path = create_timetable_path(timetable_url.name)
    if default_path:
        print(f"[i] Файл с расписанием сохранится в: {default_path.parent.absolute()}\n"
              f"[!] Оставьте следующее поле пустым или введите другой желаемый путь")
    path = input("[?] Введите существующий путь (без названия файла): ")
    if path and Path(path).is_dir():
        return Path(path + '/' + timetable_url.name)
    elif not path:
        return default_path
    else:
        print("[x] Вы ошиблись, попробуйте снова")
        return choose_path(timetable_url)


@log.catch()
def main(push_notifications: bool = False):
    timetable_url = choose_timetable_url()

    # Если пользователь выбрал расписание из `cache_timetable.json`, то мы сразу получили экземпляр расписания
    if isinstance(timetable_url, Timetable):
        timetable = timetable_url
    else:
        timetable_path = choose_path(timetable_url)
        timetable = Timetable(path=timetable_path, url=timetable_url)

    if timetable.is_exists:
        if timetable.update_and_check():
            print('[-] Расписание не изменилось')
        else:
            print(f'[+] Старое расписание заменено новым ({timetable.path.absolute()})')
    else:
        timetable.download()
        print(f'[+] Скачано новое расписание ({timetable.path.absolute()})')


if __name__ == '__main__':
    flags = configure_flags()

    if flags.debug:
        log.add(Path('error.log'), level='DEBUG', colorize=True, rotation="10 MB", compression='zip')
    else:
        log.remove()
        log.add(sys.stderr, level='WARNING')

    if 'linux' not in platform and flags.notification:
        print("[x] Пока что всплывающие уведомления можно использовать только на Linux")
        flags.notification = False

    try:
        main(flags.notification)
    except (KeyboardInterrupt, SystemExit):
        exit("\n[x] Выполнение прервано")
    else:
        exit("[i] Выполнение окончено успешно")
