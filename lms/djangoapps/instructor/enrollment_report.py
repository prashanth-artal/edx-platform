"""
Defines abstract class for the Enrollment Reports.
"""
from instructor.enrollment_report_provider import EnrollmentReportProvider
from django.contrib.auth.models import User


class BaseEnrollmentReportProvider(EnrollmentReportProvider):
    """
    The base abstract class for all Enrollment Reports that can support multiple
    backend such as MySQL/Django-ORM.

    # don't allow instantiation of this class, it must be subclassed
    """
    def get_user_profile(self, user_id, user_info_attributes, user_profile_attributes):
        """
        Returns the UserProfile information.
        """
        user_info = User.objects.select_related('profile').get(id=user_id)
        user_info_data = [getattr(user_info, x[0]) for x in user_info_attributes]
        user_profile_data = [getattr(user_info.profile, x[0]) for x in user_profile_attributes]
        return user_info_data + user_profile_data

    def get_enrollment_info(self, user, course_id, course_enrollment_attributes):
        """
        Returns the User Enrollment information.
        """
        raise NotImplementedError()

    def get_payment_info(self, user_id, course_id):
        """
        Returns the User Payment information.
        """
        raise NotImplementedError()
