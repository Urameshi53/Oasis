document.addEventListener('DOMContentLoaded', function() {
    // Initialize Swiper for hero slider
    if (document.querySelector('.swiper-hero')) {
        const heroSwiper = new Swiper('.swiper-hero', {
            loop: true,
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
            },
            effect: 'fade',
            fadeEffect: {
                crossFade: true
            },
        });
    }

    // Initialize Swiper for product thumbnails
    if (document.querySelector('.swiper-thumbnails')) {
        const thumbSwiper = new Swiper('.swiper-thumbnails', {
            slidesPerView: 4,
            spaceBetween: 10,
            freeMode: true,
            watchSlidesProgress: true,
        });

        const mainSwiper = new Swiper('.swiper-main', {
            loop: true,
            spaceBetween: 10,
            thumbs: {
                swiper: thumbSwiper,
            },
        });
    }

    // Back to top button
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        });

        backToTop.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Product image zoom
    const productImages = document.querySelectorAll('.product-image img');
    productImages.forEach(img => {
        img.addEventListener('click', function() {
            this.classList.toggle('zoom');
        });
    });

    // Quantity buttons
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.quantity-input');
            let value = parseInt(input.value);
            
            if (this.classList.contains('minus') && value > 1) {
                input.value = value - 1;
            } else if (this.classList.contains('plus')) {
                input.value = value + 1;
            }
            
            // Trigger change event for any listeners
            input.dispatchEvent(new Event('change'));
        });
    });

    // Add to cart animation
    document.querySelectorAll('.add-to-basket').forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Add animation class
            this.classList.add('adding');
            
            // Update cart count in navbar
            setTimeout(() => {
                const cartCount = document.querySelector('.cart-count');
                if (cartCount) {
                    let count = parseInt(cartCount.textContent) || 0;
                    cartCount.textContent = count + 1;
                    cartCount.classList.add('animate-bounce');
                    
                    setTimeout(() => {
                        cartCount.classList.remove('animate-bounce');
                    }, 500);
                }
            }, 500);
            
            // Remove animation class
            setTimeout(() => {
                this.classList.remove('adding');
            }, 1000);
        });
    });

    // Price range slider
    const priceRange = document.getElementById('priceRange');
    if (priceRange) {
        noUiSlider.create(priceRange, {
            start: [0, 1000],
            connect: true,
            range: {
                'min': 0,
                'max': 1000
            },
            tooltips: true,
            format: {
                to: function(value) {
                    return '$' + Math.round(value);
                },
                from: function(value) {
                    return Number(value.replace('$', ''));
                }
            }
        });

        priceRange.noUiSlider.on('update', function(values) {
            const minPrice = document.getElementById('minPrice');
            const maxPrice = document.getElementById('maxPrice');
            if (minPrice) minPrice.value = values[0];
            if (maxPrice) maxPrice.value = values[1];
        });
    }

    // Product filter toggles
    document.querySelectorAll('.filter-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const filterContent = this.nextElementSibling;
            const icon = this.querySelector('i');
            
            if (filterContent.style.maxHeight) {
                filterContent.style.maxHeight = null;
                icon.className = 'bi bi-plus';
            } else {
                filterContent.style.maxHeight = filterContent.scrollHeight + 'px';
                icon.className = 'bi bi-dash';
            }
        });
    });

    // Wishlist toggle
    document.querySelectorAll('.wishlist-toggle').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.toggle('active');
            
            const icon = this.querySelector('i');
            if (this.classList.contains('active')) {
                icon.className = 'bi bi-heart-fill text-danger';
                // Show toast notification
                showToast('Added to wishlist!', 'success');
            } else {
                icon.className = 'bi bi-heart';
                showToast('Removed from wishlist', 'info');
            }
        });
    });

    // Compare products
    document.querySelectorAll('.compare-toggle').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.toggle('active');
            
            const icon = this.querySelector('i');
            if (this.classList.contains('active')) {
                icon.className = 'bi bi-check-circle-fill text-success';
                showToast('Added to compare', 'success');
            } else {
                icon.className = 'bi bi-arrow-left-right';
            }
        });
    });

    // Quick view modal
    document.querySelectorAll('.quick-view').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            // Load product data via AJAX and show modal
            fetch(`/api/products/${productId}/quick-view/`)
                .then(response => response.json())
                .then(data => {
                    // Populate modal with product data
                    showQuickViewModal(data);
                })
                .catch(error => console.error('Error:', error));
        });
    });

    // Image gallery thumbnail click
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.addEventListener('click', function() {
            const mainImage = document.querySelector('.main-product-image');
            if (mainImage) {
                const newSrc = this.querySelector('img').src;
                mainImage.src = newSrc;
                
                // Update active thumbnail
                document.querySelectorAll('.thumbnail').forEach(t => {
                    t.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Cart sidebar toggle
    const cartToggle = document.querySelector('.cart-toggle');
    const cartSidebar = document.getElementById('cartSidebar');
    if (cartToggle && cartSidebar) {
        cartToggle.addEventListener('click', function() {
            cartSidebar.classList.toggle('show');
        });
    }

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredInputs = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showToast('Please fill all required fields', 'error');
            }
        });
    });

    // Lazy loading images
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img.lazy');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => imageObserver.observe(img));
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
});

