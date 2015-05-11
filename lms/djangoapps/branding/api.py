"""Edx footer API

"""
from django.http import HttpResponse
import logging
from util.json_request import JsonResponse

log = logging.getLogger("edx.footer")


def get_footer(request):

    context = {}

    context["logo_img"] = "/sites/all/themes/atedx/images/edx-logo-footer.png"
    context["social_links"] = social_links()
    context["about_links"] = about_edx_link()

    return JsonResponse({"footer": context}, 200)


def social_links():

    return [
        {
            "provider": "facebook",
            "title": "Facebook",
            "url": "http://www.facebook.com/EdxOnline"
        },
        {
            "provider": "twitter",
            "title": "Twitter",
            "url": "https://twitter.com/edXOnline"
        },
        {
            "provider": "linkedin",
            "title": "LinkedIn",
            "url": "http://www.linkedin.com/company/edx"
        },
        {
            "provider": "google",
            "title": "Google+",
            "url": "https://plus.google.com/+edXOnline"
        },
        {
            "provider": "tumblr",
            "title": "Tumblr",
            "url": "http://edxstories.tumblr.com/"
        },
        {
            "provider": "meetup",
            "title": "Meetup",
            "url": "http://www.meetup.com/edX-Global-Community"
        },
        {
            "provider": "reddit",
            "title": "Reddit",
            "url": "http://www.reddit.com/r/edx"
        },
        {
            "provider": "youtube",
            "title": "Youtube",
            "url": "https://www.youtube.com/user/edxonline?sub_confirmation=1"
        },
    ]

def about_edx_link():

    return [
        {
            "title":"About",
            "url": "/about-us"
        },
        {
            "title":"News & Announcements",
            "url": "/news-announcements"
        },
        {
            "title":"Contact",
            "url": "/contact-us"
        },
        {
            "title":"FAQs",
            "url": "/about/student-faq"
        },
        {
            "title":"edX Blog",
            "url": "/edx-blog"
        },
        {
            "title":"Donate to edX",
            "url": "/donate"
        },
        {
            "title":"Jobs at edX",
            "url": "/jobs"
        },
        {
            "title":"Site Map",
            "url": "/sitemap"
        },
    ]

def footer_heading():
    return ""