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

        # Папка import_data/ лежит рядом с manage.py
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
        """Читает xlsx файл и возвращает DataFrame, или None если файл не найден"""
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
            result = pd.to_datetime(value, dayfirst=True, errors='coerce')
            return None if pd.isnull(result) else result.date()
        except Exception:
            return None

    def ensure_roles(self):
        """Создаёт базовые роли если их нет"""
        for role_name in ('guest', 'client', 'manager', 'admin'):
            Role.objects.get_or_create(name=role_name)
        self.stdout.write('Роли: готово')

    def import_pickup_points(self):
        """Импорт пунктов выдачи из Пункты выдачи_import.xlsx"""
        df = self.read_xlsx('Пункты выдачи_import.xlsx')
        if df is None:
            return
        for _, row in df.iterrows():
            address = str(row.iloc[0]).strip()
            if address:
                PickupPoint.objects.get_or_create(address=address)
        self.stdout.write(f'Пункты выдачи: {len(df)} строк')

    def import_products(self):
        """
        Импорт товаров из Tovar.xlsx.
        Колонки: Наименование товара, Категория товара, Описание товара,
                 Производитель, Поставщик, Цена, Единица измерения,
                 Кол-во на складе, Действующая скидка, Фото
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
                name=row['Наименование товара'].strip(),
                manufacturer=manufacturer,
                supplier=supplier,
                defaults={
                    'category':    category,
                    'description': row.get('Описание товара', ''),
                    'price':       price,
                    'unit':        row.get('Единица измерения', 'пара') or 'пара',
                    'quantity':    quantity,
                    'discount':    discount,
                    'image':       row.get('Фото', ''),
                }
            )
        self.stdout.write(f'Товары: {len(df)} строк')

    def import_users(self):
        """
        Импорт пользователей из user_import.xlsx.
        Колонки: ФИО, Логин, Пароль, Роль сотрудника
        """
        df = self.read_xlsx('user_import.xlsx')
        if df is None:
            return

        for _, row in df.iterrows():
            role_name = ROLE_MAP.get(row['Роль сотрудника'].strip(), 'client')
            role = Role.objects.get(name=role_name)

            # Разбиваем ФИО на части
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
        self.stdout.write(f'Пользователи: {len(df)} строк')

    def import_orders(self):
        """
        Импорт заказов из Заказ_import.xlsx.
        Колонки: Номер заказа, Статус заказа, Адрес пункта выдачи,
                 Дата заказа, Дата доставки, Артикул заказа

        Артикул заказа — это наименование товара (или несколько через запятую).
        Каждый артикул привязывается к заказу через OrderItem.
        """
        df = self.read_xlsx('Заказ_import.xlsx')
        if df is None:
            return

        pickup_points = list(PickupPoint.objects.all())

        for _, row in df.iterrows():
            order_date    = self._parse_date(row['Дата заказа'])
            delivery_date = self._parse_date(row['Дата доставки'])

            # Пропускаем строки с невалидной датой заказа
            if not order_date:
                self.stdout.write(self.style.WARNING(
                    f'Пропущен заказ {row["Номер заказа"]}: невалидная дата'
                ))
                continue

            # Ищем пункт выдачи по адресу или берём первый
            pickup_address = row['Адрес пункта выдачи'].strip()
            pickup_point = PickupPoint.objects.filter(
                address__icontains=pickup_address
            ).first()
            if not pickup_point and pickup_points:
                pickup_point = pickup_points[0]
            if not pickup_point:
                self.stdout.write(self.style.WARNING(
                    f'Нет пунктов выдачи, пропущен заказ {row["Номер заказа"]}'
                ))
                continue

            status  = STATUS_MAP.get(row['Статус заказа'].strip(), 'new')
            article = row['Номер заказа'].strip()

            order, created = Order.objects.get_or_create(
                article=article,
                defaults={
                    'status':        status,
                    'pickup_point':  pickup_point,
                    'order_date':    order_date,
                    'delivery_date': delivery_date,
                }
            )

            # Привязываем товары к заказу через OrderItem
            if created:
                raw_articles = str(row.get('Артикул заказа', '')).strip()
                if not raw_articles:
                    continue

                # Артикулы перечислены через запятую
                product_names = [a.strip() for a in raw_articles.split(',') if a.strip()]

                for product_name in product_names:
                    try:
                        # Ищем товар по наименованию (артикул = наименование товара)
                        product = Product.objects.get(name=product_name)
                        OrderItem.objects.get_or_create(order=order, product=product)
                    except Product.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'Товар не найден: «{product_name}» (заказ {article})'
                        ))
                    except Product.MultipleObjectsReturned:
                        # Если несколько товаров с таким именем — берём первый
                        product = Product.objects.filter(name=product_name).first()
                        OrderItem.objects.get_or_create(order=order, product=product)

        self.stdout.write(f'Заказы: {len(df)} строк')