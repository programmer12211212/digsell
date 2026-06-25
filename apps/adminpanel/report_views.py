import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from apps.users.models import User
from apps.orders.models import Order
from django.utils import timezone
from .permissions import staff_required

@staff_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Role', 'Balance', 'Joined At'])
    
    users = User.objects.all().select_related('wallet')
    for u in users:
        writer.writerow([
            u.username, u.email, u.role, 
            u.wallet.balance if hasattr(u, 'wallet') else 0,
            u.date_joined.strftime("%Y-%m-%d %H:%M")
        ])
    
    return response

@staff_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="orders_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Buyer', 'Amount', 'Status', 'Date'])
    
    orders = Order.objects.all().select_related('buyer')
    for o in orders:
        writer.writerow([
            o.id, o.buyer.username, o.final_amount, o.status,
            o.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    
    return response


@staff_required
def export_orders_pdf(request):
    from django.template.loader import render_to_string
    orders = Order.objects.select_related('buyer').prefetch_related('items__product__seller').order_by('-created_at')[:200]
    html = render_to_string('adminpanel/reports/orders_pdf.html', {'orders': orders})
    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="orders_{timezone.now().strftime("%Y%m%d")}.html"'
    return response