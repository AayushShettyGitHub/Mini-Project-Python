import uuid
import qrcode
import io
import base64
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from models import Product, Order, OrderItem, SalesData
from app import db

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales')
@login_required
def sales():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('sales.html', orders=orders, title='Sales')

@sales_bp.route('/sales/order/<string:order_number>')
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('sales.html', order=order, title=f'Order {order.order_number}', order_detail=True)

@sales_bp.route('/sales/history')
@login_required
def order_history():
    # Get all orders with pagination
    page = request.args.get('page', 1, type=int)
    orders = Order.query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('order_history.html', orders=orders, title='Order History')

@sales_bp.route('/sales/generate_qr/<string:order_number>')
@login_required
def generate_qr(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Generate QR code data (with payment URL)
    qr_data = request.host_url + 'buyer/payment/' + order.order_number
    
    # Create QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = io.BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('sales.html', 
                          order=order, 
                          qr_code=img_str, 
                          qr_url=qr_data, 
                          title=f'QR Code for Order {order.order_number}',
                          qr_mode=True)

@sales_bp.route('/api/verify_payment/<string:order_number>', methods=['POST'])
def verify_payment(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    if order.status == 'paid':
        return jsonify({'status': 'already_paid'})
    
    # In a real application, you'd verify payment with a payment processor
    # For this simulation, we'll just mark it as paid
    
    order.status = 'paid'
    order.paid_at = datetime.utcnow()
    
    # Update inventory and sales data
    for item in order.items:
        product = Product.query.get(item.product_id)
        product.stock -= item.quantity
        
        # Update or create sales data record
        today = datetime.utcnow().date()
        sales_record = SalesData.query.filter_by(product_id=product.id, date=today).first()
        
        if sales_record:
            sales_record.quantity_sold += item.quantity
        else:
            sales_record = SalesData(
                product_id=product.id,
                date=today,
                quantity_sold=item.quantity
            )
            db.session.add(sales_record)
    
    db.session.commit()
    
    return jsonify({'status': 'success'})

@sales_bp.route('/api/sales_data')
@login_required
def sales_data():
    # Get sales data for charts
    # This can be customized based on required time period
    sales_records = SalesData.query.all()
    sales_by_product = {}
    sales_by_date = {}
    
    for record in sales_records:
        product = Product.query.get(record.product_id)
        date_str = record.date.strftime('%Y-%m-%d')
        
        # Sales by product
        if product.name in sales_by_product:
            sales_by_product[product.name] += record.quantity_sold
        else:
            sales_by_product[product.name] = record.quantity_sold
        
        # Sales by date
        if date_str in sales_by_date:
            sales_by_date[date_str] += record.quantity_sold
        else:
            sales_by_date[date_str] = record.quantity_sold
    
    return jsonify({
        'by_product': sales_by_product,
        'by_date': sales_by_date
    })
