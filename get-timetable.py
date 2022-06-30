from sys import platform
import requests
import os 
import getpass
import hashlib

dist_url = "https://mtuci.ru/upload/iblock/864/"
filename = "1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx"
url = dist_url + filename
user = getpass.getuser()


def create_path():
    if "linux" in platform:
        print('Система определена как linux')
        return '/home/' + user + '/Downloads/' + filename
    elif platform == "darwin":
        print('Система определена как MacOS')
        return '/Users/' + user + '/Downloads/' + filename
    elif platform == "win32":
        print('Система определена как Windows')
        return "C:\\Users\\" + user + "\\Desktop\\" + filename
    else:
        return f"{input('Система не определена автоматически. Введите полный путь к нужной директории: ')}/{filename}"


def get_md5(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_timetable(path):
    with open(path, "wb") as file:
        file.write(requests.get(url).content)


if __name__ == '__main__':
    try:
        request = requests.get(url)
        request.raise_for_status()
    except requests.exceptions.ConnectionError as err:
        print("Не удалось получить доступ к сайту")
        raise SystemExit(err)
    except requests.exceptions.HTTPError as err:
        print("Не удалось получить доступ к сайту")
        raise SystemExit(err)
    else:
        path_string = create_path()
        if os.path.exists(path_string):
            oldmd5 = get_md5(path_string)
            os.remove(path_string)
            download_timetable(path_string)
            if oldmd5 != get_md5(path_string):
                print('Старое расписание заменено новым')
            else:
                print('Расписание не изменилось')
        else:
            download_timetable(path_string)
            print('Скачано новое расписание')
