import os
import pandas as pd
from django.core.management.base import BaseCommand
from core.models import (
    Role, User, Category, Manufacturer, Supplier,
    Product, PickupPoint, Order, OrderItem
)

ROLE_MAP = {
    'Администратор': 'admin',
    'Менеджер': 'manager',
    'Клиент': 'client',
    'Гость': 'guest',
}

STATUS_MAP = {
    'Новый': 'new',
    'В обработке': 'processing',
    'Готов к выдаче': 'ready',
    'Завершен': 'completed',
    'Завершён': 'completed',
    'Отменён': 'cancelled',
    'Отменен': 'cancelled',
}


class Command(BaseCommand):
    help = 'Импорт данных из папки import_data/'

    def handle(self, *args, **options):
        self.stdout.write('Начало импорта...')

        self.csv_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'import_data'
        )

        self.ensure_roles()
        self.import_pickup_points()
        self.import_products()
        self.import_users()
        self.import_orders()

        self.stdout.write(self.style.SUCCESS('Импорт завершён!'))

    def read_csv(self, filename):
        path = os.path.join(self.csv_dir, filename)
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING(f'Не найден: {filename}'))
            return None
        return pd.read_csv(path, sep=None, engine='python', encoding='utf-8', dtype=str).fillna('')

    def _parse_date(self, value):
        if not value or str(value).strip().lower() == 'nan':
            return None
        try:
            result = pd.to_datetime(value, dayfirst=True, errors='coerce')
            return None if pd.isnull(result) else result.date()
        except Exception:
            return None

    def ensure_roles(self):
        for role_name in ('guest', 'client', 'manager', 'admin'):
            Role.objects.get_or_create(name=role_name)
        self.stdout.write('Роли: готово')

    def import_pickup_points(self):
        path = os.path.join(self.csv_dir, 'pickup_points.csv')
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING('Не найден: pickup_points.csv'))
            return
        df = pd.read_csv(path, encoding='utf-8')
        for _, row in df.iterrows():
            PickupPoint.objects.get_or_create(address=str(row.iloc[0]).strip())
        self.stdout.write(f'Пункты выдачи: {len(df)} строк')

    def import_products(self):
        df = self.read_csv('products.csv')
        if df is None:
            return
        for _, row in df.iterrows():
            category, _     = Category.objects.get_or_create(name=row['Категория товара'])
            manufacturer, _ = Manufacturer.objects.get_or_create(name=row['Производитель'])
            supplier, _     = Supplier.objects.get_or_create(name=row['Поставщик'])

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
                name=row['Наименование товара'],
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
        df = self.read_csv('users.csv')
        if df is None:
            return
        for _, row in df.iterrows():
            role_name = ROLE_MAP.get(row['Роль сотрудника'].strip(), 'client')
            role = Role.objects.get(name=role_name)

            parts = row['ФИО'].strip().split()
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
        df = self.read_csv('orders.csv')
        if df is None:
            return
        pickup_points = list(PickupPoint.objects.all())

        for _, row in df.iterrows():
            order_date    = self._parse_date(row['Дата заказа'])
            delivery_date = self._parse_date(row['Дата доставки'])

            if not order_date:
                self.stdout.write(self.style.WARNING(
                    f'Пропущен заказ №{row["Номер заказа"]}: невалидная дата'
                ))
                continue

            try:
                pp_index = int(float(row['Адрес пункта выдачи'])) - 1
                pickup_point = pickup_points[pp_index] if 0 <= pp_index < len(pickup_points) else pickup_points[0]
            except (ValueError, IndexError):
                pickup_point = pickup_points[0] if pickup_points else None

            if not pickup_point:
                continue

            status = STATUS_MAP.get(row['Статус заказа'].strip(), 'new')
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

            if created:
                parts = [p.strip() for p in row['Артикул заказа'].split(',')]
                i = 0
                while i < len(parts) - 1:
                    product_article = parts[i]
                    i += 2
                    try:
                        product = Product.objects.get(name=product_article)
                        OrderItem.objects.get_or_create(order=order, product=product)
                    except Product.DoesNotExist:
                        pass

        self.stdout.write(f'Заказы: {len(df)} строк')
