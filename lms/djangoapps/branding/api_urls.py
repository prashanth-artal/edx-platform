"""
Branding API endpoint urls.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^footer/$',
        'branding.api.get_footer', name="get_footer"),
)