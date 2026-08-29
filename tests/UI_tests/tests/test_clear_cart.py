import uuid

from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from utils.api_helper import create_product


def _seed_cart_with_one_item(page):
    product_name = f"Clear Cart Item {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "1")

    cart_page = CartPage(page)
    cart_page.cart_row(product_name).wait_for()
    return product_name, cart_page


def test_clear_cart_shows_confirmation_dialog(page):
    """UI-TC-17: clicking Clear Cart shows a confirmation dialog before
    anything is deleted. Dismissed (not accepted) so the assertion below
    about the dialog text is the point, not the deletion itself."""
    _, cart_page = _seed_cart_with_one_item(page)

    dialog_text = cart_page.clear_cart(accept=False)

    assert "sure" in dialog_text.lower()
    assert "clear the cart" in dialog_text.lower()


def test_confirming_clear_cart_empties_cart(page):
    """UI-TC-18"""
    _, cart_page = _seed_cart_with_one_item(page)

    cart_page.clear_cart(accept=True)

    cart_page.page.wait_for_selector("#cartBody:has-text('Cart is empty')")
    assert "0.00" in cart_page.cart_total()


def test_cancelling_clear_cart_leaves_cart_unchanged(page):
    """UI-TC-19"""
    product_name, cart_page = _seed_cart_with_one_item(page)
    total_before = cart_page.cart_total()

    cart_page.clear_cart(accept=False)

    assert cart_page.cart_row(product_name).count() == 1
    assert cart_page.cart_total() == total_before
