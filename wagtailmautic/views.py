from django.core.mail import mail_admins
from django.forms.forms import NON_FIELD_ERRORS
from django.http import Http404
from django.shortcuts import render
from django.views.generic import FormView

from .api import BaseApi as MauticApi
from .errors import WagtailMauticError
from .forms import MauticForm
from .utils import get_mautic_client


class MauticFormView(FormView):
    """
    Displays and processes a form based on a Mautic Form.
    """
    form_class = MauticForm
    page_instance = None
    form_fields = None

    def get_api_client(self, endpoint=""):
        # Get the mautic settings for the current site
        client = get_mautic_client(self.request)

        if client:
            return MauticApi(client, endpoint=endpoint)
        else:
            raise WagtailMauticError("Mautic API Improperly configured")

    def get_context_data(self, **kwargs):
        """
        Returns view context data dictionary.

        :rtype: dict.
        """
        context = super(MauticFormView, self).get_context_data(**kwargs)
        page = self.page_instance
        context.update({'self': page, 'page': page, })

        return context

    def get_form_fields(self):
        """
        Returns list of  Mautic form fields dictionaries.

        :rtype: dict.
        """

        if self.form_fields is None:
            api = self.get_api_client(endpoint="forms")
            mautic_form_id = self.page_instance.mautic_form_id
            res = api.get(mautic_form_id)

            if res.get("errors"):
                message = f"Error getting form with id: {mautic_form_id}"
                first_error = res.get("errors")[0]
                if first_error.get("message"):
                    message = first_error.get("message")
                raise Exception(message)
            self.form_fields = res.get("form", {}).get("fields", {})

        # If we don't have any fields to build a form from,
        # raise an HTTP 404 error.
        if not self.form_fields:
            raise Http404

        return self.form_fields

    def get_form(self, form_class=None):
        """
        Returns MauticForm instance.

        :param form_class: name of the form class to use.
        :rtype: MauticForm.
        """
        form_fields = self.get_form_fields()
        return MauticForm(form_fields, **self.get_form_kwargs())

    def get_template_names(self):
        """
        Returns list of available template names.

        :rtype: list.
        """
        return [self.page_instance.get_template(self.request)]

    def form_valid(self, form):
        """
        Submits data to a mautic form.

        :param form: the form instance.
        """
        form_data = form.cleaned_data
        mautic_form_id = self.page_instance.mautic_form_id

        mautic_data = {}
        for key, value in form_data.items():
            mautic_data[f"mauticform[{key}]"] = value

        mautic_data["mauticform[formId]"] = mautic_form_id

        api = self.get_api_client()
        error_traceback = None

        try:
            sent = api.submit_form_data(mautic_form_id, data=mautic_data, utm_source="nmhs_cms_integration")
        except Exception as e:
            error_traceback = e
            sent = False

        if not sent:
            form.errors[NON_FIELD_ERRORS] = form.error_class(
                ["We are having issues submitting the form to Mautic. Please try later"]
            )
            if error_traceback:
                mail_admins("Error submitting form to Mautic", str(error_traceback), fail_silently=True)

            return super(MauticFormView, self).form_invalid(form)

        # form submitted successfully
        return render(self.request, 'form_thank_you_landing.html',
                      context={'page': self.page_instance, 'self': self.page_instance})
