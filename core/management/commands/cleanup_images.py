import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Product


class Command(BaseCommand):
    help = 'Удаление неиспользуемых фотографий товаров'

    def handle(self, *args, **options):
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
