from django.db import models

from wagtail.models import Page

from wagtailmautic.models import BaseMauticFormPage


class HomePage(BaseMauticFormPage, Page):
    content_panels = Page.content_panels + BaseMauticFormPage.content_panels
