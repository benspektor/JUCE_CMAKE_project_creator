from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chocolate-bizz-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chocolate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ============ MODELS ============

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), default='יחידה')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipes = db.relationship('Recipe', backref='product', lazy=True)

class RawMaterial(db.Model):
    __tablename__ = 'raw_materials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), default='ק"ג')
    quantity = db.Column(db.Float, default=0)
    min_quantity = db.Column(db.Float, default=0)
    cost_per_unit = db.Column(db.Float, default=0)
    supplier = db.Column(db.String(100))

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_size = db.Column(db.Float, default=1)
    notes = db.Column(db.Text)
    ingredients = db.relationship('RecipeIngredient', backref='recipe', cascade='all, delete-orphan', lazy=True)

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    material = db.relationship('RawMaterial')

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='חדש')
    notes = db.Column(db.Text)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)

    @property
    def total(self):
        return sum(item.quantity * item.price for item in self.items)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

class Production(db.Model):
    __tablename__ = 'productions'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    production_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)
    cost = db.Column(db.Float, default=0)
    product = db.relationship('Product')

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='אחר')
    expense_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date, default=date.today, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    channel = db.Column(db.String(50), default='ישיר')
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date, default=date.today, nullable=False)
    supplier = db.Column(db.String(100))
    invoice_number = db.Column(db.String(50))
    category = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0)
    notes = db.Column(db.Text)
    items = db.relationship('PurchaseItem', backref='purchase', cascade='all, delete-orphan', lazy=True)

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    description = db.Column(db.String(200))
    material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=True)
    quantity = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, default=0)
    material = db.relationship('RawMaterial')


# ============ ROUTES ============

@app.route('/')
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)

    orders_today = Order.query.filter(func.date(Order.order_date) == today).count()

    monthly_revenue = db.session.query(
        func.sum(OrderItem.quantity * OrderItem.price)
    ).join(Order).filter(
        func.date(Order.order_date) >= month_start,
        Order.status != 'בוטל'
    ).scalar() or 0

    monthly_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(Expense.expense_date >= month_start).scalar() or 0

    low_stock = RawMaterial.query.filter(
        RawMaterial.min_quantity > 0,
        RawMaterial.quantity <= RawMaterial.min_quantity
    ).all()

    pending_orders = Order.query.filter(
        Order.status.in_(['חדש', 'בייצור'])
    ).order_by(Order.order_date.desc()).limit(5).all()

    recent_productions = Production.query.order_by(
        Production.production_date.desc()
    ).limit(5).all()

    return render_template('dashboard.html',
        orders_today=orders_today,
        monthly_revenue=monthly_revenue,
        monthly_expenses=monthly_expenses,
        monthly_profit=monthly_revenue - monthly_expenses,
        low_stock=low_stock,
        pending_orders=pending_orders,
        recent_productions=recent_productions
    )


# --- Products ---

@app.route('/products')
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=all_products)

@app.route('/products/add', methods=['POST'])
def add_product():
    p = Product(
        name=request.form['name'],
        description=request.form.get('description', ''),
        category=request.form.get('category', ''),
        price=float(request.form['price']),
        unit=request.form.get('unit', 'יחידה')
    )
    db.session.add(p)
    db.session.commit()
    flash('מוצר נוסף בהצלחה', 'success')
    return redirect(url_for('products'))

@app.route('/products/edit/<int:id>', methods=['POST'])
def edit_product(id):
    p = Product.query.get_or_404(id)
    p.name = request.form['name']
    p.description = request.form.get('description', '')
    p.category = request.form.get('category', '')
    p.price = float(request.form['price'])
    p.unit = request.form.get('unit', 'יחידה')
    db.session.commit()
    flash('מוצר עודכן בהצלחה', 'success')
    return redirect(url_for('products'))

@app.route('/products/toggle/<int:id>')
def toggle_product(id):
    p = Product.query.get_or_404(id)
    p.active = not p.active
    db.session.commit()
    return redirect(url_for('products'))

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('מוצר נמחק', 'warning')
    return redirect(url_for('products'))

@app.route('/api/product-price/<int:id>')
def get_product_price(id):
    p = Product.query.get_or_404(id)
    return jsonify({'price': p.price, 'unit': p.unit})


# --- Inventory ---

@app.route('/inventory')
def inventory():
    materials = RawMaterial.query.order_by(RawMaterial.name).all()
    return render_template('inventory.html', materials=materials)

