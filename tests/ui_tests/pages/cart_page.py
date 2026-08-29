from pages.base_page import BasePage


class CartPage(BasePage):
    def cart_row(self, name: str):
        return self.page.locator("#cartBody tr", has_text=name)

    def cart_total(self) -> str:
        return self.page.locator("#cartTotal").inner_text()

    def remove_item(self, name: str):
        # Note: same as ProductsPage actions — don't try to synchronize on
        # the toast; poll for the actual expected end state instead (e.g.
        # expect(cart_row(...)).to_have_count(0)).
        self.logger.info("Removing cart item via UI: name=%s", name)
        self.cart_row(name).locator(".remove-btn").click()

    def checkout(self):
        self.logger.info("Checking out via UI")
        self.page.click("#checkoutBtn")

    def checkout_button(self):
        return self.page.locator("#checkoutBtn")

    def clear_cart(self, accept: bool = True) -> str:
        """Clicks Clear Cart, handling the native confirm() dialog it
        triggers. Returns the dialog's message text so tests can assert on
        it. Pass accept=False to cancel instead of confirming."""
        dialog_info = {}

        def handle_dialog(dialog):
            dialog_info["text"] = dialog.message
            dialog.accept() if accept else dialog.dismiss()

        self.logger.info("Clearing cart via UI (accept=%s)", accept)
        self.page.once("dialog", handle_dialog)
        self.page.click("#clearCartBtn")
        self.page.wait_for_timeout(300)  # let the dialog handler settle
        return dialog_info.get("text", "")