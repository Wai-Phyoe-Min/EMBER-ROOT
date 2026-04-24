from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import authenticate
from django.core.validators import MinLengthValidator
from .models import ContactMessage, User
import re


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with email field."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'hello@emberandroot.jp',
            'id': 'loginEmail',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'Enter your password',
            'id': 'loginPassword',
        })
    )
    
    error_messages = {
        'invalid_login': "Invalid email or password. Please try again.",
        'inactive': "This account is inactive.",
    }
    
    def clean_username(self):
        return self.cleaned_data.get('username').lower()


class CustomUserCreationForm(UserCreationForm):
    """Custom registration form."""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'Kenji Tanaka',
            'id': 'registerName',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'Last Name (Optional)',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'hello@emberandroot.jp',
            'id': 'registerEmail',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field-modern',
            'placeholder': '+81 XX-XXXX-XXXX',
            'id': 'registerPhone',
        })
    )
    password1 = forms.CharField(
        label='Password',
        validators=[MinLengthValidator(6)],
        widget=forms.PasswordInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'Create a strong password',
            'id': 'registerPassword',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input-field-modern',
            'placeholder': 'Confirm your password',
            'id': 'registerConfirmPassword',
        })
    )
    terms_agree = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'termsAgree',
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation for Japan
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.username = user.email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.phone = self.cleaned_data.get('phone', '')
        user.user_type = 'customer'
        
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EmailUpdateForm(forms.ModelForm):
    """Form for updating email."""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if not self.instance.check_password(password):
            raise forms.ValidationError("Current password is incorrect.")
        return password


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form."""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password',
            'id': 'currentPassword',
        })
    )
    new_password1 = forms.CharField(
        validators=[MinLengthValidator(6)],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password',
            'id': 'editFieldValue',
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password',
            'id': 'confirmPassword',
        })
    )


class ForgotPasswordForm(forms.Form):
    """Form for password reset request."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'resetEmail',
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email.")
        return email

class ContactForm(forms.ModelForm):
    """Contact form for user messages."""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Your name',
                'id': 'contactName',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'your@email.com',
                'id': 'contactEmail',
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control-custom',
                'id': 'contactSubject',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Tell us what\'s on your mind...',
                'id': 'contactMessage',
                'rows': 5,
            }),
        }