# AgriConnect ZW

AgriConnect ZW is a Zimbabwean agricultural marketplace designed to connect farmers, buyers, and suppliers. The application supports secure user registration and login, listing management, product discovery, and order request workflows for agricultural goods and inputs.

## Features

- Secure registration and login with password hashing
- Role-based access for buyers, farmers, suppliers, and admins
- Marketplace listings with search and category filters
- Listing creation, editing, and deletion for sellers
- Order request workflow with pending, accepted, and rejected states
- Responsive UI built with HTML, CSS, JavaScript, and Flask
- SQLite database for local persistence
- Automated tests for registration, login, listings, and orders

## Tech stack

- Python 3.12+
- Flask
- SQLite
- HTML, CSS, JavaScript
- Pytest

## Project structure

```text
AgriConnect-ZW-Source-Code-
├── app/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── tests/
│   └── test_app.py
├── docs/
│   ├── Chapters/
│   ├── Diagrams/
│   └── README.md
├── app.py
├── requirements.txt
├── run_all.ps1
├── agriConnect.db
├── README.md
└── .gitignore
```

## Installation on Windows

1. Open PowerShell in the project folder.
2. Run:

```powershell
./run_all.ps1
```

The script creates a virtual environment in `.venv`, installs dependencies from `requirements.txt`, initializes the database, and starts the app.

## Manual installation

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Then open the browser at:

```text
http://127.0.0.1:5000
```

## Default admin account

A default admin user is created when the database is initialized:

- Email: admin@agriconnect.co.zw
- Password: admin123

## How the app works

### User roles

- Buyer: can browse products and request orders.
- Farmer: can create and manage listings.
- Supplier: can create and manage supply listings.
- Admin: can manage listings and approve or reject orders.

### Marketplace

- Search by product name, crop, or description.
- Filter by category.
- View listing price, quantity, unit, and location.
- Submit an order request.

### Orders

- Buyers see their order requests.
- Farmers and suppliers see incoming requests for their listings.
- Sellers can update an order to pending, accepted, or rejected.

## Database

The app uses SQLite and stores data in `agriconnect.db`. The database is initialized safely on startup by creating the required tables if they do not already exist.

## Testing

Run tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Troubleshooting

### Module errors

If you see import errors, reinstall dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Database issues

Delete the local SQLite database and restart the app if the database is corrupted:

```powershell
Remove-Item .\agriconnect.db
python app.py
```

### Port already in use

If port 5000 is already in use, stop the existing process or change the port in `app.py`.

## Academic documentation

The `docs/` folder contains chapter files and project diagrams that are preserved for the assignment. The application code is separate and is meant to support the project implementation described in the academic documentation.
