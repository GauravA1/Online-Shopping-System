# 🛒 Online Shopping System

A full-stack **Online Shopping System** built with **Python Flask** and **MySQL** database.

## ✨ Features

### Customer Side
- **User Registration & Login** with secure bcrypt password hashing
- **Product Catalog** — 17+ products across 6 categories
- **Search & Filter** — Search by name, filter by category, sort by price/rating
- **Shopping Cart** — Add, update quantity, remove items
- **Checkout** — Place orders with shipping address
- **Order History** — Track order status (Pending → Confirmed → Shipped → Delivered)

### Admin Panel
- **Dashboard** — View total products, orders, customers, and revenue
- **Product Management** — Add / Delete products
- **Order Management** — Update order status

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3 | Backend Language |
| Flask | Web Framework |
| MySQL 8.0 | Database |
| Jinja2 | HTML Templating |
| HTML5 / CSS3 | Frontend |
| JavaScript | Client-side Logic |
| bcrypt | Password Hashing |

## 📁 Project Structure

```
online-shopping-system/
├── app.py              # Main Flask application (routes & logic)
├── database.py         # Database initialization & seed data
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css       # Stylesheet (dark theme)
└── templates/
    ├── base.html           # Base template (navbar, footer)
    ├── index.html          # Home page (product catalog)
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── product_detail.html # Single product view
    ├── cart.html            # Shopping cart
    ├── checkout.html       # Checkout page
    ├── orders.html         # Order history
    ├── order_detail.html   # Single order view
    ├── admin.html          # Admin dashboard
    ├── admin_products.html # Manage products
    └── admin_orders.html   # Manage orders
```

## 🚀 How to Run

### Prerequisites
- Python 3.x installed
- MySQL 8.0 installed and running

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/GauravA1/Online-Shopping-System.git
   cd Online-Shopping-System
   ```

2. **Install dependencies**
   ```bash
   pip install flask mysql-connector-python bcrypt
   ```

3. **Set your MySQL password**
   Open `database.py` and replace `your_mysql_password_here` with your MySQL root password:
   ```python
   'password': 'your_mysql_password_here'
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   - Store: [http://localhost:5000](http://localhost:5000)
   - Admin: [http://localhost:5000/admin](http://localhost:5000/admin)

## 🔑 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Customer | john | customer123 |

## 💾 Database Schema

The MySQL database `online_shop` contains **6 tables**:

- **users** — User accounts with role-based access
- **categories** — Product categories
- **products** — Product catalog with pricing & stock
- **cart** — Shopping cart items per user
- **orders** — Customer orders with status tracking
- **order_items** — Individual items within each order

All tables use **foreign key relationships** and **auto-increment primary keys**.

## 📸 Screenshots

The application features a modern dark-themed UI with:
- Gradient hero section
- Animated product cards
- Glassmorphism navbar
- Responsive design for mobile & desktop

---

**Built with ❤️ using Python Flask + MySQL**
