/**
 * Cart functionality for buyer interface
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity controls
    initQuantityControls();
});

/**
 * Initialize quantity control buttons
 */
function initQuantityControls() {
    // Quantity decrease buttons
    const decreaseButtons = document.querySelectorAll('.quantity-decrease');
    if (decreaseButtons) {
        decreaseButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const input = this.parentNode.querySelector('input[type="number"]');
                let value = parseInt(input.value, 10);
                if (value > 1) {
                    input.value = value - 1;
                }
            });
        });
    }

    // Quantity increase buttons
    const increaseButtons = document.querySelectorAll('.quantity-increase');
    if (increaseButtons) {
        increaseButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const input = this.parentNode.querySelector('input[type="number"]');
                let value = parseInt(input.value, 10);
                const max = parseInt(input.getAttribute('max'), 10);
                if (value < max) {
                    input.value = value + 1;
                }
            });
        });
    }

    // Cart item removal confirmation
    const removeButtons = document.querySelectorAll('.remove-item');
    if (removeButtons) {
        removeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                return confirm('Are you sure you want to remove this item from your cart?');
            });
        });
    }
}

/**
 * Update cart item quantity
 * @param {string} productId - The product ID
 * @param {number} quantity - The new quantity
 */
function updateCartItem(productId, quantity) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/buyer/update_cart';
    
    const idInput = document.createElement('input');
    idInput.type = 'hidden';
    idInput.name = 'id';
    idInput.value = productId;
    
    const quantityInput = document.createElement('input');
    quantityInput.type = 'hidden';
    quantityInput.name = 'quantity';
    quantityInput.value = quantity;
    
    form.appendChild(idInput);
    form.appendChild(quantityInput);
    document.body.appendChild(form);
    form.submit();
}

/**
 * Remove item from cart
 * @param {string} productId - The product ID to remove
 */
function removeCartItem(productId) {
    if (confirm('Are you sure you want to remove this item from your cart?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/buyer/update_cart';
        
        const idInput = document.createElement('input');
        idInput.type = 'hidden';
        idInput.name = 'id';
        idInput.value = productId;
        
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = 'remove';
        
        form.appendChild(idInput);
        form.appendChild(actionInput);
        document.body.appendChild(form);
        form.submit();
    }
}
