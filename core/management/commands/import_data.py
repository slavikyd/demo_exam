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