from django.urls import path

from .views import PredictTeamView

urlpatterns = [
    path("predict-team/", PredictTeamView.as_view(), name="predict-team"),
]
