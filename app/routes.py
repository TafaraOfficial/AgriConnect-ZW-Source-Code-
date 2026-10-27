import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .models import get_db

main = Blueprint("main", __name__)


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def login_required(view):
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def role_required(*roles):
    def decorator(view):
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or user["role"] not in roles:
                flash("You do not have permission to access that page.", "warning")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)

        wrapped.__name__ = view.__name__
        return wrapped

    return decorator


@main.context_processor
def inject_user():
    return {"current_user": current_user(), "app_name": "AgriConnect ZW"}


@main.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        phone = (request.form.get("phone") or "").strip()
        role = (request.form.get("role") or "buyer").strip().lower()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("register.html")

        if role not in {"buyer", "farmer", "supplier", "admin"}:
            flash("Invalid role selected.", "danger")
            return render_template("register.html")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("This email is already registered.", "warning")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)",
            (name, email, generate_password_hash(password), role, phone or None),
        )
        db.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@main.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    db = get_db()

    if user["role"] in {"farmer", "supplier", "admin"}:
        my_listings = db.execute(
            "SELECT COUNT(*) AS total FROM listings WHERE seller_id = ?",
            (user["id"],),
        ).fetchone()["total"]
    else:
        my_listings = 0

    total_listings = db.execute("SELECT COUNT(*) AS total FROM listings WHERE status = 'active'").fetchone()["total"]
    pending_orders = db.execute(
        "SELECT COUNT(*) AS total FROM orders o JOIN listings l ON l.id = o.listing_id WHERE l.seller_id = ? AND o.status = 'pending'",
        (user["id"],),
    ).fetchone()["total"] if user["role"] in {"farmer", "supplier", "admin"} else 0

    recent_listings = db.execute(
        "SELECT l.*, u.name AS seller_name FROM listings l JOIN users u ON u.id = l.seller_id ORDER BY l.created_at DESC LIMIT 5"
    ).fetchall()

    return render_template(
        "dashboard.html",
        user=user,
        total_listings=total_listings,
        my_listings=my_listings,
        pending_orders=pending_orders,
        recent_listings=[dict(item) for item in recent_listings],
    )


@main.route("/marketplace")
def marketplace():
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "all").strip().lower()

    query = """
        SELECT l.*, u.name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.seller_id
        WHERE l.status = 'active'
    """
    params = []

    if search:
        query += " AND (LOWER(l.title) LIKE LOWER(?) OR LOWER(l.crop) LIKE LOWER(?) OR LOWER(l.description) LIKE LOWER(?))"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if category and category != "all":
        query += " AND LOWER(l.category) = LOWER(?)"
        params.append(category)

    query += " ORDER BY l.created_at DESC"

    rows = get_db().execute(query, params).fetchall()
    listings = [dict(row) for row in rows]
    categories = [
        "cereals",
        "vegetables",
        "fruits",
        "legumes",
        "livestock",
        "inputs",
    ]

    return render_template(
        "marketplace.html",
        listings=listings,
        search=search,
        category=category,
        categories=categories,
    )


@main.route("/listings/new", methods=["GET", "POST"])
@login_required
@role_required("farmer", "supplier", "admin")
def new_listing():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        crop = (request.form.get("crop") or "").strip()
        category = (request.form.get("category") or "").strip().lower()
        description = (request.form.get("description") or "").strip()
        quantity = request.form.get("quantity") or "0"
        unit = (request.form.get("unit") or "kg").strip()
        price = request.form.get("price") or "0"
        location = (request.form.get("location") or "").strip()

        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            flash("Quantity and price must be valid numbers.", "danger")
            return render_template("listing_form.html", listing=None, action="new")

        if not title or not crop or not category or not location or quantity <= 0 or price < 0:
            flash("Please fill in all required listing fields with valid values.", "danger")
            return render_template("listing_form.html", listing=None, action="new")

        db = get_db()
        db.execute(
            "INSERT INTO listings (seller_id, title, crop, category, description, quantity, unit, price, location) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (current_user()["id"], title, crop, category, description, quantity, unit, price, location),
        )
        db.commit()
        flash("Listing created successfully.", "success")
        return redirect(url_for("main.marketplace"))

    return render_template("listing_form.html", listing=None, action="new")


