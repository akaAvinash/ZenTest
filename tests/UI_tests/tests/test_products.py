import uuid

from pages.products_page import ProductsPage
from utils.api_helper import create_product

def test_new_product_appears_in_list(page):
    product_page = ProductsPage(page)
    product_page.goto()

    product_name = f"Test Mug {uuid.uuid4().hex[:8]}"
    product_page.add_product(product_name, "5.50", "10")

    row = product_page.product_row(product_name)
    row.wait_for()
    assert "5.50" in row.inner_text()
    assert "10" in row.inner_text()
