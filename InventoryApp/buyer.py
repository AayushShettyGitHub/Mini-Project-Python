import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from models import Product, Category, Order, OrderItem
from app import db

buyer_bp = Blueprint('buyer', __name__, url_prefix='/buyer')

@buyer_bp.route('/')
def home():
    categories = Category.query.all()
    products = Product.query.filter(Product.stock > 0).all()
    return render_template('buyer/home.html', products=products, categories=categories, title='Shop Products')

@buyer_bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    # Get recommended products
    recommended = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.stock > 0
    ).limit(4).all()
    return render_template('buyer/home.html', product=product, recommended=recommended, title=product.name, detail_mode=True)

@buyer_bp.route('/category/<int:id>')
def category_products(id):
    category = Category.query.get_or_404(id)
    products = Product.query.filter_by(category_id=id).filter(Product.stock > 0).all()
    categories = Category.query.all()
    return render_template('buyer/home.html', products=products, current_category=category, categories=categories, title=f'Category: {category.name}')

@buyer_bp.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    product = Product.query.get_or_404(id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        flash('Quantity must be positive', 'danger')
        return redirect(url_for('buyer.product_detail', id=id))
    
    if quantity > product.stock:
        flash(f'Only {product.stock} items available', 'warning')
        quantity = product.stock
    
    # Initialize cart in session if not present
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if product already in cart
    cart = session['cart']
    product_in_cart = False
    
    for item in cart:
        if item['id'] == id:
            item['quantity'] += quantity
            if item['quantity'] > product.stock:
                item['quantity'] = product.stock
            product_in_cart = True
            break
    
    # If product not in cart, add it
    if not product_in_cart:
        cart.append({
            'id': id,
            'name': product.name,
            'price': product.price,
            'quantity': quantity
        })
    
    session['cart'] = cart
    flash(f'Added {quantity} {product.name} to cart', 'success')
    
    return redirect(url_for('buyer.cart'))

@buyer_bp.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('buyer/cart.html', cart_items=cart_items, total=total, title='Shopping Cart')

@buyer_bp.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', [])
    item_id = int(request.form.get('id'))
    action = request.form.get('action')
    
    for i, item in enumerate(cart):
        if item['id'] == item_id:
            if action == 'increase':
                product = Product.query.get(item_id)
                if item['quantity'] < product.stock:
                    item['quantity'] += 1
            elif action == 'decrease':
                if item['quantity'] > 1:
                    item['quantity'] -= 1
                else:
                    cart.pop(i)
            elif action == 'remove':
                cart.pop(i)
            break
    
    session['cart'] = cart
    return redirect(url_for('buyer.cart'))

@buyer_bp.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared', 'info')
    return redirect(url_for('buyer.home'))

@buyer_bp.route('/checkout')
def checkout():
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('buyer.home'))
    
    # Verify stock availability before checkout
    for item in cart_items:
        product = Product.query.get(item['id'])
        if product.stock < item['quantity']:
            flash(f'Only {product.stock} of {product.name} available. Please update your cart.', 'warning')
            return redirect(url_for('buyer.cart'))
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Generate a unique order number
    order_number = str(uuid.uuid4())[:8].upper()
    
    # Create order in database
    order = Order(
        order_number=order_number,
        total_amount=total,
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    
    # Add order items
    for item in cart_items:
        order_item = OrderItem(
            order=order,
            product_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    # Clear cart after successful checkout
    session.pop('cart', None)
    
    # Generate QR code data (with payment URL)
    qr_data = request.host_url + 'buyer/payment/' + order_number
    
    return render_template('buyer/checkout.html', order=order, order_items=order.items, qr_url=qr_data, title='Checkout')

@buyer_bp.route('/payment/<string:order_number>')
def payment(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    if order.status == 'paid':
        flash('This order has already been paid', 'info')
    
    return render_template('buyer/payment.html', order=order, order_items=order.items, title='Payment')

@buyer_bp.route('/process_payment/<string:order_number>', methods=['POST'])
def process_payment(order_number):
    # In a real application, this would interact with a payment gateway
    # For this simulation, we'll just mark the order as paid
    
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    if order.status == 'paid':
        flash('This order has already been paid', 'info')
        return redirect(url_for('buyer.payment', order_number=order_number))
    
    # Update order status
    order.status = 'paid'
    order.paid_at = datetime.utcnow()
    
    # Update inventory
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product.stock >= item.quantity:
            product.stock -= item.quantity
        else:
            # Handle insufficient stock (unlikely due to pre-checkout verification)
            flash(f'Insufficient stock for {product.name}', 'danger')
            return redirect(url_for('buyer.payment', order_number=order_number))
    
    db.session.commit()
    flash('Payment successful! Thank you for your purchase.', 'success')
    
    return redirect(url_for('buyer.payment_success', order_number=order_number))

@buyer_bp.route('/payment_success/<string:order_number>')
def payment_success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('buyer/payment.html', order=order, order_items=order.items, success=True, title='Payment Successful')
