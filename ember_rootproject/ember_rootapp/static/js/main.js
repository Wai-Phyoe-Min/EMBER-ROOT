/**
 * EMBER & ROOT - Main JavaScript
 * Handles cart, authentication, modals, and animations
 * Data comes from Django backend
 */

(function(){
    "use strict";
    
    // ==================== STATE ====================
    let cart = JSON.parse(localStorage.getItem('emberCart')) || [];
    let mapInstance = null;
    let miniMapInstance = null;
    
    // ==================== UI ELEMENTS ====================
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastBody');
    let toastTimeout = null;
    
    // ==================== UTILITY FUNCTIONS ====================
    window.showToast = function(msg, type = 'success', title = null) {
        // Remove existing toasts if more than 3
        const existingToasts = document.querySelectorAll('.toast-modern');
        if (existingToasts.length >= 3) {
            existingToasts[0].remove();
        }
        
        // If type is a boolean (from old calls), convert it
        if (typeof type === 'boolean') {
            type = type ? 'success' : 'error';
        }
        
        // Set title based on type if not provided
        if (!title) {
            const titles = {
                'success': 'Success!',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Notice'
            };
            title = titles[type] || 'Notification';
        }
        
        // Set icon based on type
        const icons = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast-modern ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || 'ℹ'}</div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${msg}</div>
            </div>
            <div class="toast-close" onclick="this.closest('.toast-modern').remove()">✕</div>
        `;
        
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentNode) toast.remove();
                }, 400);
            }
        }, 4000);
        
        return toast;
    };
    
    window.showModal = function(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
    };
    
    function ensureSharedUI() {
        if (!document.getElementById('liveToast')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="toast-custom d-none" id="liveToast">
                    <span id="toastBody"></span>
                </div>
            `);
        }

        if (!document.getElementById('globalLoadingScreen')) {
            document.body.insertAdjacentHTML('afterbegin', `
                <div class="loading-screen" id="globalLoadingScreen">
                    <div class="loading-spinner"><span></span></div>
                    <div class="loading-screen-text">Lighting the fire, just for you...</div>
                </div>
            `);
        }

        if (!document.getElementById('cartOffcanvas')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="offcanvas offcanvas-end cart-offcanvas" tabindex="-1" id="cartOffcanvas">
                    <div class="offcanvas-header cart-header">
                        <h4 class="offcanvas-title" style="font-family: 'Newsreader', serif;">Your Order</h4>
                        <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
                    </div>
                    <div class="offcanvas-body p-0">
                        <div id="cartItemsContainer"></div>
                        <div id="pairingBox"></div>
                        <div class="p-4 border-top">
                            <div class="d-flex justify-content-between mb-2"><span>Subtotal</span><span id="cartSubtotal">¥0</span></div>
                            <div class="d-flex justify-content-between mb-3"><span class="fw-bold">Total</span><span class="fw-bold" id="cartTotal">¥0</span></div>
                            <button class="btn btn-ember w-100 mb-2" id="checkoutBtn">CHECKOUT</button>
                            <p class="small text-muted text-center mb-0">Pickup only. Karuizawa, Nagano.</p>
                        </div>
                    </div>
                </div>
            `);
        }

        if (!document.getElementById('checkoutModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="checkoutModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered modal-lg">
                        <div class="modal-content border-0 shadow-lg" style="border-radius: 32px; overflow: hidden;">
                            <div class="modal-header border-0 text-white" style="background: linear-gradient(135deg, #1a1a2e 0%, #2d2d4e 100%); padding: 1.5rem 2rem;">
                                <div class="d-flex align-items-center gap-3">
                                    <div style="width: 50px; height: 50px; background: rgba(211,84,0,0.2); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
                                        <i class="bi bi-cart-check-fill" style="font-size: 1.5rem; color: #E8C07A;"></i>
                                    </div>
                                    <div>
                                        <h5 class="modal-title text-white" style="font-size: 1.4rem; font-weight: 700;">Complete Your Order</h5>
                                        <p class="text-white-50 small mb-0">Pickup at Karuizawa · ~20 minutes</p>
                                    </div>
                                </div>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" style="opacity: 0.5;"></button>
                            </div>
                            <div class="modal-body p-4">
                                <div class="order-summary-section mb-4">
                                    <h6 class="fw-bold text-uppercase small mb-3" style="color: var(--ember);">
                                        <i class="bi bi-receipt me-2"></i>Order Summary
                                    </h6>
                                    <div class="order-items-container" id="checkoutOrderItems" style="max-height: 250px; overflow-y: auto;"></div>
                                    <div class="order-totals mt-3 pt-3 border-top">
                                        <div class="d-flex justify-content-between mb-2">
                                            <span class="text-muted">Subtotal</span>
                                            <span class="fw-semibold" id="checkoutSubtotal">¥0</span>
                                        </div>
                                        <div class="d-flex justify-content-between">
                                            <span class="fw-bold">Total</span>
                                            <span class="fw-bold" id="checkoutTotal" style="color: var(--ember); font-size: 1.3rem;">¥0</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="pickup-info-section mb-4">
                                    <h6 class="fw-bold text-uppercase small mb-3" style="color: var(--ember);">
                                        <i class="bi bi-pin-map-fill me-2"></i>Pickup Information
                                    </h6>
                                    <div class="row g-3">
                                        <div class="col-md-6">
                                            <div class="info-card p-3 rounded-3" style="background: #f8f9fa;">
                                                <div class="d-flex align-items-center gap-3">
                                                    <div style="width: 40px; height: 40px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                                        <i class="bi bi-clock" style="color: var(--ember);"></i>
                                                    </div>
                                                    <div>
                                                        <small class="text-muted">Ready in</small>
                                                        <div class="fw-bold">~20 minutes</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="info-card p-3 rounded-3" style="background: #f8f9fa;">
                                                <div class="d-flex align-items-center gap-3">
                                                    <div style="width: 40px; height: 40px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                                        <i class="bi bi-geo-alt" style="color: var(--ember);"></i>
                                                    </div>
                                                    <div>
                                                        <small class="text-muted">Location</small>
                                                        <div class="fw-bold">Karuizawa, Nagano</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="special-instructions-section mb-4">
                                    <label class="form-label fw-semibold small text-uppercase" style="color: var(--ember);">
                                        <i class="bi bi-chat-text me-2"></i>Special Instructions (Optional)
                                    </label>
                                    <textarea class="form-control rounded-3" id="checkoutInstructions" rows="2" 
                                            placeholder="Any dietary restrictions or special requests?" 
                                            style="resize: vertical; border: 1px solid #e0e0e0;"></textarea>
                                </div>
                                <div class="form-check mb-3">
                                    <input class="form-check-input" type="checkbox" id="confirmPickup" style="cursor: pointer;">
                                    <label class="form-check-label small" for="confirmPickup" style="cursor: pointer;">
                                        I understand this is a pickup-only order from Karuizawa, Nagano.
                                    </label>
                                </div>
                            </div>
                            <div class="modal-footer border-0 px-4 pb-4 pt-0">
                                <button type="button" class="btn btn-outline-secondary px-4" data-bs-dismiss="modal" style="border-radius: 50px;">
                                    <i class="bi bi-x-lg me-2"></i>Cancel
                                </button>
                                <button type="button" class="btn px-4 text-white" id="confirmCheckoutBtn" disabled 
                                        style="background: linear-gradient(135deg, #D35400, #E8C07A); border-radius: 50px; opacity: 0.6;">
                                    <i class="bi bi-check-lg me-2"></i>Confirm Order
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }

        if (!document.getElementById('orderSuccessModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="orderSuccessModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 shadow-lg" style="border-radius: 32px; overflow: hidden;">
                            <div class="modal-body p-0">
                                <div class="text-center p-5">
                                    <div class="success-animation mb-4">
                                        <div class="success-circle">
                                            <i class="bi bi-check-lg"></i>
                                        </div>
                                        <div class="success-pulse"></div>
                                    </div>
                                    <h3 class="fw-bold mb-2" style="color: #1a1a2e;">Order Confirmed!</h3>
                                    <p class="text-muted mb-3" id="successOrderNumber">Order #ORD-000000</p>
                                    <div class="pickup-info-box mb-4">
                                        <div class="d-flex align-items-center justify-content-center gap-2 text-muted">
                                            <i class="bi bi-clock"></i>
                                            <span>Ready for pickup in <strong>~20 minutes</strong></span>
                                        </div>
                                        <div class="d-flex align-items-center justify-content-center gap-2 text-muted mt-2">
                                            <i class="bi bi-geo-alt"></i>
                                            <span>EMBER & ROOT · Karuizawa, Nagano</span>
                                        </div>
                                    </div>
                                    <button type="button" class="btn px-4 text-white" data-bs-dismiss="modal" 
                                            style="background: linear-gradient(135deg, #D35400, #E8C07A); border-radius: 50px;">
                                        <i class="bi bi-check-lg me-2"></i>Got it!
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }

        if (!document.getElementById('originModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="originModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content rounded-0">
                            <div class="modal-header">
                                <h5 class="modal-title" style="font-family: 'Newsreader', serif;"><span id="originPizzaName"></span></h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <span class="badge bg-dark rounded-0 origin-farm-badge">
                                        <i class="bi bi-pin"></i> <span id="originFarmLabel"></span>
                                    </span>
                                    <span class="ms-2 text-muted small">
                                        <i class="bi bi-map"></i> <span id="originDistance"></span> from Karuizawa
                                    </span>
                                </div>
                                <div id="originMap" style="height: 350px; width: 100%;"></div>
                                <div class="mt-4">
                                    <h6 class="fw-bold text-uppercase small">Farmer's Note</h6>
                                    <p class="text-muted" id="originStory"></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }
    }

    // ==================== CART FUNCTIONS ====================
    function saveCart() {
        localStorage.setItem('emberCart', JSON.stringify(cart));
    }
    
    function updateCartUI() {
        const savedCart = JSON.parse(localStorage.getItem('emberCart')) || [];
        cart = savedCart;

        const container = document.getElementById('cartItemsContainer');
        const subtotalEl = document.getElementById('cartSubtotal');
        const totalEl = document.getElementById('cartTotal');
        const counter = document.getElementById('cartCounter');
        if (!container) return;

        if (cart.length === 0) {
            container.innerHTML = `
                <div class="cart-empty p-4 text-center text-muted">
                    Your order is empty. Add a pizza to see pairing recommendations.
                </div>
            `;
            if (subtotalEl) subtotalEl.textContent = '¥0';
            if (totalEl) totalEl.textContent = '¥0';
            if (counter) counter.textContent = '(0)';
            generatePairing();
            return;
        }

        let subtotal = 0;
        let html = '';

        cart.forEach((item, idx) => {
            subtotal += item.price * item.qty;
            html += `
                <div class="cart-item d-flex flex-column" style="animation: slideIn 0.3s ease ${idx * 0.05}s both;">
                    <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
                        <div>
                            <div class="fw-bold">${item.name}</div>
                            <div class="small text-muted">¥${item.price.toLocaleString()} each</div>
                        </div>
                        <div class="text-end">
                            <div class="fw-bold">¥${(item.price * item.qty).toLocaleString()}</div>
                            <button class="btn btn-sm text-danger p-0 remove-item" data-index="${idx}">
                                <i class="bi bi-trash3"></i>
                            </button>
                        </div>
                    </div>
                    <div class="d-flex align-items-center justify-content-between flex-wrap gap-3">
                        <div class="qty-control d-flex align-items-center gap-2">
                            <button class="btn btn-outline-secondary btn-sm qty-btn" data-action="decrease" data-index="${idx}"><i class="bi bi-dash"></i></button>
                            <span class="qty-value">${item.qty}</span>
                            <button class="btn btn-outline-secondary btn-sm qty-btn" data-action="increase" data-index="${idx}"><i class="bi bi-plus"></i></button>
                        </div>
                        <div class="text-muted small">Subtotal: ¥${(item.price * item.qty).toLocaleString()}</div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        if (subtotalEl) subtotalEl.textContent = `¥${subtotal.toLocaleString()}`;
        if (totalEl) totalEl.textContent = `¥${subtotal.toLocaleString()}`;
        if (counter) {
            counter.textContent = `(${cart.reduce((acc, i) => acc + i.qty, 0)})`;
            counter.style.animation = 'pulse 0.3s ease';
            setTimeout(() => counter.style.animation = '', 300);
        }

        container.querySelectorAll('.qty-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index, 10);
                const item = cart[idx];
                if (!item) return;
                if (btn.dataset.action === 'increase') {
                    item.qty += 1;
                } else if (btn.dataset.action === 'decrease') {
                    item.qty = Math.max(1, item.qty - 1);
                }
                saveCart();
                updateCartUI();
            });
        });

        container.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index, 10);
                const itemName = cart[idx]?.name;
                cart.splice(idx, 1);
                saveCart();
                updateCartUI();
                if (itemName) window.showToast(`Removed ${itemName}`);
            });
        });

        generatePairing();
    }
    
    window.addToCart = function(name, price) {
        const existing = cart.find(item => item.name === name);
        if (existing) {
            existing.qty += 1;
        } else {
            cart.push({ name, price: parseFloat(price), qty: 1 });
        }
        saveCart();
        updateCartUI();
        window.showToast(`🍕 ${name} added to order`);
        
        const cartOffcanvas = document.getElementById('cartOffcanvas');
        if (cartOffcanvas) {
            new bootstrap.Offcanvas(cartOffcanvas).show();
        }
        
        if (!window.PIZZAS || window.PIZZAS.length === 0) {
            const cached = localStorage.getItem('emberPizzasCache');
            if (cached) {
                try {
                    const parsed = JSON.parse(cached);
                    window.PIZZAS = Array.isArray(parsed) ? parsed : (parsed.pizzas || []);
                } catch(e) {}
            }
        }
        
        // Force pairing generation after cart is opened
        setTimeout(() => generatePairing(), 100);
    };
    
    window.addSideToCart = function(name, price) {
        window.addToCart(name, price);
    };
    
    function generatePairing() {
        const pairingBox = document.getElementById('pairingBox');
        if (!pairingBox) return;
        
        const currentCart = JSON.parse(localStorage.getItem('emberCart')) || [];
        const lastItem = currentCart[currentCart.length - 1];
        
        if (!lastItem) {
            pairingBox.innerHTML = '';
            return;
        }
        
        console.log('🔍 Looking for pairing for:', lastItem.name);
        
        let pizzaItem = null;
        
        // Try multiple sources
        if (typeof window.PIZZAS !== 'undefined' && Array.isArray(window.PIZZAS) && window.PIZZAS.length > 0) {
            pizzaItem = window.PIZZAS.find(p => p.name === lastItem.name);
            if (pizzaItem) {
                console.log('Found in window.PIZZAS');
            }
        }
        
        // Try global PIZZAS (from menu page)
        if (!pizzaItem && typeof PIZZAS !== 'undefined' && Array.isArray(PIZZAS) && PIZZAS.length > 0) {
            pizzaItem = PIZZAS.find(p => p.name === lastItem.name);
            if (pizzaItem) console.log('Found in PIZZAS');
        }
        
        // Try localStorage cache
        if (!pizzaItem) {
            const cached = localStorage.getItem('emberPizzasCache');
            if (cached) {
                try {
                    const cachedPizzas = JSON.parse(cached);
                    const pizzasArray = Array.isArray(cachedPizzas) ? cachedPizzas : (cachedPizzas.pizzas || []);
                    pizzaItem = pizzasArray.find(p => p.name === lastItem.name);
                    if (pizzaItem) {
                        window.PIZZAS = pizzasArray;
                        console.log('Found in cache');
                    }
                } catch(e) {}
            }
        }
        
        // If still not found, fetch from API
        if (!pizzaItem) {
            console.log('⚠️ Pizza not found, fetching from API...');
            pairingBox.innerHTML = `
                <div class="pairing-card" style="opacity: 0.6;">
                    <div class="pairing-content p-3 text-center">
                        <div class="spinner-border spinner-border-sm text-secondary mb-2" role="status"></div>
                        <p class="small text-muted mb-0">Loading pairing...</p>
                    </div>
                </div>
            `;
            
            fetch('/api/pizzas/')
                .then(response => response.json())
                .then(data => {
                    const pizzasArray = Array.isArray(data) ? data : (data.pizzas || []);
                    if (pizzasArray.length > 0) {
                        window.PIZZAS = pizzasArray;
                        localStorage.setItem('emberPizzasCache', JSON.stringify(pizzasArray));
                        console.log('✅ PIZZAS loaded from API, retrying...');
                        generatePairing();
                    }
                })
                .catch(err => console.log('❌ Could not fetch pizzas:', err));
            return;
        }
        
        const pairingName = pizzaItem.recommended_pairing;
        
        // Check for empty, null, undefined, or containing " or "
        if (!pairingName || pairingName === 'null' || pairingName === 'None' || pairingName.includes(' or ')) {
            console.log('❌ No valid pairing found for:', lastItem.name);
            pairingBox.innerHTML = '';
            return;
        }
        
        const pairingPrice = pizzaItem.recommended_pairing_price || 0;
        
        // OPTIMIZED: Use a smaller, faster loading image approach
        let pairingImage = pizzaItem.recommended_pairing_image || pizzaItem.image || '';
        
        // If no image available, use a minimal placeholder (no external placeholder service)
        if (!pairingImage || pairingImage === 'null' || pairingImage === 'None') {
            // Use a data URI or inline SVG for instant loading
            pairingImage = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"%3E%3Crect width="100" height="100" fill="%23D35400"/%3E%3Ctext x="50" y="55" text-anchor="middle" fill="white" font-size="40"%3E🍷%3C/text%3E%3C/svg%3E';
        }
        
        // Preload the image before rendering (optional)
        const img = new Image();
        img.src = pairingImage;
        
        const pairingDescription = pizzaItem.recommended_pairing_description || 
                                `Pairs beautifully with ${pairingName}.`;
        
        const pairingButton = pairingPrice > 0 ? `
            <button class="btn btn-ember btn-sm" onclick="window.addSideToCart('${pairingName.replace(/'/g, "\\'")}', ${pairingPrice})">
                <i class="bi bi-plus-lg me-1"></i> Add (¥${pairingPrice.toLocaleString()})
            </button>
        ` : `
            <button class="btn btn-outline-secondary btn-sm" disabled>
                <i class="bi bi-info-circle me-1"></i> Suggested Pairing
            </button>
        `;
        
        // Use a simpler card layout with better image loading
        pairingBox.innerHTML = `
            <div class="pairing-card" style="animation: slideIn 0.4s ease;">
                <div class="pairing-image-wrapper" style="width: 80px; min-height: 80px; flex-shrink: 0;">
                    <img src="${pairingImage}" alt="${pairingName}" 
                        style="width: 100%; height: 80px; object-fit: cover; display: block;"
                        loading="lazy"
                        onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'%3E%3Crect width=\'100\' height=\'100\' fill=\'%23D35400\'/%3E%3Ctext x=\'50\' y=\'55\' text-anchor=\'middle\' fill=\'white\' font-size=\'40\'%3E🍷%3C/text%3E%3C/svg%3E'">
                </div>
                <div class="pairing-content" style="flex: 1; padding: 0.75rem;">
                    <div class="d-flex justify-content-between align-items-start gap-2 mb-2 flex-wrap">
                        <div>
                            <div class="text-uppercase small text-muted">Recommended Pairing</div>
                            <h6 class="mb-0" style="font-size: 0.9rem;">${escapeHtml(pairingName)}</h6>
                        </div>
                        ${pairingPrice > 0 ? `<span class="pairing-price" style="font-weight: 700; color: var(--ember); font-size: 0.9rem;">¥${pairingPrice.toLocaleString()}</span>` : ''}
                    </div>
                    <p class="pairing-description small mb-2" style="color: var(--ash); font-size: 0.75rem;">${escapeHtml(pairingDescription)}</p>
                    <div class="d-flex flex-wrap gap-2 align-items-center">
                        ${pairingButton}
                        <span class="text-muted small">Pairs with <strong>${escapeHtml(lastItem.name)}</strong></span>
                    </div>
                </div>
            </div>
        `;
    }

    // Add escapeHtml helper if not already present
    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // ==================== MAP FUNCTIONS ====================
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    window.showOriginMap = function(pizza, farm, lat, lng) {
        const pizzaNameEl = document.getElementById('originPizzaName');
        const farmLabelEl = document.getElementById('originFarmLabel');
        const storyEl = document.getElementById('originStory');
        const distanceEl = document.getElementById('originDistance');
        const farmBadge = document.querySelector('.origin-farm-badge');
        
        if (pizzaNameEl) pizzaNameEl.textContent = pizza;
        
        let cleanFarmName = farm;
        if (farm && farm.includes(',')) {
            cleanFarmName = farm.split(',')[0];
        }
        if (farmLabelEl) farmLabelEl.textContent = cleanFarmName;
        
        let pizzaItem = null;
        if (typeof window.PIZZAS !== 'undefined') {
            pizzaItem = window.PIZZAS.find(p => p.name === pizza);
        } else if (typeof PIZZAS !== 'undefined') {
            pizzaItem = PIZZAS.find(p => p.name === pizza);
        }
        
        if (storyEl) {
            storyEl.textContent = (pizzaItem && pizzaItem.farm_story) || 
                `${cleanFarmName} is a family-owned farm within 120km of Karuizawa.`;
        }
        
        if (farmBadge) {
            if (pizza.includes('Margherita') || pizza.includes('Marinara') || pizza.includes('Potato') || pizza.includes('Field')) {
                farmBadge.innerHTML = '<i class="bi bi-tree-fill"></i> Vegetable Farm';
            } else if (pizza.includes('Diavola') || pizza.includes('Ember')) {
                farmBadge.innerHTML = '<i class="bi bi-egg-fried"></i> Pork Farm';
            } else if (pizza.includes('Quattro') || pizza.includes('Bianca')) {
                farmBadge.innerHTML = '<i class="bi bi-cup-straw"></i> Dairy Farm';
            } else if (pizza.includes('Funghi') || pizza.includes('Root')) {
                farmBadge.innerHTML = '<i class="bi bi-flower1"></i> Mushroom Forest';
            } else {
                farmBadge.innerHTML = '<i class="bi bi-tree-fill"></i> Partner Farm';
            }
        }
        
        const karuizawaLat = 36.348;
        const karuizawaLng = 138.597;
        const distance = calculateDistance(karuizawaLat, karuizawaLng, lat, lng);
        if (distanceEl) {
            distanceEl.textContent = `${Math.round(distance)}km`;
        }
        
        const modalElement = document.getElementById('originModal');
        if (!modalElement) return;
        
        if (mapInstance) {
            mapInstance.remove();
            mapInstance = null;
        }
        
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        modalElement.addEventListener('shown.bs.modal', function onModalShown() {
            setTimeout(() => {
                const mapContainer = document.getElementById('originMap');
                if (mapContainer && !mapInstance) {
                    try {
                        mapInstance = L.map('originMap').setView([lat, lng], 13);
                        
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                            maxZoom: 19,
                            minZoom: 3
                        }).addTo(mapInstance);
                        
                        const marker = L.marker([lat, lng]).addTo(mapInstance);
                        marker.bindPopup(`
                            <div style="text-align: center; padding: 0.25rem;">
                                <strong style="color: #D35400;">${cleanFarmName}</strong><br>
                                <small>${Math.round(distance)}km from Karuizawa</small>
                            </div>
                        `).openPopup();
                        
                        L.circle([lat, lng], {
                            radius: 3000,
                            color: '#D35400',
                            weight: 1,
                            opacity: 0.4,
                            fillColor: '#D35400',
                            fillOpacity: 0.05
                        }).addTo(mapInstance);
                        
                    } catch (error) {
                        console.error('Error initializing map:', error);
                    }
                }
            }, 200);
            
            modalElement.removeEventListener('shown.bs.modal', onModalShown);
        });
    };
    
    function initMiniMap() {
        const mapContainer = document.getElementById('miniMap');
        if (!mapContainer) return;
        
        const karuizawaLat = 36.348;
        const karuizawaLng = 138.597;
        
        miniMapInstance = L.map('miniMap').setView([karuizawaLat, karuizawaLng], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(miniMapInstance);
        L.marker([karuizawaLat, karuizawaLng]).addTo(miniMapInstance)
            .bindPopup('<b>Ember & Root</b><br>Karuizawa, Nagano').openPopup();
    }

    // ==================== CHECKOUT ====================
    function populateCheckoutModal() {
        const container = document.getElementById('checkoutOrderItems');
        const subtotalEl = document.getElementById('checkoutSubtotal');
        const totalEl = document.getElementById('checkoutTotal');
        
        if (!container) return;
        
        let subtotal = 0;
        let html = '';
        
        cart.forEach(item => {
            subtotal += item.price * item.qty;
            html += `
                <div class="checkout-item">
                    <div class="checkout-item-name">
                        <span class="checkout-item-qty">${item.qty}x</span>
                        <span>${item.name}</span>
                    </div>
                    <span class="checkout-item-price">¥${(item.price * item.qty).toLocaleString()}</span>
                </div>
            `;
        });
        
        container.innerHTML = html || '<p class="text-muted text-center py-3">No items in cart</p>';
        if (subtotalEl) subtotalEl.textContent = `¥${subtotal.toLocaleString()}`;
        if (totalEl) totalEl.textContent = `¥${subtotal.toLocaleString()}`;
        
        const confirmCheckbox = document.getElementById('confirmPickup');
        const confirmBtn = document.getElementById('confirmCheckoutBtn');
        
        if (confirmCheckbox) {
            confirmCheckbox.checked = false;
            const newCheckbox = confirmCheckbox.cloneNode(true);
            confirmCheckbox.parentNode.replaceChild(newCheckbox, confirmCheckbox);
            
            newCheckbox.addEventListener('change', function() {
                const btn = document.getElementById('confirmCheckoutBtn');
                if (btn) {
                    btn.disabled = !this.checked;
                    btn.style.opacity = this.checked ? '1' : '0.6';
                }
            });
        }
        
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.style.opacity = '0.6';
            
            const newBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
            
            newBtn.addEventListener('click', processCheckout);
        }
    }

    function processCheckout(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';
        
        const instructions = document.getElementById('checkoutInstructions')?.value || '';
        
        let csrfToken = window.csrfToken || '';
        if (!csrfToken) {
            const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
            if (cookieMatch) csrfToken = cookieMatch[1];
        }
        
        const orderData = {
            items: cart,
            subtotal: cart.reduce((acc, i) => acc + (i.price * i.qty), 0),
            total: cart.reduce((acc, i) => acc + (i.price * i.qty), 0),
            instructions: instructions
        };
        
        fetch('/ajax/place-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(data => {
            const checkoutModal = bootstrap.Modal.getInstance(document.getElementById('checkoutModal'));
            if (checkoutModal) checkoutModal.hide();
            
            if (data.success) {
                document.getElementById('successOrderNumber').textContent = `Order #${data.order_number}`;
                
                const successModal = new bootstrap.Modal(document.getElementById('orderSuccessModal'));
                successModal.show();
                
                cart = [];
                saveCart();
                updateCartUI();
                
                const cartOffcanvas = bootstrap.Offcanvas.getInstance(document.getElementById('cartOffcanvas'));
                if (cartOffcanvas) cartOffcanvas.hide();
                
                window.showToast(`✅ ${data.message}`);
            } else {
                window.showToast(data.message || 'Error placing order', 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Checkout error:', error);
            window.showToast('Network error. Please try again.', 'error');
            
            const checkoutModal = bootstrap.Modal.getInstance(document.getElementById('checkoutModal'));
            if (checkoutModal) checkoutModal.hide();
            
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }

    window.initCheckout = function() {
        const checkoutBtn = document.getElementById('checkoutBtn');
        if (!checkoutBtn) return;
        
        const newBtn = checkoutBtn.cloneNode(true);
        checkoutBtn.parentNode.replaceChild(newBtn, checkoutBtn);
        
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (cart.length === 0) {
                window.showToast('🍕 Add something first. The oven is hot!');
                return;
            }
            
            const authArea = document.getElementById('authArea');
            const isAuthenticated = authArea && authArea.querySelector('.user-dropdown') !== null;
            
            if (!isAuthenticated) {
                window.showToast('Please sign in to complete your order');
                window.location.href = '/auth/';
                return;
            }
            
            populateCheckoutModal();
            
            const cartOffcanvas = bootstrap.Offcanvas.getInstance(document.getElementById('cartOffcanvas'));
            if (cartOffcanvas) cartOffcanvas.hide();
            
            const checkoutModal = new bootstrap.Modal(document.getElementById('checkoutModal'));
            checkoutModal.show();
        });
    };

    // ==================== AUTHENTICATION ====================
    function setupDjangoDropdown() {
        const dropdownBtn = document.getElementById('userDropdown');
        if (!dropdownBtn) return;
        
        dropdownBtn.removeAttribute('data-bs-toggle');
        
        const newBtn = dropdownBtn.cloneNode(true);
        if (dropdownBtn.parentNode) {
            dropdownBtn.parentNode.replaceChild(newBtn, dropdownBtn);
        }
        
        const menu = newBtn.nextElementSibling;
        if (!menu || !menu.classList.contains('dropdown-menu')) return;
        
        function toggleMenu(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (menu.classList.contains('show')) {
                menu.classList.remove('show');
                menu.style.display = 'none';
                newBtn.setAttribute('aria-expanded', 'false');
            } else {
                document.querySelectorAll('.dropdown-menu.show').forEach(m => {
                    if (m !== menu) {
                        m.classList.remove('show');
                        m.style.display = 'none';
                        const btn = m.closest('.user-dropdown')?.querySelector('.dropdown-toggle');
                        if (btn) btn.setAttribute('aria-expanded', 'false');
                    }
                });
                
                menu.classList.add('show');
                menu.style.display = 'block';
                newBtn.setAttribute('aria-expanded', 'true');
            }
        }
        
        newBtn.addEventListener('click', toggleMenu);
        
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.user-dropdown')) {
                menu.classList.remove('show');
                menu.style.display = 'none';
                newBtn.setAttribute('aria-expanded', 'false');
            }
        });
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                menu.classList.remove('show');
                menu.style.display = 'none';
                newBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // ==================== LOADING SCREEN ====================
    function hideLoadingScreen() {
        const screen = document.getElementById('globalLoadingScreen');
        if (!screen) return;
        screen.style.opacity = '0';
        screen.style.pointerEvents = 'none';
        setTimeout(() => {
            if (screen.parentNode) screen.parentNode.removeChild(screen);
        }, 500);
    }
    
    window.addEventListener('load', hideLoadingScreen);

    // ==================== ENHANCED ANIMATIONS ====================
    
    // Scroll progress bar
    function initScrollProgress() {
        const progressBar = document.createElement('div');
        progressBar.className = 'scroll-progress';
        document.body.appendChild(progressBar);
        
        window.addEventListener('scroll', () => {
            const winScroll = document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        });
    }
    
    // Particle background effect
    function initParticleBackground(containerSelector = '.hero-section') {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        container.style.position = 'relative';
        container.style.overflow = 'hidden';
        
        const particleContainer = document.createElement('div');
        particleContainer.className = 'particle-bg';
        container.appendChild(particleContainer);
        
        function createParticle() {
            const particle = document.createElement('div');
            particle.className = 'particle';
            const size = Math.random() * 6 + 2;
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 5 + 's';
            particle.style.animationDuration = Math.random() * 4 + 3 + 's';
            particleContainer.appendChild(particle);
            
            setTimeout(() => particle.remove(), 8000);
        }
        
        setInterval(createParticle, 800);
    }
    
    // Ripple effect on buttons
    function initRippleEffect() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-ember, .btn-outline-ember');
            if (!btn) return;
            
            const ripple = document.createElement('span');
            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.position = 'absolute';
            ripple.style.width = size + 'px';
            ripple.style.height = size + 'px';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.4)';
            ripple.style.top = y + 'px';
            ripple.style.left = x + 'px';
            ripple.style.pointerEvents = 'none';
            ripple.style.animation = 'ripple 0.6s linear forwards';
            
            btn.style.position = 'relative';
            btn.style.overflow = 'hidden';
            btn.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    }
    
    // Intersection Observer for scroll-triggered animations
    function initScrollTriggerAnimations() {
        const elements = document.querySelectorAll('.pizza-card, .testimonial-card, .philosophy-card, .stat-badge, .hero-section, .section-header');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal-text');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        elements.forEach(el => {
            el.style.opacity = '0';
            observer.observe(el);
        });
    }
    
    // Smooth number counter animation
    function animateNumber(element, start, end, duration = 1000) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                element.textContent = end.toLocaleString();
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, 16);
    }
    
    // Counter animation for stats
    function initStatsCounter() {
        const stats = document.querySelectorAll('.stat-badge strong, .distance-number');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const targetValue = parseInt(el.textContent.replace(/,/g, ''));
                    if (!isNaN(targetValue)) {
                        animateNumber(el, 0, targetValue, 1500);
                    }
                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.5 });
        
        stats.forEach(stat => observer.observe(stat));
    }
    
    // Parallax scroll effect
    function initParallax() {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const hero = document.querySelector('.hero-section');
            const heroImage = document.querySelector('.hero-image-wrapper img');
            
            if (hero) {
                hero.style.transform = `translateY(${scrolled * 0.3}px)`;
            }
            if (heroImage) {
                heroImage.style.transform = `translateY(${scrolled * 0.2}px)`;
            }
        });
    }
    
    // Staggered fade-in for grid
    function initStaggeredFade() {
        const containers = document.querySelectorAll('.row.g-4, .row.g-5');
        containers.forEach(container => {
            container.classList.add('stagger-fade');
        });
    }
    
    // Hover lift for cards
    function initHoverLift() {
        const cards = document.querySelectorAll('.pizza-card, .testimonial-card, .philosophy-card');
        cards.forEach(card => {
            card.classList.add('hover-lift');
        });
    }
    
    // Image zoom effect
    function initImageZoom() {
        const imageContainers = document.querySelectorAll('.pizza-image-container, .hero-image-wrapper');
        imageContainers.forEach(container => {
            container.classList.add('image-zoom-container');
        });
    }
    
    // Notification badge animation for cart
    function animateCartBadge() {
        const cartCounter = document.getElementById('cartCounter');
        if (!cartCounter) return;
        
        const observer = new MutationObserver(() => {
            cartCounter.classList.add('notification-badge');
            setTimeout(() => cartCounter.classList.remove('notification-badge'), 500);
        });
        
        observer.observe(cartCounter, { childList: true, subtree: true, characterData: true });
    }
    
    // Smooth page transitions
    function initPageTransition() {
        document.body.classList.add('page-transition');
        
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    // Loading skeleton for images
    function initImageLoadingSkeleton() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.complete) {
                const parent = img.parentElement;
                const skeleton = document.createElement('div');
                skeleton.className = 'skeleton';
                skeleton.style.position = 'absolute';
                skeleton.style.top = '0';
                skeleton.style.left = '0';
                skeleton.style.width = '100%';
                skeleton.style.height = '100%';
                skeleton.style.zIndex = '1';
                parent.style.position = 'relative';
                parent.appendChild(skeleton);
                
                img.addEventListener('load', () => skeleton.remove());
            }
        });
    }
    
    // Hover glow effect
    function initHoverGlow() {
        const elements = document.querySelectorAll('.pizza-card, .btn-ember, .btn-outline-ember');
        elements.forEach(el => {
            el.classList.add('hover-glow');
        });
    }
    
    // Sliding underline for nav links
    function initSlidingUnderline() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.add('sliding-underline');
        });
    }
    
    // Scroll animations for cards
    function initScrollAnimations() {
        const animatedElements = document.querySelectorAll(
            '.pizza-card, .testimonial-card, .philosophy-card, .stat-badge, .hero-title, .hero-subtitle, .section-title, .founder-quote'
        );
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.style.transition = 'opacity 0.6s cubic-bezier(0.165, 0.84, 0.44, 1), transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1)';
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        animatedElements.forEach(el => {
            if (el) {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                observer.observe(el);
            }
        });
    }

    // Initialize all enhanced animations
    function initEnhancedAnimations() {
        initScrollProgress();
        initParticleBackground();
        initRippleEffect();
        initScrollTriggerAnimations();
        initStatsCounter();
        initParallax();
        initStaggeredFade();
        initHoverLift();
        initImageZoom();
        animateCartBadge();
        initPageTransition();
        initImageLoadingSkeleton();
        initHoverGlow();
        initSlidingUnderline();
        initScrollAnimations();
        
        console.log('✨ Enhanced animations initialized!');
    }

    // ==================== INJECT ANIMATION STYLES ====================
    function injectAnimationStyles() {
        if (document.getElementById('ember-animations')) return;
        
        const style = document.createElement('style');
        style.id = 'ember-animations';
        style.textContent = `
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(40px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.15); }
            }
            @keyframes shimmer {
                0% { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }
            @keyframes ripple {
                0% { transform: scale(0); opacity: 0.5; }
                100% { transform: scale(4); opacity: 0; }
            }
            @keyframes slideIn {
                from { opacity: 0; transform: translateX(20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes revealText {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes floatParticle {
                0% { opacity: 0; transform: translateY(0) scale(0); }
                20% { opacity: 0.3; }
                80% { opacity: 0.1; }
                100% { opacity: 0; transform: translateY(-100px) scale(1); }
            }
            @keyframes typing {
                from { width: 0; }
                to { width: 100%; }
            }
            @keyframes blink-caret {
                from, to { border-color: transparent; }
                50% { border-color: var(--ember); }
            }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
            }
            @keyframes pageFadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .pizza-card, .testimonial-card, .philosophy-card {
                will-change: transform, opacity;
            }
            
            .btn-ember:active {
                transform: scale(0.96) !important;
            }
            
            .navbar-brand {
                transition: transform 0.3s ease;
            }
            
            .navbar-brand:hover {
                transform: scale(1.02);
            }
            
            .hero-image-wrapper img {
                transition: transform 0.8s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            
            .hero-image-wrapper:hover img {
                transform: scale(1.02);
            }
            
            /* Scroll Progress Bar */
            .scroll-progress {
                position: fixed;
                top: 0;
                left: 0;
                width: 0%;
                height: 3px;
                background: linear-gradient(90deg, var(--ember), var(--wheat));
                z-index: 10000;
                transition: width 0.1s ease;
            }
            
            /* Particle Background */
            .particle-bg {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 0;
            }
            
            .particle {
                position: absolute;
                background: radial-gradient(circle, var(--ember), transparent);
                border-radius: 50%;
                opacity: 0;
                animation: floatParticle 4s infinite ease-in-out;
            }
            
            /* Typewriter Effect */
            .typewriter {
                overflow: hidden;
                border-right: 2px solid var(--ember);
                white-space: nowrap;
                animation: typing 3.5s steps(40, end), blink-caret 0.75s step-end infinite;
            }
            
            /* Stagger Fade */
            .stagger-fade > * {
                opacity: 0;
                animation: fadeInUp 0.6s ease forwards;
            }
            
            .stagger-fade > *:nth-child(1) { animation-delay: 0.05s; }
            .stagger-fade > *:nth-child(2) { animation-delay: 0.1s; }
            .stagger-fade > *:nth-child(3) { animation-delay: 0.15s; }
            .stagger-fade > *:nth-child(4) { animation-delay: 0.2s; }
            .stagger-fade > *:nth-child(5) { animation-delay: 0.25s; }
            .stagger-fade > *:nth-child(6) { animation-delay: 0.3s; }
            
            /* Hover Lift */
            .hover-lift {
                transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.4s ease;
            }
            
            .hover-lift:hover {
                transform: translateY(-6px);
                box-shadow: 0 20px 30px rgba(0, 0, 0, 0.06);
            }
            
            /* Image Zoom */
            .image-zoom-container {
                position: relative;
                overflow: hidden;
            }
            
            .image-zoom-container img {
                transition: transform 0.5s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            
            .image-zoom-container:hover img {
                transform: scale(1.05);
            }
            
            /* Notification Badge */
            .notification-badge {
                animation: bounce 0.5s ease;
            }
            
            /* Page Transition */
            .page-transition {
                animation: pageFadeIn 0.5s ease;
            }
            
            /* Hover Glow */
            .hover-glow {
                transition: all 0.3s ease;
            }
            
            .hover-glow:hover {
                box-shadow: 0 0 20px rgba(211, 84, 0, 0.2);
                border-color: var(--ember);
            }
            
            /* Sliding Underline */
            .sliding-underline {
                position: relative;
            }
            
            .sliding-underline::after {
                content: '';
                position: absolute;
                bottom: -4px;
                left: 0;
                width: 0;
                height: 2px;
                background: var(--ember);
                transition: width 0.3s ease;
            }
            
            .sliding-underline:hover::after {
                width: 100%;
            }
            
            /* Reveal Text */
            .reveal-text {
                animation: revealText 0.8s cubic-bezier(0.165, 0.84, 0.44, 1) forwards !important;
            }
            
            /* Skeleton Loading */
            .skeleton {
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 4px;
            }
            
            /* Pairing Card */
            .pairing-card {
                display: flex;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                margin: 1rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            .pairing-image {
                width: 100px;
                min-height: 100px;
                background-size: cover;
                background-position: center;
            }
            .pairing-content {
                flex: 1;
                padding: 1rem;
            }
            .pairing-price {
                font-weight: 700;
                color: var(--ember);
                font-size: 1.1rem;
            }
            .pairing-description {
                font-size: 0.85rem;
                color: var(--ash);
                line-height: 1.4;
            }
        `;
        document.head.appendChild(style);
    }

    // ==================== INITIALIZATION ====================
    function init() {
        injectAnimationStyles();
        ensureSharedUI();
        updateCartUI();
        initMiniMap();
        initCheckout();
        initEnhancedAnimations();
        
        const originModal = document.getElementById('originModal');
        if (originModal) {
            originModal.addEventListener('shown.bs.modal', () => {
                if (mapInstance) mapInstance.invalidateSize();
            });
        }
        
        window.addEventListener('resize', () => {
            if (mapInstance) mapInstance.invalidateSize();
            if (miniMapInstance) miniMapInstance.invalidateSize();
        });
        
        // Add hover animation to stat badges
        document.querySelectorAll('.stat-badge').forEach(badge => {
            badge.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px)';
                this.style.transition = 'transform 0.2s ease';
                this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
            });
            badge.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
        
        console.log('🔥 Ember & Root - Ready to serve!');
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            setTimeout(setupDjangoDropdown, 100);
        });
    } else {
        init();
        setTimeout(setupDjangoDropdown, 100);
    }

    // Expose globally
    window.showOriginMap = window.showOriginMap;
    window.addToCart = window.addToCart;
    window.addSideToCart = window.addSideToCart;
    window.showToast = window.showToast;
    window.showModal = window.showModal;
    window.initCheckout = window.initCheckout;
    
})();