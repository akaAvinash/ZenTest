from pages.base_page import BasePage
from utils.config import FRONTEND_URL


class ProductsPage(BasePage):
    def goto(self):
        self.logger.debug("Navigating to %s", FRONTEND_URL)
        self.page.goto(FRONTEND_URL)

    def add_product(self, name: str, price: float, stock: int):
        # Note: app.js fires the toast *before* awaiting loadProducts(), so
        # don't try to synchronize on the toast here — callers should poll
        # for their actual expected end state (e.g. product_row(...).wait_for()).
        self.logger.info("Adding product via UI: name=%s price=%s stock=%s", name, price, stock)
        self.page.fill("#productName", name)
        self.page.fill("#productPrice", str(price))
        self.page.fill("#productStock", str(stock))
        self.page.click("#productForm button[type='submit']")

    def product_row(self, name: str):
        return self.page.locator(f"#productsBody tr", has_text=name)

    def add_to_cart(self, name: str, quantity: str = "1"):
        # Same note as add_product(): the toast isn't a reliable signal
        # that the cart/products re-render has finished.
        self.logger.info("Adding to cart via UI: name=%s quantity=%s", name, quantity)
        row = self.product_row(name)
        row.locator(".qty-input").fill(quantity)
        row.locator(".add-cart-btn").click()
        # Wait for this add's async cycle to settle before returning —
        # either a cart row for this product appears (success), or the
        # toast shows an error (rejection, e.g. over-stock), whichever
        # happens first. Two failure modes this avoids:
        #  - Chaining a second add_to_cart() for a *different* product
        #    right after this one can otherwise race this call's in-flight
        #    products-table rebuild (loadProducts() replaces every row
        #    with a fresh element, qty-input reset to "1"); if that lands
        #    between the next call's .fill(quantity) and .click(), the
        #    typed quantity is silently lost.
        #  - Waiting a fixed timeout for the cart row alone burns that
        #    whole timeout on a *rejected* add (no row ever appears),
        #    which previously ate into the toast's ~2.5s auto-dismiss
        #    window and made it disappear before a test could assert on
        #    it. Racing both conditions resolves as soon as either is
        #    true, so it never wastes time either way.
        try:
            self.page.wait_for_function(
                """(name) => {
                    const rows = document.querySelectorAll('#cartBody tr');
                    const hasRow = Array.from(rows).some((r) => r.textContent.includes(name));
                    const toast = document.getElementById('toast');
                    const hasError = !!toast && toast.classList.contains('show') && toast.classList.contains('error');
                    return hasRow || hasError;
                }""",
                arg=name,
                timeout=3000,
            )
        except Exception:
            pass