@main.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    db = get_db()
    listing = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not listing:
        flash("Listing not found.", "warning")
        return redirect(url_for("main.marketplace"))

    user = current_user()
    if user["role"] != "admin" and user["id"] != listing["seller_id"]:
        flash("You are not allowed to edit that listing.", "warning")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        crop = (request.form.get("crop") or "").strip()
        category = (request.form.get("category") or "").strip().lower()
        description = (request.form.get("description") or "").strip()
        quantity = request.form.get("quantity") or "0"
        unit = (request.form.get("unit") or "kg").strip()
        price = request.form.get("price") or "0"
        location = (request.form.get("location") or "").strip()

        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            flash("Quantity and price must be valid numbers.", "danger")
            return render_template("listing_form.html", listing=dict(listing), action="edit")

        if not title or not crop or not category or not location or quantity <= 0 or price < 0:
            flash("Please fill in all required listing fields with valid values.", "danger")
            return render_template("listing_form.html", listing=dict(listing), action="edit")

        db.execute(
            "UPDATE listings SET title = ?, crop = ?, category = ?, description = ?, quantity = ?, unit = ?, price = ?, location = ? WHERE id = ?",
            (title, crop, category, description, quantity, unit, price, location, listing_id),
        )
        db.commit()
        flash("Listing updated successfully.", "success")
        return redirect(url_for("main.marketplace"))

    return render_template("listing_form.html", listing=dict(listing), action="edit")


@main.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    db = get_db()
    listing = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not listing:
        flash("Listing not found.", "warning")
        return redirect(url_for("main.marketplace"))

    user = current_user()
    if user["role"] not in {"admin"} and user["id"] != listing["seller_id"]:
        flash("You cannot delete that listing.", "warning")
        return redirect(url_for("main.marketplace"))

    db.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    db.commit()
    flash("Listing removed.", "success")
    return redirect(url_for("main.marketplace"))


@main.route("/listings/<int:listing_id>/order", methods=["POST"])
@login_required
def place_order(listing_id):
    user = current_user()
    if user["role"] not in {"buyer", "admin"}:
        flash("Only buyers can place order requests.", "warning")
        return redirect(url_for("main.marketplace"))

    db = get_db()
    listing = db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not listing or listing["status"] != "active":
        flash("This listing is not available.", "warning")
        return redirect(url_for("main.marketplace"))

    if listing["seller_id"] == user["id"]:
        flash("You cannot order your own listing.", "warning")
        return redirect(url_for("main.marketplace"))

    try:
        quantity = int(request.form.get("quantity") or "1")
    except ValueError:
        flash("Order quantity must be a valid number.", "danger")
        return redirect(url_for("main.marketplace"))

    if quantity <= 0:
        flash("Order quantity must be greater than zero.", "danger")
        return redirect(url_for("main.marketplace"))

    if quantity > listing["quantity"]:
        flash("The requested quantity exceeds the available stock.", "danger")
        return redirect(url_for("main.marketplace"))

    note = (request.form.get("note") or "").strip()
    db.execute(
        "INSERT INTO orders (buyer_id, listing_id, quantity, note, status) VALUES (?, ?, ?, ?, 'pending')",
        (user["id"], listing_id, quantity, note),
    )
    db.commit()
    flash("Order request created successfully.", "success")
    return redirect(url_for("main.orders_page"))


@main.route("/orders", methods=["GET"])
@login_required
def orders_page():
    user = current_user()
    db = get_db()

    if user["role"] in {"farmer", "supplier", "admin"}:
        rows = db.execute(
            """
            SELECT o.*, l.title, l.price, u.name AS buyer_name
            FROM orders o
            JOIN listings l ON l.id = o.listing_id
            JOIN users u ON u.id = o.buyer_id
            WHERE l.seller_id = ?
            ORDER BY o.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        order_type = "incoming"
    else:
        rows = db.execute(
            """
            SELECT o.*, l.title, l.price, u.name AS seller_name
            FROM orders o
            JOIN listings l ON l.id = o.listing_id
            JOIN users u ON u.id = l.seller_id
            WHERE o.buyer_id = ?
            ORDER BY o.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        order_type = "outgoing"

    orders = [dict(row) for row in rows]
    return render_template("orders.html", orders=orders, order_type=order_type)


@main.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    user = current_user()
    db = get_db()
    order = db.execute(
        "SELECT o.*, l.seller_id, l.quantity AS stock_quantity FROM orders o JOIN listings l ON l.id = o.listing_id WHERE o.id = ?",
        (order_id,),
    ).fetchone()

    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for("main.orders_page"))

    if user["role"] not in {"admin"} and user["id"] != order["seller_id"]:
        flash("You cannot update that order.", "warning")
        return redirect(url_for("main.orders_page"))

    status = (request.form.get("status") or "pending").strip().lower()
    if status not in {"pending", "accepted", "rejected"}:
        flash("Invalid order status.", "danger")
        return redirect(url_for("main.orders_page"))

    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

    if status == "accepted":
        remaining = max(0, order["stock_quantity"] - order["quantity"])
        db.execute("UPDATE listings SET quantity = ?, status = ? WHERE id = ?", (remaining, "active" if remaining > 0 else "sold", order["listing_id"]))

    db.commit()
    flash(f"Order marked as {status}.", "success")
    return redirect(url_for("main.orders_page"))


@main.route("/health")
def health():
    return {"status": "ok"}, 200
