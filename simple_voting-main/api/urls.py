from django.urls import path

from .views import *

urlpatterns = [
    path('survey/create/', create_survey),
    path('survey/get/', get_survey),
    path('survey/history/', get_user_history),
    path('survey/new/', get_new_surveys),
    path('survey/user/', get_user_surveys),
    path('survey/vote/', vote_survey),
]

