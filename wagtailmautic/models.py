from django import forms
from django.core.exceptions import ValidationError
from .api import BaseApi as MauticApi
from django.db import models
from django.utils.translation import gettext as _
from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from wagtailmautic.utils import get_mautic_client


@register_setting
class MauticSettings(BaseSiteSetting):
    mautic_base_url = models.URLField(
        help_text="Your Mautic site URL including the https:// prefix - do NOT add a trailing slash",
        null=True,
        blank=True,
    )
    mautic_client_id = models.CharField(
        max_length=256,
        help_text="Mautic Client ID. Obtain from Mautic Settings",
        null=True,
        blank=True,
    )
    mautic_client_secret = models.CharField(
        max_length=256,
        help_text="Mautic Client Secret. Obtain from Mautic Settings",
        null=True,
        blank=True,
    )
    mautic_username = models.CharField(
        max_length=256,
        help_text="Mautic username. Add if not using client ID and secret",
        null=True,
        blank=True,
    )
    mautic_password = models.CharField(
        max_length=256,
        help_text="Mautic Password. Add if not using client ID and client secret. Will not be visible once saved. "
                  "Saving again will override any previously saved password",
        null=True,
        blank=True
    )

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("mautic_base_url"),
        ], heading="URL"),
        ObjectList([
            FieldPanel("mautic_client_id"),
            FieldPanel("mautic_client_secret"),
        ], heading="OAuth2"),
        ObjectList([
            FieldPanel("mautic_username"),
            FieldPanel("mautic_password", widget=forms.PasswordInput),
        ], heading="Basic Auth"),
    ])


class BaseMauticFormPage(models.Model):
    mautic_form_id = models.CharField(_('Mautic Form ID'), max_length=256, blank=True, null=True,
                                      help_text=_(
                                          "Form ID to use. Make sure you have created the "
                                          "form with all the required fields on Mautic"),
                                      )
    thank_you_text = models.TextField(blank=True, null=True, help_text="Message to show on successful submission")

    class Meta(object):
        abstract = True

    def clean(self):
        super().clean()

        if self.mautic_form_id:
            # create mautic api client
            client = get_mautic_client()

            if client:
                api = MauticApi(client=client, endpoint="forms")
                # check if the form exists
                form = api.get(self.mautic_form_id)

                if form.get("errors"):
                    raise ValidationError({
                        "mautic_form_id": f"Form with id: '{self.mautic_form_id}' does not exist on Mautic. "
                                          f"Please make sure this form is created on Mautic before saving"})

    def serve(self, request):
        """
        Serves the page as a MauticFormView.

        :param request: the request object.
        :rtype: django.http.HttpResponse.
        """

        if self.mautic_form_id:
            from .views import MauticFormView

            view = MauticFormView.as_view(page_instance=self)
            return view(request)

        # user default Wagtail Page serve method
        return super().serve(request)

    content_panels = [
        FieldPanel('mautic_form_id'),
        FieldPanel('thank_you_text')
    ]
