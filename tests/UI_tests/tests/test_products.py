import uuid

from pages.products_page import ProductsPage
from utils.api_helper import create_product


def test_products_table_loads_existing_products(page):
    """UI-TC-02: at least one product already exists (seeded via API), and
    the Products table shows it on page load without any manual action."""
    product_name = f"Preload Product {uuid.uuid4().hex[:8]}"
    create_product(product_name, 3.00, 5)

    product_page = ProductsPage(page)
    product_page.goto()

    row = product_page.product_row(product_name)
    row.wait_for()
    assert product_name in row.inner_text()


def test_new_product_appears_in_list(page):
    """UI-TC-03, UI-TC-04"""
    product_page = ProductsPage(page)
    product_page.goto()

    product_name = f"Test Mug {uuid.uuid4().hex[:8]}"
    product_page.add_product(product_name, "5.50", "10")

    row = product_page.product_row(product_name)
    row.wait_for()
    assert "5.50" in row.inner_text()
    assert "10" in row.inner_text()


def test_price_displayed_in_currency_format(page):
    """UI-TC-05: a price entered as "9.5" (one decimal) displays as the
    full currency-formatted "$9.50", not the raw input."""
    product_page = ProductsPage(page)
    product_page.goto()

    product_name = f"Currency Check {uuid.uuid4().hex[:8]}"
    product_page.add_product(product_name, "9.5", "3")

    row = product_page.product_row(product_name)
    row.wait_for()
    assert "$9.50" in row.inner_text()


def test_add_to_cart_disabled_for_out_of_stock_product(page):
    """UI-TC-12: a product with stock 0 shows a disabled "Out of stock"
    button and a disabled quantity input."""
    product_name = f"Out Of Stock {uuid.uuid4().hex[:8]}"
    create_product(product_name, 4.00, 0)

    product_page = ProductsPage(page)
    product_page.goto()

    row = product_page.product_row(product_name)
    row.wait_for()

    add_button = row.locator(".add-cart-btn")
    qty_input = row.locator(".qty-input")

    assert add_button.inner_text().strip() == "Out of stock"
    assert add_button.is_disabled()
    assert qty_input.is_disabled()
