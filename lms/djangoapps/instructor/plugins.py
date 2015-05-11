"""
Registers the Instructor tab feature for the edX platform.
"""

from django.utils.translation import ugettext as _

from courseware.access import has_access


class InstructorViewType(object):
    """
    The representation of the Instructor view type.
    """

    name = "instructor"
    title = _('Instructor')
    view_name = "instructor_dashboard"
    is_persistent = False

    @classmethod
    def is_enabled(cls, course, settings, user=None):  # pylint: disable=unused-argument
        """
        Returns true if the specified user has staff access.
        """
        return user and has_access(user, 'staff', course, course.id)
