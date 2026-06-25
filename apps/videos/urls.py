from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('my/', views.MyCoursesView.as_view(), name='my_courses'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/watch/', views.CourseWatchView.as_view(), name='course_watch'),
    path('<slug:slug>/stream/', views.serve_hls_playlist, name='serve_stream'),
    path('<slug:slug>/segment/<str:segment>', views.serve_hls_segment, name='serve_segment'),
    path('<slug:slug>/purchase/', views.course_purchase, name='course_purchase'),
]
