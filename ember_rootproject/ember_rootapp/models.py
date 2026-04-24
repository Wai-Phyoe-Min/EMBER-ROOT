from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        # REMOVED: extra_fields.setdefault('is_admin', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with user types and additional fields."""
    
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.CharField(max_length=1, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        return self.email
    
    def get_avatar_initial(self):
        if self.first_name:
            return self.first_name[0].upper()
        return self.email[0].upper()
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    @property
    def is_customer(self):
        return self.user_type == 'customer'
    
    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser


class Pizza(models.Model):
    """Pizza model with farm-to-table information."""
    
    CATEGORY_CHOICES = (
        ('classics', 'Classics'),
        ('signature', 'Signature'),
        ('white', 'White Pizzas'),
        ('seasonal', 'Seasonal'),
    )
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='classics')
    description = models.TextField()
    price = models.IntegerField(validators=[MinValueValidator(0)])
    calories = models.IntegerField(default=0)
    dietary = models.JSONField(default=list, blank=True)  # Store as list: ['Vegetarian', 'Spicy']
    farm = models.CharField(max_length=200)
    farm_story = models.TextField(blank=True, null=True)
    latitude = models.FloatField(default=36.348)
    longitude = models.FloatField(default=138.597)
    image = models.URLField(max_length=500, blank=True, null=True)
    bestseller = models.BooleanField(default=False)
    seasonal_note = models.CharField(max_length=200, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    # Pairing details
    recommended_pairing = models.CharField(max_length=100, blank=True, null=True)
    recommended_pairing_price = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    recommended_pairing_description = models.TextField(blank=True, null=True)
    recommended_pairing_image = models.URLField(max_length=500, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pizzas_created')
    
    class Meta:
        db_table = 'pizzas'
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
    
    def get_dietary_tags(self):
        return self.dietary if isinstance(self.dietary, list) else []


class Order(models.Model):
    """Order model for customer purchases."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Order details
    items = models.JSONField(default=list)  # Store cart items as JSON
    subtotal = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    
    # Pickup information
    pickup_time = models.DateTimeField(null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number: ORD-YYYYMMDD-XXXX
            from django.utils import timezone
            import random
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices('0123456789', k=4))
            self.order_number = f"ORD-{date_str}-{random_str}"
        super().save(*args, **kwargs)


class Favorite(models.Model):
    """User's favorite pizzas."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE, related_name='favorited_by')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorites'
        unique_together = ['user', 'pizza']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.pizza.name}"


class UserActivity(models.Model):
    """Track user activities."""
    
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Register'),
        ('order_placed', 'Order Placed'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('favorite_add', 'Favorite Added'),
        ('favorite_remove', 'Favorite Removed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"


class UserSession(models.Model):
    """Track user sessions."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class ContactMessage(models.Model):
    """Contact form messages from users."""
    
    SUBJECT_CHOICES = (
        ('general', 'General Inquiry'),
        ('order', 'Order Question'),
        ('group', 'Group Booking (10+ people)'),
        ('farm', 'Farm Partnership'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    read_by_user = models.BooleanField(default=False)
    
    # Optional: link to user if logged in
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_messages')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Staff reply
    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='replied_messages')
    replied_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_messages'
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} - {self.created_at.strftime('%Y-%m-%d')}"
    
class MenuItem(models.Model):
    """Sides and drinks menu items."""
    
    CATEGORY_CHOICES = (
        ('sides', 'Sides'),
        ('drinks', 'Drinks'),
    )
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=200)
    price = models.IntegerField(validators=[MinValueValidator(0)])
    image = models.URLField(max_length=500, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_items'
        ordering = ['category', 'display_order', 'name']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
class BusinessHours(models.Model):
    """Business hours for the restaurant."""
    
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    day = models.CharField(max_length=10, choices=DAY_CHOICES, unique=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., 'Visiting partner farms'")
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_hours'
        ordering = ['display_order', 'day']
        verbose_name = 'Business Hours'
        verbose_name_plural = 'Business Hours'
    
    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_display()}: Closed"
        return f"{self.get_day_display()}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"