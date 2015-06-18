# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from cms.admin.placeholderadmin import (
    FrontendEditableAdminMixin,
    PlaceholderAdminMixin,
)
from parler.forms import TranslatableModelForm
from parler.admin import TranslatableAdmin
from aldryn_apphooks_config.admin import BaseAppHookConfig, ModelAppHookConfig
from aldryn_people.models import Person
from aldryn_reversion.admin import VersionedPlaceholderAdminMixin

from . import models


def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)
make_published.short_description = _(
    "Mark selected articles as published")


def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)
make_unpublished.short_description = _(
    "Mark selected articles as not published")


def make_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)
make_featured.short_description = _(
    "Mark selected articles as featured")


def make_not_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)
make_not_featured.short_description = _(
    "Mark selected articles as not featured")


class ArticleAdminForm(TranslatableModelForm):

    class Meta:
        model = models.Article
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)

        qs = models.Article.objects

        if hasattr(self.instance, 'app_config'):
            qs = models.Article.objects.filter(
                app_config=self.instance.app_config)
        elif 'initial' in kwargs and 'app_config' in kwargs['initial']:
            qs = models.Article.objects.filter(
                app_config=kwargs['initial']['app_config'])

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if 'related' in self.fields:
            self.fields['related'].queryset = qs

        # Don't allow app_configs to be added here. The correct way to add an
        # apphook-config is to create an apphook on a cms Page.
        self.fields['app_config'].widget.can_add_related = False


class ArticleAdmin(
    VersionedPlaceholderAdminMixin,
    FrontendEditableAdminMixin,
    ModelAppHookConfig,
    TranslatableAdmin
):
    form = ArticleAdminForm
    list_display = ('title', 'app_config', 'slug', 'is_featured',
                    'is_published')
    actions = (
        make_featured, make_not_featured,
        make_published, make_unpublished,
    )
    fieldsets = (
        (None, {
            'fields': (
                'app_config',
                'title',
                'featured_image',
                ('owner', 'author', ),
            )
        }),
        ('Details', {
            'fields': (
                ('is_published', 'publishing_date', ),
                'is_featured',
                'tags',
                'categories',
                'lead_in',
                'related',
            )
        }),
        ('Meta options', {
            'classes': ('collapse',),
            'fields': (
                'slug',
                'meta_title',
                'meta_description',
                'meta_keywords',
            )
        }),
    )
    app_config_values = {
        'default_published': 'is_published'
    }

    def add_view(self, request, *args, **kwargs):
        data = request.GET.copy()
        try:
            person = Person.objects.get(user=request.user)
            data['author'] = person.pk
            request.GET = data
        except Person.DoesNotExist:
            pass

        data['owner'] = request.user.pk
        request.GET = data
        return super(ArticleAdmin, self).add_view(request, *args, **kwargs)


admin.site.register(models.Article, ArticleAdmin)


class NewsBlogConfigAdmin(
    PlaceholderAdminMixin,
    BaseAppHookConfig,
    TranslatableAdmin
):
    def get_config_fields(self):
        return (
            'app_title', 'permalink_type', 'non_permalink_handling',
            'template_prefix',
            'paginate_by', 'create_authors', 'search_indexed',
            'config.default_published', )

admin.site.register(models.NewsBlogConfig, NewsBlogConfigAdmin)
