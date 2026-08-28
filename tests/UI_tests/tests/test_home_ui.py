from pages.home_page import HomeUi

def test_api_status(page):
    home_page = HomeUi(page)
    home_page.goto()

    status = home_page.api_status("API online")
    status.wait_for()
    assert "API online" in status.inner_text()

    dot = home_page.api_dot()
    dot.wait_for()
    assert "online" in dot.get_attribute("class")
