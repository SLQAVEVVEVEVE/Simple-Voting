from django.urls import path
from .views import *

urlpatterns = [
    path('', index_page),
    path('account/signup/', signup),
    path('account/login/', login),
    path('account/logout/', logout),
    path('account/', view_account),
    path("history/", view_history),
    path('issue/create/', create_issue),
    path('issue/chats/', issue_chats),
    path('issue/close/', close_issue),
    path("issue/messages/", issue_chat_messages),
    path("admin/", admin_issues),
]
