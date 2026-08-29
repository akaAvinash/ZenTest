import uuid

from playwright.sync_api import expect

from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from utils.api_helper import create_product


def test_add_to_cart_shows_correct_total(page):
    """UI-TC-06, UI-TC-07, UI-TC-08"""
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


def test_adding_same_product_twice_merges_quantity(page):
    """UI-TC-09: adding a product already in the cart merges into the
    existing row instead of creating a second one. Uses expect() (polling)
    rather than a single-shot read, since app.js fires its toast before
    awaiting the cart re-render — the DOM update can still be in flight
    right after add_to_cart() returns."""
    product_name = f"Merge Item {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 10)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "2")
    products_page.add_to_cart(product_name, "3")

    cart_page = CartPage(page)
    row = cart_page.cart_row(product_name)
    expect(row).to_have_count(1)
    expect(row).to_contain_text("5")


def test_add_multiple_different_products_to_cart(page):
    """UI-TC-10: two different products each get their own cart row, and
    the cart total is the sum of both."""
    product_a = f"Multi A {uuid.uuid4().hex[:8]}"
    product_b = f"Multi B {uuid.uuid4().hex[:8]}"
    create_product(product_a, 2.00, 5)
    create_product(product_b, 3.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_a, "1")
    products_page.add_to_cart(product_b, "2")

    cart_page = CartPage(page)
    cart_page.cart_row(product_a).wait_for()
    cart_page.cart_row(product_b).wait_for()
    expect(page.locator("#cartTotal")).to_contain_text("8.00")  # 2.00*1 + 3.00*2


def test_add_to_cart_exceeding_stock_is_rejected(page):
    """UI-TC-11: entering a quantity greater than available stock shows an
    error toast and does not add the item. Safe to wait on the toast here
    (unlike other actions) — app.js's catch branch calls showToast() and
    nothing else, so there's no re-render race to worry about."""
    product_name = f"Low Stock {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 3)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "999")

    toast = products_page.wait_for_toast()
    assert "error" in (toast.get_attribute("class") or "")
    assert "3 units available" in toast.inner_text()

    cart_page = CartPage(page)
    assert cart_page.cart_row(product_name).count() == 0


def test_checkout_button_disabled_when_cart_empty(page):
    """UI-TC-13: reset_cart autouse fixture already empties the cart
    before this test runs."""
    products_page = ProductsPage(page)
    products_page.goto()

    cart_page = CartPage(page)
    expect(page.locator("#cartBody")).to_contain_text("Cart is empty")
    expect(cart_page.checkout_button()).to_be_disabled()


def test_remove_single_item_from_cart(page):
    """UI-TC-14"""
    product_name = f"Remove Me {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "1")

    cart_page = CartPage(page)
    cart_page.cart_row(product_name).wait_for()
    cart_page.remove_item(product_name)

    expect(cart_page.cart_row(product_name)).to_have_count(0)


def test_cart_returns_to_empty_state_after_removing_only_item(page):
    """UI-TC-15"""
    product_name = f"Last Item {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "1")

    cart_page = CartPage(page)
    cart_page.cart_row(product_name).wait_for()
    cart_page.remove_item(product_name)

    expect(page.locator("#cartBody")).to_contain_text("Cart is empty")
    expect(page.locator("#cartTotal")).to_contain_text("0.00")
    expect(cart_page.checkout_button()).to_be_disabled()


def test_checkout_with_items_clears_cart(page):
    """UI-TC-16"""
    product_name = f"Checkout Item {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "1")

    cart_page = CartPage(page)
    cart_page.cart_row(product_name).wait_for()
    cart_page.checkout()

    expect(page.locator("#cartBody")).to_contain_text("Cart is empty")
    expect(page.locator("#cartTotal")).to_contain_text("0.00")


def test_toast_notification_appears_and_auto_dismisses(page):
    """UI-TC-20: a toast shows immediately after an action and disappears
    on its own (no user interaction) after a few seconds."""
    product_name = f"Toast Check {uuid.uuid4().hex[:8]}"
    create_product(product_name, 2.00, 5)

    products_page = ProductsPage(page)
    products_page.goto()
    products_page.add_to_cart(product_name, "1")

    toast = products_page.wait_for_toast()
    assert "show" in (toast.get_attribute("class") or "")

    page.wait_for_timeout(3000)
    assert "show" not in (toast.get_attribute("class") or "")
