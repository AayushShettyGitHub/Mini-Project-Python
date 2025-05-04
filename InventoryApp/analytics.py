from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import Product, Category, Order, SalesData
from sqlalchemy import func
from datetime import datetime, timedelta
from ml import predict_stock_needs, generate_recommendations

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    # Count totals for dashboard
    product_count = Product.query.count()
    category_count = Category.query.count()
    
    # Calculate total sales and revenue
    total_orders = Order.query.filter_by(status='paid').count()
    total_revenue = Order.query.filter_by(status='paid').with_entities(
        func.sum(Order.total_amount)).scalar() or 0
    
    # Get low stock products
    low_stock_products = Product.query.filter(Product.stock < 10).all()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get stock prediction data
    stock_predictions = predict_stock_needs()
    
    return render_template(
        'dashboard.html',
        product_count=product_count,
        category_count=category_count,
        total_orders=total_orders,
        total_revenue=total_revenue,
        low_stock_products=low_stock_products,
        recent_orders=recent_orders,
        stock_predictions=stock_predictions,
        title='Dashboard'
    )

@analytics_bp.route('/analytics')
@login_required
def analytics():
    # Get date range for analytics
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get product recommendations
    recommendations = generate_recommendations()
    
    return render_template('analytics.html', start_date=start_date, end_date=end_date, 
                          recommendations=recommendations, title='Analytics')

@analytics_bp.route('/api/sales_by_category')
@login_required
def sales_by_category():
    # Get sales aggregated by category
    categories = Category.query.all()
    result = []
    
    for category in categories:
        # Sum up sales for products in this category
        sales = db.session.query(func.sum(OrderItem.quantity)).join(
            Product, OrderItem.product_id == Product.id
        ).filter(
            Product.category_id == category.id
        ).scalar() or 0
        
        result.append({
            'category': category.name,
            'sales': sales
        })
    
    return jsonify(result)

@analytics_bp.route('/api/sales_over_time')
@login_required
def sales_over_time():
    # Get daily sales for the last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Initialize the result with all dates
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'sales': 0
        })
        current_date += timedelta(days=1)
    
    # Get actual sales data
    daily_sales = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        Order.status == 'paid',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).group_by(
        func.date(Order.created_at)
    ).all()
    
    # Update the dates with actual sales data
    for sale in daily_sales:
        date_str = sale.date.strftime('%Y-%m-%d')
        for date_data in dates:
            if date_data['date'] == date_str:
                date_data['sales'] = float(sale.total)
                break
    
    return jsonify(dates)

@analytics_bp.route('/api/stock_levels')
@login_required
def stock_levels():
    # Get current stock levels for all products
    products = Product.query.all()
    result = []
    
    for product in products:
        result.append({
            'product': product.name,
            'stock': product.stock
        })
    
    return jsonify(result)

@analytics_bp.route('/api/product_performance')
@login_required
def product_performance():
    # Get sales performance for top products
    product_sales = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('quantity'),
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).group_by(
        Product.id
    ).order_by(
        func.sum(OrderItem.quantity * OrderItem.price).desc()
    ).limit(10).all()
    
    result = []
    for product in product_sales:
        result.append({
            'product': product.name,
            'quantity': product.quantity,
            'revenue': float(product.revenue)
        })
    
    return jsonify(result)
