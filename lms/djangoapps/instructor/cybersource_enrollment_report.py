"""
Defines concrete class for cybersource  Enrollment Report.

"""
from courseware.access import has_access
from courseware.courses import get_course_by_id
from instructor.enrollment_report import BaseEnrollmentReportProvider
from shoppingcart.models import RegistrationCodeRedemption, PaidCourseRegistration, CouponRedemption
from student.models import CourseEnrollment
from student.roles import CourseStaffRole


class CyberSourceEnrollmentReportProvider(BaseEnrollmentReportProvider):
    """
    The concrete class for all CyberSource Enrollment Reports.
    """

    def get_enrollment_info(self, user, course_id, course_enrollment_attributes):
        """
        Returns the User Enrollment information.
        """
        is_registration_code_redeemed = False
        is_paid_course_item = False
        course = get_course_by_id(course_id, depth=0)
        is_course_staff = has_access(user, 'staff', course)

        # check the user enrollment role
        if user.is_staff:
            enrollment_role = 'Edx Staff'
        elif is_course_staff:
            enrollment_role = 'Course Staff'
        else:
            enrollment_role = 'Student'

        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)

        if not is_course_staff:
            # check if the registration code used for course enrollment
            is_registration_code_redeemed = RegistrationCodeRedemption.is_registration_code_user_for_enrollment(
                course_enrollment)
            # check if the user payed for the course enrollment
            paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
                user=user,
                course_id=course_id,
                course_enrollment=course_enrollment
            )

        # from where the user get here
        if is_course_staff:
            enrollment_source = 'Staff'
        elif is_registration_code_redeemed:
            enrollment_source = 'Used Registration Code'
        elif paid_course_reg_item.exists():
            enrollment_source = 'Credit Card - Individual'
        else:
            enrollment_source = 'Manually Enrolled'

        course_enrollment_data = [
            getattr(course_enrollment, x[0]).strftime("%B %d, %Y") if 'created' in x[0] else getattr(
                course_enrollment, x[0]) for x in course_enrollment_attributes]
        course_enrollment_data.extend([enrollment_source, enrollment_role])
        return course_enrollment_data

    def get_payment_info(self, user, course_id):
        """
        Returns the User Payment information.
        """
        coupon_codes = ''
        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)
        paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
            user=user,
            course_id=course_id,
            course_enrollment=course_enrollment
        )
        if paid_course_reg_item is not None:
            coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(order_id=paid_course_reg_item.order_id)

        if coupon_redemption.exists():
            coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
            coupon_codes = ", ".join(coupon_codes)
        payment_data = [
            paid_course_reg_item.unit_cost, total_amount, coupon_codes,
            paid_course_reg_item.status, paid_course_reg_item.order_id
        ]
        return payment_data