@app.route('/inventory/add', methods=['POST'])
def add_material():
    m = RawMaterial(
        name=request.form['name'],
        unit=request.form.get('unit', 'ק"ג'),
        quantity=float(request.form.get('quantity', 0)),
        min_quantity=float(request.form.get('min_quantity', 0)),
        cost_per_unit=float(request.form.get('cost_per_unit', 0)),
        supplier=request.form.get('supplier', '')
    )
    db.session.add(m)
    db.session.commit()
    flash('חומר גלם נוסף', 'success')
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:id>', methods=['POST'])
def edit_material(id):
    m = RawMaterial.query.get_or_404(id)
    m.name = request.form['name']
    m.unit = request.form.get('unit', 'ק"ג')
    m.quantity = float(request.form.get('quantity', 0))
    m.min_quantity = float(request.form.get('min_quantity', 0))
    m.cost_per_unit = float(request.form.get('cost_per_unit', 0))
    m.supplier = request.form.get('supplier', '')
    db.session.commit()
    flash('חומר גלם עודכן', 'success')
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_material(id):
    m = RawMaterial.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    flash('חומר גלם נמחק', 'warning')
    return redirect(url_for('inventory'))


# --- Customers ---

@app.route('/customers')
def customers():
    all_customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/add', methods=['POST'])
