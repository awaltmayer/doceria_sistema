// Sistema de Doceria - JavaScript Interativo

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Form validation for login and register
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('input[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#f56565';
                } else {
                    field.style.borderColor = '';
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Por favor, preencha todos os campos obrigatórios.', 'error');
            }
        });
    });

    // Enhanced quantity input handling
    const quantityInputs = document.querySelectorAll('.quantidade-input');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            if (this.value < 0) {
                this.value = 0;
            }
            if (this.value > 50) {
                this.value = 50;
                showNotification('Quantidade máxima é 50 unidades por produto.', 'warning');
            }
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add loading state to buttons
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<span>Processando...</span>';
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = this.innerHTML.replace('Processando...', this.textContent);
            }, 2000);
        });
    });

    // Checkout confirmation
    const checkoutForm = document.querySelector('form[action*="checkout"]');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (confirm('Confirma a finalização do pedido?')) {
                this.submit();
            }
        });
    }

    // Add animation to cards
    const cards = document.querySelectorAll('.trufa-card, .cart-container, .auth-container');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
    });
});

// Utility function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash flash-${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.flash-messages') || document.body;
    container.appendChild(notification);
    
    setTimeout(function() {
        notification.style.opacity = '0';
        setTimeout(function() {
            notification.remove();
        }, 300);
    }, 4000);
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to submit forms
    if (e.ctrlKey && e.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            activeForm.submit();
        }
    }
    
    // Escape to clear focus
    if (e.key === 'Escape') {
        document.activeElement.blur();
    }
});

// Enhanced cart functionality
function updateCartDisplay() {
    const cartItems = document.querySelectorAll('.cart-table tbody tr');
    const cartTotal = document.querySelector('.cart-total');
    
    if (cartItems.length === 0 && cartTotal) {
        showNotification('Carrinho vazio!', 'info');
    }
}

// Call on page load
updateCartDisplay();