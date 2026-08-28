from config import FRONTEND_URL
from pages.base_page import BasePage


class HomeUi(BasePage):

    def goto(self):
        self.page.goto(FRONTEND_URL)

    def api_status(self, name: "str"):
        return self.page.locator("#apiStatusText", has_text=name)

    def api_dot(self):
        return self.page.locator("#apiDot")