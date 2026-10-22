from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import bcrypt
from database import get_connection, initialize_database
from functools import wraps

app = Flask(__name__)
app.secret_key = 'online-shop-secret-key-2024'

# Initialize database on startup
initialize_database()


# ─── Helpers ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_cart_count():
    if 'user_id' not in session:
        return 0
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE user_id = %s", (session['user_id'],))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


@app.context_processor
def inject_cart_count():
    return dict(cart_count=get_cart_count())


# ─── AUTH ROUTES ───────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password, full_name) VALUES (%s,%s,%s,%s)",
                (username, email, hashed, full_name)
            )
            conn.commit()
            user_id = cur.lastrowid
            cur.close()
            conn.close()

            session['user_id'] = user_id
            session['username'] = username
            session['full_name'] = full_name
            session['role'] = 'customer'
            flash('Account created successfully!', 'success')
            return redirect(url_for('home'))
        except mysql.connector.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))


# ─── MAIN ROUTES ──────────────────────────────────────────
@app.route('/')
def home():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get categories
    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()

    # Filters
    category_id = request.args.get('category', 'all')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'default')

    query = """
        SELECT p.*, c.name AS category_name, c.icon AS category_icon
        FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1
    """
    params = []

    if category_id != 'all':
        query += " AND p.category_id = %s"
        params.append(int(category_id))
    if search:
        query += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])

    if sort == 'price_low':
        query += " ORDER BY p.price ASC"
    elif sort == 'price_high':
        query += " ORDER BY p.price DESC"
    elif sort == 'rating':
        query += " ORDER BY p.rating DESC"
    else:
        query += " ORDER BY p.id ASC"

    cur.execute(query, params)
    products = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', products=products, categories=categories,
                           selected_category=category_id, search_query=search, selected_sort=sort)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.name AS category_name, c.icon AS category_icon
        FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = %s
    """, (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('home'))
    return render_template('product_detail.html', product=product)


# ─── CART ROUTES ──────────────────────────────────────────
@app.route('/cart')
@login_required
def cart():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.id, c.quantity, p.id AS product_id, p.name, p.price, p.image_url, p.stock
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s
    """, (session['user_id'],))
    items = cur.fetchall()
    total = sum(item['price'] * item['quantity'] for item in items)
    cur.close()
    conn.close()
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    if not product:
        flash('Product not found.', 'danger')
    elif product['stock'] <= 0:
        flash('Product is out of stock.', 'warning')
    else:
        try:
            cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,1)", (session['user_id'], product_id))
            conn.commit()
            flash(f'"{product["name"]}" added to cart!', 'success')
        except mysql.connector.IntegrityError:
            cur.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = %s AND product_id = %s",
                        (session['user_id'], product_id))
            conn.commit()
            flash(f'"{product["name"]}" quantity updated in cart!', 'success')
    cur.close()
    conn.close()
    return redirect(request.referrer or url_for('home'))


@app.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    quantity = int(request.form['quantity'])
    conn = get_connection()
    cur = conn.cursor()
    if quantity <= 0:
        cur.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    else:
        cur.execute("UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s", (quantity, cart_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    flash('Cart updated.', 'info')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


# ─── ORDER ROUTES ─────────────────────────────────────────
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT c.*, p.price, p.stock, p.name, p.image_url
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s
    """, (session['user_id'],))
    items = cur.fetchall()

    if not items:
        flash('Your cart is empty.', 'warning')
        cur.close()
        conn.close()
        return redirect(url_for('home'))

    total = sum(item['price'] * item['quantity'] for item in items)

    if request.method == 'POST':
        address = request.form['shipping_address']
        if not address.strip():
            flash('Shipping address is required.', 'danger')
            return render_template('checkout.html', items=items, total=total)

        # Check stock
        for item in items:
            if item['stock'] < item['quantity']:
                flash(f'Not enough stock for "{item["name"]}".', 'danger')
                return render_template('checkout.html', items=items, total=total)

        # Create order
        cur.execute("INSERT INTO orders (user_id, total_amount, shipping_address) VALUES (%s,%s,%s)",
                     (session['user_id'], total, address))
        order_id = cur.lastrowid

        # Add items & update stock
        for item in items:
            cur.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)",
                        (order_id, item['product_id'], item['quantity'], item['price']))
            cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (item['quantity'], item['product_id']))

        # Clear cart
        cur.execute("DELETE FROM cart WHERE user_id = %s", (session['user_id'],))
        conn.commit()
        cur.close()
        conn.close()
        flash(f'Order #{order_id} placed successfully! 🎉', 'success')
        return redirect(url_for('orders'))

    cur.close()
    conn.close()
    return render_template('checkout.html', items=items, total=total)


@app.route('/orders')
@login_required
def orders():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.*, (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS item_count
        FROM orders o WHERE o.user_id = %s ORDER BY o.created_at DESC
    """, (session['user_id'],))
    orders_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('orders.html', orders=orders_list)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cur.fetchone()
    if not order:
        flash('Order not found.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('orders'))

    cur.execute("""
        SELECT oi.*, p.name, p.image_url FROM order_items oi
        JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s
    """, (order_id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('order_detail.html', order=order, items=items)


# ─── ADMIN ROUTES ─────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS count FROM products")
    total_products = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) AS count FROM orders")
    total_orders = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) AS count FROM users WHERE role='customer'")
    total_users = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS total FROM orders WHERE status != 'cancelled'")
    total_revenue = cur.fetchone()['total']

    cur.execute("""
        SELECT o.*, u.username, u.full_name FROM orders o
        JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 10
    """)
    recent_orders = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('admin.html', total_products=total_products, total_orders=total_orders,
                           total_users=total_users, total_revenue=total_revenue, recent_orders=recent_orders)


@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.name AS category_name FROM products p
        LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.id DESC
    """)
    products = cur.fetchall()
    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_products.html', products=products, categories=categories)


@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price, image_url, category_id, stock) VALUES (%s,%s,%s,%s,%s,%s)",
        (request.form['name'], request.form['description'], float(request.form['price']),
         request.form['image_url'], int(request.form['category_id']), int(request.form['stock']))
    )
    conn.commit()
    cur.close()
    conn.close()
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE product_id = %s", (product_id,))
    cur.execute("DELETE FROM order_items WHERE product_id = %s", (product_id,))
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.*, u.username, u.full_name,
        (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS item_count
        FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC
    """)
    orders_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_orders.html', orders=orders_list)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    status = request.form['status']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Order #{order_id} status updated to {status}.', 'success')
    return redirect(url_for('admin_orders'))


# ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n--- Online Shopping System ---")
    print("   Store: http://localhost:5000")
    print("   Admin: http://localhost:5000/admin")
    print("\n   Login Credentials:")
    print("   Admin:    admin / admin123")
    print("   Customer: john  / customer123\n")
    app.run(debug=True, port=5000)
