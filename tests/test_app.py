import re
import tempfile

from app import create_app
from app.models import init_db


def make_client(config=None):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    app_config = {
        "TESTING": True,
        "DATABASE": tmp.name,
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    }
    if config:
        app_config.update(config)
    app = create_app(app_config)
    return app, tmp.name


def test_register_and_login_and_dashboard_ai():
    app, _ = make_client()
    with app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "Farmer One",
                "email": "farmer1@example.com",
                "password": "strongpass",
                "phone": "+263771234567",
                "role": "farmer",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Registration successful" in response.data

        login_response = client.post(
            "/login",
            data={"email": "farmer1@example.com", "password": "strongpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200
        assert b"Seasonal price forecast" in login_response.data
        assert b"Market demand outlook" in login_response.data
        assert b"Crop suitability" in login_response.data


def test_demo_market_has_50_idempotent_listings():
    app, _ = make_client()
    with app.app_context():
        init_db()
        from app.models import get_db
        conn = get_db()
        assert conn.execute("SELECT COUNT(*) FROM demo_listing_seed").fetchone()[0] == 50
        assert conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'active'").fetchone()[0] == 50
        assert conn.execute(
            "SELECT COUNT(*) FROM listings l JOIN users u ON u.id = l.seller_id WHERE l.category = 'inputs' AND u.role = 'supplier'"
        ).fetchone()[0] == 5
        init_db()
        assert conn.execute("SELECT COUNT(*) FROM demo_listing_seed").fetchone()[0] == 50
        assert conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'active'").fetchone()[0] == 50
        with app.test_client() as client:
            marketplace = client.get("/marketplace")
            assert marketplace.status_code == 200
            assert marketplace.data.count(b'class="card listing-card"') == 50
            assert b"Maize grain - Harare" in marketplace.data


def test_crop_recommendation_form_validates_then_redirects():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={"name": "Buyer", "email": "buyer@example.com", "password": "strongpass", "role": "buyer"},
        )
        client.post("/login", data={"email": "buyer@example.com", "password": "strongpass"})
        response = client.post(
            "/ai/recommend",
            data={"province": "Midlands", "season": "summer", "rainfall": "650", "temperature": "24"},
        )
        assert response.status_code == 302
        assert "rainfall=650.0" in response.headers["Location"]
        invalid = client.post(
            "/ai/recommend",
            data={"province": "Harare", "season": "summer", "rainfall": "-10", "temperature": "24"},
            follow_redirects=True,
        )
        assert b"Rainfall must be between" in invalid.data


def test_listing_and_order_flow():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={"name": "Farmer Two", "email": "farmer2@example.com", "password": "strongpass", "phone": "+263771234568", "role": "farmer"},
        )
        client.post("/login", data={"email": "farmer2@example.com", "password": "strongpass"})
        create_listing = client.post(
            "/listings/new",
            data={"title": "Fresh maize", "crop": "Maize", "category": "cereals", "description": "High quality maize suitable for milling.", "quantity": "50", "unit": "kg", "price": "18.50", "location": "Harare"},
            follow_redirects=True,
        )
        assert create_listing.status_code == 200
        assert b"Listing created successfully." in create_listing.data

        client.post("/logout")
        client.post(
            "/register",
            data={"name": "Buyer One", "email": "buyer1@example.com", "password": "buyerpass", "phone": "+263771234569", "role": "buyer"},
        )
        client.post("/login", data={"email": "buyer1@example.com", "password": "buyerpass"})

        order_response = client.post(
            "/listings/1/order",
            data={"quantity": "10", "note": "Please deliver to Chitungwiza."},
            follow_redirects=True,
        )
        assert order_response.status_code == 200
        assert b"Order request created successfully." in order_response.data
        assert client.get("/orders").status_code == 200


