Django-приложение
=====
Данное приложение создано в рамках изучения Django. Сайт имеет функционал регистрации/авторизации пользователей, создания/редактирования/удаления/комментирования постов, редактирования профиля.

Установка
---------
Создайте и активируйте виртуальное окружение, установите необходимые библиотеки:

    pip install -r requirements.txt

Настройка:
---------
Выполните миграции из папки с файлом manage.py:

    python3 manage.py makemigrations
    python3 manage.py migrate

Запуск
-------

В активированном виртуальном окружении введите:

    python3 manage.py runserver
