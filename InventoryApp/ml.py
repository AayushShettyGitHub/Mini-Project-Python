import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from models import Product, Order, OrderItem, SalesData
from app import db

def prepare_sales_data():
    """Prepare sales data for ML models"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    products = Product.query.all()
    product_data = {}
    
    for product in products:
       
        sales_records = SalesData.query.filter(
            SalesData.product_id == product.id,
            SalesData.date >= start_date,
            SalesData.date <= end_date
        ).order_by(SalesData.date).all()
        
        # Create a time series of sales
        sales_timeseries = []
        current_date = start_date
        while current_date <= end_date:
            # Find sales for this date
            sales_for_date = next(
                (record.quantity_sold for record in sales_records if record.date == current_date),
                0
            )
            sales_timeseries.append(sales_for_date)
            current_date += timedelta(days=1)
        
        product_data[product.id] = {
            'name': product.name,
            'current_stock': product.stock,
            'sales_timeseries': sales_timeseries,
            'category_id': product.category_id
        }
    
    return product_data

def predict_stock_needs():
    """Predict stock needs using logistic regression"""
    product_data = prepare_sales_data()
    predictions = []
    
    for product_id, data in product_data.items():
        sales_timeseries = data['sales_timeseries']
        
        # Skip products with no sales history
        if sum(sales_timeseries) == 0:
            continue
        
        # Create features (we'll use a simple moving average of the last 7 days)
        X = []
        y = []
        
        for i in range(7, len(sales_timeseries)):
            # Feature: average sales of the previous 7 days
            X.append([np.mean(sales_timeseries[i-7:i])])
            # Target: did we sell more than the 7-day average?
            y.append(1 if sales_timeseries[i] > np.mean(sales_timeseries[i-7:i]) else 0)
        
        # If we don't have enough data points, make a simple prediction
        if len(X) < 2:
            # Predict based on the average daily sales
            avg_daily_sales = np.mean(sales_timeseries) if sales_timeseries else 0
            predicted_weekly_sales = avg_daily_sales * 7
            
            # If current stock is less than predicted weekly sales, recommend restocking
            if data['current_stock'] < predicted_weekly_sales:
                predictions.append({
                    'product_id': product_id,
                    'name': data['name'],
                    'current_stock': data['current_stock'],
                    'predicted_need': predicted_weekly_sales,
                    'restock_needed': True
                })
            continue
        
        try:
            # Use logistic regression to predict if sales will increase
            model = LogisticRegression(random_state=42)
            model.fit(X, y)
            
            # Predict using the most recent 7-day average
            recent_avg = np.mean(sales_timeseries[-7:])
            prediction = model.predict([[recent_avg]])[0]
            
            # Calculate predicted need based on recent average and prediction
            predicted_need = recent_avg * 7
            if prediction == 1:
                # If we predict an increase, add a buffer
                predicted_need *= 1.2
            
            # Round to whole number
            predicted_need = round(predicted_need)
            
            # Add prediction if restock is needed
            if data['current_stock'] < predicted_need:
                predictions.append({
                    'product_id': product_id,
                    'name': data['name'],
                    'current_stock': data['current_stock'],
                    'predicted_need': predicted_need,
                    'restock_needed': True
                })
        except Exception as e:
            # If model fails, use the simple prediction approach
            print(f"Error predicting stock for {data['name']}: {e}")
            avg_daily_sales = np.mean(sales_timeseries) if sales_timeseries else 0
            predicted_weekly_sales = avg_daily_sales * 7
            
            if data['current_stock'] < predicted_weekly_sales:
                predictions.append({
                    'product_id': product_id,
                    'name': data['name'],
                    'current_stock': data['current_stock'],
                    'predicted_need': predicted_weekly_sales,
                    'restock_needed': True
                })
    
    return predictions

def generate_recommendations():
    """Generate product recommendations using KNN"""
    # Get all completed orders
    orders = Order.query.filter_by(status='paid').all()
    
    if not orders:
        return []
    
    # Create a user-product matrix where each row is an order
    # and each column is a product (with the value being 1 if the product was in the order)
    products = Product.query.all()
    product_indices = {product.id: i for i, product in enumerate(products)}
    
    # Create a sparse matrix of orders x products
    order_product_matrix = np.zeros((len(orders), len(products)))
    order_indices = {order.id: i for i, order in enumerate(orders)}
    
    for order in orders:
        for item in order.items:
            if item.product_id in product_indices:
                order_product_matrix[order_indices[order.id], product_indices[item.product_id]] = 1
    
    # Skip if we don't have enough orders
    if len(orders) < 5:
        return []
    
    # Standardize the feature matrix
    scaler = StandardScaler()
    try:
        order_product_matrix_scaled = scaler.fit_transform(order_product_matrix)
    except:
        # If standardization fails, use the original matrix
        order_product_matrix_scaled = order_product_matrix
    
    # Train KNN model for recommendations
    try:
        knn = KNeighborsClassifier(n_neighbors=min(5, len(orders)))
        knn.fit(order_product_matrix_scaled, range(len(orders)))
        
        # For each product, find recommended products
        recommendations = []
        
        for product_id, product_idx in product_indices.items():
            # Skip if this product has never been bought
            if not any(row[product_idx] == 1 for row in order_product_matrix):
                continue
            
            # Find orders that included this product
            orders_with_product = [
                i for i, row in enumerate(order_product_matrix) if row[product_idx] == 1
            ]
            
            if not orders_with_product:
                continue
            
            # Find similar orders
            product_vector = np.zeros(len(products))
            product_vector[product_idx] = 1
            
            try:
                # Standardize the query vector
                product_vector_scaled = scaler.transform([product_vector])[0]
                
                # Find nearest neighbors
                distances, indices = knn.kneighbors([product_vector_scaled], n_neighbors=min(5, len(orders)))
                
                # Count products in similar orders
                product_counts = defaultdict(int)
                for order_idx in indices[0]:
                    order_products = np.where(order_product_matrix[order_idx] == 1)[0]
                    for prod_idx in order_products:
                        if prod_idx != product_idx:  # Exclude the product itself
                            product_id_from_idx = next(
                                (pid for pid, idx in product_indices.items() if idx == prod_idx),
                                None
                            )
                            if product_id_from_idx:
                                product_counts[product_id_from_idx] += 1
                
                # Get top 3 recommended products
                top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                
                if top_products:
                    product = Product.query.get(product_id)
                    recommended_products = [
                        {'id': rec_id, 'name': Product.query.get(rec_id).name} 
                        for rec_id, _ in top_products
                    ]
                    
                    recommendations.append({
                        'product_id': product_id,
                        'product_name': product.name,
                        'recommendations': recommended_products
                    })
            except Exception as e:
                print(f"Error generating recommendations for product {product_id}: {e}")
        
        return recommendations
    except Exception as e:
        print(f"Error in KNN algorithm: {e}")
        return []
