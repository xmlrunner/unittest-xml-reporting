import allure_commons
from allure_commons import plugin_manager
from allure_commons.logger import AllureFileLogger

from q2_atf.lib.allure_report.listener import AllureListener
# Utils function
import os
from q2_atf.lib.allure_report.utils import get_suit_name, get_domain_name


class AllureHook:

    def __init__(self):
        self.file_logger = None
        self.listener = AllureListener()

    def register_allure_plugins(self, test_runner):
        dir_name = os.path.join("test-reports", "allure-results", get_domain_name(test_runner),
                                get_suit_name(test_runner))
        self.file_logger = AllureFileLogger(dir_name, clean=True)
        plugin_manager.register(self.listener)
        plugin_manager.register(self.file_logger)

    def unregister_allure_plugins(self):
        plugin_manager.unregister(plugin=self.listener)
        plugin_manager.unregister(plugin=self.file_logger)
