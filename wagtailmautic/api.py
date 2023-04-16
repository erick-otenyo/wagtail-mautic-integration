import requests
from requests_oauthlib import OAuth2Session
from html.parser import HTMLParser


class MauticFormResponseParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_well_div = False
        self.well_div_data = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for name, value in attrs:
                if name == 'class' and 'well text-center' in value:
                    self.in_well_div = True

    def handle_data(self, data):
        if self.in_well_div:
            self.well_div_data += data.strip()

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_well_div:
            self.in_well_div = False


class MauticOauth2Client(object):
    def __init__(
            self,
            base_url,
            client_id,
            client_secret=None,
            scope=None,
            token=None,
            token_updater=None
    ):
        """
        :param base_url: str Base URL for Mautic API E.g. `https://<your-domain>.mautic.net`
        :param client_id: str Mautic API Public Key
        :param client_secret: str Mautic API Secret Key - needed to autorefresh token
        :param scope: list|str
        :param token: dict with access token data
        :param token_updater: function used for token autorefresh.
        """
        if scope and not isinstance(scope, (list, tuple)):
            scope = scope.split(',')
        self.base_url = base_url.strip(' /')

        self.access_token_url = base_url + '/oauth/v2/token'
        self.authorization_base_url = base_url + '/oauth/v2/authorize'

        if token_updater is not None and client_secret is not None:
            kwargs = {
                'auto_refresh_url': self.access_token_url,
                'auto_refresh_kwargs': {
                    'client_id': client_id,
                    'client_secret': client_secret
                },
                'token_updater': token_updater
            }
        else:
            kwargs = {}

        self.session = OAuth2Session(
            client_id, scope=scope, token=token, **kwargs
        )


class MauticBasicAuthClient(object):
    def __init__(
            self,
            base_url,
            username,
            password
    ):
        """
        :param base_url: str Base URL for Mautic API E.g. `https://<your-domain>.mautic.net`
        :param username: str Mautic Username
        :param password: str Mautic Password
        """

        self.base_url = base_url.strip(' /')

        self.session = requests.Session()
        self.session.auth = (username, password)


class BaseApi(object):

    def __init__(self, client, endpoint=""):
        self._client = client
        self.endpoint_url = '{base_url}/api/{endpoint}'.format(
            base_url=self._client.base_url,
            endpoint=endpoint.strip(' /')
        )

    @staticmethod
    def process_response(response):
        if response.ok:
            return response.json()
        try:
            return response.json()
        except ValueError:
            # no json object could be decoded
            return response.content

    @staticmethod
    def action_not_supported(action):
        """
        Returns a not supported error
        :param action: str
        :return: dict
        """
        return {
            'error': {
                'code': 500,
                'message':
                    '{action} is not supported at this time'.format(action=action)
            }
        }

    def get(self, obj_id):
        """
        Get a single item

        :param obj_id: int
        :return: dict|str
        """
        response = self._client.session.get(
            '{url}/{id}'.format(
                url=self.endpoint_url, id=obj_id
            )
        )
        return self.process_response(response)

    def get_list(
            self,
            search='',
            start=0,
            limit=0,
            order_by='',
            order_by_dir='ASC',
            published_only=False,
            minimal=False
    ):
        """
        Get a list of items

        :param search: str
        :param start: int
        :param limit: int
        :param order_by: str
        :param order_by_dir: str
        :param published_only: bool
        :param minimal: bool
        :return: dict|str
        """

        parameters = {}
        args = ['search', 'start', 'limit', 'minimal']
        for arg in args:
            if arg in locals() and locals()[arg]:
                parameters[arg] = locals()[arg]
        if order_by:
            parameters['orderBy'] = order_by
        if order_by_dir:
            parameters['orderByDir'] = order_by_dir
        if published_only:
            parameters['publishedOnly'] = 'true'
        response = self._client.session.get(
            self.endpoint_url, params=parameters
        )
        return self.process_response(response)

    def get_published_list(
            self, search='', start=0, limit=0, order_by='', order_by_dir='ASC'
    ):
        """
        Proxy function to get_list with published_only set to True
        :param search: str
        :param start: int
        :param limit: int
        :param order_by: str
        :param order_by_dir: str
        :return: dict|str
        """
        return self.get_list(
            search=search,
            start=start,
            limit=limit,
            order_by=order_by,
            order_by_dir=order_by_dir,
            published_only=True
        )

    def create(self, parameters):
        """
        Create a new item (if supported)

        :param parameters: dict
        :return: dict|str
        """
        response = self._client.session.post(
            '{url}/new'.format(url=self.endpoint_url), data=parameters
        )
        return self.process_response(response)

    def edit(self, obj_id, parameters, create_if_not_exists=False):
        """
        Edit an item with option to create if it doesn't exist

        :param obj_id: int
        :param create_if_not_exists: bool
        :param parameters: dict
        :return: dict|str
        """
        if create_if_not_exists:
            response = self._client.session.put(
                '{url}/{id}/edit'.format(
                    url=self.endpoint_url, id=obj_id
                ),
                data=parameters
            )
        else:
            response = self._client.session.patch(
                '{url}/{id}/edit'.format(
                    url=self.endpoint_url, id=obj_id
                ),
                data=parameters
            )
        return self.process_response(response)

    def delete(self, obj_id):
        """
        Delete an item

        :param obj_id: int
        :return: dict|str
        """
        response = self._client.session.delete(
            '{url}/{id}/delete'.format(
                url=self.endpoint_url, id=obj_id
            )
        )
        return self.process_response(response)

    def submit_form_data(self, form_id, data, utm_source=None):
        params = {
            "formId": form_id,
        }
        if utm_source:
            params.update({"utm_source": utm_source})

        res = self._client.session.post(f"{self._client.base_url}/form/submit", params=params, data=data)

        res.raise_for_status()

        parser = MauticFormResponseParser()
        parser.feed(res.text)
        message = parser.well_div_data

        if message.startswith("Errors") or message.startswith("This form is no longer available"):
            return False

        return True
