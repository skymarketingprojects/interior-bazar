from django.contrib import admin

from interior_forms.models import FormDefinition


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    list_display = ('key', 'page', 'component', 'version', 'is_active', 'updatedOn')
    list_filter = ('is_active',)
    search_fields = ('key', 'page', 'component')
    readonly_fields = ('createdOn', 'updatedOn')
