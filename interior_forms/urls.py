from django.urls import path

from interior_forms.Views import FormDefinitionView

urlpatterns = [
    # public — the SPA fetches the form schema to render by key
    path('definitions/<slug:key>/', FormDefinitionView.GetFormDefinitionView, name='form-definition-detail'),
]
