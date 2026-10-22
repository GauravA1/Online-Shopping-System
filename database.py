import mysql.connector
import bcrypt
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.environ.get('MYSQL_PASSWORD', 'your_mysql_password_here')  # Set your MySQL password here
}

DB_NAME = 'online_shop'


def get_connection():
    """Get a MySQL connection to the online_shop database."""
    config = {**DB_CONFIG, 'database': DB_NAME}
    return mysql.connector.connect(**config)


def initialize_database():
    """Create database, tables, and seed with sample data."""
    # Connect without database first to create it
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # ── Create Tables ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            role ENUM('customer', 'admin') DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            icon VARCHAR(10) DEFAULT '📦'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            image_url VARCHAR(500),
            category_id INT,
            stock INT DEFAULT 0,
            rating DECIMAL(2,1) DEFAULT 4.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status ENUM('pending','confirmed','shipped','delivered','cancelled') DEFAULT 'pending',
            shipping_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE KEY unique_cart_item (user_id, product_id)
        )
    """)

    # ── Seed Data (only if empty) ──
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor)

    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Database initialized successfully!")


def _seed_data(cursor):
    """Insert sample data into the database."""
    # Users
    admin_pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    cust_pw = bcrypt.hashpw('customer123'.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO users (username, email, password, full_name, role) VALUES (%s,%s,%s,%s,%s)",
        ('admin', 'admin@shop.com', admin_pw, 'Admin User', 'admin')
    )
    cursor.execute(
        "INSERT INTO users (username, email, password, full_name, role) VALUES (%s,%s,%s,%s,%s)",
        ('john', 'john@example.com', cust_pw, 'John Doe', 'customer')
    )
    cursor.execute(
        "INSERT INTO users (username, email, password, full_name, role) VALUES (%s,%s,%s,%s,%s)",
        ('jane', 'jane@example.com', cust_pw, 'Jane Smith', 'customer')
    )

    # Categories
    categories = [
        ('Electronics', '💻'), ('Clothing', '👕'), ('Books', '📚'),
        ('Home & Garden', '🏡'), ('Sports', '⚽'), ('Beauty', '💄')
    ]
    cursor.executemany("INSERT INTO categories (name, icon) VALUES (%s, %s)", categories)

    # Products
    products = [
        ('Wireless Bluetooth Headphones', 'Premium noise-cancelling headphones with 30hr battery life and crystal clear sound.', 2499.00,
         'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop', 1, 50, 4.5),
        ('Smart Watch Pro', 'Feature-rich smartwatch with heart rate monitor, GPS, and 7-day battery.', 4999.00,
         'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop', 1, 30, 4.7),
        ('Portable Speaker', 'Waterproof Bluetooth speaker with 360° sound and 12hr playtime.', 1799.00,
         'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop', 1, 45, 4.3),
        ('USB-C Hub Adapter', '7-in-1 USB-C hub with HDMI, USB 3.0, SD card reader and PD charging.', 1299.00,
         'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400&h=300&fit=crop', 1, 100, 4.1),

        ('Classic Denim Jacket', 'Timeless denim jacket with modern fit. Perfect for all seasons.', 2199.00,
         'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=400&h=300&fit=crop', 2, 25, 4.4),
        ('Running Shoes', 'Lightweight and breathable running shoes with cushioned sole.', 3499.00,
         'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop', 2, 60, 4.6),
        ('Cotton T-Shirt Pack', 'Pack of 3 premium cotton t-shirts in assorted colors.', 999.00,
         'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=300&fit=crop', 2, 200, 4.2),
        ('Aviator Sunglasses', 'Classic aviator sunglasses with UV400 protection and polarized lenses.', 1499.00,
         'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=300&fit=crop', 2, 80, 4.5),

        ('JavaScript: The Good Parts', 'Essential guide to JavaScript programming by Douglas Crockford.', 449.00,
         'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&h=300&fit=crop', 3, 150, 4.8),
        ('The Art of Programming', 'Comprehensive programming guide covering algorithms and data structures.', 599.00,
         'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400&h=300&fit=crop', 3, 120, 4.6),
        ('Design Patterns', 'Learn software design patterns with practical examples and use cases.', 699.00,
         'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400&h=300&fit=crop', 3, 90, 4.7),

        ('Indoor Plant Set', 'Set of 3 beautiful indoor plants with decorative pots.', 1299.00,
         'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=300&fit=crop', 4, 40, 4.3),
        ('Scented Candle Collection', 'Premium scented candles set with 4 unique fragrances.', 799.00,
         'https://images.unsplash.com/photo-1602028915047-37269d1a73f7?w=400&h=300&fit=crop', 4, 70, 4.4),

        ('Yoga Mat Premium', 'Non-slip yoga mat with carrying strap. 6mm thickness for comfort.', 899.00,
         'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400&h=300&fit=crop', 5, 55, 4.5),
        ('Water Bottle Steel', 'Insulated stainless steel water bottle — keeps drinks cold 24hrs.', 499.00,
         'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=300&fit=crop', 5, 150, 4.6),

        ('Skincare Gift Set', 'Complete skincare routine set with cleanser, toner, and moisturizer.', 1899.00,
         'https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400&h=300&fit=crop', 6, 45, 4.7),
        ('Hair Care Bundle', 'Professional hair care set with shampoo, conditioner, and serum.', 1299.00,
         'https://images.unsplash.com/photo-1522338242992-e1a54571a9f7?w=400&h=300&fit=crop', 6, 60, 4.4),
    ]
    cursor.executemany(
        "INSERT INTO products (name, description, price, image_url, category_id, stock, rating) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        products
    )

    print("   [OK] Seeded users, categories & 17 products")
    print("   Admin Login:    admin / admin123")
    print("   Customer Login: john  / customer123")


if __name__ == '__main__':
    initialize_database()
