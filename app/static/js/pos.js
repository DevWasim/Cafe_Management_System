// POS Logic

let cart = [];
let currentPaymentMethod = 'Cash';

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    renderCart();
});

// Helper to add from card (cleaner HTML)
function addToCartFromCard(element) {
    const id = parseInt(element.getAttribute('data-id'));
    const name = element.getAttribute('data-name');
    const price = parseFloat(element.getAttribute('data-price'));
    const image = element.getAttribute('data-image');
    addToCart(id, name, price, image);
}

// Filter Products by Category
function filterCategory(category) {
    const products = document.querySelectorAll('.product-card-wrapper');
    products.forEach(el => {
        if (category === 'All' || el.getAttribute('data-category') === category) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    });
}

// Add Item to Cart
function addToCart(id, name, price, image) {
    // Check if exists
    const existing = cart.find(item => item.id === id);
    if (existing) {
        existing.quantity++;
    } else {
        cart.push({
            id: id,
            name: name,
            price: price,
            image: image,
            quantity: 1,
            options: {} // Future expansion
        });
    }
    renderCart();
}

// Remove/Decrease Item
function adjustQuantity(id, change) {
    const index = cart.findIndex(item => item.id === id);
    if (index === -1) return;

    cart[index].quantity += change;

    if (cart[index].quantity <= 0) {
        cart.splice(index, 1);
    }
    renderCart();
}

// Render Cart Table
function renderCart() {
    const tbody = document.getElementById('cart-table-body');
    const totalEl = document.getElementById('cart-total');
    const subtotalEl = document.getElementById('cart-subtotal');

    tbody.innerHTML = '';

    let total = 0;

    if (cart.length === 0) {
        tbody.innerHTML = `
            <tr class="text-center text-muted">
                <td class="p-4" colspan="4">Cart is empty</td>
            </tr>`;
    } else {
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="align-middle" style="width: 50%;">
                    <div class="d-flex align-items-center">
                        <div>
                            <span class="fw-bold d-block">${item.name}</span>
                            ${item.options && item.options.notes ? `<small class="text-muted" style="font-size: 0.75rem;"><i data-feather="edit-2" style="width:10px; height:10px;"></i> ${item.options.notes}</small>` : ''}
                        </div>
                    </div>
                </td>
                <td class="align-middle text-end">
                     $${item.price.toFixed(2)}
                </td>
                <td class="align-middle text-center" style="width: 25%;">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary" onclick="adjustQuantity(${item.id}, -1)">-</button>
                        <button class="btn btn-outline-secondary disabled" style="width: 30px; color: black; font-weight: bold;">${item.quantity}</button>
                        <button class="btn btn-outline-secondary" onclick="adjustQuantity(${item.id}, 1)">+</button>
                    </div>
                    <button class="btn btn-sm btn-link text-muted p-0 ms-1" onclick="openModifiers(${item.id})"><i data-feather="edit"></i></button>
                </td>
                <td class="align-middle text-end fw-bold">
                    $${itemTotal.toFixed(2)}
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Re-init feather icons for new elements
        if (typeof feather !== 'undefined') feather.replace();
    }

    totalEl.innerText = `$${total.toFixed(2)}`;
    subtotalEl.innerText = `$${total.toFixed(2)}`;
}

// Modifiers Logic
let currentModifierId = null;

function openModifiers(id) {
    const item = cart.find(i => i.id === id);
    if (!item) return;

    currentModifierId = id;
    document.getElementById('modifier-item-name').innerText = item.name;
    document.getElementById('modifier-notes').value = item.options.notes || '';

    const modal = new bootstrap.Modal(document.getElementById('modifiersModal'));
    modal.show();
}

function addNote(note) {
    const textarea = document.getElementById('modifier-notes');
    let current = textarea.value;
    if (current) current += ', ';
    textarea.value = current + note;
}

function saveModifiers() {
    const note = document.getElementById('modifier-notes').value;
    const itemIndex = cart.findIndex(i => i.id === currentModifierId);

    if (itemIndex > -1) {
        cart[itemIndex].options = { notes: note };
        renderCart();
    }

    const modalEl = document.getElementById('modifiersModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();
}

function clearCart() {
    if (confirm('Clear cart?')) {
        cart = [];
        renderCart();
    }
}

// Payment UI
function showPaymentModal(method) {
    if (cart.length === 0) {
        alert('Cart is empty!');
        return;
    }

    currentPaymentMethod = method;
    const total = calculateTotal();

    document.getElementById('modal-total-display').innerText = `$${total.toFixed(2)}`;
    document.getElementById('modal-method-display').innerText = `Method: ${method}`;
    const cashUI = document.getElementById('cash-change-ui');

    if (method === 'Cash') {
        cashUI.classList.remove('d-none');
        document.getElementById('amount-tendered').value = '';
        document.getElementById('change-display').innerText = 'Change: $0.00';
    } else {
        cashUI.classList.add('d-none');
    }

    const bsModal = new bootstrap.Modal(document.getElementById('paymentModal'));
    bsModal.show();
}

function calculateTotal() {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

function calculateChange() {
    const total = calculateTotal();
    const tendered = parseFloat(document.getElementById('amount-tendered').value) || 0;
    const change = tendered - total;

    const changeEl = document.getElementById('change-display');
    if (change >= 0) {
        changeEl.innerText = `Change: $${change.toFixed(2)}`;
        changeEl.classList.remove('text-danger');
        changeEl.classList.add('text-success');
    } else {
        changeEl.innerText = `Due: $${Math.abs(change).toFixed(2)}`;
        changeEl.classList.remove('text-success');
        changeEl.classList.add('text-danger');
    }
}

// Process Order API
function processOrder() {
    const total = calculateTotal();
    const tableNum = document.getElementById('table-selector').value || 0;

    if (currentPaymentMethod === 'Cash') {
        const tendered = parseFloat(document.getElementById('amount-tendered').value) || 0;
        if (tendered < total) {
            alert('Insufficient cash tendered!');
            return;
        }
    }

    const payload = {
        cart: cart,
        total: total,
        payment_method: currentPaymentMethod,
        table_number: tableNum
    };

    fetch(API_CREATE_ORDER, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken() // Try to get CSRF token if available
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close Modal
                const modalEl = document.getElementById('paymentModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                modal.hide();

                // Print Receipt (Mock)
                alert(`Order #${data.order_id} Success! Printing receipt...`);

                // Reset
                cart = [];
                renderCart();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to process order');
        });
}

// Helper to get CSRF token from Flask hidden form if exists
function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    return token ? token.value : '';
}
