"""Edx footer API

"""
from django.http import HttpResponse
import logging

log = logging.getLogger("edx.footer")


def get_footer(request):

    return HttpResponse('ok')