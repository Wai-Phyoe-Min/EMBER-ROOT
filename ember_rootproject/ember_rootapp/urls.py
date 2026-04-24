from django.urls import path
from . import views

urlpatterns = [
    # Page views
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('story/', views.story, name='story'),
    path('distance/', views.distance, name='distance'),
    path('visit/', views.visit, name='visit'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    
    # Authentication
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # AJAX endpoints
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/register/', views.ajax_register, name='ajax_register'),
    path('ajax/update-profile/', views.update_profile, name='update_profile'),
    path('ajax/update-email/', views.update_email, name='update_email'),
    path('ajax/change-password/', views.change_password, name='change_password'),
    path('ajax/delete-account/', views.delete_account, name='delete_account'),
    path('ajax/submit-contact/', views.submit_contact, name='submit_contact'),
    path('ajax/mark-messages-read/', views.mark_messages_as_read, name='mark_messages_read'),
    
    # Orders
    path('ajax/place-order/', views.place_order, name='place_order'),
    path('ajax/order-history/', views.order_history, name='order_history'),
    
    # Favorites
    path('ajax/favorite/<int:pizza_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('ajax/favorites/', views.get_favorites, name='get_favorites'),
    
    # API
    path('api/pizzas/', views.api_pizzas, name='api_pizzas'),
    path('api/farm-stories/', views.api_farm_stories, name='api_farm_stories'),
    path('api/business-hours/', views.api_business_hours, name='api_business_hours'),
    path('api/stats/', views.get_stats, name='api_stats'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/pizza/create/', views.admin_pizza_create, name='admin_pizza_create'),
    path('admin-dashboard/pizza/<int:pizza_id>/', views.admin_pizza_detail, name='admin_pizza_detail'),
    path('admin-dashboard/pizza/<int:pizza_id>/update/', views.admin_pizza_update, name='admin_pizza_update'),
    path('admin-dashboard/pizza/<int:pizza_id>/delete/', views.admin_pizza_delete, name='admin_pizza_delete'),
    path('admin-dashboard/menu-item/create/', views.admin_menuitem_create, name='admin_menuitem_create'),
    path('admin-dashboard/menu-item/<int:item_id>/', views.admin_menuitem_detail, name='admin_menuitem_detail'),
    path('admin-dashboard/menu-item/<int:item_id>/update/', views.admin_menuitem_update, name='admin_menuitem_update'),
    path('admin-dashboard/menu-item/<int:item_id>/delete/', views.admin_menuitem_delete, name='admin_menuitem_delete'),
    path('admin-dashboard/order/<int:order_id>/status/', views.admin_order_status, name='admin_order_status'),
    path('admin-dashboard/order/<int:order_id>/detail/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-dashboard/message/<int:message_id>/', views.admin_message_detail, name='admin_message_detail'),
    path('admin-dashboard/message/<int:message_id>/reply/', views.admin_message_reply, name='admin_message_reply'),
    path('admin-dashboard/profile/', views.admin_profile, name='admin_profile'),
    path('admin-dashboard/profile/update/', views.admin_profile_update, name='admin_profile_update'),
    path('admin-dashboard/hours/', views.admin_hours_list, name='admin_hours_list'),
    path('admin-dashboard/hours/update/', views.admin_hours_update, name='admin_hours_update'),
]