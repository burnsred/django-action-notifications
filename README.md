# django-action-notifications

This is a Django module designed to work with [Django Activity Stream](https://github.com/justquick/django-activity-stream) to allow for notifications. It has the following features:

- Tracking of whether notifications have been read by the user;
- A REST API for listing notifications (with filters), and for marking notifications read;
- Emails about notifications, including:
    - Customising content of the emails based on the properties of the activity;
    - Specifying how frequently to email about the activity.

Install requires

- `Django >= 1.6, < 1.9`
- `django-activity-stream >= 0.6.0`
- `djangorestframework >= 3.1.1`
- `django-filter >= 0.9.2`
- `django-kronos >= 0.6`