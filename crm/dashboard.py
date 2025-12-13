from django.db.models import Sum, Count, Q
from django.utils.translation import gettext_lazy as _


def dashboard_callback(request, context):
    from accounts.models import Customer, Tour, Booking

    # Calculate metrics
    total_customers = Customer.objects.count()
    total_tours = Tour.objects.count()
    total_revenue = Booking.objects.filter(payment_status='paid').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    accounts_receivable = Booking.objects.exclude(payment_status='paid').aggregate(
        total=Sum('total_price')
    )['total'] or 0
    pending_payments = Booking.objects.exclude(payment_status='paid').aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
    accounts_receivable = accounts_receivable - pending_payments

    # Customers by country
    customers_by_country = list(Customer.objects.values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    # Customers by city
    customers_by_city = list(Customer.objects.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    # Customers by age groups
    age_groups = {
        '18-25': Customer.objects.filter(age__gte=18, age__lte=25).count(),
        '26-35': Customer.objects.filter(age__gte=26, age__lte=35).count(),
        '36-45': Customer.objects.filter(age__gte=36, age__lte=45).count(),
        '46-55': Customer.objects.filter(age__gte=46, age__lte=55).count(),
        '56+': Customer.objects.filter(age__gte=56).count(),
    }

    # Customers by gender
    gender_stats = list(Customer.objects.values('gender').annotate(
        count=Count('id')
    ))

    context.update({
        "dashboard_stats": {
            "total_customers": total_customers,
            "total_tours": total_tours,
            "total_revenue": f"€{total_revenue:,.2f}",
            "accounts_receivable": f"€{accounts_receivable:,.2f}",
        },
        "customers_by_country": customers_by_country,
        "customers_by_city": customers_by_city,
        "age_groups": age_groups,
        "gender_stats": gender_stats,
    })

    return context
