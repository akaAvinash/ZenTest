import uuid

from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from utils.api_helper import create_product


def test_add_to_cart_shows_correct_total(page):
    product_name = f"Test Pen {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "3")

    cart_page = CartPage(page)
    row = cart_page.cart_row(product_name)
    row.wait_for()
    assert "3" in row.inner_text()
    assert "6.00" in cart_page.cart_total()