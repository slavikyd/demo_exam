import os
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from PIL import Image as PilImage

from .models import (
    User, Product, Category, Manufacturer,
    Supplier, Order, PickupPoint, OrderItem
)


def login_view(request):
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
            request.session['user_id']        = user.id
            request.session['user_role']      = user.role.name
            request.session['user_full_name'] = user.get_full_name()
            return redirect('product_list')
        except User.DoesNotExist:
            return render(request, 'core/login.html', {
                'error': 'Неверный логин или пароль.'
            })

    return render(request, 'core/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def product_list_view(request):
    role = request.session.get('user_role', 'guest')

    products = Product.objects.select_related(
        'category', 'manufacturer', 'supplier'
    ).all()

    search_query    = ''
    # supplier_filter = ''  # закомментирован
    discount_range  = ''
    sort_by         = ''

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

        # Фильтр по поставщику — закомментирован
        # supplier_filter = request.GET.get('supplier', '').strip()
        # if supplier_filter:
        #     products = products.filter(supplier__name=supplier_filter)

        # Фильтр по диапазону скидки
        discount_range = request.GET.get('discount_range', '').strip()
        if discount_range == '0-11':
            products = products.filter(discount__gte=0, discount__lt=11)
        elif discount_range == '11-15':
            products = products.filter(discount__gte=11, discount__lte=15)
        elif discount_range == '15-19':
            products = products.filter(discount__gt=15, discount__lte=19)
        elif discount_range == '19+':
            products = products.filter(discount__gt=19)

        # Сортировка по количеству или цене
        sort_by = request.GET.get('sort', '')
        if sort_by == 'quantity_asc':
            products = products.order_by('quantity')
        elif sort_by == 'quantity_desc':
            products = products.order_by('-quantity')
        elif sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')

    suppliers = Supplier.objects.all()

    return render(request, 'core/product_list.html', {
        'products':        products,
        'role':            role,
        'suppliers':       suppliers,
        'search_query':    search_query,
        # 'supplier_filter': supplier_filter,  # закомментирован
        'discount_range':  discount_range,
        'sort_by':         sort_by,
        'user_full_name':  request.session.get('user_full_name', ''),
    })


def product_create_view(request):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    categories    = Category.objects.all()
    manufacturers = Manufacturer.objects.all()
    suppliers     = Supplier.objects.all()
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
        'categories':     categories,
        'manufacturers':  manufacturers,
        'suppliers':      suppliers,
        'errors':         errors,
        'title':          'Добавить товар',
        'is_create':      True,
        'role':           request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def product_update_view(request, pk):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    # Защита от открытия двух окон редактирования одновременно:
    # если в сессии уже есть editing_product и это другой товар — отказываем
    editing = request.session.get('editing_product')
    if editing and editing != pk:
        return render(request, 'core/product_list.html', {
            'error': (
                'Уже открыто окно редактирования другого товара. '
                'Закройте его перед тем как открыть новое.'
            ),
            'products': Product.objects.select_related(
                'category', 'manufacturer', 'supplier'
            ).all(),
            'suppliers':      Supplier.objects.all(),
            'role':           request.session.get('user_role'),
            'user_full_name': request.session.get('user_full_name', ''),
        })

    # Помечаем в сессии что редактируется этот товар
    request.session['editing_product'] = pk

    product       = get_object_or_404(Product, pk=pk)
    categories    = Category.objects.all()
    manufacturers = Manufacturer.objects.all()
    suppliers     = Supplier.objects.all()
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
                # Удаляем старое фото с диска перед заменой
                if product.image:
                    old_path = os.path.join('media', product.image)
                    if os.path.isfile(old_path):
                        os.remove(old_path)
                product.image = save_product_image(request.FILES['image'])

            product.save()
            # Снимаем блокировку после успешного сохранения
            request.session.pop('editing_product', None)
            return redirect('product_list')

    return render(request, 'core/product_form.html', {
        'product':        product,
        'categories':     categories,
        'manufacturers':  manufacturers,
        'suppliers':      suppliers,
        'errors':         errors,
        'title':          f'Редактировать: {product.name}',
        'is_create':      False,
        'role':           request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def save_product_image(image_file):
    """Сохраняет фото товара с ресайзом до 300x200 через Pillow"""
    img = PilImage.open(image_file)
    img = img.resize((300, 200), PilImage.LANCZOS)
    save_path = os.path.join('media', 'products', image_file.name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    img.save(save_path)
    return f'products/{image_file.name}'


def product_delete_view(request, pk):
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
                'suppliers':      Supplier.objects.all(),
                'role':           request.session.get('user_role'),
                'user_full_name': request.session.get('user_full_name', ''),
            })

        if product.image:
            image_path = os.path.join('media', product.image)
            if os.path.isfile(image_path):
                os.remove(image_path)

        product.delete()
        # Снимаем блокировку редактирования если вдруг осталась
        request.session.pop('editing_product', None)
        return redirect('product_list')

    return redirect('product_list')


def order_list_view(request):
    if request.session.get('user_role') not in ('manager', 'admin'):
        return redirect('login')

    orders = Order.objects.select_related('pickup_point').all()

    return render(request, 'core/order_list.html', {
        'orders':         orders,
        'role':           request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_create_view(request):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    pickup_points = PickupPoint.objects.all()
    errors = {}

    if not pickup_points.exists():
        errors['pickup_point'] = (
            'Нет доступных пунктов выдачи. Сначала добавьте пункты выдачи.'
        )

    if request.method == 'POST':
        article         = request.POST.get('article', '').strip()
        status          = request.POST.get('status', 'new')
        pickup_point_id = request.POST.get('pickup_point', '').strip()
        order_date      = request.POST.get('order_date', '').strip()
        delivery_date   = request.POST.get('delivery_date', '').strip() or None

        if not article:
            errors['article'] = 'Укажите артикул заказа.'
        if not order_date:
            errors['order_date'] = 'Укажите дату заказа.'
        if not pickup_point_id:
            errors['pickup_point'] = 'Выберите пункт выдачи.'

        if not errors:
            Order.objects.create(
                article=article,
                status=status,
                pickup_point_id=int(pickup_point_id),
                order_date=order_date,
                delivery_date=delivery_date,
            )
            return redirect('order_list')

    return render(request, 'core/order_form.html', {
        'pickup_points':  pickup_points,
        'errors':         errors,
        'status_choices': Order.STATUS_CHOICES,
        'title':          'Добавить заказ',
        'is_create':      True,
        'role':           request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_update_view(request, pk):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    order         = get_object_or_404(Order, pk=pk)
    pickup_points = PickupPoint.objects.all()
    errors = {}

    if request.method == 'POST':
        article         = request.POST.get('article', '').strip()
        status          = request.POST.get('status', 'new')
        pickup_point_id = request.POST.get('pickup_point', '').strip()
        order_date      = request.POST.get('order_date', '').strip()
        delivery_date   = request.POST.get('delivery_date', '').strip() or None

        if not article:
            errors['article'] = 'Укажите артикул заказа.'
        if not order_date:
            errors['order_date'] = 'Укажите дату заказа.'
        if not pickup_point_id:
            errors['pickup_point'] = 'Выберите пункт выдачи.'

        if not errors:
            order.article         = article
            order.status          = status
            order.pickup_point_id = int(pickup_point_id)
            order.order_date      = order_date
            order.delivery_date   = delivery_date
            order.save()
            return redirect('order_list')

    return render(request, 'core/order_form.html', {
        'order':          order,
        'pickup_points':  pickup_points,
        'errors':         errors,
        'status_choices': Order.STATUS_CHOICES,
        'title':          f'Редактировать заказ: {order.article}',
        'is_create':      False,
        'role':           request.session.get('user_role'),
        'user_full_name': request.session.get('user_full_name', ''),
    })


def order_delete_view(request, pk):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.delete()
        return redirect('order_list')

    return redirect('order_list')