
from mailchimp3 import MailChimp
from mailchimp3.helpers import get_subscriber_hash
from mailchimp3.mailchimpclient import MailChimpError

from plone import api

from collective.mailchimp import logger
from collective.mailchimp.exceptions import MailChimpException
from collective.mailchimp.interfaces import IMailchimpLocator
from collective.mailchimp.interfaces import IMailchimpSettings


def get_mailchimp():
    api_key = api.portal.get_registry_record(
        "api_key",
        interface=IMailchimpSettings)
    if not api_key:
        logger.warning("No MailChimp API Key provided")
        return None
    return MailChimp(mc_api=api_key)


def get_mailchimp_lists(id_is_key=True):
    client = get_mailchimp()
    if not client:
        return {}
    mc_lists = client.lists.all(get_all=True, fields="lists.name,lists.id")
    try:
        if id_is_key:
            return { ls['id']:ls['name'] for ls in mc_lists['lists'] }
        return { ls['name']:ls['id'] for ls in mc_lists['lists'] }
    except:
        return {}


def add_subscriber(list_id, email, first_name, last_name, **merge_fields):
    client = get_mailchimp()
    if not client:
        return {}
    merge_fields["FNAME"] = first_name
    merge_fields["LNAME"] = last_name
    try:
        client.lists.members.create(list_id, {
            'email_address': email,
            'status': 'subscribed',
            'merge_fields': merge_fields,
        })
    except MailChimpError as e:
        logger.error(e)


def remove_subscriber(list_id, email):
    client = get_mailchimp()
    if not client:
        return
    email_hash = get_subscriber_hash(email)
    try:
        client.lists.members.delete(list_id=list_id, subscriber_hash=email_hash)
    except MailChimpError as e:
        logger.error(e)


def create_mailchimp_list(
        name,
        message=None,
        contact=None,
        campaign_defaults=None,
        **data
    ):
    """Create a new list in your Mailchimp account.
    
    See https://developer.mailchimp.com/documentation/mailchimp/reference/lists/#create-post_lists
    for more details.
    
    :params:
        name: List name
        contact: List Contact. A dictionary consisting of company, address, city, state, zip and country
        permission_reminder: Permission reminder.
        campaign_defaults: Campaign Defaults.  A dictionary consisting of from_name, from_email, subject and language.
    """
    client = get_mailchimp()
    if not client:
        return {}
    from_address = api.portal.get_registry_record('plone.email_from_address')
    from_name = api.portal.get_registry_record('plone.email_from_name')
    site_title = api.portal.get_registry_record('plone.site_title')
    
    if not message:
        message = ("You are receiving this email because you signed up "
                   "for updates about {}".format(name))
    if not contact:
        contact = {
            "company": site_title,
            "address1":"675 Ponce De Leon Ave NE",
            "city":"Atlanta",
            "state":"GA",
            "zip":"30308",
            "country":"US",
        }
    if not campaign_defaults:
        campaign_defaults = {
            "from_name": from_name,
            "from_email": from_address,
            "subject": "",
            "language": "en"
        }
    data['name'] = name
    data['permission_reminder'] = message
    data["email_type_option"] = True
    data["campaign_defaults"] = campaign_defaults
    data["contact"] = contact
    
    return client.lists.create(data=data)