from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.static import serve as serve_media

urlpatterns = [
    path("admin/", admin.site.urls),
    # Authentication URLs
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Password change (when logged in)
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Password reset (when forgotten)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # App URLs
    path("", include("invoices.urls")),
]

# Uploaded files (company logo, saved PDFs) hold business details, so they are only
# served to logged-in users, with or without DEBUG.
urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
        login_required(serve_media),
        {"document_root": settings.MEDIA_ROOT},
    ),
]

admin.site.site_header = "Invoice Generator"
admin.site.site_title = "Invoice Generator"
admin.site.index_title = "Welcome to Your Site"
