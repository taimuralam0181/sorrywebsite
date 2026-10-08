from django.urls import path

from . import views


app_name = "sorry"

urlpatterns = [
    path("", views.home, name="home"),
    path("create/", views.create_page, name="create"),
    path("preview/<slug:slug>/", views.preview_page, name="preview"),
    path("preview/<slug:slug>/publish/", views.publish_page, name="publish"),
    path("published/<slug:slug>/", views.published_success, name="published"),
    path("s/<slug:slug>/", views.published_page, name="public"),
]
