from wagtail.models import Site

from .api import MauticBasicAuthClient, MauticOauth2Client
from .errors import WagtailMauticError


def get_mautic_client(request=None):
    from .models import MauticSettings
    if request is None:
        site = Site.objects.get(is_default_site=True)
        mautic_settings = MauticSettings.for_site(site)
    else:
        mautic_settings = MauticSettings.for_request(request)

    base_url = mautic_settings.mautic_base_url
    client_id = mautic_settings.mautic_client_id
    client_secret = mautic_settings.mautic_client_secret
    username = mautic_settings.mautic_username
    password = mautic_settings.mautic_password

    if not base_url:
        raise WagtailMauticError("Base url required in Mautic Settings")
    if client_id and client_secret:
        return MauticOauth2Client(base_url, client_id, client_secret)
    if username and password:
        return MauticBasicAuthClient(base_url, username, password)
    return None
