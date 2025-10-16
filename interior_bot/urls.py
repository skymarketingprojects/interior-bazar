from django.urls import path, include
from interior_bot import views
urlpatterns = [
    path('messages/',views.GetMessagesView, name='GetMessagesView'),
]
