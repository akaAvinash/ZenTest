// The frontend is served by the same FastAPI app as the API, so requests
// are always same-origin — no separate host/port needed.
const API_BASE = "";

const productsBody = document.getElementById("productsBody");
const cartBody = document.getElementById("cartBody");
const cartTotalEl = document.getElementById("cartTotal");
const productForm = document.getElementById("productForm");
const checkoutBtn = document.getElementById("checkoutBtn");
const clearCartBtn = document.getElementById("clearCartBtn");
const toast = document.getElementById("toast");
const apiDot = document.getElementById("apiDot");
const apiStatusText = document.getElementById("apiStatusText");

function showToast(message, type = "success") {
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => {
    toast.className = "toast";
  }, 2500);
}

function formatMoney(value) {
  return `$${Number(value).toFixed(2)}`;
}

async function apiFetch(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function checkApiHealth() {
  try {
    await apiFetch("/api/health");
    apiDot.className = "dot online";
    apiStatusText.textContent = "API online";
  } catch (err) {
    apiDot.className = "dot offline";
    apiStatusText.textContent = "API offline";
  }
}

function clearChildren(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function renderProducts(products) {
  clearChildren(productsBody);

  if (products.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="5" class="empty-row">No products yet</td>';
    productsBody.appendChild(row);
    return;
  }

  products.forEach((product) => {
    const row = document.createElement("tr");

    const idCell = document.createElement("td");
    idCell.textContent = product.id;

    const nameCell = document.createElement("td");
    nameCell.textContent = product.name;

    const priceCell = document.createElement("td");
    priceCell.textContent = formatMoney(product.price);

    const stockCell = document.createElement("td");
    stockCell.textContent = product.stock;
    if (product.stock === 0) stockCell.classList.add("stock-low");

    const actionCell = document.createElement("td");
    const qtyInput = document.createElement("input");
    qtyInput.type = "number";
    qtyInput.min = "1";
    qtyInput.max = String(product.stock || 1);
    qtyInput.value = "1";
    qtyInput.className = "qty-input";
    qtyInput.disabled = product.stock === 0;

    const addBtn = document.createElement("button");
    addBtn.textContent = product.stock === 0 ? "Out of stock" : "Add to cart";
    addBtn.className = "add-cart-btn";
    addBtn.disabled = product.stock === 0;
    addBtn.addEventListener("click", () => addToCart(product.id, qtyInput));

    actionCell.appendChild(qtyInput);
    actionCell.appendChild(addBtn);

    row.appendChild(idCell);
    row.appendChild(nameCell);
    row.appendChild(priceCell);
    row.appendChild(stockCell);
    row.appendChild(actionCell);

    productsBody.appendChild(row);
  });
}

function renderCart(cart) {
  clearChildren(cartBody);

  if (cart.items.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="5" class="empty-row">Cart is empty</td>';
    cartBody.appendChild(row);
  } else {
    cart.items.forEach((item) => {
      const row = document.createElement("tr");

      const nameCell = document.createElement("td");
      nameCell.textContent = item.name;

      const priceCell = document.createElement("td");
      priceCell.textContent = formatMoney(item.price);

      const qtyCell = document.createElement("td");
      qtyCell.textContent = item.quantity;

      const totalCell = document.createElement("td");
      totalCell.textContent = formatMoney(item.total);

      const actionCell = document.createElement("td");
      const removeBtn = document.createElement("button");
      removeBtn.textContent = "Remove";
      removeBtn.className = "remove-btn";
      removeBtn.addEventListener("click", () => removeFromCart(item.product_id));
      actionCell.appendChild(removeBtn);

      row.appendChild(nameCell);
      row.appendChild(priceCell);
      row.appendChild(qtyCell);
      row.appendChild(totalCell);
      row.appendChild(actionCell);

      cartBody.appendChild(row);
    });
  }

  cartTotalEl.textContent = formatMoney(cart.cart_total);
  checkoutBtn.disabled = cart.items.length === 0;
}

async function loadProducts() {
  try {
    const products = await apiFetch("/api/products");
    renderProducts(products);
  } catch (err) {
    productsBody.innerHTML = `<tr><td colspan="5" class="empty-row">${err.message}</td></tr>`;
  }
}

async function loadCart() {
  try {
    const cart = await apiFetch("/api/cart");
    renderCart(cart);
  } catch (err) {
    cartBody.innerHTML = `<tr><td colspan="5" class="empty-row">${err.message}</td></tr>`;
  }
}

async function addToCart(productId, qtyInput) {
  const quantity = parseInt(qtyInput.value, 10) || 1;
  try {
    await apiFetch("/api/cart", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    showToast("Added to cart");
    await Promise.all([loadCart(), loadProducts()]);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function removeFromCart(productId) {
  try {
    await apiFetch(`/api/cart/${productId}`, { method: "DELETE" });
    showToast("Removed from cart");
    await Promise.all([loadCart(), loadProducts()]);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function checkout() {
  try {
    const result = await apiFetch("/api/checkout", { method: "POST" });
    showToast(result.message);
    await loadCart();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function clearCart() {
  try {
    if (!confirm("Are you sure you want to clear the cart?")) {
      return;
    }

    const result = await apiFetch("/api/delete", {
      method: "DELETE",
    });

    showToast(result.message);
    await loadCart();
  } catch (err) {
    showToast(err.message, "error");
  }
}

productForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("productName").value.trim();
  const price = parseFloat(document.getElementById("productPrice").value);
  const stock = parseInt(document.getElementById("productStock").value, 10);

  try {
    await apiFetch("/api/products", {
      method: "POST",
      body: JSON.stringify({ name, price, stock }),
    });
    showToast("Product added");
    productForm.reset();
    await loadProducts();
  } catch (err) {
    showToast(err.message, "error");
  }
});

checkoutBtn.addEventListener("click", checkout);

clearCartBtn.addEventListener("click", clearCart);

(async function init() {
  await checkApiHealth();
  await Promise.all([loadProducts(), loadCart()]);
})();
