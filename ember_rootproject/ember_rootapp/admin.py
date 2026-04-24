from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import BusinessHours, ContactMessage, MenuItem, User, Pizza, Order, Favorite, UserActivity, UserSession


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin configuration."""
    
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_at', 'last_login_at')
    list_filter = ('user_type', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_login_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login_at')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    """Pizza admin configuration."""
    
    list_display = ('name', 'category', 'price', 'bestseller', 'is_available', 'created_at')
    list_filter = ('category', 'bestseller', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'farm')
    list_editable = ('price', 'bestseller', 'is_available')
    ordering = ('category', 'name')
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'category', 'description', 'price')}),
        ('Nutrition', {'fields': ('calories', 'dietary')}),
        ('Farm Info', {'fields': ('farm', 'farm_story', 'latitude', 'longitude')}),
        ('Display', {'fields': ('image', 'bestseller', 'seasonal_note', 'is_available')}),
        ('Recommended Pairing', {
            'fields': ('recommended_pairing', 'recommended_pairing_price', 
                      'recommended_pairing_description', 'recommended_pairing_image'),
            'classes': ('wide',),
            'description': 'Add a drink or side that pairs well with this pizza'
        }),
        ('Metadata', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('day', 'open_time', 'close_time', 'is_closed', 'note')
    list_editable = ('open_time', 'close_time', 'is_closed')
    ordering = ('display_order',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin configuration."""
    
    list_display = ('order_number', 'user_email', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__email')
    ordering = ('-created_at',)
    
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'status')}),
        ('Items', {'fields': ('items',)}),
        ('Amounts', {'fields': ('subtotal', 'total')}),
        ('Pickup', {'fields': ('pickup_time', 'special_instructions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'completed_at')}),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Favorite admin configuration."""
    
    list_display = ('user_email', 'pizza_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'pizza__name')
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def pizza_name(self, obj):
        return obj.pizza.name
    pizza_name.short_description = 'Pizza'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """User Activity admin configuration."""
    
    list_display = ('user_email', 'activity_type', 'description', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__email', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'user_agent', 'created_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def has_add_permission(self, request):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session admin configuration."""
    
    list_display = ('user_email', 'session_key', 'ip_address', 'created_at', 'last_activity', 'is_expired')
    list_filter = ('created_at', 'last_activity')
    search_fields = ('user__email', 'session_key', 'ip_address')
    ordering = ('-last_activity',)
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'created_at', 'last_activity', 'expires_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
    
    def has_add_permission(self, request):
        return False
    
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact Message admin configuration."""
    
    list_display = ('name', 'email', 'subject', 'status', 'created_at', 'has_reply')
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Message Info', {'fields': ('name', 'email', 'subject', 'message', 'status')}),
        ('User Info', {'fields': ('user', 'ip_address', 'user_agent')}),
        ('Reply', {'fields': ('reply', 'replied_by', 'replied_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_reply(self, obj):
        return bool(obj.reply)
    has_reply.boolean = True
    has_reply.short_description = 'Replied'
    
    def save_model(self, request, obj, form, change):
        if obj.reply and not obj.replied_by:
            obj.replied_by = request.user
            obj.replied_at = timezone.now()
            obj.status = 'replied'
        super().save_model(request, obj, form, change)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Menu Item admin configuration."""
    
    list_display = ('name', 'category', 'price', 'is_available', 'display_order', 'created_at')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available', 'display_order')
    ordering = ('category', 'display_order', 'name')
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'category', 'description', 'price')}),
        ('Display', {'fields': ('image', 'is_available', 'display_order')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')