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
