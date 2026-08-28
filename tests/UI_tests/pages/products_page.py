from pages.base_page import BasePage
from config import FRONTEND_URL


class ProductsPage(BasePage):
    def goto(self):
        self.page.goto(FRONTEND_URL)

    def add_product(self, name: str, price: float, stock: int):
        self.page.fill("#productName", name)
        self.page.fill("#productPrice", str(price))
        self.page.fill("#productStock", str(stock))
        self.page.click("#productForm button[type='submit']")

    def product_row(self, name: str):
        return self.page.locator(f"#productsBody tr", has_text=name)

    def add_to_cart(self, name: str, quantity: str = "1"):
        row = self.product_row(name)
        row.locator(".qty-input").fill(quantity)
        row.locator(".add-cart-btn").click()