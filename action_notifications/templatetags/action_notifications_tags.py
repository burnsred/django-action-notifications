from django.template import Library

from action_notifications import messages

register = Library()

register.simple_tag(messages.get_message, name='notification_message')
