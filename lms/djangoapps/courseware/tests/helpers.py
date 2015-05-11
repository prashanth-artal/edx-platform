import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module

from student.models import Registration

from util.milestones_helpers import (
    add_milestone,
    add_course_milestone,
    get_namespace_choices,
    generate_milestone_namespace,
    add_course_content_milestone,
    get_milestone_relationship_types,
)


def get_request_for_user(user):
    """Create a request object for user."""
    request = RequestFactory()
    request.user = user
    request.COOKIES = {}
    request.META = {}
    request.is_secure = lambda: True
    request.get_host = lambda: "edx.org"
    request.method = 'GET'
    return request


def answer_entrance_exam_problem(course, request, problem, user=None):
    """
    Takes a required milestone `problem` in a `course` and fulfills it.

    Args:
        course (Course): Course object, the course the required problem is in
        request (Request): request Object
        problem (xblock): xblock object, the problem to be fulfilled
        user (User): User object in case it is different from request.user
    """
    if not user:
        user = request.user

    # pylint: disable=maybe-no-member,no-member
    grade_dict = {'value': 1, 'max_value': 1, 'user_id': user.id}
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id,
        user,
        course,
        depth=2
    )
    # pylint: disable=protected-access
    module = get_module(
        user,
        request,
        problem.scope_ids.usage_id,
        field_data_cache,
    )._xmodule
    module.system.publish(problem, 'grade', grade_dict)


def add_entrance_exam_milestone(course, entrance_exam):
    """
    Adds the milestone for given `entrance_exam` in `course`

    Args:
        course (Course): Course object in which the extrance_exam is located
        entrance_exam (xblock): xblock object, the entrance exam to be added as a milestone
    """
    namespace_choices = get_namespace_choices()
    milestone_relationship_types = get_milestone_relationship_types()

    milestone_namespace = generate_milestone_namespace(
        namespace_choices.get('ENTRANCE_EXAM'),
        course.id
    )
    milestone = add_milestone(
        {
            'name': 'Test Milestone',
            'namespace': milestone_namespace,
            'description': 'Testing Courseware Entrance Exam Chapter',
        }
    )
    add_course_milestone(
        unicode(course.id),
        milestone_relationship_types['REQUIRES'],
        milestone
    )
    add_course_content_milestone(
        unicode(course.id),
        unicode(entrance_exam.location),
        milestone_relationship_types['FULFILLS'],
        milestone
    )


class LoginEnrollmentTestCase(TestCase):
    """
    Provides support for user creation,
    activation, login, and course enrollment.
    """
    user = None

    def setup_user(self):
        """
        Create a user account, activate, and log in.
        """
        self.email = 'foo@test.com'
        self.password = 'bar'
        self.username = 'test'
        self.user = self.create_account(
            self.username,
            self.email,
            self.password,
        )
        self.activate_user(self.email)
        self.login(self.email, self.password)

    def assert_request_status_code(self, status_code, url, method="GET", **kwargs):
        make_request = getattr(self.client, method.lower())
        response = make_request(url, **kwargs)
        self.assertEqual(
            response.status_code, status_code,
            "{method} request to {url} returned status code {actual}, "
            "expected status code {expected}".format(
                method=method, url=url,
                actual=response.status_code, expected=status_code
            )
        )
        return response

    # ============ User creation and login ==============

    def login(self, email, password):
        """
        Login, check that the corresponding view's response has a 200 status code.
        """
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])

    def logout(self):
        """
        Logout; check that the HTTP response code indicates redirection
        as expected.
        """
        # should redirect
        self.assert_request_status_code(302, reverse('logout'))

    def create_account(self, username, email, password):
        """
        Create the account and check that it worked.
        """
        url = reverse('create_account')
        request_data = {
            'username': username,
            'email': email,
            'password': password,
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }
        resp = self.assert_request_status_code(200, url, method="POST", data=request_data)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], True)
        # Check both that the user is created, and inactive
        user = User.objects.get(email=email)
        self.assertFalse(user.is_active)
        return user

    def activate_user(self, email):
        """
        Look up the activation key for the user, then hit the activate view.
        No error checking.
        """
        activation_key = Registration.objects.get(user__email=email).activation_key
        # and now we try to activate
        url = reverse('activate', kwargs={'key': activation_key})
        self.assert_request_status_code(200, url)
        # Now make sure that the user is now actually activated
        self.assertTrue(User.objects.get(email=email).is_active)

    def enroll(self, course, verify=False):
        """
        Try to enroll and return boolean indicating result.
        `course` is an instance of CourseDescriptor.
        `verify` is an optional boolean parameter specifying whether we
        want to verify that the student was successfully enrolled
        in the course.
        """
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': course.id.to_deprecated_string(),
            'check_access': True,
        })
        result = resp.status_code == 200
        if verify:
            self.assertTrue(result)
        return result

    def unenroll(self, course):
        """
        Unenroll the currently logged-in user, and check that it worked.
        `course` is an instance of CourseDescriptor.
        """
        url = reverse('change_enrollment')
        request_data = {
            'enrollment_action': 'unenroll',
            'course_id': course.id.to_deprecated_string(),
        }
        self.assert_request_status_code(200, url, method="POST", data=request_data)
