from django.core import exceptions


class PricePolicyDoesNotExist(Exception):
    """The requested object does not exist"""
    pass
