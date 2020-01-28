class UserPreferenceMixin:
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
