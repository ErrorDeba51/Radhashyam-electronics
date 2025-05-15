// radhashyam/static/js/main.js
import { initCardAnimations } from './modules/animations.js';

document.addEventListener('DOMContentLoaded', () => {
    // Initialize product card animations
    initCardAnimations();

    // Image Zoom with Constraints
    document.querySelectorAll('.product-thumbnail').forEach(img => {
        // Handle loading state
        const handleLoad = () => img.classList.add('loaded');

        img.addEventListener('load', handleLoad);
        if (img.complete) handleLoad();

        // Enhanced zoom functionality
        img.addEventListener('click', function () {
            if (!this.classList.contains('zoomed')) {
                const container = this.closest('.product-card');
                const containerRect = container.getBoundingClientRect();

                const maxScale = Math.min(
                    window.innerWidth / containerRect.width,
                    window.innerHeight / containerRect.height
                ) * 0.8;

                this.style.transform = `scale(${Math.min(maxScale, 2)})`;
            } else {
                this.style.transform = 'scale(1)';
            }
            this.classList.toggle('zoomed');
            this.style.cursor = this.classList.contains('zoomed')
                ? 'zoom-out'
                : 'zoom-in';
        });
    });

    // Cart Functionality
    const handleQuantityChange = async (productId, newQuantity) => {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        try {
            const response = await fetch(`/cart/update/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `quantity=${newQuantity}`
            });

            if (response.ok) {
                const data = await response.json();
                updateCartUI(data);
            }
        } catch (error) {
            console.error('Error updating cart:', error);
        }
    };

    const handleDeleteItem = async (productId) => {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        try {
            const response = await fetch(`/cart/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                const data = await response.json();
                document.querySelector(`[data-product-id="${productId}"]`).closest('.cart-item').remove();
                updateCartUI(data);

                if (data.cart_count === 0) {
                    document.querySelector('.cart-container').innerHTML = `
                        <div class="empty-cart text-center py-5">
                            <i class="bi bi-cart-x fs-1 text-muted"></i>
                            <p class="h5 mt-3">Your cart is empty</p>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Error removing item:', error);
        }
    };

    const updateCartUI = (data) => {
        document.querySelectorAll('.cart-total').forEach(el => {
            el.textContent = `₹${data.total}`;
        });
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = data.cart_count;
        });
        document.querySelectorAll('.nav-cart-count').forEach(el => {
            el.textContent = data.cart_count;
        });
    };

    // Event Delegation for Cart
    document.querySelector('.cart-container')?.addEventListener('click', (e) => {
        const productId = e.target.dataset.productId;

        if (e.target.classList.contains('increment')) {
            const input = e.target.previousElementSibling;
            input.value = Math.min(parseInt(input.value) + 1, input.max);
            handleQuantityChange(productId, input.value);
        }

        if (e.target.classList.contains('decrement')) {
            const input = e.target.nextElementSibling;
            input.value = Math.max(parseInt(input.value) - 1, 1);
            handleQuantityChange(productId, input.value);
        }

        if (e.target.classList.contains('delete-item')) {
            handleDeleteItem(productId);
        }
    });

    document.querySelectorAll('.cart-quantity').forEach(input => {
        input.addEventListener('change', function () {
            const productId = this.dataset.productId;
            handleQuantityChange(productId, this.value);
        });
    });

    // Buy Selected Items
    document.getElementById('buySelected')?.addEventListener('click', () => {
        const selected = Array.from(document.querySelectorAll('.item-checkbox:checked'))
            .map(checkbox => checkbox.value);
        // Implement selected items checkout
        console.log('Selected items:', selected);
    });

    // Pincode Validation with Error Handling
    const pincodeCheckBtn = document.getElementById('pincodeCheck');
    if (pincodeCheckBtn) {
        pincodeCheckBtn.addEventListener('click', async () => {
            const pincodeInput = document.getElementById('pincodeInput');
            const pincode = pincodeInput.value.trim();

            if (!/^\d{6}$/.test(pincode)) {
                alert('Please enter a valid 6-digit pincode');
                pincodeInput.focus();
                return;
            }

            try {
                const response = await fetch(`/api/check-pincode/${pincode}/`);
                if (!response.ok) throw new Error('Service unavailable');

                const result = await response.json();
                const deliveryInfo = document.getElementById('deliveryInfo');

                if (result.valid) {
                    deliveryInfo.classList.remove('d-none');
                    document.getElementById('deliveryDate').textContent = result.delivery_date;
                } else {
                    alert('Delivery not available for this pincode');
                }
            } catch (error) {
                console.error('Pincode check error:', error);
                alert('Service temporarily unavailable. Please try again later.');
            }
        });
    }

    // Cleanup event listeners on navigation
    document.addEventListener('htmx:beforeSwap', () => {
        document.querySelectorAll('.product-thumbnail').forEach(img => {
            img.removeEventListener('load', handleLoad);
            img.removeEventListener('click', handleZoom);
        });
    });
});