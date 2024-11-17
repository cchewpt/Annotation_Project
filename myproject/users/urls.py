from django.urls import path
from . import views
from .views import login_view
from .views import texttopost
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('login/accounts/mainlogin/', views.mainlogin, name='mainlogin'),
    path('annotatepage/', views.annotatepage, name='annotatepage'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
    path('reset-password-confirm/<uidb64>/<token>/', views.forgotpass2, name='forgotpass2'),
    path('login/accounts/texttopost/', texttopost, name='texttopost'),
    path('login/accounts/texttopostFile/', views.texttopostFile, name='texttopostFile'),
    path('login/accounts/txtverify/', views.txtverify, name='txtverify'),
    path('login/accounts/txtverifyFile/', views.txtverifyFile, name='txtverifyFile'),
    path('registration/', views.registration, name='registration'),
    path('login/accounts/annotateselect/', views.annotateselect, name='annotateselect'),
    path('login/accounts/edit_profile/', views.edit_profile, name='edit_profile'),
    path('login/accounts/user_profile/', views.user_profile, name='user_profile'),
    path('login/accounts/admin_profile/', views.admin_profile, name='admin_profile'),
    path('login/accounts/user_propose_history/', views.user_propose_history, name='user_propose_history'),
    path('login/accounts/admin_edit_user/', views.admin_edit_user, name='admin_edit_user'),
    path('login/accounts/admin_edit_user2/<int:user_id>/', views.admin_edit_user2, name='admin_edit_user2'),
    path('login/accounts/admin_edit_profile/', views.admin_edit_profile, name='admin_edit_profile'),
    path('update_text_status/', views.update_text_status, name='update_text_status'),
    path('assign_user_tasks/', views.assign_user_tasks, name='assign_user_tasks'),
    path('login/accounts/admin_approved1/', views.admin_approved1, name='admin_approved1'),
    path('login/accounts/admin_approved2/<int:user_id>/', views.admin_approved2, name='admin_approved2_with_user_id'),
    path('login/accounts/admin_mng_datasets1/', views.admin_mng_datasets1, name='admin_mng_datasets1'),
    path('login/accounts/userannotatehist/', views.userannotatehist, name='userannotatehist'),
    path('userannotatehist2/<int:task_id>/', views.userannotatehist2, name='userannotatehist2'),
    path('login/accounts/admin_add_datasets/', views.admin_add_datasets, name='admin_add_datasets'),
    path('login/accounts/admin_add_userText/', views.admin_add_userText, name='admin_add_userText'),
    path('login/accounts/admin_assign_data/<int:task_id>/', views.admin_assign_data, name='admin_assign_data'),
    path('usersannotating/<int:task_id>/<int:current_index>/', views.usersannotating, name='usersannotating'),
    path('update_annotated_class/<int:annotated_id>/', views.update_annotated_class, name='update_annotated_class'),
    path('update_annotation/<int:annotated_id>/', views.update_annotation, name='update_annotation'),
    path('confirm_annotation/<int:task_id>/<int:current_index>/', views.confirm_annotation, name='confirm_annotation'),
    path('login/accounts/admin_kappa/', views.admin_kappa, name='admin_kappa'),
    path('login/accounts/user_annotated_stat/', views.user_annotated_stat, name='user_annotated_stat'),
    path('usersannotating/<int:task_id>/<int:current_index>/', views.usersannotating, name='usersannotating'),
]
