from django.urls import path
from . import views
from stats.views import UpcomingList, UpcomingDetailView, UpcomingUpdateView, UpcomingDeleteView

urlpatterns = [
    path('', views.home, name='stats-home'),
    path('home/<slug:gameType>/', views.homeUpdate, name='stats-home-update'),
    path('about/', views.about, name='stats-about'),
    path('newgame/', views.newgame, name='stats-newgame'),
    path('game/<slug:slug>/', views.GameDetailView.as_view(), name='stats-game'),
    path('results/', views.results, name='stats-results'),
    path('createCompany/', views.createCompany, name='stats-createCompany'),
    path('company/', views.company, name='stats-company'),
    path('schedule/', views.UpcomingList.as_view(), name='stats-schedule'),
    path('schedule/new/', views.newmatch, name='stats-newmatch'),
    path('schedule/<int:pk>/', views.UpcomingDetailView.as_view(), name='stats-upcoming'),
    path('schedule/<int:pk>/update/', views.UpcomingUpdateView.as_view(), name='stats-updatematch'),
    path('schedule/<int:pk>/delete/', views.UpcomingDeleteView.as_view(), name='stats-deletematch')
]