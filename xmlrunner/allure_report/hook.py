import os
from allure_commons import plugin_manager
from allure_commons.logger import AllureFileLogger
from xmlrunner.allure_report.listener import AllureListener


class AllureHook:

    def __init__(self):
        self.file_logger = None
        self.listener = AllureListener()

    def register_allure_plugins(self, test, file_name, domain):
        dir_name = os.path.join("test-reports", "allure-results", domain, file_name)
        self.file_logger = AllureFileLogger(dir_name, clean=True)
        plugin_manager.register(self.listener)
        plugin_manager.register(self.file_logger)

    def unregister_allure_plugins(self):
        plugin_manager.unregister(plugin=self.listener)
        plugin_manager.unregister(plugin=self.file_logger)
