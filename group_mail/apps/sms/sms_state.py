from Messages import *


class IntroState:
    next_state = None

    def parse_user_msg(self, msg):
        # get the user's email
        email = msg

        # create a new user

        # create response
        return Messages.ask_for_email


class GetEmailState:


    map[ (lambda error_list: len(error_list) == 0, "GetNameState"),

    next_state = None

    def parse_user_msg(self, msg):
        # get the user's email
        email = msg

        # create a new user

        # create response
        return Messages.ask_for_name


class GetNameState:
    next_state = None

    def parse_user_msg(self, msg):
        # get the user's name
        name = msg

        # create a new user

        # create
        return Messages.ask_for_name
