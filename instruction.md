# Полная пошаговая инструкция: Демоэкзамен 09.02.07 — ООО «Обувь»

> **Стек:** Python 3.13 · Django 5 · PostgreSQL 18 · UV · VS Code · Windows  
> **Время:** до 5 часов (4ч инвариант + 1ч вариатив)  
> **Баллов:** 100 (75 инвариант + 25 вариатив)

---

## СОДЕРЖАНИЕ

1. [Подготовка окружения](#1-подготовка-окружения)
2. [Настройка PostgreSQL](#2-настройка-postgresql)
3. [Создание Django проекта с UV](#3-создание-django-проекта-с-uv)
4. [ВАРИАНТ А — SQL + inspectdb](#4-вариант-а--sql--inspectdb)
5. [ВАРИАНТ Б — Модели Django + миграции](#5-вариант-б--модели-django--миграции)
6. [Скрипт импорта CSV (вариатив)](#6-скрипт-импорта-csv-вариатив)
7. [ER-диаграмма в PDF](#7-er-диаграмма-в-pdf)
8. [URLs и структура приложения](#8-urls-и-структура-приложения)
9. [Views — авторизация](#9-views--авторизация)
10. [Views — список товаров](#10-views--список-товаров)
11. [Фильтры, сортировка, поиск — подробно](#11-фильтры-сортировка-поиск--подробно)
12. [Views — форма добавления/редактирования товара](#12-views--форма-добавленияредактирования-товара)
13. [Views — удаление товара](#13-views--удаление-товара)
14. [Views — заказы](#14-views--заказы)
15. [Шаблоны и CSS](#15-шаблоны-и-css)
16. [Вариативная часть — cleanup неиспользуемых фото](#16-вариативная-часть--cleanup-неиспользуемых-фото)
17. [SQL дамп и Git](#17-sql-дамп-и-git)
18. [Чеклист перед сдачей](#18-чеклист-перед-сдачей)
19. [Быстрые команды](#19-быстрые-команды)
20. [Очистка истории команд PowerShell](#20-очистка-истории-команд-powershell)

---

## 1. Подготовка окружения

### Что должно быть на экзаменационном ПК
- Python 3.13+
- PostgreSQL 18 (уже запущен как служба Windows)
- VS Code
- Git
- UV

### Ресурсы из Приложения 2 (дадут на экзамене)
- `picture.png` — заглушка для товаров без фото
- `Icon.ico` — иконка приложения
- Логотип компании
- CSV-файлы с пометкой `import`

### Цвета стиля (запомнить)

| Назначение | HEX |
|---|---|
| Основной фон | `#FFFFFF` |
| Дополнительный фон | `#7FFF00` |
| Акцент | `#00FA9A` |
| Скидка > 15% (фон строки) | `#2E8B57` |
| Нет на складе (фон строки) | `lightblue` |
| Перечёркнутая цена | красный шрифт |
| Итоговая цена | чёрный шрифт |

Шрифт везде: **Times New Roman**

---

## 2. Настройка PostgreSQL

### Шаг 2.1 — Добавить в PATH (если не добавлен)
Система → Переменные среды → PATH → добавить:
```
C:\Program Files\PostgreSQL\18\bin
```
Перезапустить PowerShell / VS Code.

### Шаг 2.2 — Создать базу данных
```powershell
psql -U postgres
```

> ⚠️ **Warning:** если команда `psql` не найдена — найди `psql.exe` вручную через Проводник или Пуск и запусти напрямую:
> ```powershell
> & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
> ```

Внутри psql:
```sql
CREATE DATABASE shoe_store OWNER postgres;
\q
```

### Шаг 2.3 — Запомнить данные подключения

```
HOST:     localhost
PORT:     5432
NAME:     shoe_store
USER:     postgres
PASSWORD: (пароль заданный при установке — обычно postgres)
```

---

## 3. Создание Django проекта с UV

### Создать папку и проект

```powershell
mkdir shoe_store
cd shoe_store

uv init --no-readme
uv venv
.venv\Scripts\activate

uv add django psycopg2-binary pillow

django-admin startproject config .
python manage.py startapp core
```

### Создать структуру папок

```powershell
mkdir core\templates\core
mkdir core\management
mkdir core\management\commands
mkdir static\css
mkdir static\images
mkdir media\products
mkdir import_data

type nul > core\management\__init__.py
type nul > core\management\commands\__init__.py
```

### Скопировать ресурсы

Из архива Приложения 2:
- `picture.png` → `static\images\picture.png`
- `Icon.ico` → `static\images\Icon.ico`
- логотип → `static\images\logo.png`
- CSV файлы → `import_data\`

### config/settings.py

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-demoexam-key-2026'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shoe_store',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

---

## 4. ВАРИАНТ А — SQL + inspectdb

> Создаём таблицы вручную SQL скриптом, затем Django читает их через `inspectdb`.  
> **Плюсы:** быстро, не надо думать о миграциях, сразу есть рабочая БД с данными.  
> **Когда выбирать:** если уверен в SQL и хочешь сначала данные, а потом код.

### Шаг А1 — Написать schema.sql

```sql
-- Роли пользователей
CREATE TABLE role (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Пользователи системы
CREATE TABLE "user" (
    id          SERIAL PRIMARY KEY,
    last_name   VARCHAR(100) NOT NULL,
    first_name  VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100) DEFAULT '',
    login       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role_id     INTEGER NOT NULL REFERENCES role(id)
);

-- Категории товаров
CREATE TABLE category (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Производители
CREATE TABLE manufacturer (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- Поставщики
CREATE TABLE supplier (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- Товары
CREATE TABLE product (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES category(id),
    description     TEXT DEFAULT '',
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturer(id),
    supplier_id     INTEGER NOT NULL REFERENCES supplier(id),
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    unit            VARCHAR(50) DEFAULT 'пара',
    quantity        INTEGER DEFAULT 0 CHECK (quantity >= 0),
    discount        NUMERIC(5,2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    image           VARCHAR(500) DEFAULT ''
);

-- Пункты выдачи
CREATE TABLE pickup_point (
    id      SERIAL PRIMARY KEY,
    address VARCHAR(500) NOT NULL
);

-- Заказы
CREATE TABLE "order" (
    id              SERIAL PRIMARY KEY,
    article         VARCHAR(100) NOT NULL UNIQUE,
    status          VARCHAR(50) DEFAULT 'new',
    pickup_point_id INTEGER NOT NULL REFERENCES pickup_point(id),
    order_date      DATE NOT NULL,
    delivery_date   DATE
);

-- Позиции заказа
CREATE TABLE order_item (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES product(id)
);

-- Начальные данные: роли
INSERT INTO role (name) VALUES ('guest'), ('client'), ('manager'), ('admin');

-- Тестовые пользователи
INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Иванов', 'Иван', 'Иванович', 'admin', 'admin', 4);

INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Петров', 'Пётр', 'Петрович', 'manager', 'manager', 3);

INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Сидоров', 'Сидор', 'Сидорович', 'client', 'client', 2);
```

### Шаг А2 — Выполнить скрипт

```powershell
psql -U postgres -d shoe_store -f schema.sql
```

### Шаг А3 — Сгенерировать models.py через inspectdb

```powershell
python manage.py inspectdb > core/models.py
```

### Шаг А4 — Подправить models.py

`inspectdb` генерирует рабочий код, но нужно добавить вспомогательные методы
и убедиться что `id` прописан явно, `managed = False` стоит в каждой модели.

```python
from django.db import models


class Role(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = 'role'

    def __str__(self):
        return self.name


class User(models.Model):
    id = models.IntegerField(primary_key=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default='')
    login = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, db_column='role_id')

    class Meta:
        managed = False
        db_table = 'user'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def get_full_name(self):
        """Возвращает полное ФИО пользователя"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


class Category(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        managed = False
        db_table = 'category'

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        managed = False
        db_table = 'manufacturer'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        managed = False
        db_table = 'supplier'

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, db_column='category_id'
    )
    description = models.TextField(blank=True, default='')
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, db_column='manufacturer_id'
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, db_column='supplier_id'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='пара')
    quantity = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Путь к файлу хранится строкой, не через ImageField
    image = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        managed = False
        db_table = 'product'

    def __str__(self):
        return self.name

    def get_final_price(self):
        """Итоговая цена с учётом скидки"""
        if self.discount > 0:
            return round(self.price * (1 - self.discount / 100), 2)
        return self.price

    def has_discount(self):
        return self.discount > 0

    def is_big_discount(self):
        """Скидка превышает 15% — нужна зелёная подсветка"""
        return self.discount > 15

    def is_in_stock(self):
        return self.quantity > 0


class PickupPoint(models.Model):
    id = models.IntegerField(primary_key=True)
    address = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'pickup_point'

    def __str__(self):
        return self.address


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]

    id = models.IntegerField(primary_key=True)
    article = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    pickup_point = models.ForeignKey(
        PickupPoint, on_delete=models.PROTECT, db_column='pickup_point_id'
    )
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'order'

    def __str__(self):
        return f'Заказ {self.article}'


class OrderItem(models.Model):
    id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        db_column='order_id', related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, db_column='product_id'
    )

    class Meta:
        managed = False
        db_table = 'order_item'
```

### Шаг А5 — Применить миграции (только для сессий)

Таблицы уже созданы через SQL, Django их не трогает (`managed = False`).
Нужно только создать таблицу сессий:

```powershell
python manage.py migrate
```

---

## 5. ВАРИАНТ Б — Модели Django + миграции

> Пишем модели в `models.py`, Django сам создаёт таблицы через миграции.  
> **Плюсы:** чисто по-джанговски, не нужно писать SQL вручную.  
> **Когда выбирать:** если хочешь работать только в Python без прямого SQL.

### Шаг Б1 — Написать models.py

Берём те же модели что в Варианте А, но:
- убираем `id = models.IntegerField(primary_key=True)` из каждой модели — Django добавит `id` сам
- убираем `managed = False` из каждого `Meta` — Django будет управлять таблицами
- убираем `db_column='role_id'` и подобные — Django сам правильно назовёт колонки FK

```python
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'role'

    def __str__(self):
        return self.name


class User(models.Model):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default='')
    login = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def get_full_name(self):
        """Возвращает полное ФИО пользователя"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'manufacturer'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'supplier'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField(blank=True, default='')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='пара')
    quantity = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    image = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.name

    def get_final_price(self):
        """Итоговая цена с учётом скидки"""
        if self.discount > 0:
            return round(self.price * (1 - self.discount / 100), 2)
        return self.price

    def has_discount(self):
        return self.discount > 0

    def is_big_discount(self):
        """Скидка превышает 15% — нужна зелёная подсветка"""
        return self.discount > 15

    def is_in_stock(self):
        return self.quantity > 0


class PickupPoint(models.Model):
    address = models.CharField(max_length=500)

    class Meta:
        db_table = 'pickup_point'

    def __str__(self):
        return self.address


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]

    article = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.PROTECT)
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'order'

    def __str__(self):
        return f'Заказ {self.article}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    class Meta:
        db_table = 'order_item'
```

### Шаг Б2 — Создать и применить миграции

```powershell
python manage.py makemigrations
python manage.py migrate
```

### Шаг Б3 — Заполнить начальные данные

```powershell
psql -U postgres -d shoe_store
```

```sql
INSERT INTO role (name) VALUES ('guest'), ('client'), ('manager'), ('admin');

INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Иванов', 'Иван', 'Иванович', 'admin', 'admin', 4);

INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Петров', 'Пётр', 'Петрович', 'manager', 'manager', 3);

INSERT INTO "user" (last_name, first_name, middle_name, login, password, role_id)
VALUES ('Сидоров', 'Сидор', 'Сидорович', 'client', 'client', 2);
\q
```

---

## 6. Скрипт импорта xlsx (вариатив)

Создать `core/management/commands/import_data.py`.

Данные берутся из xlsx файлов в папке `import_data/` рядом с `manage.py`:
- `Tovar.xlsx` — товары (артикул, наименование, цена, поставщик, производитель, категория, скидка, количество, описание, фото)
- `user_import.xlsx` — пользователи (роль, ФИО, логин, пароль)
- `Заказ_import.xlsx` — заказы (номер, артикулы товаров с количеством, даты, пункт выдачи по индексу, ФИО клиента, код получения, статус)
- `Пункты выдачи_import.xlsx` — адреса пунктов выдачи (без заголовка, каждая строка — адрес)

> ⚠️ **Важно:** поле "Артикул заказа" содержит пары артикул+количество через запятую:  
> `А112Т4, 2, F635R4, 2` → товар А112Т4 в количестве 2шт, товар F635R4 в количестве 2шт.  
> "Адрес пункта выдачи" — числовой индекс (1-based) строки в файле пунктов выдачи.

> ⚠️ **Важно:** название файла пунктов выдачи содержит пробел — `Пункты выдачи_import.xlsx`.  
> Перед запуском убедись что все xlsx файлы скопированы в папку `import_data/`.

```python
import os
import pandas as pd
from django.core.management.base import BaseCommand
from core.models import (
    Role, User, Category, Manufacturer, Supplier,
    Product, PickupPoint, Order, OrderItem
)

ROLE_MAP = {
    'Администратор': 'admin',
    'Менеджер':      'manager',
    'Клиент':        'client',
    'Гость':         'guest',
}

STATUS_MAP = {
    'Новый':          'new',
    'В обработке':    'processing',
    'Готов к выдаче': 'ready',
    'Завершен':       'completed',
    'Завершён':       'completed',
    'Отменён':        'cancelled',
    'Отменен':        'cancelled',
}


class Command(BaseCommand):
    help = 'Импорт данных из xlsx файлов в папке import_data/'

    def handle(self, *args, **options):
        self.stdout.write('Начало импорта...')

        self.data_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                )
            ),
            'import_data'
        )

        self.ensure_roles()
        self.import_pickup_points()
        self.import_products()
        self.import_users()
        self.import_orders()

        self.stdout.write(self.style.SUCCESS('Импорт завершён!'))

    def read_xlsx(self, filename):
        """Читает xlsx файл, возвращает DataFrame или None"""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING(f'Не найден: {filename}'))
            return None
        return pd.read_excel(path, dtype=str).fillna('')

    def _parse_date(self, value):
        """Парсит дату из строки, возвращает date или None"""
        if not value or str(value).strip() in ('', 'nan'):
            return None
        try:
            # dayfirst=False потому что даты в формате YYYY-MM-DD
            result = pd.to_datetime(value, dayfirst=False, errors='coerce')
            return None if pd.isnull(result) else result.date()
        except Exception:
            return None

    def ensure_roles(self):
        """Создаёт базовые роли если их нет"""
        for role_name in ('guest', 'client', 'manager', 'admin'):
            Role.objects.get_or_create(name=role_name)
        self.stdout.write('Роли: готово')

    def import_pickup_points(self):
        """
        Импорт пунктов выдачи из Пункты выдачи_import.xlsx.
        Файл не имеет заголовка — каждая строка это адрес.
        Читаем с header=None чтобы не потерять первую строку.
        Сохраняем список адресов в self.pickup_index для использования в import_orders.
        """
        path = os.path.join(self.data_dir, 'Пункты выдачи_import.xlsx')
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING('Не найден: Пункты выдачи_import.xlsx'))
            self.pickup_index = []
            return

        # header=None — все строки это данные, первая не заголовок
        df = pd.read_excel(path, header=None, dtype=str).fillna('')
        self.pickup_index = []  # список PickupPoint в порядке строк файла (1-based индекс)

        for _, row in df.iterrows():
            address = str(row.iloc[0]).strip()
            if address:
                pp, _ = PickupPoint.objects.get_or_create(address=address)
                self.pickup_index.append(pp)

        self.stdout.write(f'Пункты выдачи: {len(self.pickup_index)} записей')

    def import_products(self):
        """
        Импорт товаров из Tovar.xlsx.
        Колонки: Артикул, Наименование товара, Единица измерения, Цена,
                 Поставщик, Производитель, Категория товара,
                 Действующая скидка, Кол-во на складе, Описание товара, Фото
        """
        df = self.read_xlsx('Tovar.xlsx')
        if df is None:
            return

        for _, row in df.iterrows():
            category, _     = Category.objects.get_or_create(
                name=row['Категория товара'].strip()
            )
            manufacturer, _ = Manufacturer.objects.get_or_create(
                name=row['Производитель'].strip()
            )
            supplier, _     = Supplier.objects.get_or_create(
                name=row['Поставщик'].strip()
            )

            try:
                price = float(row['Цена'])
            except (ValueError, TypeError):
                price = 0
            try:
                quantity = int(float(row['Кол-во на складе']))
            except (ValueError, TypeError):
                quantity = 0
            try:
                discount = float(row['Действующая скидка'])
            except (ValueError, TypeError):
                discount = 0

            Product.objects.get_or_create(
                article=row['Артикул'].strip(),
                defaults={
                    'name':         row['Наименование товара'].strip(),
                    'category':     category,
                    'description':  row.get('Описание товара', ''),
                    'manufacturer': manufacturer,
                    'supplier':     supplier,
                    'price':        price,
                    'unit':         row.get('Единица измерения', 'шт.') or 'шт.',
                    'quantity':     quantity,
                    'discount':     discount,
                    'image':        row.get('Фото', ''),
                }
            )
        self.stdout.write(f'Товары: {len(df)} записей')

    def import_users(self):
        """
        Импорт пользователей из user_import.xlsx.
        Колонки: Роль сотрудника, ФИО, Логин, Пароль
        """
        df = self.read_xlsx('user_import.xlsx')
        if df is None:
            return

        for _, row in df.iterrows():
            role_name = ROLE_MAP.get(row['Роль сотрудника'].strip(), 'client')
            role = Role.objects.get(name=role_name)

            parts       = row['ФИО'].strip().split()
            last_name   = parts[0] if len(parts) > 0 else ''
            first_name  = parts[1] if len(parts) > 1 else ''
            middle_name = parts[2] if len(parts) > 2 else ''

            User.objects.get_or_create(
                login=row['Логин'].strip(),
                defaults={
                    'last_name':   last_name,
                    'first_name':  first_name,
                    'middle_name': middle_name,
                    'password':    row['Пароль'].strip(),
                    'role':        role,
                }
            )
        self.stdout.write(f'Пользователи: {len(df)} записей')

    def import_orders(self):
        """
        Импорт заказов из Заказ_import.xlsx.
        Колонки: Номер заказа, Артикул заказа, Дата заказа, Дата доставки,
                 Адрес пункта выдачи, ФИО авторизированного клиента,
                 Код для получения, Статус заказа

        Артикул заказа — строка вида «А112Т4, 2, F635R4, 2»:
        чередующиеся пары артикул товара + количество.

        Адрес пункта выдачи — числовой индекс (1-based) в таблице пунктов выдачи.

        ФИО клиента — ищем по имени в таблице User.
        """
        df = self.read_xlsx('Заказ_import.xlsx')
        if df is None:
            return

        for _, row in df.iterrows():
            order_date    = self._parse_date(row['Дата заказа'])
            delivery_date = self._parse_date(row['Дата доставки'])

            if not order_date:
                self.stdout.write(self.style.WARNING(
                    f'Пропущен заказ {row["Номер заказа"]}: невалидная дата'
                ))
                continue

            # Пункт выдачи — числовой индекс (1-based) по порядку строк в файле
            try:
                pp_index = int(float(row['Адрес пункта выдачи'])) - 1
                pickup_point = self.pickup_index[pp_index]
            except (ValueError, IndexError) as e:
                self.stdout.write(self.style.WARNING(
                    f'Пункт выдачи не найден для заказа {row["Номер заказа"]}: {e}'
                ))
                continue

            # Ищем пользователя по ФИО
            user = None
            fio = row.get('ФИО авторизированного клиента', '').strip()
            if fio:
                parts = fio.split()
                if len(parts) >= 2:
                    try:
                        user = User.objects.get(
                            last_name=parts[0],
                            first_name=parts[1]
                        )
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        pass

            status  = STATUS_MAP.get(row['Статус заказа'].strip(), 'new')
            article = str(row['Номер заказа']).strip()
            code    = str(row.get('Код для получения', '')).strip()

            order, created = Order.objects.get_or_create(
                article=article,
                defaults={
                    'status':        status,
                    'pickup_point':  pickup_point,
                    'user':          user,
                    'code':          code,
                    'order_date':    order_date,
                    'delivery_date': delivery_date,
                }
            )

            if created:
                # Парсим «А112Т4, 2, F635R4, 2» как пары артикул+количество
                raw = str(row.get('Артикул заказа', '')).strip()
                if not raw:
                    continue

                parts = [p.strip() for p in raw.split(',')]
                # Идём по парам: parts[0]=артикул, parts[1]=количество, ...
                i = 0
                while i < len(parts) - 1:
                    product_article = parts[i]
                    try:
                        qty = int(parts[i + 1])
                    except (ValueError, IndexError):
                        qty = 1
                    i += 2

                    try:
                        product = Product.objects.get(article=product_article)
                        OrderItem.objects.get_or_create(
                            order=order,
                            product=product,
                            defaults={'quantity': qty}
                        )
                    except Product.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'Товар не найден: «{product_article}» (заказ {article})'
                        ))

        self.stdout.write(f'Заказы: {len(df)} записей')

```

Перед первым импортом убедись что таблицы пусты. Если нужно переимпортировать:
```sql
TRUNCATE order_item, "order", pickup_point RESTART IDENTITY CASCADE;
```

```powershell
python manage.py import_data
```

---

## 7. ER-диаграмма в PDF

1. Открыть **draw.io** (десктоп или diagrams.net)
2. New → Blank → добавить таблицы через Entity Relationship
3. Добавить все 9 таблиц с полями, PK, FK
4. Нарисовать связи:
   - `user` → `role`
   - `product` → `category`, `manufacturer`, `supplier`
   - `order` → `pickup_point`
   - `order_item` → `order`, `product`
5. File → Export as → PDF → сохранить как `er_diagram.pdf`

---

## 8. URLs и структура приложения

### config/urls.py

```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from core import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_create_view, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update_view, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),

    path('orders/', views.order_list_view, name='order_list'),
    path('orders/add/', views.order_create_view, name='order_create'),
    path('orders/<int:pk>/edit/', views.order_update_view, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete_view, name='order_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 9. Views — авторизация

### core/views.py

```python
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from PIL import Image as PilImage

from .models import (
    User, Product, Category, Manufacturer,
    Supplier, Order, PickupPoint, OrderItem
)


def login_view(request):
    """Страница входа — первое что видит пользователь"""
    if request.method == 'POST':
        login = request.POST.get('login', '').strip()
        password = request.POST.get('password', '').strip()

        if not login or not password:
            return render(request, 'core/login.html', {
                'error': 'Введите логин и пароль.'
            })

        try:
            user = User.objects.select_related('role').get(
                login=login, password=password
            )
            request.session['user_id'] = user.id
            request.session['user_role'] = user.role.name
            request.session['user_full_name'] = user.get_full_name()
            return redirect('product_list')
        except User.DoesNotExist:
            return render(request, 'core/login.html', {
                'error': 'Неверный логин или пароль.'
            })

    return render(request, 'core/login.html')


def logout_view(request):
    """Выход — очищаем сессию"""
    request.session.flush()
    return redirect('login')
```

---

## 10. Views — список товаров

```python
def product_list_view(request):
    """
    Список товаров для всех ролей.
    Поиск/фильтр/сортировка — только менеджер и администратор.
    """
    role = request.session.get('user_role', 'guest')

    products = Product.objects.select_related(
        'category', 'manufacturer', 'supplier'
    ).all()

    search_query = ''
    supplier_filter = ''
    sort_by = ''

    if role in ('manager', 'admin'):
        # Поиск по всем текстовым полям одновременно
        search_query = request.GET.get('search', '').strip()
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(manufacturer__name__icontains=search_query) |
                Q(supplier__name__icontains=search_query) |
                Q(unit__icontains=search_query)
            )

        # Фильтр по поставщику
        supplier_filter = request.GET.get('supplier', '').strip()
        if supplier_filter:
            products = products.filter(supplier__name=supplier_filter)

        # Сортировка по количеству на складе
        sort_by = request.GET.get('sort', '')
        if sort_by == 'quantity_asc':
            products = products.order_by('quantity')
        elif sort_by == 'quantity_desc':
            products = products.order_by('-quantity')

    suppliers = Supplier.objects.all()

    return render(request, 'core/product_list.html', {
        'products': products,
        'role': role,
        'suppliers': suppliers,
        'search_query': search_query,
        'supplier_filter': supplier_filter,
        'sort_by': sort_by,
        'user_full_name': request.session.get('user_full_name', ''),
    })
```

---

## 11. Фильтры, сортировка, поиск — подробно

Всё реализовано в `product_list_view` в `views.py` и в шаблоне `product_list.html`.
Доступно только менеджеру и администратору. Все параметры передаются через GET и применяются совместно — порядок важен: сначала поиск, потом фильтр по скидке, потом сортировка.

### Поиск

Поиск по всем текстовым полям одновременно через `Q`-объекты:

```python
search_query = request.GET.get('search', '').strip()
if search_query:
    products = products.filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(category__name__icontains=search_query) |
        Q(manufacturer__name__icontains=search_query) |
        Q(supplier__name__icontains=search_query) |
        Q(unit__icontains=search_query)
    )
```

В шаблоне — `<input>` с JS debounce 300мс, перезагружает страницу с параметром `?search=...`.

### Фильтр по поставщику

Закомментирован, оставлен для возможного возврата:

```python
# supplier_filter = request.GET.get('supplier', '').strip()
# if supplier_filter:
#     products = products.filter(supplier__name=supplier_filter)
```

В шаблоне `<select>` по поставщику также закомментирован через `{% comment %}`.

### Фильтр по диапазону скидки

Четыре диапазона — 0–11%, 11–15%, 15–19%, более 19%:

```python
discount_range = request.GET.get('discount_range', '').strip()
if discount_range == '0-11':
    products = products.filter(discount__gte=0, discount__lt=11)
elif discount_range == '11-15':
    products = products.filter(discount__gte=11, discount__lte=15)
elif discount_range == '15-19':
    products = products.filter(discount__gt=15, discount__lte=19)
elif discount_range == '19+':
    products = products.filter(discount__gt=19)
```

В шаблоне:

```html
<select id="discount_range">
    <option value="">Любая скидка</option>
    <option value="0-11"  {% if discount_range == '0-11'  %}selected{% endif %}>0–11%</option>
    <option value="11-15" {% if discount_range == '11-15' %}selected{% endif %}>11–15%</option>
    <option value="15-19" {% if discount_range == '15-19' %}selected{% endif %}>15–19%</option>
    <option value="19+"   {% if discount_range == '19+'   %}selected{% endif %}>Более 19%</option>
</select>
```

### Сортировка

Четыре варианта — количество и цена в обе стороны:

```python
sort_by = request.GET.get('sort', '')
if sort_by == 'quantity_asc':
    products = products.order_by('quantity')
elif sort_by == 'quantity_desc':
    products = products.order_by('-quantity')
elif sort_by == 'price_asc':
    products = products.order_by('price')
elif sort_by == 'price_desc':
    products = products.order_by('-price')
```

В шаблоне:

```html
<select id="sort">
    <option value="">Без сортировки</option>
    <option value="quantity_asc"  {% if sort_by == 'quantity_asc'  %}selected{% endif %}>Количество ↑</option>
    <option value="quantity_desc" {% if sort_by == 'quantity_desc' %}selected{% endif %}>Количество ↓</option>
    <option value="price_asc"     {% if sort_by == 'price_asc'     %}selected{% endif %}>Цена ↑</option>
    <option value="price_desc"    {% if sort_by == 'price_desc'    %}selected{% endif %}>Цена ↓</option>
</select>
```

### JS — применение без кнопки

Все фильтры срабатывают сразу при изменении. Параметры сохраняются вместе в URL — сортировка не сбрасывается при смене фильтра:

```javascript
function applyFilters() {
    const params = new URLSearchParams();
    const search         = document.getElementById('search').value;
    const discount_range = document.getElementById('discount_range').value;
    const sort           = document.getElementById('sort').value;
    if (search)         params.set('search', search);
    if (discount_range) params.set('discount_range', discount_range);
    if (sort)           params.set('sort', sort);
    window.location.href = '/products/?' + params.toString();
}

let timer;
document.getElementById('search').addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(applyFilters, 300);  // debounce 300мс
});
document.getElementById('discount_range').addEventListener('change', applyFilters);
document.getElementById('sort').addEventListener('change', applyFilters);
```

### Защита от двух окон редактирования

Флаг в сессии в `product_update_view` — если открыт другой товар, показываем ошибку:

```python
editing = request.session.get('editing_product')
if editing and editing != pk:
    return render(request, 'core/product_list.html', {
        'error': 'Уже открыто окно редактирования другого товара. Закройте его перед тем как открыть новое.',
        ...
    })
request.session['editing_product'] = pk
# ... редактирование ...
request.session.pop('editing_product', None)  # снимаем после сохранения
```

При выходе `session.flush()` снимает блокировку автоматически.

---

## 12. Views — форма добавления/редактирования товара

```python
def product_create_view(request):
    """Добавление товара — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()
    suppliers = Supplier.objects.all()
    errors = {}

    if request.method == 'POST':
        name            = request.POST.get('name', '').strip()
        category_id     = request.POST.get('category')
        description     = request.POST.get('description', '').strip()
        manufacturer_id = request.POST.get('manufacturer')
        supplier_id     = request.POST.get('supplier')
        price           = request.POST.get('price', '').strip()
        unit            = request.POST.get('unit', '').strip()
        quantity        = request.POST.get('quantity', '').strip()
        discount        = request.POST.get('discount', '0').strip()

        if not name:
            errors['name'] = 'Укажите наименование товара.'
        try:
            price_val = float(price)
            if price_val < 0:
                errors['price'] = 'Цена не может быть отрицательной.'
        except ValueError:
            errors['price'] = 'Введите корректную цену.'
        try:
            quantity_val = int(quantity)
            if quantity_val < 0:
                errors['quantity'] = 'Количество не может быть отрицательным.'
        except ValueError:
            errors['quantity'] = 'Введите корректное количество.'

        if not errors:
            product = Product(
                name=name,
                category_id=category_id,
                description=description,
                manufacturer_id=manufacturer_id,
                supplier_id=supplier_id,
                price=price_val,
                unit=unit,
                quantity=quantity_val,
                discount=float(discount) if discount else 0,
            )
            if 'image' in request.FILES:
                product.image = save_product_image(request.FILES['image'])
            product.save()
            return redirect('product_list')

    return render(request, 'core/product_form.html', {
        'categories': categories,
        'manufacturers': manufacturers,
        'suppliers': suppliers,
        'errors': errors,
        'title': 'Добавить товар',
        'is_create': True,
        'role': request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def product_update_view(request, pk):
    """Редактирование товара — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()
    suppliers = Supplier.objects.all()
    errors = {}

    if request.method == 'POST':
        name            = request.POST.get('name', '').strip()
        category_id     = request.POST.get('category')
        description     = request.POST.get('description', '').strip()
        manufacturer_id = request.POST.get('manufacturer')
        supplier_id     = request.POST.get('supplier')
        price           = request.POST.get('price', '').strip()
        unit            = request.POST.get('unit', '').strip()
        quantity        = request.POST.get('quantity', '').strip()
        discount        = request.POST.get('discount', '0').strip()

        if not name:
            errors['name'] = 'Укажите наименование товара.'
        try:
            price_val = float(price)
            if price_val < 0:
                errors['price'] = 'Цена не может быть отрицательной.'
        except ValueError:
            errors['price'] = 'Введите корректную цену.'
        try:
            quantity_val = int(quantity)
            if quantity_val < 0:
                errors['quantity'] = 'Количество не может быть отрицательным.'
        except ValueError:
            errors['quantity'] = 'Введите корректное количество.'

        if not errors:
            product.name            = name
            product.category_id     = category_id
            product.description     = description
            product.manufacturer_id = manufacturer_id
            product.supplier_id     = supplier_id
            product.price           = price_val
            product.unit            = unit
            product.quantity        = quantity_val
            product.discount        = float(discount) if discount else 0

            if 'image' in request.FILES:
                # Удаляем старое фото с диска
                if product.image:
                    old_path = os.path.join('media', product.image)
                    if os.path.isfile(old_path):
                        os.remove(old_path)
                product.image = save_product_image(request.FILES['image'])

            product.save()
            return redirect('product_list')

    return render(request, 'core/product_form.html', {
        'product': product,
        'categories': categories,
        'manufacturers': manufacturers,
        'suppliers': suppliers,
        'errors': errors,
        'title': f'Редактировать: {product.name}',
        'is_create': False,
        'role': request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def save_product_image(image_file):
    """
    Сохраняет фото товара с ресайзом до 300x200 через Pillow.
    Возвращает относительный путь для хранения в БД.
    """
    img = PilImage.open(image_file)
    img = img.resize((300, 200), PilImage.LANCZOS)

    save_path = os.path.join('media', 'products', image_file.name)
    img.save(save_path)

    return f'products/{image_file.name}'
```

---

## 13. Views — удаление товара

```python
def product_delete_view(request, pk):
    """Удаление товара — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        # Нельзя удалить товар, который есть в заказах
        if OrderItem.objects.filter(product=product).exists():
            return render(request, 'core/product_list.html', {
                'error': (
                    f'Нельзя удалить товар «{product.name}»: '
                    f'он присутствует в заказах.'
                ),
                'products': Product.objects.select_related(
                    'category', 'manufacturer', 'supplier'
                ).all(),
                'suppliers': Supplier.objects.all(),
                'role': request.session.get('user_role'),
                'user_full_name': request.session.get('user_full_name', ''),
            })

        # Удаляем фото с диска
        if product.image:
            image_path = os.path.join('media', product.image)
            if os.path.isfile(image_path):
                os.remove(image_path)

        product.delete()
        return redirect('product_list')

    return redirect('product_list')
```

---

## 14. Views — заказы

```python
def order_list_view(request):
    """Список заказов — менеджер и администратор"""
    if request.session.get('user_role') not in ('manager', 'admin'):
        return redirect('login')

    orders = Order.objects.select_related('pickup_point').all()

    return render(request, 'core/order_list.html', {
        'orders': orders,
        'role': request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_create_view(request):
    """Добавление заказа — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    pickup_points = PickupPoint.objects.all()
    errors = {}

    if request.method == 'POST':
        article         = request.POST.get('article', '').strip()
        status          = request.POST.get('status', 'new')
        pickup_point_id = request.POST.get('pickup_point')
        order_date      = request.POST.get('order_date')
        delivery_date   = request.POST.get('delivery_date') or None

        if not article:
            errors['article'] = 'Укажите артикул заказа.'
        if not order_date:
            errors['order_date'] = 'Укажите дату заказа.'

        if not errors:
            Order.objects.create(
                article=article,
                status=status,
                pickup_point_id=pickup_point_id,
                order_date=order_date,
                delivery_date=delivery_date,
            )
            return redirect('order_list')

    return render(request, 'core/order_form.html', {
        'pickup_points': pickup_points,
        'errors': errors,
        'status_choices': Order.STATUS_CHOICES,
        'title': 'Добавить заказ',
        'is_create': True,
        'role': request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_update_view(request, pk):
    """Редактирование заказа — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    order = get_object_or_404(Order, pk=pk)
    pickup_points = PickupPoint.objects.all()
    errors = {}

    if request.method == 'POST':
        article         = request.POST.get('article', '').strip()
        status          = request.POST.get('status', 'new')
        pickup_point_id = request.POST.get('pickup_point')
        order_date      = request.POST.get('order_date')
        delivery_date   = request.POST.get('delivery_date') or None

        if not article:
            errors['article'] = 'Укажите артикул заказа.'
        if not order_date:
            errors['order_date'] = 'Укажите дату заказа.'

        if not errors:
            order.article          = article
            order.status           = status
            order.pickup_point_id  = pickup_point_id
            order.order_date       = order_date
            order.delivery_date    = delivery_date
            order.save()
            return redirect('order_list')

    return render(request, 'core/order_form.html', {
        'order': order,
        'pickup_points': pickup_points,
        'errors': errors,
        'status_choices': Order.STATUS_CHOICES,
        'title': f'Редактировать заказ: {order.article}',
        'is_create': False,
        'role': request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_delete_view(request, pk):
    """Удаление заказа — только администратор"""
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.delete()
        return redirect('order_list')

    return redirect('order_list')
```

---

## 15. Шаблоны и CSS

### core/templates/core/login.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход — ООО Обувь</title>
    <link rel="icon" href="{% static 'images/Icon.ico' %}">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
<div class="login-page">
    <img src="{% static 'images/logo.png' %}" alt="Логотип" class="logo-large">
    <div class="login-box">
        <h1>Вход в систему</h1>
        {% if error %}
            <div class="msg-error">{{ error }}</div>
        {% endif %}
        <form method="post">
            {% csrf_token %}
            <div class="field">
                <label>Логин</label>
                <input type="text" name="login" required>
            </div>
            <div class="field">
                <label>Пароль</label>
                <input type="password" name="password" required>
            </div>
            <div class="row-btns">
                <button type="submit" class="btn-accent">Войти</button>
                <a href="{% url 'product_list' %}" class="btn-secondary">Войти как гость</a>
            </div>
        </form>
    </div>
</div>
</body>
</html>
```

### core/templates/core/product_list.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Список товаров — ООО Обувь</title>
    <link rel="icon" href="{% static 'images/Icon.ico' %}">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
<header class="header">
    <div class="header-left">
        <img src="{% static 'images/logo.png' %}" alt="Логотип" class="logo">
        <span>ООО «Обувь»</span>
    </div>
    <div class="header-right">
        {% if user_full_name %}<span class="username">{{ user_full_name }}</span>{% endif %}
        {% if role != 'guest' %}
            <a href="{% url 'logout' %}" class="btn-secondary">Выйти</a>
        {% else %}
            <a href="{% url 'login' %}" class="btn-accent">Войти</a>
        {% endif %}
    </div>
</header>

<main>
    <div class="page-top">
        <h1>Список товаров</h1>
        <div class="row-btns">
            {% if role == 'manager' or role == 'admin' %}
                <a href="{% url 'order_list' %}" class="btn-secondary">Заказы</a>
            {% endif %}
            {% if role == 'admin' %}
                <a href="{% url 'product_create' %}" class="btn-accent">+ Добавить товар</a>
            {% endif %}
        </div>
    </div>

    {% if error %}
        <div class="msg-error">{{ error }}</div>
    {% endif %}

    {% if role == 'manager' or role == 'admin' %}
    <div class="filters">
        <input type="text" id="search" placeholder="Поиск по всем полям..."
               value="{{ search_query }}">
        <select id="supplier">
            <option value="">Все поставщики</option>
            {% for s in suppliers %}
                <option value="{{ s.name }}"
                    {% if s.name == supplier_filter %}selected{% endif %}>
                    {{ s.name }}
                </option>
            {% endfor %}
        </select>
        <select id="sort">
            <option value="">Без сортировки</option>
            <option value="quantity_asc"
                {% if sort_by == 'quantity_asc' %}selected{% endif %}>Количество ↑</option>
            <option value="quantity_desc"
                {% if sort_by == 'quantity_desc' %}selected{% endif %}>Количество ↓</option>
        </select>
    </div>
    {% endif %}

    {% for product in products %}
    <div class="product-card
        {% if product.is_big_discount %}card-green
        {% elif not product.is_in_stock %}card-blue{% endif %}"
        {% if role == 'admin' %}
            onclick="location.href='{% url 'product_edit' product.pk %}'"
            style="cursor:pointer"
        {% endif %}>

        <div class="product-img">
            {% if product.image %}
                <img src="/media/{{ product.image }}" alt="{{ product.name }}">
            {% else %}
                <img src="{% static 'images/picture.png' %}" alt="Нет фото">
            {% endif %}
        </div>

        <div class="product-info">
            <strong>{{ product.category.name }} | {{ product.name }}</strong>
            <div>Описание: {{ product.description|default:"—" }}</div>
            <div>Производитель: {{ product.manufacturer.name }}</div>
            <div>Поставщик: {{ product.supplier.name }}</div>
            <div class="price-row">
                {% if product.has_discount %}
                    <span class="price-old">{{ product.price }} ₽</span>
                    <span class="price-new">{{ product.get_final_price }} ₽</span>
                {% else %}
                    <span>{{ product.price }} ₽</span>
                {% endif %}
            </div>
            <div>Единица измерения: {{ product.unit }}</div>
            <div>Количество на складе: {{ product.quantity }}</div>
        </div>

        <div class="product-discount">
            {% if product.has_discount %}{{ product.discount }}%{% else %}—{% endif %}
        </div>

        {% if role == 'admin' %}
        <div class="product-del" onclick="event.stopPropagation()">
            <form method="post" action="{% url 'product_delete' product.pk %}"
                  onsubmit="return confirm('Удалить товар «{{ product.name }}»?')">
                {% csrf_token %}
                <button type="submit" class="btn-danger">Удалить</button>
            </form>
        </div>
        {% endif %}
    </div>
    {% empty %}
        <p class="empty">Товары не найдены.</p>
    {% endfor %}
</main>

{% if role == 'manager' or role == 'admin' %}
<script>
    function applyFilters() {
        const params = new URLSearchParams();
        const search   = document.getElementById('search').value;
        const supplier = document.getElementById('supplier').value;
        const sort     = document.getElementById('sort').value;
        if (search)   params.set('search', search);
        if (supplier) params.set('supplier', supplier);
        if (sort)     params.set('sort', sort);
        window.location.href = '/products/?' + params.toString();
    }

    let timer;
    document.getElementById('search').addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(applyFilters, 300);
    });
    document.getElementById('supplier').addEventListener('change', applyFilters);
    document.getElementById('sort').addEventListener('change', applyFilters);
</script>
{% endif %}
</body>
</html>
```

### core/templates/core/product_form.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} — ООО Обувь</title>
    <link rel="icon" href="{% static 'images/Icon.ico' %}">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
<header class="header">
    <div class="header-left">
        <img src="{% static 'images/logo.png' %}" alt="Логотип" class="logo">
        <span>ООО «Обувь»</span>
    </div>
    <div class="header-right">
        <span class="username">{{ user_full_name }}</span>
        <a href="{% url 'logout' %}" class="btn-secondary">Выйти</a>
    </div>
</header>
<main>
    <a href="{% url 'product_list' %}" class="btn-secondary">← Назад</a>
    <h1>{{ title }}</h1>

    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}

        {% if not is_create %}
        <div class="field">
            <label>ID товара</label>
            <input type="text" value="{{ product.pk }}" readonly class="readonly">
        </div>
        {% endif %}

        <div class="field">
            <label>Фото товара</label>
            {% if product.image %}
                <img src="/media/{{ product.image }}" id="preview" class="img-preview">
            {% else %}
                <img src="{% static 'images/picture.png' %}" id="preview" class="img-preview">
            {% endif %}
            <input type="file" name="image" accept="image/*">
        </div>

        <div class="field">
            <label>Наименование *</label>
            <input type="text" name="name" value="{{ product.name|default:'' }}" required>
            {% if errors.name %}<div class="msg-error">{{ errors.name }}</div>{% endif %}
        </div>

        <div class="field">
            <label>Категория *</label>
            <select name="category">
                {% for c in categories %}
                    <option value="{{ c.pk }}"
                        {% if product.category_id == c.pk %}selected{% endif %}>
                        {{ c.name }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <div class="field">
            <label>Описание</label>
            <textarea name="description">{{ product.description|default:'' }}</textarea>
        </div>

        <div class="field">
            <label>Производитель *</label>
            <select name="manufacturer">
                {% for m in manufacturers %}
                    <option value="{{ m.pk }}"
                        {% if product.manufacturer_id == m.pk %}selected{% endif %}>
                        {{ m.name }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <div class="field">
            <label>Поставщик *</label>
            <select name="supplier">
                {% for s in suppliers %}
                    <option value="{{ s.pk }}"
                        {% if product.supplier_id == s.pk %}selected{% endif %}>
                        {{ s.name }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <div class="field">
            <label>Цена (₽) * — не может быть отрицательной</label>
            <input type="number" name="price" step="0.01" min="0"
                   value="{{ product.price|default:'' }}" required>
            {% if errors.price %}<div class="msg-error">{{ errors.price }}</div>{% endif %}
        </div>

        <div class="field">
            <label>Единица измерения *</label>
            <input type="text" name="unit" value="{{ product.unit|default:'пара' }}">
        </div>

        <div class="field">
            <label>Количество на складе * — не может быть отрицательным</label>
            <input type="number" name="quantity" min="0"
                   value="{{ product.quantity|default:0 }}" required>
            {% if errors.quantity %}<div class="msg-error">{{ errors.quantity }}</div>{% endif %}
        </div>

        <div class="field">
            <label>Скидка (%) — от 0 до 100</label>
            <input type="number" name="discount" step="0.01" min="0" max="100"
                   value="{{ product.discount|default:0 }}">
        </div>

        <div class="row-btns">
            <button type="submit" class="btn-accent">
                {% if is_create %}Добавить{% else %}Сохранить{% endif %}
            </button>
            <a href="{% url 'product_list' %}" class="btn-secondary">Отмена</a>
        </div>
    </form>
</main>
<script>
    document.querySelector('input[type=file]').addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = e => document.getElementById('preview').src = e.target.result;
            reader.readAsDataURL(file);
        }
    });
</script>
</body>
</html>
```

### core/templates/core/order_list.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Заказы — ООО Обувь</title>
    <link rel="icon" href="{% static 'images/Icon.ico' %}">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
<header class="header">
    <div class="header-left">
        <img src="{% static 'images/logo.png' %}" alt="Логотип" class="logo">
        <span>ООО «Обувь»</span>
    </div>
    <div class="header-right">
        <span class="username">{{ user_full_name }}</span>
        <a href="{% url 'logout' %}" class="btn-secondary">Выйти</a>
    </div>
</header>
<main>
    <div class="page-top">
        <h1>Заказы</h1>
        <div class="row-btns">
            <a href="{% url 'product_list' %}" class="btn-secondary">← Товары</a>
            {% if role == 'admin' %}
                <a href="{% url 'order_create' %}" class="btn-accent">+ Добавить заказ</a>
            {% endif %}
        </div>
    </div>

    {% for order in orders %}
    <div class="order-card"
        {% if role == 'admin' %}
            onclick="location.href='{% url 'order_edit' order.pk %}'"
            style="cursor:pointer"
        {% endif %}>
        <div class="order-info">
            <strong>Артикул заказа: {{ order.article }}</strong>
            <div>Статус заказа: {{ order.get_status_display }}</div>
            <div>Адрес пункта выдачи: {{ order.pickup_point.address }}</div>
            <div>Дата заказа: {{ order.order_date }}</div>
        </div>
        <div class="order-delivery">
            Дата доставки<br>
            <strong>{{ order.delivery_date|default:"—" }}</strong>
        </div>
        {% if role == 'admin' %}
        <div class="product-del" onclick="event.stopPropagation()">
            <form method="post" action="{% url 'order_delete' order.pk %}"
                  onsubmit="return confirm('Удалить заказ «{{ order.article }}»?')">
                {% csrf_token %}
                <button type="submit" class="btn-danger">Удалить</button>
            </form>
        </div>
        {% endif %}
    </div>
    {% empty %}
        <p class="empty">Заказы не найдены.</p>
    {% endfor %}
</main>
</body>
</html>
```

### core/templates/core/order_form.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} — ООО Обувь</title>
    <link rel="icon" href="{% static 'images/Icon.ico' %}">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
<header class="header">
    <div class="header-left">
        <img src="{% static 'images/logo.png' %}" alt="Логотип" class="logo">
        <span>ООО «Обувь»</span>
    </div>
    <div class="header-right">
        <span class="username">{{ user_full_name }}</span>
        <a href="{% url 'logout' %}" class="btn-secondary">Выйти</a>
    </div>
</header>
<main>
    <a href="{% url 'order_list' %}" class="btn-secondary">← Назад</a>
    <h1>{{ title }}</h1>

    <form method="post">
        {% csrf_token %}

        {% if not is_create %}
        <div class="field">
            <label>ID заказа</label>
            <input type="text" value="{{ order.pk }}" readonly class="readonly">
        </div>
        {% endif %}

        <div class="field">
            <label>Артикул *</label>
            <input type="text" name="article"
                   value="{{ order.article|default:'' }}" required>
            {% if errors.article %}<div class="msg-error">{{ errors.article }}</div>{% endif %}
        </div>

        <div class="field">
            <label>Статус заказа *</label>
            <select name="status">
                {% for val, label in status_choices %}
                    <option value="{{ val }}"
                        {% if order.status == val %}selected{% endif %}>
                        {{ label }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <div class="field">
            <label>Адрес пункта выдачи *</label>
            <select name="pickup_point">
                {% for pp in pickup_points %}
                    <option value="{{ pp.pk }}"
                        {% if order.pickup_point_id == pp.pk %}selected{% endif %}>
                        {{ pp.address }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <div class="field">
            <label>Дата заказа *</label>
            <input type="date" name="order_date"
                   value="{{ order.order_date|default:'' }}" required>
            {% if errors.order_date %}
                <div class="msg-error">{{ errors.order_date }}</div>
            {% endif %}
        </div>

        <div class="field">
            <label>Дата выдачи</label>
            <input type="date" name="delivery_date"
                   value="{{ order.delivery_date|default:'' }}">
        </div>

        <div class="row-btns">
            <button type="submit" class="btn-accent">
                {% if is_create %}Добавить{% else %}Сохранить{% endif %}
            </button>
            <a href="{% url 'order_list' %}" class="btn-secondary">Отмена</a>
        </div>
    </form>
</main>
</body>
</html>
```

### static/css/style.css

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Times New Roman', Times, serif;
    background: #FFFFFF;
    color: #333;
}

/* ===== ШАПКА ===== */
.header {
    background: #7FFF00;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    border-bottom: 1px solid #ccc;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.logo { height: 50px; width: auto; object-fit: contain; }
.logo-large { height: 80px; width: auto; object-fit: contain; margin-bottom: 16px; }
.username { font-weight: bold; }

/* ===== КНОПКИ ===== */
.btn-accent {
    background: #00FA9A; color: #000;
    padding: 8px 16px; border: none; border-radius: 4px;
    cursor: pointer; font-family: inherit; font-size: 1em;
    text-decoration: none; display: inline-block;
}
.btn-secondary {
    background: #7FFF00; color: #000;
    padding: 8px 16px; border: none; border-radius: 4px;
    cursor: pointer; font-family: inherit; font-size: 1em;
    text-decoration: none; display: inline-block;
}
.btn-danger {
    background: #dc3545; color: #fff;
    padding: 6px 12px; border: none; border-radius: 4px;
    cursor: pointer; font-family: inherit;
}

/* ===== СТРАНИЦА ВХОДА ===== */
.login-page {
    min-height: 100vh; background: #7FFF00;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; padding: 20px;
}
.login-box {
    background: #fff; padding: 30px; border-radius: 8px;
    width: 100%; max-width: 400px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.login-box h1 { margin-bottom: 20px; font-size: 1.4em; text-align: center; }

/* ===== ПОЛЯ ФОРМ ===== */
main { padding: 20px; max-width: 1100px; margin: 0 auto; }
h1 { margin: 12px 0; }

.field { margin-bottom: 14px; }
.field label { display: block; margin-bottom: 4px; font-weight: bold; }
.field input,
.field select,
.field textarea {
    width: 100%; padding: 7px; border: 1px solid #ccc;
    border-radius: 4px; font-family: inherit; font-size: 1em;
}
.field textarea { resize: vertical; min-height: 70px; }
.readonly { background: #f5f5f5; cursor: not-allowed; }
.row-btns { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }

/* ===== ВЕРХНЯЯ ПАНЕЛЬ ===== */
.page-top {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 16px;
}

/* ===== ФИЛЬТРЫ ===== */
.filters { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.filters input,
.filters select {
    padding: 7px; border: 1px solid #ccc; border-radius: 4px;
    font-family: inherit; font-size: 1em;
}
.filters input { flex: 1; min-width: 180px; }

/* ===== КАРТОЧКА ТОВАРА ===== */
.product-card {
    display: flex; align-items: stretch;
    border: 1px solid #ccc; border-radius: 4px;
    background: #fff; margin-bottom: 8px; overflow: hidden;
}
.card-green { background: #2E8B57; color: #fff; }
.card-blue  { background: lightblue; }

.product-img {
    width: 120px; min-width: 120px;
    display: flex; align-items: center; justify-content: center;
    padding: 8px; background: rgba(255,255,255,0.25);
}
.product-img img { width: 100px; height: 75px; object-fit: contain; }

.product-info {
    flex: 1; padding: 10px;
    display: flex; flex-direction: column; gap: 3px;
}

/* Перечёркнутая цена красная, итоговая чёрная */
.price-old { text-decoration: line-through; color: red; margin-right: 8px; }
.price-new { color: black; font-weight: bold; }

.product-discount {
    width: 75px; min-width: 75px;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; border-left: 1px solid #ccc; padding: 8px;
}
.product-del {
    display: flex; align-items: center;
    padding: 8px; border-left: 1px solid #ccc;
}

/* ===== КАРТОЧКА ЗАКАЗА ===== */
.order-card {
    display: flex; align-items: stretch;
    border: 1px solid #ccc; border-radius: 4px;
    background: #fff; margin-bottom: 8px; overflow: hidden;
}
.order-info { flex: 1; padding: 10px; display: flex; flex-direction: column; gap: 3px; }
.order-delivery {
    width: 140px; min-width: 140px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 10px; border-left: 1px solid #ccc; text-align: center;
}

/* ===== ПРЕВЬЮ ФОТО В ФОРМЕ ===== */
.img-preview {
    width: 300px; height: 200px;
    object-fit: contain; border: 1px solid #ccc;
    margin-bottom: 8px; display: block;
}

/* ===== СООБЩЕНИЯ ===== */
.msg-error {
    background: #f8d7da; color: #721c24;
    padding: 8px 12px; border-radius: 4px;
    margin-bottom: 12px; border: 1px solid #f5c6cb;
}
.empty { text-align: center; color: #666; padding: 30px; font-size: 1.1em; }
```

---

## 16. Вариативная часть — cleanup неиспользуемых фото

Создать `core/management/commands/cleanup_images.py`:

```python
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Product


class Command(BaseCommand):
    """Удаление файлов из media/products/, не привязанных ни к одному товару"""
    help = 'Удаление неиспользуемых фотографий товаров'

    def handle(self, *args, **options):
        # Собираем имена файлов которые реально используются
        used_images = set()
        for product in Product.objects.exclude(image=''):
            if product.image:
                used_images.add(os.path.basename(product.image))

        products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        if not os.path.exists(products_dir):
            self.stdout.write('Папка media/products/ не существует.')
            return

        deleted = 0
        for filename in os.listdir(products_dir):
            if filename not in used_images:
                os.remove(os.path.join(products_dir, filename))
                deleted += 1
                self.stdout.write(f'Удалён: {filename}')

        self.stdout.write(self.style.SUCCESS(f'Готово. Удалено файлов: {deleted}'))
```

```powershell
python manage.py cleanup_images
```

---

## 17. SQL дамп и Git

### Дамп базы данных

```powershell
# Только схема
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -s shoe_store > schema.sql

# Полный дамп (схема + данные)
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres shoe_store > full_dump.sql
```

### Git

```powershell
git init

echo .venv/ > .gitignore
echo __pycache__/ >> .gitignore
echo "*.pyc" >> .gitignore
echo media/ >> .gitignore

git config user.name "Student"
git config user.email "student@exam.ru"

git add .
git commit -m "module 1: db schema and models"

git add .
git commit -m "module 1: csv import script"

git add .
git commit -m "module 2: login and product list"

git add .
git commit -m "module 3: search filter sort product crud pillow"

git add .
git commit -m "module 4: orders crud"

git add schema.sql full_dump.sql er_diagram.pdf
git commit -m "add db dump and er diagram"

# URL скажут на экзамене
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

---

## 18. Чеклист перед сдачей

### Модуль 1 (10 баллов)
- [ ] БД создана в PostgreSQL (3НФ, ссылочная целостность)
- [ ] ER-диаграмма в PDF (таблицы, связи, атрибуты, ключи)
- [ ] CSV данные загружены: `python manage.py import_data`
- [ ] SQL дамп: `schema.sql` + `full_dump.sql`

### Модуль 2 (15 баллов)
- [ ] Блок-схема алгоритма в PDF (ГОСТ 19.701-90)
- [ ] Страница входа — первая для пользователя
- [ ] Кнопка "Войти как гость" работает
- [ ] Авторизация по логину/паролю из БД
- [ ] ФИО пользователя в правом верхнем углу
- [ ] Кнопка "Выйти" работает
- [ ] Список товаров для всех ролей
- [ ] Фото товара или заглушка picture.png
- [ ] Подсветка скидка > 15% → `#2E8B57`
- [ ] Подсветка нет на складе → голубой
- [ ] Цена перечёркнута красным + итоговая чёрным
- [ ] Шрифт Times New Roman везде
- [ ] Цвета `#FFFFFF` / `#7FFF00` / `#00FA9A`
- [ ] Логотип на главной форме (не искажён, пропорции сохранены)
- [ ] Иконка приложения `Icon.ico`
- [ ] Скриншоты корректной работы в docx

### Модуль 3 (24 балла)
- [ ] Кнопка "← Назад" на всех страницах
- [ ] Заголовки страниц соответствуют назначению
- [ ] Сообщения об ошибках информативны
- [ ] Комментарии в коде там где нужно
- [ ] Поиск в реальном времени по всем текстовым полям
- [ ] Фильтр по поставщику (закомментирован, оставлен в коде)
- [ ] Фильтр по диапазону скидки: 0–11%, 11–15%, 15–19%, более 19%
- [ ] Сортировка по количеству ↑↓ и цене ↑↓
- [ ] Поиск + фильтр работают совместно
- [ ] Сортировка сохраняется при поиске/фильтре
- [ ] Нельзя открыть два окна редактирования одновременно
- [ ] Форма добавления товара (только администратор)
- [ ] Клик по товару → редактирование (только администратор)
- [ ] Все поля заполняются при редактировании
- [ ] ID скрыт при добавлении, read-only при редактировании
- [ ] Ресайз фото 300×200 через Pillow
- [ ] Старое фото удаляется при замене
- [ ] Нельзя удалить товар если он есть в заказах
- [ ] Список обновляется после каждой операции

### Модуль 4 (23 балла)
- [ ] Кнопка "Заказы" у менеджера и администратора
- [ ] Список заказов по макету
- [ ] Форма добавления заказа (только администратор)
- [ ] Клик по заказу → редактирование (только администратор)
- [ ] Удаление заказа
- [ ] Список обновляется после каждой операции

### Вариативная часть (25 баллов)
- [ ] `import_data` management command работает
- [ ] `{% csrf_token %}` во всех POST-формах
- [ ] `cleanup_images` management command работает
- [ ] Pillow ресайзит до 300×200
- [ ] Проект на Django, зависимости в `pyproject.toml`

### Git
- [ ] Коммиты по модулям
- [ ] Исходный код запушен структурой (не архив)
- [ ] `schema.sql` в репозитории
- [ ] `er_diagram.pdf` в репозитории

---

## 19. Быстрые команды

```powershell
# Активировать venv
.venv\Scripts\activate

# Запустить сервер
python manage.py runserver

# === ВАРИАНТ А ===
psql -U postgres -d shoe_store -f schema.sql
python manage.py inspectdb > core/models.py
python manage.py migrate

# === ВАРИАНТ Б ===
python manage.py makemigrations
python manage.py migrate

# Импорт CSV
python manage.py import_data

# Очистка неиспользуемых фото
python manage.py cleanup_images

# Дамп БД
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -s shoe_store > schema.sql
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres shoe_store > full_dump.sql

# Git
git add .
git commit -m "описание"
git push
```

---

## 20. Очистка истории команд PowerShell

На экзамене эксперты могут просматривать историю команд через удалённый доступ.  
Чтобы очистить историю сессии и файл истории:

```powershell
# Очистить историю текущей сессии
Clear-History

# Удалить файл истории PowerShell (история между сессиями)
Remove-Item (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue

# Убедиться что файл удалён
Test-Path (Get-PSReadlineOption).HistorySavePath
# Должно вернуть False
```

> ⚠️ После `Remove-Item` история не восстанавливается. Новые команды после этого снова начнут записываться в новый файл истории.

---

*Инструкция для КОД 09.02.07-2-2026, ГИА ДЭ ПУ.*  
*Python 3.13 · Django 5 · PostgreSQL 18 · UV · VS Code · Windows*