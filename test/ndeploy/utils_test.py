import os
import unittest

from ndeploy.utils import create_temp_directory, rmtree


class UtilsTest(unittest.TestCase):

    def test_should_be_possible_to_create_and_remove_a_temporary_directory(self):
        temp_dir = create_temp_directory()
        self.assertTrue(os.path.isdir(temp_dir))
        rmtree(temp_dir)
        self.assertFalse(os.path.isdir(temp_dir))