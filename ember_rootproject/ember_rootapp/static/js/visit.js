/**
 * EMBER & ROOT - Visit Page JavaScript
 */

(function(){
    "use strict";
    
    // Cart state
    let cart = JSON.parse(localStorage.getItem('emberCart')) || [];
    
    // Toast function
    window.showToast = function(msg) {
        const toastEl = document.getElementById('liveToast');
        const toastBody = document.getElementById('toastBody');
        if (toastEl && toastBody) {
            toastBody.textContent = msg;
            toastEl.classList.remove('d-none');
            setTimeout(() => toastEl.classList.add('d-none'), 3000);
        }
    };
    
    // Update cart UI
    function updateCartUI() {
        const container = document.getElementById('cartItemsContainer');
        const counter = document.getElementById('cartCounter');
        const subtotalEl = document.getElementById('cartSubtotal');
        
        if (!container) return;
        
        if (cart.length === 0) {
            container.innerHTML = '<p class="text-center text-muted py-5">No items yet. The oven is waiting.</p>';
            if (subtotalEl) subtotalEl.textContent = '¥0';
            if (counter) counter.textContent = '(0)';
            return;
        }
        
        let subtotal = 0;
        let html = '';
        cart.forEach((item, idx) => {
            subtotal += item.price * item.qty;
            html += `
                <div class="cart-item d-flex justify-content-between p-3 border-bottom">
                    <div>
                        <div class="fw-bold">${item.name}</div>
                        <div class="small text-muted">Qty: ${item.qty}</div>
                    </div>
                    <div class="text-end">
                        <div>¥${(item.price * item.qty).toLocaleString()}</div>
                        <button class="btn btn-sm text-danger p-0 remove-item" data-index="${idx}">
                            <i class="bi bi-trash3"></i> Remove
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        if (subtotalEl) subtotalEl.textContent = `¥${subtotal.toLocaleString()}`;
        if (counter) counter.textContent = `(${cart.reduce((acc, i) => acc + i.qty, 0)})`;
        
        container.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                cart.splice(idx, 1);
                localStorage.setItem('emberCart', JSON.stringify(cart));
                updateCartUI();
            });
        });
    }
    
    // Auth UI
    function updateAuthUI() {
        const authArea = document.getElementById('authArea');
        if (!authArea) return;
        
        const loggedIn = localStorage.getItem('emberLoggedIn') === 'true';
        const currentUser = localStorage.getItem('emberUser');
        
        if (loggedIn && currentUser) {
            authArea.innerHTML = `
                <div class="dropdown user-dropdown">
                    <button class="btn dropdown-toggle user-dropdown-toggle d-flex align-items-center gap-2 border-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <span class="user-avatar">${currentUser.charAt(0).toUpperCase()}</span>
                        <span class="user-name d-none d-md-inline">${currentUser}</span>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end rounded-0">
                        <li><a class="dropdown-item" href="#" onclick="showToast('📋 Order history')"><i class="bi bi-clock-history me-2"></i>My Orders</a></li>
                        <li><a class="dropdown-item" href="#" onclick="showToast('👤 Profile settings')"><i class="bi bi-person me-2"></i>Profile</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" onclick="handleLogout()"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
                    </ul>
                </div>
            `;
        } else {
            authArea.innerHTML = `
                <button class="btn btn-link text-dark text-decoration-none" onclick="showToast('Sign in feature coming soon')">
                    <i class="bi bi-person-circle"></i> SIGN IN
                </button>
            `;
        }
    }
    
    window.handleLogout = function() {
        localStorage.removeItem('emberLoggedIn');
        localStorage.removeItem('emberUser');
        updateAuthUI();
        showToast('You have been logged out');
    };
    
    // Initialize
    updateAuthUI();
    updateCartUI();
    
})();