from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.html import format_html
from django import forms
from unfold.admin import ModelAdmin
from .models import Customer, Tour, Booking, UserProfile

# Unregister default User admin
admin.site.unregister(User)


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False, help_text='First name')
    last_name = forms.CharField(max_length=150, required=False, help_text='Last name')
    email = forms.EmailField(required=False, help_text='Email address')

    # Profile fields
    photo = forms.ImageField(required=False, help_text='Profile photo')
    phone = forms.CharField(max_length=20, required=False, help_text='Phone number')
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text='Birth date')
    gender = forms.ChoiceField(choices=[('', '-------')] + UserProfile.GENDER_CHOICES, required=False)
    status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES, initial='active', required=False)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')

        if commit:
            user.save()
            # Update or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.birth_date = self.cleaned_data.get('birth_date')
            profile.gender = self.cleaned_data.get('gender', '')
            profile.status = self.cleaned_data.get('status', 'active')

            # Handle photo upload
            photo = self.cleaned_data.get('photo')
            if photo:
                profile.photo = photo

            profile.save()

        return user


class CustomUserChangeForm(UserChangeForm):
    # Profile fields
    photo = forms.ImageField(required=False, help_text='Profile photo')
    phone = forms.CharField(max_length=20, required=False, help_text='Phone number')
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text='Birth date')
    gender = forms.ChoiceField(choices=[('', '-------')] + UserProfile.GENDER_CHOICES, required=False)
    status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES, required=False)

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate profile fields if editing existing user
        if self.instance and self.instance.pk and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['phone'].initial = profile.phone
            self.fields['birth_date'].initial = profile.birth_date
            self.fields['gender'].initial = profile.gender
            self.fields['status'].initial = profile.status

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            # Update or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.birth_date = self.cleaned_data.get('birth_date')
            profile.gender = self.cleaned_data.get('gender', '')
            profile.status = self.cleaned_data.get('status', 'active')

            # Handle photo upload
            photo = self.cleaned_data.get('photo')
            if photo:
                profile.photo = photo

            profile.save()

        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ['get_photo', 'username', 'get_full_name', 'email', 'get_phone', 'get_role', 'get_status', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    list_editable = ['is_active']

    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'password'),
            'description': 'Basic account credentials'
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email'),
            'description': 'User personal details'
        }),
        ('Profile Information', {
            'fields': ('photo', 'phone', 'birth_date', 'gender', 'status'),
            'description': 'Profile photo and additional information'
        }),
        ('Permissions & Role', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'User role: Admin = Superuser ✓, Moderator = Staff ✓, Reader = Normal User'
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('Account Information', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
            'description': 'Create username and password for the new user'
        }),
        ('Personal Information', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
            'description': 'Enter personal details'
        }),
        ('Profile Information', {
            'classes': ('wide',),
            'fields': ('photo', 'phone', 'birth_date', 'gender', 'status'),
            'description': 'Upload photo and enter additional profile information'
        }),
        ('Permissions & Role', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'User role: Admin = Superuser ✓, Moderator = Staff ✓, Reader = Normal User'
        }),
    )

    def get_photo(self, obj):
        if hasattr(obj, 'profile') and obj.profile.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.profile.photo.url)
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background: #D4AF37; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{}</div>',
                          obj.username[0].upper() if obj.username else '?')
    get_photo.short_description = 'Photo'

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else '-'
    get_full_name.short_description = 'Full Name'

    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') and obj.profile.phone else '-'
    get_phone.short_description = 'Phone'

    def get_role(self, obj):
        if obj.is_superuser:
            return format_html('<span style="background: #D4AF37; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Admin</span>')
        elif obj.is_staff:
            return format_html('<span style="background: #445656; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Moderator</span>')
        else:
            return format_html('<span style="background: #9CA3AF; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Reader</span>')
    get_role.short_description = 'Role'

    def get_status(self, obj):
        if hasattr(obj, 'profile'):
            status = obj.profile.status
            if status == 'active':
                return format_html('<span style="color: #16a34a; font-weight: 600;">●</span> Active')
            else:
                return format_html('<span style="color: #dc2626; font-weight: 600;">●</span> Passive')
        return '-'
    get_status.short_description = 'Status'


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'country', 'city', 'age', 'gender', 'created_at']
    list_filter = ['country', 'city', 'gender', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']

@admin.register(Tour)
class TourAdmin(ModelAdmin):
    list_display = ['name', 'destination', 'duration_days', 'price', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'destination', 'start_date']
    search_fields = ['name', 'destination', 'description']

@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['customer', 'tour', 'number_of_participants', 'total_price', 'amount_paid', 'payment_status', 'booking_date']
    list_filter = ['payment_status', 'booking_date', 'tour']
    search_fields = ['customer__first_name', 'customer__last_name', 'tour__name']
    readonly_fields = ['accounts_receivable']
