from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm, UserChangeForm
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import reverse
from django import forms
from unfold.admin import ModelAdmin, StackedInline
from unfold.forms import AdminPasswordChangeForm, UserCreationForm, UserChangeForm as UnfoldUserChangeForm
from unfold.widgets import UnfoldAdminSplitDateTimeWidget, UnfoldAdminDateWidget
from .models import Customer, Tour, Booking, UserProfile
import datetime

# Unregister default User admin
admin.site.unregister(User)


class UserCreationFormNoHelp(UserCreationForm):
    """Unfold's UserCreationForm without help text"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].help_text = None


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['phone', 'birth_date', 'gender']


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    add_form = UserCreationFormNoHelp
    form = UnfoldUserChangeForm
    change_password_form = AdminPasswordChangeForm
    inlines = [UserProfileInline]

    list_display = ['get_photo', 'username', 'get_full_name', 'email', 'get_created', 'get_role', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    list_editable = ['is_active']
    actions = ['edit_selected_user']

    # Add user fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Permissions', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
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

    def get_created(self, obj):
        return obj.date_joined.strftime('%Y-%m-%d %H:%M') if obj.date_joined else '-'
    get_created.short_description = 'Created'

    def get_role(self, obj):
        if obj.is_superuser:
            return format_html('<span style="background: #D4AF37; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Admin</span>')
        elif obj.is_staff:
            return format_html('<span style="background: #445656; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Moderator</span>')
        else:
            return format_html('<span style="background: #9CA3AF; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Reader</span>')
    get_role.short_description = 'Role'

    def save_model(self, request, obj, form, change):
        """Sync is_active with profile status"""
        super().save_model(request, obj, form, change)
        if hasattr(obj, 'profile'):
            obj.profile.status = 'active' if obj.is_active else 'passive'
            obj.profile.save()

    def edit_selected_user(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one user to edit.', level='warning')
            return
        user = queryset.first()
        url = reverse('admin:auth_user_change', args=[user.pk])
        return redirect(url)
    edit_selected_user.short_description = 'Edit selected user'


class SeasonListFilter(admin.SimpleListFilter):
    title = 'Sezon'
    parameter_name = 'season'

    def lookups(self, request, model_admin):
        years = set([d.year for d in Customer.objects.dates('created_at', 'year')])
        return [(year, str(year)) for year in sorted(years, reverse=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_at__year=self.value())
        return queryset


class TourListFilter(admin.SimpleListFilter):
    title = 'Tur'
    parameter_name = 'tour'

    def lookups(self, request, model_admin):
        tours = Tour.objects.all().values_list('id', 'name')
        return [(tour[0], tour[1]) for tour in tours]

    def queryset(self, request, queryset):
        if self.value():
            # Filter customers who have bookings for this tour
            return queryset.filter(bookings__tour_id=self.value()).distinct()
        return queryset


class CustomerAdminForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'birth_date': UnfoldAdminDateWidget(),
            'passport_issue_date': UnfoldAdminDateWidget(),
            'passport_expiry_date': UnfoldAdminDateWidget(),
        }

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    form = CustomerAdminForm
    list_display = ['get_photo', 'customer_number', 'first_name', 'last_name', 'email', 'phone', 'nationality', 'created_at']
    list_filter = [SeasonListFilter, TourListFilter, 'country', 'city', 'gender', 'nationality']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'customer_number', 'passport_number']
    readonly_fields = ['customer_number', 'created_at', 'updated_at', 'photo_preview']
    actions = ['delete_selected', 'edit_selected_customer']
    list_display_links = ['customer_number', 'first_name', 'last_name']  # Clickable fields for view mode

    fieldsets = (
        ('General Information', {
            'fields': (
                'customer_number',
                ('first_name', 'last_name'),
                ('passport_number', 'identity_number'),
                ('birth_date', 'birth_place'),
                ('mother_name', 'father_name'),
                ('phone', 'email'),
                ('nationality', 'gender'),
                ('emergency_contact_name', 'emergency_contact_phone'),
                'photo_preview',
            )
        }),
        ('Address Information', {
            'fields': (
                ('country', 'city'),
                ('district', 'street'),
                ('building_no', 'apartment_no'),
                'postal_code',
                'address_description',
            )
        }),
        ('Meta Information', {
            'fields': (
                ('is_visitor', 'is_disabled', 'is_student', 'has_chronic_disease'),
                ('document_type', 'marital_status'),
                ('education', 'occupation'),
                ('passport_type', 'passport_address'),
                ('issuing_authority', 'language'),
                ('passport_issue_date', 'passport_expiry_date'),
            )
        }),
    )

    def get_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background: #D4AF37; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{}</div>',
                          obj.first_name[0].upper() if obj.first_name else '?')
    get_photo.short_description = 'Photo'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<div style="margin-top: 10px;">'
                '<img src="{}" style="max-width: 600px; max-height: 800px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" />'
                '</div>',
                obj.photo.url
            )
        return "No passport image uploaded"
    photo_preview.short_description = 'Passport Image'

    def edit_selected_customer(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one customer to edit.', level='warning')
            return
        customer = queryset.first()
        url = reverse('admin:accounts_customer_change', args=[customer.pk]) + '?edit=true'
        return redirect(url)
    edit_selected_customer.short_description = 'Edit selected customer'

    # def changelist_view(self, request, extra_context=None):
    #     # Ensure has_add_permission is True for changelist
    #     extra_context = extra_context or {}
    #     extra_context['has_add_permission'] = self.has_add_permission(request)
    #     return super().changelist_view(request, extra_context)

    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     # By default, open in readonly mode when clicking from list
    #     # Only allow editing via "Edit selected customer" action
    #     if 'edit' not in request.GET and not request.POST:
    #         extra_context = extra_context or {}
    #         extra_context['show_save'] = False
    #         extra_context['show_save_and_continue'] = False
    #         extra_context['show_save_and_add_another'] = False
    #         extra_context['readonly'] = True
    #     return super().change_view(request, object_id, form_url, extra_context)

    # def has_add_permission(self, request):
    #     return True

    # def has_change_permission(self, request, obj=None):
    #     # Only allow editing via "Edit selected customer" action
    #     if obj and 'edit' not in request.GET and request.method == 'GET':
    #         return False
    #     return super().has_change_permission(request, obj)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None:
            # When adding new customer, hide customer_number (will be auto-generated)
            return (
                ('General Information', {
                    'fields': (
                        ('first_name', 'last_name'),
                        ('passport_number', 'identity_number'),
                        ('birth_date', 'birth_place'),
                        ('mother_name', 'father_name'),
                        ('phone', 'email'),
                        ('nationality', 'gender'),
                        ('emergency_contact_name', 'emergency_contact_phone'),
                        'photo_preview',
                    )
                }),
                ('Address Information', {
                    'fields': (
                        ('country', 'city'),
                        ('district', 'street'),
                        ('building_no', 'apartment_no'),
                        'postal_code',
                        'address_description',
                    )
                }),
                ('Meta Information', {
                    'fields': (
                        ('is_visitor', 'is_disabled', 'is_student', 'has_chronic_disease'),
                        ('document_type', 'marital_status'),
                        ('education', 'occupation'),
                        ('passport_type', 'passport_address'),
                        ('issuing_authority', 'language'),
                        ('passport_issue_date', 'passport_expiry_date'),
                    )
                }),
            )
        return fieldsets

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
