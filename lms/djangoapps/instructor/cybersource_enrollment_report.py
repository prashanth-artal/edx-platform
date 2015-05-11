"""
Defines concrete class for cybersource  Enrollment Report.

"""
from courseware.access import has_access
from django.utils.translation import ugettext as _
from courseware.courses import get_course_by_id
from instructor.enrollment_report import BaseEnrollmentReportProvider
from shoppingcart.models import RegistrationCodeRedemption, PaidCourseRegistration, CouponRedemption, OrderItem
from student.models import CourseEnrollment


class CyberSourceEnrollmentReportProvider(BaseEnrollmentReportProvider):
    """
    The concrete class for all CyberSource Enrollment Reports.
    """

    def get_enrollment_info(self, user, course_id):
        """
        Returns the User Enrollment information.
        """
        course = get_course_by_id(course_id, depth=0)
        is_course_staff = has_access(user, 'staff', course)

        # check the user enrollment role
        if user.is_staff:
            enrollment_role = _('Edx Staff')
        elif is_course_staff:
            enrollment_role = _('Course Staff')
        else:
            enrollment_role = _('Student')

        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)

        if is_course_staff:
            enrollment_source = _('Staff')
        else:
            # get the registration_code_redemption object if exists
            registration_code_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(
                course_enrollment)
            # get the paid_course registration item if exists
            paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
                user=user,
                course_id=course_id,
                course_enrollment=course_enrollment
            )

            # from where the user get here
            if registration_code_redemption is not None:
                enrollment_source = _('Used Registration Code')
            elif paid_course_reg_item is not None:
                enrollment_source = _('Credit Card - Individual')
            else:
                enrollment_source = _('Manually Enrolled')

        enrollment_date = getattr(course_enrollment, 'created').strftime("%B %d, %Y")
        currently_enrolled = getattr(course_enrollment, 'is_active')

        course_enrollment_data = [enrollment_date, currently_enrolled, enrollment_source, enrollment_role]
        return course_enrollment_data

    def get_payment_info(self, user, course_id):
        """
        Returns the User Payment information.
        """
        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)
        paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
            user=user,
            course_id=course_id,
            course_enrollment=course_enrollment
        )
        # check if the user made a single self purchase scenario
        # for enrollment in the course.
        if paid_course_reg_item is not None:
            coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(
                order_id=paid_course_reg_item.order_id)
            coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
            coupon_codes = ", ".join(coupon_codes)
            payment_data = [
                paid_course_reg_item.unit_cost, paid_course_reg_item.line_cost, coupon_codes,
                paid_course_reg_item.status, paid_course_reg_item.order_id
            ]
        else:
            # check if the user used a registration code for the enrollment.
            registration_code_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(
                course_enrollment)
            if registration_code_redemption is not None:
                registration_code = registration_code_redemption.registration_code
                if getattr(registration_code, 'invoice_item_id'):
                    list_price = getattr(registration_code.invoice_item, 'unit_price')
                    total_amount = registration_code_redemption.registration_code.invoice.total_amount
                    qty = registration_code_redemption.registration_code.invoice_item.qty
                    payment_amount = total_amount / qty
                    is_valid = registration_code_redemption.registration_code.invoice.is_valid
                    transaction_reference_number = registration_code_redemption.registration_code.invoice_id
                    if is_valid:
                        status = _('Invoice Paid')
                    else:
                        status = _('Invoice Outstanding')

                    payment_data = [list_price, payment_amount, 'N/A', status, transaction_reference_number]
                elif getattr(registration_code_redemption.registration_code, 'order_id'):
                    order_item = OrderItem.objects.get(order=registration_code_redemption.registration_code.order,
                                                       courseregcodeitem__course_id=course_id)

                    coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(
                        order_id=registration_code_redemption.registration_code.order)
                    coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
                    coupon_codes = ", ".join(coupon_codes)
                    payment_data = [
                        order_item.list_price, order_item.unit_cost, coupon_codes,
                        order_item.status, order_item.order_id
                    ]
                else:
                    # this happens when the registration code is not created via invoice or bulk purchase
                    # scenario.
                    payment_data = [
                        'N/A', 'N/A', 'N/A', _('Data Integrity Error'), 'N/A'
                    ]
            else:
                # this happens when the user is manually enrolled and
                # further checks if the user is active or not.
                if course_enrollment.is_active:
                    payment_status = _('Manual Entry')
                else:
                    payment_status = _('Refunded')
                payment_data = [
                    'N/A', 'N/A', 'N/A', payment_status, 'N/A'
                ]
        return payment_data
