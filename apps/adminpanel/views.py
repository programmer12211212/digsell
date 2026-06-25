from django.shortcuts import render

from .services import get_dashboard_stats, get_analytics_chart, get_recent_activities
from .permissions import staff_required


@staff_required
def admin_enterprise_dashboard(request):
    stats = get_dashboard_stats()
    chart = get_analytics_chart('30d')
    activities = get_recent_activities(limit=15)
    return render(request, 'adminpanel/enterprise_dashboard.html', {
        'stats': stats,
        'chart': chart,
        'activities': activities,
    })