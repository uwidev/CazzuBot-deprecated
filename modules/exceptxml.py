'''Holds all custom exceptions'''

class BadConfigs(Exception):
    def __init__(self, message):
        self.message = message
