from pages.base_page import BasePage


class CartPage(BasePage):
    def cart_row(self, name: str):
        return self.page.locator("#cartBody tr", has_text=name)

    def cart_total(self) -> str:
        return self.page.locator("#cartTotal").inner_text()

    def remove_item(self, name: str):
        self.logger.info("Removing cart item via UI: name=%s", name)
        self.cart_row(name).locator(".remove-btn").click()

    def checkout(self):
        self.logger.info("Checking out via UI")
        self.page.click("#checkoutBtn")