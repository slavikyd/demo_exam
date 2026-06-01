from django.db import models


class Role(models.Model):
    """Роль пользователя в системе"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название роли')

    class Meta:
        db_table = 'role'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class User(models.Model):
    """Пользователь системы"""
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    login = models.CharField(max_length=100, unique=True, verbose_name='Логин')
    password = models.CharField(max_length=255, verbose_name='Пароль')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name='Роль')

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def get_full_name(self):
        """Возвращает ФИО пользователя"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


class Category(models.Model):
    """Категория товара"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Производитель товара"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')

    class Meta:
        db_table = 'manufacturer'
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Поставщик товара"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')

    class Meta:
        db_table = 'supplier'
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар (обувь)"""
    name = models.CharField(max_length=200, verbose_name='Наименование')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    description = models.TextField(blank=True, verbose_name='Описание')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, verbose_name='Производитель')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name='Поставщик')
    # Цена не может быть отрицательной
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    unit = models.CharField(max_length=50, default='пара', verbose_name='Единица измерения')
    # Количество не может быть отрицательным
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество на складе')
    # Скидка в процентах (0-100)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Скидка (%)')
    # Путь к изображению хранится в БД
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото')

    class Meta:
        db_table = 'product'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def get_final_price(self):
        """Вычисляет итоговую цену с учётом скидки"""
        if self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price

    def has_discount(self):
        """Проверяет, есть ли скидка на товар"""
        return self.discount > 0

    def is_big_discount(self):
        """Проверяет, превышает ли скидка 15%"""
        return self.discount > 15

    def is_in_stock(self):
        """Проверяет, есть ли товар на складе"""
        return self.quantity > 0


class PickupPoint(models.Model):
    """Пункт выдачи заказа"""
    address = models.CharField(max_length=500, verbose_name='Адрес')

    class Meta:
        db_table = 'pickup_point'
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'

    def __str__(self):
        return self.address


class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]

    article = models.CharField(max_length=100, unique=True, verbose_name='Артикул')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    pickup_point = models.ForeignKey(
        PickupPoint, on_delete=models.PROTECT, verbose_name='Пункт выдачи'
    )
    order_date = models.DateField(verbose_name='Дата заказа')
    delivery_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи')

    class Meta:
        db_table = 'order'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ {self.article}'


class OrderItem(models.Model):
    """Позиция в заказе (товар в заказе)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')

    class Meta:
        db_table = 'order_item'
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'

    def __str__(self):
        return f'{self.order} — {self.product}'