def test_sellers_can_contact_buyer_from_their_order_only():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={"name": "Seller Contact", "email": "seller-contact@example.com", "password": "strongpass", "phone": "+263771111111", "role": "farmer"},
        )
        client.post("/login", data={"email": "seller-contact@example.com", "password": "strongpass"})
        client.post(
            "/listings/new",
            data={"title": "Contact test onions", "crop": "Onions", "category": "vegetables", "description": "Fresh onions.", "quantity": "35", "unit": "kg", "price": "1.20", "location": "Gweru"},
        )
        with app.app_context():
            from app.models import get_db
            listing = get_db().execute(
                "SELECT id FROM listings WHERE title = ?", ("Contact test onions",)
            ).fetchone()
            listing_id = listing["id"]

        client.post("/logout")
        client.post(
            "/register",
            data={"name": "Buyer Contact", "email": "buyer-contact@example.com", "password": "strongpass", "phone": "+263771234567", "role": "buyer"},
        )
        client.post("/login", data={"email": "buyer-contact@example.com", "password": "strongpass"})
        client.post(f"/listings/{listing_id}/order", data={"quantity": "3"})

        buyer_orders = client.get("/orders")
        assert buyer_orders.status_code == 200
        assert b"buyer-contact@example.com" not in buyer_orders.data
        assert b"tel:+263771234567" not in buyer_orders.data
        assert b"Contact seller" in buyer_orders.data
        assert b"Email seller" in buyer_orders.data
        assert b"tel:+263771111111" in buyer_orders.data
        assert b"Call Seller Contact" in buyer_orders.data

        client.post("/logout")
        client.post("/login", data={"email": "seller-contact@example.com", "password": "strongpass"})
        seller_orders = client.get("/orders")
        assert seller_orders.status_code == 200
        assert b"Contact buyer" in seller_orders.data
        assert b"buyer-contact%40example.com" in seller_orders.data
        assert b"tel:+263771234567" in seller_orders.data
        assert b"Call Buyer Contact" in seller_orders.data

        client.post("/logout")
        client.post(
            "/register",
            data={"name": "Other Seller", "email": "other-seller@example.com", "password": "strongpass", "role": "supplier"},
        )
        client.post("/login", data={"email": "other-seller@example.com", "password": "strongpass"})
        other_orders = client.get("/orders")
        assert other_orders.status_code == 200
        assert b"buyer-contact@example.com" not in other_orders.data
        assert b"Contact buyer" not in other_orders.data


def test_supplier_and_buyer_can_contact_each_other_from_order():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={"name": "Input Supplier", "email": "supplier-contact@example.com", "password": "strongpass", "phone": "+263772222222", "role": "supplier"},
        )
        client.post("/login", data={"email": "supplier-contact@example.com", "password": "strongpass"})
        client.post(
            "/listings/new",
            data={"title": "Seed supplier contact item", "crop": "Compound D", "category": "inputs", "description": "Fertilizer.", "quantity": "12", "unit": "bag", "price": "34", "location": "Harare"},
        )
        with app.app_context():
            from app.models import get_db
            listing = get_db().execute(
                "SELECT id FROM listings WHERE title = ?", ("Seed supplier contact item",)
            ).fetchone()
            listing_id = listing["id"]

        client.post("/logout")
        client.post(
            "/register",
            data={"name": "Contact Buyer", "email": "contact-buyer@example.com", "password": "strongpass", "phone": "+263773333333", "role": "buyer"},
        )
        client.post("/login", data={"email": "contact-buyer@example.com", "password": "strongpass"})
        client.post(f"/listings/{listing_id}/order", data={"quantity": "2"})
        buyer_orders = client.get("/orders")
        assert b"Contact seller" in buyer_orders.data
        assert b"supplier-contact%40example.com" in buyer_orders.data
        assert b"tel:+263772222222" in buyer_orders.data

        client.post("/logout")
        client.post("/login", data={"email": "supplier-contact@example.com", "password": "strongpass"})
        supplier_orders = client.get("/orders")
        assert b"Contact buyer" in supplier_orders.data
        assert b"contact-buyer%40example.com" in supplier_orders.data
        assert b"tel:+263773333333" in supplier_orders.data


def test_admin_console_updates_training_data_and_is_dark(monkeypatch, tmp_path):
    import ai.models as ai_models

    training_file = tmp_path / "price-history.csv"
    original_rows = ai_models.load_price_history()
    monkeypatch.setattr(ai_models, "PRICE_HISTORY_PATH", training_file)
    ai_models.save_price_history(original_rows)
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/login",
            data={"email": "admin@agriconnect.co.zw", "password": "admin123"},
        )
        admin_home = client.get("/dashboard")
        assert admin_home.status_code == 302
        assert admin_home.headers["Location"].endswith("/admin")
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"class=\"admin-theme\"" in response.data
        assert b"Seasonal price observations" in response.data
        assert b"Save dataset and retrain" in response.data
        assert b"Edit" in response.data
        assert b"Orders</a>" not in response.data

        updated_rows = [dict(row) for row in original_rows]
        updated_rows[0]["tomatoes"] = 1.25
        form_data = {
            f"price_{row['month']}_{crop}": str(row[crop])
            for row in updated_rows
            for crop in ai_models.PRICE_CROPS
        }
        client.post("/admin", data=form_data, follow_redirects=True)
        saved_rows = ai_models.load_price_history()
        assert saved_rows[0]["tomatoes"] == 1.25
        assert training_file.exists()
    ai_models.train_price_models.cache_clear()


