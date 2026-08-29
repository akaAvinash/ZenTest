from utils.logger import get_logger


class BasePage:
    def __init__(self, page):
        self.page = page
        self.logger = get_logger(self.__class__.__module__)