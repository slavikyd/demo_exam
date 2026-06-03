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
    # Артикул товара — уникальный идентификатор из xlsx
    article = models.CharField(max_length=100, unique=True, blank=True, default='')
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
        return f'{self.article} — {self.name}'

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
    # Клиент, сделавший заказ (null допустим — заказ мог быть создан вручную)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    # Код для получения заказа
    code = models.CharField(max_length=100, blank=True, default='')
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'order'

    def __str__(self):
        return f'Заказ {self.article}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    # Количество единиц товара в позиции заказа
    quantity = models.IntegerField(default=1)

    class Meta:
        db_table = 'order_item'

    def __str__(self):
        return f'{self.order} — {self.product.article} x{self.quantity}'