def test_admin_training_data_rejects_invalid_price_and_blocks_non_admin(monkeypatch, tmp_path):
    import ai.models as ai_models

    training_file = tmp_path / "price-history.csv"
    original_rows = ai_models.load_price_history()
    monkeypatch.setattr(ai_models, "PRICE_HISTORY_PATH", training_file)
    ai_models.save_price_history(original_rows)
    original_contents = training_file.read_text(encoding="utf-8")
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={"name": "Data Buyer", "email": "data-buyer@example.com", "password": "strongpass", "role": "buyer"},
        )
        client.post("/login", data={"email": "data-buyer@example.com", "password": "strongpass"})
        denied = client.get("/admin")
        assert denied.status_code == 302
        assert denied.headers["Location"].endswith("/dashboard")

        client.post("/logout")
        client.post("/login", data={"email": "admin@agriconnect.co.zw", "password": "admin123"})
        form_data = {
            f"price_{row['month']}_{crop}": str(row[crop])
            for row in original_rows
            for crop in ai_models.PRICE_CROPS
        }
        form_data["price_1_tomatoes"] = "-1"
        response = client.post("/admin", data=form_data, follow_redirects=True)
        assert b"Crop prices must be finite numbers greater than zero." in response.data
        assert training_file.read_text(encoding="utf-8") == original_contents
    ai_models.train_price_models.cache_clear()


def test_login_locks_after_three_failed_attempts_and_resets_after_success():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={
                "name": "Lockout Test",
                "email": "lockout@example.com",
                "password": "strongpass",
                "role": "buyer",
            },
        )

        for attempt in range(1, 4):
            response = client.post(
                "/login",
                data={"email": "lockout@example.com", "password": "incorrect"},
            )
            assert response.status_code == (429 if attempt == 3 else 200)

        blocked_valid_password = client.post(
            "/login",
            data={"email": "lockout@example.com", "password": "strongpass"},
        )
        assert blocked_valid_password.status_code == 429
        assert b"Too many failed sign-in attempts" in blocked_valid_password.data

        with app.app_context():
            from app.models import get_db

            get_db().execute(
                "UPDATE login_attempts SET locked_until = 0 WHERE email = ?",
                ("lockout@example.com",),
            )
            get_db().commit()

        successful_login = client.post(
            "/login",
            data={"email": "lockout@example.com", "password": "strongpass"},
        )
        assert successful_login.status_code == 302
        with app.app_context():
            from app.models import get_db

            assert get_db().execute(
                "SELECT 1 FROM login_attempts WHERE email = ?",
                ("lockout@example.com",),
            ).fetchone() is None


def test_csrf_required_for_post_routes_and_logout_is_post_only(tmp_path):
    database = tmp_path / "csrf-test.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database),
            "SECRET_KEY": "csrf-test-secret",
        }
    )
    with app.test_client() as client:
        login_page = client.get("/login")
        token_match = re.search(
            rb'name="csrf_token" value="([^"]+)"', login_page.data
        )
        assert token_match
        token = token_match.group(1).decode()

        missing_token = client.post(
            "/login",
            data={"email": "nobody@example.com", "password": "wrongpass"},
        )
        invalid_token = client.post(
            "/login",
            data={
                "email": "nobody@example.com",
                "password": "wrongpass",
                "csrf_token": "not-a-valid-token",
            },
        )
        assert missing_token.status_code == 400
        assert invalid_token.status_code == 400

        registered = client.post(
            "/register",
            data={
                "csrf_token": token,
                "name": "CSRF Buyer",
                "email": "csrf-buyer@example.com",
                "password": "strongpass",
                "role": "buyer",
            },
        )
        assert registered.status_code == 302
        login = client.post(
            "/login",
            data={
                "csrf_token": token,
                "email": "csrf-buyer@example.com",
                "password": "strongpass",
            },
        )
        assert login.status_code == 302
        assert client.get("/logout").status_code == 405

        dashboard = client.get("/dashboard")
        assert b'action="/logout"' in dashboard.data
        assert b'name="csrf_token"' in dashboard.data
        logout_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', dashboard.data
        ).group(1).decode()
        logout = client.post("/logout", data={"csrf_token": logout_token})
        assert logout.status_code == 302
        assert logout.headers["Location"].endswith("/login")


def test_session_cookie_security_attributes_are_configurable():
    app, _ = make_client(
        {
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
        }
    )
    with app.test_client() as client:
        response = client.post(
            "/login",
            data={"email": "admin@agriconnect.co.zw", "password": "admin123"},
            base_url="https://localhost",
        )
        cookie = response.headers["Set-Cookie"]
        assert "Secure" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=Lax" in cookie


def test_public_registration_cannot_create_admin_account():
    app, _ = make_client()
    with app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "Unexpected Admin",
                "email": "unexpected-admin@example.com",
                "password": "strongpass",
                "role": "admin",
            },
            follow_redirects=True,
        )
        assert b"Invalid role selected." in response.data
        with app.app_context():
            from app.models import get_db

            assert get_db().execute(
                "SELECT 1 FROM users WHERE email = ?",
                ("unexpected-admin@example.com",),
            ).fetchone() is None
