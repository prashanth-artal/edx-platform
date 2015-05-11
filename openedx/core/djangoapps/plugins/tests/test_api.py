"""
Tests for the features API
"""

from django.test import TestCase

from ..api import CourseViewTypeManager, FeatureManager, PluginError


class TestFeaturesApi(TestCase):
    """
    Unit tests for the features API
    """

    def test_get_feature(self):
        """
        Verify the behavior of get_feature.
        """
        feature = FeatureManager.get_plugin("instructor")
        self.assertEqual(feature.title, "Instructor Tab")

        with self.assertRaises(PluginError):
            FeatureManager.get_plugin("no_such_feature")

    def test_get_course_view_type(self):
        """
        Verify the behavior of get_feature.
        """
        course_view_type = CourseViewTypeManager.get_plugin("instructor")
        self.assertEqual(course_view_type.title, "Instructor")

        with self.assertRaises(PluginError):
            CourseViewTypeManager.get_plugin("no_such_type")
