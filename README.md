# Wagtail Mautic
Integration of [Mautic](https://github.com/mautic/mautic) forms in Wagtail Projects.

# Background

We needed to allow our users to subscribe to a mailing list directly from a form rendered on a Wagtail Page.

Mautic is an open-source alternative to Mailchimp and fitted our needs. 

The aim of this package is to render a given Mautic Form on a Wagtail page, and send the submitted data to Mautic.
Other Mautic functionalities might be added later as need arises.


# Installation
Install using pip - Not yet Published

```
pip install  
```

Add `wagtailmautic` to your installed apps

```
 INSTALLED_APPS = [
        ...
        "wagtailmautic",
        ...
        ]
```


Run migrations
```
python manage.py migrate
```

# Settings

`NOTE`: This instructions assume you have knowledge of setting up Wagtail and configuring Mautic, as we don't cover the specifics.

Mautic Settings will be added to the Wagtail Admin Menu as below

![Navigation in Wagtail admin](screenshots/locate_mautic_settings.png)

Add in the URL for your Mautic instance (including the https://) to the Mautic Url field.

![Set Mautic Base Url](screenshots/base_url.png)

You can use two methods for authentication:

- OAuth2 that requires client id and client secret from Mautic
- Basic Authentication that needs username and password. To use Basic Auth, you must enable this on Mautic Configuration

OAth2
![OAuth2](screenshots/oauth.png)

Basic 

![Basic](screenshots/basic.png)


# Usage

THe package provides an abstract wagtail page that uses a custom view to serve the Mautic Form.

Below is a sample snippet on how you can use it on your wagtail page that you want to serve the form.

Let us say you have a subscribe page, that should show a Mautic Form that your users can fill to subscribe to your mailing list

in your app's `models.py`:
```
from wagtail.models import Page

from wagtailmautic.models import BaseMauticFormPage


class MailingListSubscribePage(BaseMauticFormPage, Page):
    pass
```


Create the Page as you usual in your CMS admin.

Edit the Page to add the Mautic Form ID

![Form Page](screenshots/form_page.png)

Add the form in your page's template

```
    <form method="POST">
        {% csrf_token %}
        {{ form }}
        <div class="field">
            <button type="submit" class="button submit-button has-no-border">Submit</button>
        </div>
    </form>

```
The rendered page should now include a form with matching fields as setup on your Mautic form.

Submitting will send the form data to Mautic and show the thank message that was set

You may want to override the default provided `form_thank_you_landing.html` template at `wagtailmautic/form_thank_you_landing.html`

- First, create a templates directory in your project's root directory if it does not exist already.

- Inside the templates directory, create a directory with the name `wagtailmautic` whose template we want to override. 

- Inside the `wagtailmautic` directory, create a file with the same name as the template we want to override. In this case, create a file named `form_thank_you_landing.html`.

- Edit the new `form_thank_you_landing.html` template as desired.

