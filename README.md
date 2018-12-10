## my_restore
MYSQL helper for creating and restoring backup copies of tables using the mysqldump utility

### Prerequisites
Tested OS: debian 9
* apt install python3
* apt install percona-server-client-5.7 # containing mysqldump
* pip3 install PyYAML # for parsing yaml files like python dict()

### How to use
Запуск из косоли:
``` python
python3 my_restore.py
```

Минимальные требования для работы, это:
> присутсвие yaml файла с перечисленными базами и таблицам для восстановления `autodump.yml` в формате yaml:
```yaml
restore:
  slave:
    databases: # required key
      database_name_0: # the name of the database which one we want to backup
        table_name_0: # the name of the table that we will backup
          where: False # --where option in mysqldump command (IN BETA!)
          restore_to_db: restore_db # the name of database for restore a saved table. If `False` will be used master database (in our example - database_name_0)
        # the same options for table `table_name_1` in `db database_name_0`
        table_name_1:
          where: False
          restore_to_db: restore_db
```
> присутсвие `.my.cnf` файла для подключения к базам MySQL из которых будут выполняться бэкапы и MySQL сервер, в которые дынне бэкапы будут восстанавливаться
```bash
# by default suffix `Dump` used for restore backups. All options below are required
[clientDump]
host=localhost
user=root
password=Root_Password
port=3306

# by default suffix `Restore` used for restore backups. All options below are required
[clientRestore]
host=localhost
user=root
password=Root_Password
port=3306

```

####скрипт my_restore.py
```python
dumper_instance = RestoreTable(my_cnf='.my.cnf', my_cnf_suffix_dump='mysqldumpDump')
```
* Если аргумент `my_cnf` представлен, то будут использоваться данные для подключения к MySQL бэкапа и восстановления именно из этого файла!
* Если же убрать `my_cnf` и оставить дефолтное значение None, то будут использоваться данные для подключения к мастер серверу и бэкапу из файла `autodump_master.yml` и для восстановления из файла `autodump.yml`


# Что не учтено:
* Логированние с использованием логгера
* Файл `autodump.yml` должен либо очищаться либо выставлять дефолтные занчения для всех существующих бд с опциями `False` (т.е. не бэкапить, пока не указано иное)
* Лок файл, на случай, если одновременно будут выполняться несколько воссатновлений
* Параллельное выполнение с дефолтным регулированием кол-ва тредов
* Бэкап без создания дамп файла (т.е. в потоке. Необходимо тестирование т.к. были найдены негативные отзыва при такой схеме)
* Ключ `where` в файл  `autodump.yml` нуждается в тестировании
* Возможность управления опциями команды `mysqldump`
* Код не покрыт комментариями
* Не тестировалось на таблицах более 1Gb

### Безопасность:
* файл `.my.cnf` возможно необходимо выносить в недоступное для разработчиков пространство
* файл `autodump_master.yml` использует пароль и юзера в почти открытом виде в консоле (удобно использовать при дебаге, но, не безопасно)