from webbrowser import get
from sys import platform
import requests
import os 
import getpass
import hashlib 
import urllib.request

url = "https://mtuci.ru/upload/iblock/864/1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx"
user = getpass.getuser()
def create_path():
    if platform == "linux" or platform == "linux2":
        print('Система определена как linux')
        return '/home/' + user + '/Downloads/1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx'
    elif platform == "darwin":
        print('Система определена как MacOS')
        return '/Users/' + user + '/Downloads/1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx'
    elif platform == "win32":
        print('Система определена как Windows')
        return "C:\\Users\\" + user + "\\Desktop\\" + "1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx"

path_string = create_path()

def check_acsess():
    return urllib.request.urlopen(url).getcode() == 200
        
def is_exist():
    if os.path.exists(path_string) == True:
        return True
    else:
        return False


def get_md5(fname):
    hash_md5 = hashlib.md5()
    with open(path_string, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_timetable():
    file=open(path_string,"wb")
    file_request = requests.get(url)
    file.write(file_request.content)
    file.close()


if check_acsess():
    if is_exist():
        oldmd5 = get_md5(path_string)
        os.remove(path_string)
        download_timetable()
        newmd5 = get_md5(path_string)
        if oldmd5 != newmd5:
            print('Старое расписание заменено новым')
        else:
            print('Расписание не изменилось')
    else:
        download_timetable()
        print('Скачано новое расписание')
else:
    print('Сервер недоступен')