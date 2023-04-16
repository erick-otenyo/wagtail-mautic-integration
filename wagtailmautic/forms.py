from collections import OrderedDict

from django import forms
from django.core.validators import FileExtensionValidator

from .fields import CountryField


class MauticForm(forms.Form):
    required_css_class = 'required'

    """
    Mautic form class.
    """

    def __init__(self, mautic_form_fields, *args, **kwargs):
        """
        Initailizes the form instance, adding fields from given
        Mautic form.

        :param mautic_form_fields: list of form fields.
        """
        # Initialize the form instance.
        super(MauticForm, self).__init__(*args, **kwargs)

        # Add form fields.
        for field in mautic_form_fields:
            for data in self.mautic_field_factory(field).items():
                name, field = data
                self.fields.update({name: field})

    def mautic_field_factory(self, form_field):
        """
        Returns a form field instance for specified mautic form Field.

        :param form_field: mautic field dictionary.
        :rtype: django.forms.Field.
        """
        fields = OrderedDict()
        mc_type = form_field.get('type', None)
        name = form_field.get('alias', '')
        mc_properties = form_field.get('properties', {})
        kwargs = {
            'label': form_field.get('label', None),
            'required': form_field.get('isRequired', True),
            'initial': form_field.get('defaultValue', None),
            'help_text': form_field.get('helpMessage', None),
        }

        if mc_type == 'email':
            fields.update({name: forms.EmailField(**kwargs)})

        if mc_type == 'text':
            fields.update({name: forms.CharField(**kwargs)})

        if mc_type == 'number':
            fields.update({name: forms.IntegerField(**kwargs)})

        if mc_type == "hidden":
            kwargs.update({"widget": forms.HiddenInput})
            fields.update({name: forms.CharField(**kwargs)})

        if mc_type == 'password':
            kwargs.update({"widget": forms.PasswordInput})
            fields.update({name: forms.CharField(**kwargs)})

        if mc_type == 'textarea':
            kwargs.update({"widget": forms.Textarea})
            fields.update({name: forms.CharField(**kwargs, )})

        if mc_type == 'radiogrp':
            choices = ((c.get("value"), c.get("label")) for c in
                       mc_properties.get('optionlist', {}).get("list", []))
            kwargs.update({'choices': choices, 'widget': forms.RadioSelect})
            fields.update({name: forms.ChoiceField(**kwargs)})

        if mc_type == 'select':
            choices = ((c.get("value"), c.get("label")) for c in
                       mc_properties.get('list', {}).get("list", []))
            kwargs.update({'choices': choices})
            multiple = mc_properties.get('multiple', 0)

            if multiple == 0:
                fields.update({name: forms.ChoiceField(**kwargs)})
            else:
                kwargs.update({"widget": forms.CheckboxSelectMultiple})
                fields.update({name: forms.MultipleChoiceField(**kwargs)})

        if mc_type == 'date':
            kwargs.update({"widget": forms.DateInput(attrs={'type': 'date'})})
            fields.update({name: forms.DateField(**kwargs)})

        if mc_type == 'datetime':
            kwargs.update({"widget": forms.DateTimeInput(attrs={'type': 'datetime-local'})})
            fields.update({name: forms.DateTimeField(**kwargs)})

        if mc_type == 'tel':
            fields.update({name: forms.CharField(**kwargs)})

        if mc_type == 'url':
            fields.update({name: forms.URLField(**kwargs)})

        if mc_type == 'file':
            allowed_file_extensions = mc_properties.get("allowed_file_extensions", [])
            if allowed_file_extensions:
                kwargs.update({"validators": [FileExtensionValidator(allowed_file_extensions)]})
            fields.update({name: forms.FileField(**kwargs)})

        if mc_type == "country":
            fields.update({name: CountryField(**kwargs)})

        return fields
