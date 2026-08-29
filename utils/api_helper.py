from utils.api_client import ApiClient
from utils.logger import get_logger

logger = get_logger(__name__)

client = ApiClient()


def create_product(name: str, price: float, stock: int) -> int:
    "Create product via API and returns product ID"
    logger.info("Creating product via API: name=%s price=%s stock=%s", name, price, stock)
    res = client.create_product(name, price, stock)
    res.raise_for_status()
    product_id = res.json()["product_id"]
    logger.debug("Product created via API: id=%s", product_id)
    return product_id


def clear_cart():
    logger.debug("Clearing cart via API")
    client.checkout()  # 400 on already-empty cart is fine to ignore here
