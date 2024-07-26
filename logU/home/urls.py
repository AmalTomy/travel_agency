from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views 

urlpatterns = [
    path('', views.index, name="index"),
    path('signup', views.signup, name="signup"),
    path('login', views.loginn, name="login"),
    path('welcome', views.welcome, name="welcome"),
    path('profile/', views.profile, name='profile'),
    path('booking/', views.booking, name='booking'),
    path('admin1/', views.admin1, name='admin1'),
    path('mod_reg/', views.mod_reg, name='mod_reg'),  
    path('signup_moderator/', views.signup_moderator, name='signup_moderator'),
    path('mod_sch/', views.mod_sch, name='mod_sch'),



    
    
   path('password_reset/',auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'),name="password_reset"),
    path('password_reset_done/',auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_sent.html'
    ),name="password_reset_done"),
    path('password_reset_confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ),name="password_reset_confirm"),
    path('password_reset_complete/',auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ),name="password_reset_complete"),
    
    path('accounts/', include('allauth.urls')),
]