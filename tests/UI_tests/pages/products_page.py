from pages.base_page import BasePage
from utils.config import FRONTEND_URL


class ProductsPage(BasePage):
    def goto(self):
        self.logger.debug("Navigating to %s", FRONTEND_URL)
        self.page.goto(FRONTEND_URL)

    def add_product(self, name: str, price: float, stock: int):
        self.logger.info("Adding product via UI: name=%s price=%s stock=%s", name, price, stock)
        self.page.fill("#productName", name)
        self.page.fill("#productPrice", str(price))
        self.page.fill("#productStock", str(stock))
        self.page.click("#productForm button[type='submit']")

    def product_row(self, name: str):
        return self.page.locator(f"#productsBody tr", has_text=name)

    def add_to_cart(self, name: str, quantity: str = "1"):
        self.logger.info("Adding to cart via UI: name=%s quantity=%s", name, quantity)
        row = self.product_row(name)
        row.locator(".qty-input").fill(quantity)
        row.locator(".add-cart-btn").click()