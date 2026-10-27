import tempfile

from app import create_app


def make_client():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    app = create_app({"TESTING": True, "DATABASE": tmp.name, "SECRET_KEY": "test-secret"})
    return app, tmp.name


def test_register_and_login():
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
        assert b"Dashboard" in login_response.data


def test_listing_and_order_flow():
    app, _ = make_client()
    with app.test_client() as client:
        client.post(
            "/register",
            data={
                "name": "Farmer Two",
                "email": "farmer2@example.com",
                "password": "strongpass",
                "phone": "+263771234568",
                "role": "farmer",
            },
        )
        client.post(
            "/login",
            data={"email": "farmer2@example.com", "password": "strongpass"},
        )
        create_listing = client.post(
            "/listings/new",
            data={
                "title": "Fresh maize",
                "crop": "Maize",
                "category": "cereals",
                "description": "High quality maize suitable for milling.",
                "quantity": "50",
                "unit": "kg",
                "price": "18.50",
                "location": "Harare",
            },
            follow_redirects=True,
        )
        assert create_listing.status_code == 200
        assert b"Listing created successfully." in create_listing.data

        client.get("/logout")

        client.post(
            "/register",
            data={
                "name": "Buyer One",
                "email": "buyer1@example.com",
                "password": "buyerpass",
                "phone": "+263771234569",
                "role": "buyer",
            },
        )
        client.post(
            "/login",
            data={"email": "buyer1@example.com", "password": "buyerpass"},
        )

        order_response = client.post(
            "/listings/1/order",
            data={"quantity": "10", "note": "Please deliver to Chitungwiza."},
            follow_redirects=True,
        )
        assert order_response.status_code == 200
        assert b"Order request created successfully." in order_response.data

        orders_response = client.get("/orders")
        assert orders_response.status_code == 200
        assert b"My orders" in orders_response.data
