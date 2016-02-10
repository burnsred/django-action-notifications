try:
    from django.apps import apps

    def get_model(app_label, model_name):
        return apps.get_registered_model(app_label, model_name)
except ImportError:
    from django.db.models.loading import get_model

from django.contrib.auth.models import User
from django.utils import six

handlers = []

def register_message_handler(handler, **kwargs):
    handlers.insert(0, (
        kwargs,
        handler,
    ))

def message_handler(**kwargs):
    def wrap(handler):
        register_message_handler(handler, **kwargs)
        return handler
    return wrap

def get_message(action, *args, **kwargs):
    '''Finds a handler to match the message. Handlers are evaluated in the
    reverse order to which they were registered in, and the first handler to
    satisfy all conditions will be used. The default handler is just the
    default message provided by actstream'''
    for conditions, handler in handlers:
        all_satisfied = True

        for condition, value in conditions.iteritems():
            if condition.endswith('_type'):
                if isinstance(value, six.string_types):
                    try:
                        app_label, model_name = value.split('.')
                    except ValueError:
                        raise ValueError(
                            'Specified type must either be a type or a '
                            'model name of the \'app_label.ModelName\' form.'
                        )

                    value = get_model(app_label, model_name)
                is_satisfied = isinstance(getattr(action, condition[0:-5]), value)
            else:
                is_satisfied = getattr(action, condition) == value

            all_satisfied = all_satisfied and is_satisfied

        if all_satisfied:
            return handler(action, *args, **kwargs)

@message_handler()
def default_handler(action, **_):
    return action.__unicode__()

@message_handler(actor_type=User)
def user_actor_handler(action, **_):
    context = {
        'actor_name': '{} {}'.format(action.actor.first_name, action.actor.last_name),
        'verb': action.verb,
        'action_object': action.action_object,
        'target': action.target,
        'timesince': action.timesince()
    }
    if action.target:
        if action.action_object:
            return '%(actor_name)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago' % context
        return '%(actor_name)s %(verb)s %(target)s %(timesince)s ago' % context
    if action.action_object:
        return '%(actor_name)s %(verb)s %(action_object)s %(timesince)s ago' % context
    return '%(actor_name)s %(verb)s %(timesince)s ago' % context
