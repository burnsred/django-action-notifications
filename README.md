# django-action-notifications

This is a Django module designed to work with [Django Activity Stream](https://github.com/justquick/django-activity-stream) to allow for notifications. It has the following features:

- Tracking of whether notifications have been read by the user;
- A REST API for listing notifications (with filters), and for marking notifications read;
- Emails about notifications, including:
    - Customising content of the emails based on the properties of the activity;
    - Specifying how frequently to email about the activity.
    - Allowing users to specify personal preference regarding grouping of notification and delivery schedule
    
#### Settings
- ``ACTION_NOTIFICATION_USER_PREFERENCES``: Boolean - Registers cron task to process emails with user preferences
- ``ACTION_NOTIFICATION_USER_PREFERENCE_FIELD_NAME``: String - Specifies the field name to reference on the User Model.
 This fields should an object that extends the class ``UserPreferenceMixin`` in the mixins module of this library.
- ```ACTION_NOTIFICATION_USER_PREFERENCE_CRON_INTERVAL```: String - Needs to be in Cron Format and sets the frequency of
task that processes user preference notifications.

#### UserPreferenceMixin
```python
class UserPreferenceMixin(object):
    def get_preference_for_action_verb(self, verb, action=None):
        """
        Abstract method called in the default Action created listener, used to create notifications based on a
        User's personal preference for a particular Activity. Classes using this mixin must provide an 
        implementation of this method 
        
        :param verb: Action verb that is being processed
        :param action: Action currently being processed, in case more complex schedules need to be constructed by child
        classes, the Action object is available to the preference object example: constructing a localized time based on
        when the action was created
        :return: A tuple that will be mapped to the ActionNotification.do_not_send_before, 
        ActionNotification.is_should_email_separately in that order
        """
        raise NotImplementedError(
            'Classes using this mixin need to implement this method, it should return a tuple of preferences'
            'example: (datetime, boolean) that will bind to ActionNotification.do_not_send_before, '
            'ActionNotification.is_should_email_separately'
        )
```
Install requires

- `Django >= 1.6, < 1.9`
- `django-activity-stream >= 0.6.0`
- `djangorestframework >= 3.1.1`
- `django-filter >= 0.9.2`
- `django-kronos >= 0.6`