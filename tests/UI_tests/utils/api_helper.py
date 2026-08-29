import requests
from config import API_URL
from utils.logger import get_logger

logger = get_logger(__name__)

def create_product(name: str, price: float, stock: int) -> int:
    "Create product via API and returns product ID"
    logger.info("Creating product via API: name=%s price=%s stock=%s", name, price, stock)
    res = requests.post(
        f"{API_URL}/api/products", json={"name": name, "price": price, "stock": stock}
    )
    res.raise_for_status()
    product_id = res.json()["product_id"]
    logger.debug("Product created via API: id=%s", product_id)
    return product_id

def clear_cart():
    logger.debug("Clearing cart via API")
    requests.post(f"{API_URL}/api/checkout")