def add_customer():
    c = Customer(
        name=request.form['name'],
        email=request.form.get('email', ''),
        phone=request.form.get('phone', ''),
        address=request.form.get('address', ''),
        notes=request.form.get('notes', '')
    )
    db.session.add(c)
    db.session.commit()
    flash('לקוח נוסף', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/edit/<int:id>', methods=['POST'])
def edit_customer(id):
    c = Customer.query.get_or_404(id)
    c.name = request.form['name']
    c.email = request.form.get('email', '')
    c.phone = request.form.get('phone', '')
    c.address = request.form.get('address', '')
    c.notes = request.form.get('notes', '')
    db.session.commit()
    flash('לקוח עודכן', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    c = Customer.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('לקוח נמחק', 'warning')
    return redirect(url_for('customers'))


# --- Orders ---

@app.route('/orders')
def orders():
    all_orders = Order.query.order_by(Order.order_date.desc()).all()
    all_customers = Customer.query.order_by(Customer.name).all()
    all_products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template('orders.html', orders=all_orders, customers=all_customers, products=all_products)

@app.route('/orders/add', methods=['POST'])
def add_order():
    o = Order(
        customer_id=int(request.form['customer_id']),
        delivery_date=datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date() if request.form.get('delivery_date') else None,
        notes=request.form.get('notes', ''),
        status='חדש'
    )
    db.session.add(o)
    db.session.flush()

    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('quantity[]')
    prices = request.form.getlist('price[]')

    for pid, qty, price in zip(product_ids, quantities, prices):
        if pid and qty:
            item = OrderItem(
                order_id=o.id,
                product_id=int(pid),
                quantity=float(qty),
                price=float(price)
            )
            db.session.add(item)

    db.session.commit()
    flash(f'הזמנה #{o.id} נוצרה בהצלחה', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/<int:id>')
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('order_detail.html', order=order)

@app.route('/orders/<int:id>/status', methods=['POST'])
def update_order_status(id):
    o = Order.query.get_or_404(id)
    o.status = request.form['status']
    db.session.commit()
    flash('סטטוס הזמנה עודכן', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/delete/<int:id>', methods=['POST'])
def delete_order(id):
    o = Order.query.get_or_404(id)
    db.session.delete(o)
    db.session.commit()
    flash('הזמנה נמחקה', 'warning')
    return redirect(url_for('orders'))


# --- Production ---

@app.route('/production')
def production():
    all_productions = Production.query.order_by(Production.production_date.desc()).all()
    all_products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template('production.html', productions=all_productions, products=all_products)

@app.route('/production/add', methods=['POST'])
def add_production():
    p = Production(
        product_id=int(request.form['product_id']),
        quantity=float(request.form['quantity']),
        production_date=datetime.strptime(request.form['production_date'], '%Y-%m-%d').date(),
        notes=request.form.get('notes', ''),
        cost=float(request.form.get('cost', 0))
    )
    db.session.add(p)
    db.session.commit()
    flash('רשומת ייצור נוספה', 'success')
    return redirect(url_for('production'))

@app.route('/production/delete/<int:id>', methods=['POST'])
def delete_production(id):
    p = Production.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('רשומת ייצור נמחקה', 'warning')
    return redirect(url_for('production'))


# --- Recipes ---

@app.route('/recipes')
def recipes():
    all_recipes = Recipe.query.join(Product).order_by(Product.name).all()
    all_products = Product.query.filter_by(active=True).order_by(Product.name).all()
    all_materials = RawMaterial.query.order_by(RawMaterial.name).all()
    return render_template('recipes.html', recipes=all_recipes, products=all_products, materials=all_materials)

@app.route('/recipes/add', methods=['POST'])
def add_recipe():
    r = Recipe(
        product_id=int(request.form['product_id']),
        batch_size=float(request.form.get('batch_size', 1)),
        notes=request.form.get('notes', '')
    )
    db.session.add(r)
    db.session.flush()

    mat_ids = request.form.getlist('material_id[]')
    quantities = request.form.getlist('ing_quantity[]')

    for mid, qty in zip(mat_ids, quantities):
        if mid and qty:
            ing = RecipeIngredient(
                recipe_id=r.id,
                material_id=int(mid),
                quantity=float(qty)
            )
            db.session.add(ing)

    db.session.commit()
    flash('מתכון נוסף', 'success')
    return redirect(url_for('recipes'))

@app.route('/recipes/delete/<int:id>', methods=['POST'])
def delete_recipe(id):
    r = Recipe.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('מתכון נמחק', 'warning')
    return redirect(url_for('recipes'))


# --- Finances ---

@app.route('/finances')
def finances():
    all_expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    today = date.today()
    month_start = today.replace(day=1)

    monthly_revenue = db.session.query(
        func.sum(OrderItem.quantity * OrderItem.price)
    ).join(Order).filter(
        func.date(Order.order_date) >= month_start,
        Order.status != 'בוטל'
    ).scalar() or 0

    monthly_expenses_total = db.session.query(
        func.sum(Expense.amount)
    ).filter(Expense.expense_date >= month_start).scalar() or 0

    total_revenue = db.session.query(
        func.sum(OrderItem.quantity * OrderItem.price)
    ).join(Order).filter(Order.status != 'בוטל').scalar() or 0

    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0

    expense_categories = db.session.query(
        Expense.category, func.sum(Expense.amount)
    ).group_by(Expense.category).all()

    return render_template('finances.html',
        expenses=all_expenses,
        monthly_revenue=monthly_revenue,
        monthly_expenses=monthly_expenses_total,
        monthly_profit=monthly_revenue - monthly_expenses_total,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        total_profit=total_revenue - total_expenses,
        expense_categories=expense_categories
    )

@app.route('/finances/add', methods=['POST'])
def add_expense():
    e = Expense(
        description=request.form['description'],
        amount=float(request.form['amount']),
        category=request.form.get('category', 'אחר'),
        expense_date=datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date(),
        notes=request.form.get('notes', '')
    )
    db.session.add(e)
    db.session.commit()
    flash('הוצאה נרשמה', 'success')
    return redirect(url_for('finances'))

@app.route('/finances/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    e = Expense.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash('הוצאה נמחקה', 'warning')
    return redirect(url_for('finances'))


# --- Sales ---

@app.route('/sales')
def sales():
    all_sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    today = date.today()
    month_start = today.replace(day=1)
    monthly_total = db.session.query(func.sum(Sale.amount)).filter(
        Sale.sale_date >= month_start
    ).scalar() or 0
    total_all = db.session.query(func.sum(Sale.amount)).scalar() or 0
    return render_template('sales.html',
        sales=all_sales,
        monthly_total=monthly_total,
        total_all=total_all
    )

@app.route('/sales/add', methods=['POST'])
def add_sale():
    s = Sale(
        sale_date=datetime.strptime(request.form['sale_date'], '%Y-%m-%d').date(),
        description=request.form['description'],
        channel=request.form.get('channel', 'ישיר'),
        amount=float(request.form['amount']),
        notes=request.form.get('notes', '')
    )
    db.session.add(s)
    db.session.commit()
    flash(f'מכירה נרשמה — ₪{s.amount:.2f}', 'success')
    return redirect(url_for('sales'))

@app.route('/sales/delete/<int:id>', methods=['POST'])
def delete_sale(id):
    s = Sale.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash('מכירה נמחקה', 'warning')
    return redirect(url_for('sales'))


# --- Balance ---

@app.route('/balance')
def balance():
    from sqlalchemy import extract
    # Build monthly data for the last 12 months
    today = date.today()
    months = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    rows = []
    for y, m in months:
        sales_total = db.session.query(func.sum(Sale.amount)).filter(
            extract('year', Sale.sale_date) == y,
            extract('month', Sale.sale_date) == m
        ).scalar() or 0

        orders_total = db.session.query(
            func.sum(OrderItem.quantity * OrderItem.price)
        ).join(Order).filter(
            extract('year', Order.order_date) == y,
            extract('month', Order.order_date) == m,
            Order.status != 'בוטל'
        ).scalar() or 0

        purchases_total = db.session.query(func.sum(Purchase.total)).filter(
            extract('year', Purchase.purchase_date) == y,
            extract('month', Purchase.purchase_date) == m
        ).scalar() or 0

        expenses_total = db.session.query(func.sum(Expense.amount)).filter(
            extract('year', Expense.expense_date) == y,
            extract('month', Expense.expense_date) == m
        ).scalar() or 0

        income = sales_total + orders_total
        outgoing = purchases_total + expenses_total
        rows.append({
            'label': f'{m:02d}/{y}',
            'income': income,
            'outgoing': outgoing,
            'balance': income - outgoing
        })

    total_income = sum(r['income'] for r in rows)
    total_outgoing = sum(r['outgoing'] for r in rows)

    return render_template('balance.html',
        rows=rows,
        total_income=total_income,
        total_outgoing=total_outgoing,
        total_balance=total_income - total_outgoing
    )


# --- Purchases ---

@app.route('/purchases')
def purchases():
    all_purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()
    all_materials = RawMaterial.query.order_by(RawMaterial.name).all()
    today = date.today()
    month_start = today.replace(day=1)
    monthly_total = db.session.query(func.sum(Purchase.total)).filter(
        Purchase.purchase_date >= month_start
    ).scalar() or 0
    total_all = db.session.query(func.sum(Purchase.total)).scalar() or 0
    return render_template('purchases.html',
        purchases=all_purchases,
        materials=all_materials,
        monthly_total=monthly_total,
        total_all=total_all
    )

@app.route('/purchases/add', methods=['POST'])
def add_purchase():
    category = request.form['category']
    p = Purchase(
        purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date(),
        supplier=request.form.get('supplier', ''),
        invoice_number=request.form.get('invoice_number', ''),
        category=category,
        notes=request.form.get('notes', '')
    )
    db.session.add(p)
    db.session.flush()

    total = 0
    if category == 'חומרי גלם':
        mat_ids = request.form.getlist('material_id[]')
        quantities = request.form.getlist('item_quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        for mid, qty, up in zip(mat_ids, quantities, unit_prices):
            if mid and qty:
                qty_f = float(qty)
                up_f = float(up) if up else 0
                item = PurchaseItem(
                    purchase_id=p.id,
                    material_id=int(mid),
                    quantity=qty_f,
                    unit_price=up_f
                )
                db.session.add(item)
                total += qty_f * up_f
                material = RawMaterial.query.get(int(mid))
                if material:
                    material.quantity += qty_f
    else:
        desc = request.form.get('item_description', '')
        amount = float(request.form.get('item_amount', 0))
        item = PurchaseItem(
            purchase_id=p.id,
            description=desc,
            quantity=1,
            unit_price=amount
        )
        db.session.add(item)
        total = amount

    manual_total = request.form.get('manual_total', '')
    p.total = float(manual_total) if manual_total else total
    db.session.commit()
    flash(f'קנייה נרשמה בהצלחה — ₪{p.total:.2f}', 'success')
    return redirect(url_for('purchases'))

@app.route('/purchases/delete/<int:id>', methods=['POST'])
def delete_purchase(id):
    p = Purchase.query.get_or_404(id)
    if p.category == 'חומרי גלם':
        for item in p.items:
            if item.material_id:
                mat = RawMaterial.query.get(item.material_id)
                if mat:
                    mat.quantity = max(0, mat.quantity - item.quantity)
    db.session.delete(p)
    db.session.commit()
    flash('קנייה נמחקה (המלאי עודכן בהתאם)', 'warning')
    return redirect(url_for('purchases'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
