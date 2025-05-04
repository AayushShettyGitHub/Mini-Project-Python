from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from models import Product, Category
from app import db

inventory_bp = Blueprint('inventory', __name__)

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    def validate_name(self, name):
        category = Category.query.filter_by(name=name.data).first()
        if category and category.id != self.id:
            raise ValidationError('This category name already exists.')

@inventory_bp.route('/inventory')
@login_required
def inventory():
    products = Product.query.all()
    return render_template('inventory.html', products=products, title='Inventory')

@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    # If no categories exist, prompt to create one first
    if not form.category_id.choices:
        flash('Please create a category first.', 'warning')
        return redirect(url_for('inventory.add_category'))
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('inventory.inventory'))
    
    return render_template('inventory.html', form=form, title='Add Product', add_mode=True)

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('inventory.inventory'))
    
    return render_template('inventory.html', form=form, title='Edit Product', edit_mode=True)

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    try:
        # Fetch the product by id, or raise an error if not found
        product = Product.query.get_or_404(id)
        
        # If the product is found, delete it from the database
        db.session.delete(product)
        db.session.commit()
        
        # Provide success feedback to the user
        flash('Product deleted successfully!', 'success')
        
        # Redirect back to the inventory page
        return redirect(url_for('inventory.inventory'))
    
    except Exception as e:
        # Handle unexpected errors
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
        return redirect(url_for('inventory.inventory'))



@inventory_bp.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('inventory.html', categories=categories, title='Categories', categories_mode=True)

@inventory_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('inventory.categories'))
    
    return render_template('inventory.html', cat_form=form, title='Add Category', add_category_mode=True)

@inventory_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    form.id = category.id  # For validation
    
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('inventory.categories'))
    
    return render_template('inventory.html', cat_form=form, title='Edit Category', edit_category_mode=True)

@inventory_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # Check if category has products
    if Product.query.filter_by(category_id=id).first():
        flash('Cannot delete category that has products. Remove or reassign products first.', 'danger')
        return redirect(url_for('inventory.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('inventory.categories'))

# API endpoints for inventory management (used by AJAX requests)
@inventory_bp.route('/api/inventory')
@login_required
def api_inventory():
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'category': product.category.name
        })
    return jsonify(result)
