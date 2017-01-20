import os
import unittest

from ndeploy.utils import get_temp_dir_app_if_exists, create_temp_directory, rmtree


class UtilsTest(unittest.TestCase):

    def test_should_be_possible_to_create_and_remove_a_temporary_directory(self):
        temp_dir = self._create_and_validate_temp_directory()
        rmtree(temp_dir)
        self.assertFalse(os.path.isdir(temp_dir))

    def test_should_be_possible_to_get_a_temporary_directory(self):
        app_name = "appteste-"
        self._create_and_validate_temp_directory(app_name)

        app_temp_dir = get_temp_dir_app_if_exists(app_name)
        self.assertIsNotNone(app_temp_dir)

        rmtree(app_temp_dir)
        self.assertFalse(os.path.isdir(app_temp_dir))

    def test_when_the_temporary_dir_does_not_exist_it_should_return_none(self):
        app_name = "appteste-"
        app_temp_dir = get_temp_dir_app_if_exists(app_name)
        self.assertIsNone(app_temp_dir)

    # Helpers

    def _create_and_validate_temp_directory(self, prefix="app_teste-"):
        temp_dir = create_temp_directory(prefix=prefix)
        self.assertTrue(os.path.isdir(temp_dir))
        return temp_dir
