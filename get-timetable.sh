#!/bin/bash
domain="https://mtuci.ru/upload/iblock/864/1-kurs-_KiIB_10.05.02-Informatsionnaya-bezopasnost-telekommunikatsionnykh-sistem-M-.xlsx"
status=$(curl -Is $domain | head -1)
filename=$(echo $domain | cut -c 36-)
oldhash=$(md5sum ./$filename | cut -c 1-33)
if [[ $status="HTTP/2 200" ]]
then 
	echo "Расписание доступно!"
	echo "Удаляю старый файл"
	rm -f ./$filename
	echo "Скачиваю новый"
	curl -O $domain
	newhash=$(md5sum ./$filename | cut -c 1-33)
	if [ "$newhash" != "$oldhash" ]
	then 
		echo "Загружено новое расаписание!"
	else
		echo "Загруженное раписание не изменилось"
	fi
else 
	echo "Сервер с расписанием недоступен "
fi