// Toast notification function
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000
    });
    
    toast.show();
    
    // Remove toast from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function getToastIcon(type) {
    const icons = {
        'success': 'bi-check-circle',
        'error': 'bi-x-circle',
        'warning': 'bi-exclamation-triangle',
        'info': 'bi-info-circle'
    };
    return icons[type] || 'bi-info-circle';
}

// Quick view modal function
function showQuickViewModal(product) {
    const modalHtml = `
        <div class="modal fade" id="quickViewModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-body">
                        <button type="button" class="btn-close position-absolute top-0 end-0 m-3" data-bs-dismiss="modal"></button>
                        <div class="row">
                            <div class="col-md-6">
                                <img src="${product.image}" class="img-fluid rounded" alt="${product.title}">
                            </div>
                            <div class="col-md-6">
                                <h5 class="fw-bold">${product.title}</h5>
                                <div class="product-price-lg mb-3">${product.price}</div>
                                <div class="product-rating mb-3">
                                    <div class="rating-stars">
                                        ${getStarRating(product.rating)}
                                    </div>
                                    <span class="rating-count">(${product.review_count} reviews)</span>
                                </div>
                                <p class="text-muted mb-4">${product.description}</p>
                                <form class="mb-4">
                                    <div class="row g-3">
                                        ${product.variants ? getVariantOptions(product.variants) : ''}
                                        <div class="col-12">
                                            <div class="input-group" style="max-width: 200px;">
                                                <button type="button" class="btn btn-outline-secondary quantity-btn minus">
                                                    <i class="bi bi-dash"></i>
                                                </button>
                                                <input type="number" class="form-control text-center quantity-input" value="1" min="1">
                                                <button type="button" class="btn btn-outline-secondary quantity-btn plus">
                                                    <i class="bi bi-plus"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </form>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-primary btn-lg flex-fill add-to-basket">
                                        <i class="bi bi-cart-plus me-2"></i>Add to Cart
                                    </button>
                                    <button class="btn btn-outline-secondary wishlist-toggle">
                                        <i class="bi bi-heart"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('quickViewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM and show it
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
    modal.show();
}

function getStarRating(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.floor(rating)) {
            stars += '<i class="bi bi-star-fill"></i>';
        } else if (i === Math.ceil(rating) && !Number.isInteger(rating)) {
            stars += '<i class="bi bi-star-half"></i>';
        } else {
            stars += '<i class="bi bi-star"></i>';
        }
    }
    return stars;
}

function getVariantOptions(variants) {
    let options = '';
    variants.forEach(variant => {
        options += `
            <div class="col-12">
                <label class="form-label">${variant.name}</label>
                <select class="form-select">
                    ${variant.options.map(option => `<option value="${option.value}">${option.label}</option>`).join('')}
                </select>
            </div>
        `;
    });
    return options;
}