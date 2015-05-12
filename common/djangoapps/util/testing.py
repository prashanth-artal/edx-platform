import sys

from datetime import datetime
from pytz import UTC
from mock import patch

from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.partitions.partitions import UserPartition, Group
from student.tests.factories import CourseEnrollmentFactory, UserFactory


class UrlResetMixin(object):
    """Mixin to reset urls.py before and after a test

    Django memoizes the function that reads the urls module (whatever module
    urlconf names). The module itself is also stored by python in sys.modules.
    To fully reload it, we need to reload the python module, and also clear django's
    cache of the parsed urls.

    However, the order in which we do this doesn't matter, because neither one will
    get reloaded until the next request

    Doing this is expensive, so it should only be added to tests that modify settings
    that affect the contents of urls.py
    """

    def _reset_urls(self, urlconf_modules):
        """Reset `urls.py` for a set of Django apps."""
        for urlconf in urlconf_modules:
            if urlconf in sys.modules:
                reload(sys.modules[urlconf])
        clear_url_caches()

        # Resolve a URL so that the new urlconf gets loaded
        resolve('/')

    def setUp(self, *args, **kwargs):
        """Reset Django urls before tests and after tests

        If you need to reset `urls.py` from a particular Django app (or apps),
        specify these modules in *args.

        Examples:

            # Reload only the root urls.py
            super(MyTestCase, self).setUp()

            # Reload urls from my_app
            super(MyTestCase, self).setUp("my_app.urls")

            # Reload urls from my_app and another_app
            super(MyTestCase, self).setUp("my_app.urls", "another_app.urls")

        """
        super(UrlResetMixin, self).setUp(**kwargs)

        urlconf_modules = [settings.ROOT_URLCONF]
        if args:
            urlconf_modules.extend(args)

        self._reset_urls(urlconf_modules)
        self.addCleanup(lambda: self._reset_urls(urlconf_modules))


class EventTestMixin(object):
    """
    Generic mixin for verifying that events were emitted during a test.
    """
    def setUp(self, tracker):
        super(EventTestMixin, self).setUp()
        self.tracker = tracker
        patcher = patch(self.tracker)
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_no_events_were_emitted(self):
        """
        Ensures no events were emitted since the last event related assertion.
        """
        self.assertFalse(self.mock_tracker.emit.called)  # pylint: disable=maybe-no-member

    def assert_event_emitted(self, event_name, **kwargs):
        """
        Verify that an event was emitted with the given parameters.
        """
        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            event_name,
            kwargs
        )

    def reset_tracker(self):
        """
        Reset the mock tracker in order to forget about old events.
        """
        self.mock_tracker.reset_mock()


class ContentGroupTestCase(ModuleStoreTestCase):
    """
    Sets up discussion modules visible to content groups 'Alpha' and
    'Beta', as well as a module visible to all students.  Creates a
    staff user, users with access to Alpha/Beta (by way of cohorts),
    and a non-cohorted user with no special access.
    """
    def setUp(self):
        super(ContentGroupTestCase, self).setUp()

        self.course = CourseFactory.create(
            org='org', number='number', run='run',
            # This test needs to use a course that has already started --
            # discussion topics only show up if the course has already started,
            # and the default start date for courses is Jan 1, 2030.
            start=datetime(2012, 2, 3, tzinfo=UTC),
            user_partitions=[
                UserPartition(
                    0,
                    'Content Group Configuration',
                    '',
                    [Group(1, 'Alpha'), Group(2, 'Beta')],
                    scheme_id='cohort'
                )
            ],
            grading_policy={
                "GRADER": [{
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "HW",
                    "weight": 1.0
                }]
            },
            cohort_config={'cohorted': True},
            discussion_topics={}
        )

        self.staff_user = UserFactory.create(is_staff=True)
        self.alpha_user = UserFactory.create()
        self.beta_user = UserFactory.create()
        self.non_cohorted_user = UserFactory.create()
        for user in [self.staff_user, self.alpha_user, self.beta_user, self.non_cohorted_user]:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        alpha_cohort = CohortFactory(
            course_id=self.course.id,
            name='Cohort Alpha',
            users=[self.alpha_user]
        )
        beta_cohort = CohortFactory(
            course_id=self.course.id,
            name='Cohort Beta',
            users=[self.beta_user]
        )
        CourseUserGroupPartitionGroup.objects.create(
            course_user_group=alpha_cohort,
            partition_id=self.course.user_partitions[0].id,
            group_id=self.course.user_partitions[0].groups[0].id
        )
        CourseUserGroupPartitionGroup.objects.create(
            course_user_group=beta_cohort,
            partition_id=self.course.user_partitions[0].id,
            group_id=self.course.user_partitions[0].groups[1].id
        )
        self.alpha_module = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='alpha_group_discussion',
            discussion_target='Visible to Alpha',
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[0].id]}
        )
        self.beta_module = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='beta_group_discussion',
            discussion_target='Visible to Beta',
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[1].id]}
        )
        self.global_module = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='global_group_discussion',
            discussion_target='Visible to Everyone'
        )
        self.course = self.store.get_item(self.course.location)
