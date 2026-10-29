# AgriConnect ZW

AgriConnect ZW is a Zimbabwean agricultural marketplace designed to connect farmers, buyers, and suppliers. The application supports secure user registration and login, listing management, product discovery, and order request workflows for agricultural goods and inputs.

## Features

- Secure registration and login with password hashing
- Role-based access for buyers, farmers, suppliers, and admins
- Marketplace listings with search and category filters
- Listing creation, editing, and deletion for sellers
- Order request workflow with pending, accepted, and rejected states
- Admin-only dark data console for marketplace listing maintenance
- Editable 12-month seasonal price dataset with validated model retraining
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
|-- app/
|   |-- static/
|   |-- templates/
|   |-- __init__.py
|   |-- models.py
|   `-- routes.py
|-- ai/
|   |-- models.py
|   |-- market_price_history.csv
|   |-- demo_products.py
|   |-- price_prediction.py
|   |-- demand_forecasting.py
|   `-- crop_recommendation.py
|-- tests/
|   |-- test_app.py
|   `-- test_ai_models.py
|-- docs/
|   |-- Chapters/
|   |-- Diagrams/
|   `-- README.md
|-- app.py
|-- requirements.txt
|-- run_all.ps1
|-- agriconnect.db
|-- README.md
`-- .gitignore
```

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
- Admin: uses the dark Data console to update seasonal price-training data, retrain the price model, and edit or delete marketplace listings. The admin landing page does not show the standard dashboard and order workflow.

### Admin data console

Sign in with an admin account and open **Data console**. Update the monthly USD/kg observations for all seven supported crops, then select **Save dataset and retrain**. The app requires one row for each month and positive finite prices; successful updates replace `ai/market_price_history.csv` and refit the seasonal regression models. The preloaded values are illustrative examples, so replace them with consistently sourced observations before using the forecasts for decisions.

The console also shows database totals and the 100 most recent listings. Admins can edit a listing or delete it; deleting a listing also removes its related order records.

### Marketplace

- Search by product name, crop, or description.
- Filter by category.
- View listing price, quantity, unit, and location.
- Submit an order request.

### Orders

- Buyers see their order requests.
- Farmers and suppliers see incoming requests for their listings.
- Sellers can update an order to pending, accepted, or rejected.
- Farmers and suppliers can email or call buyers from incoming orders; buyer contacts are only shown to the seller of that listing.

## Database

The app uses SQLite and stores data in `agriconnect.db`. The database is initialized safely on startup by creating the required tables if they do not already exist.

## Security configuration

- Every Flask `POST` route is protected by Flask-WTF CSRF validation. All in-app `POST` forms, including logout, include a CSRF token; logout accepts `POST` only.
- Login attempts are tracked by normalized email in SQLite. The third incorrect password locks that email for 15 minutes. A successful login clears the failed-attempt record.
- Session cookies are `HttpOnly` and use `SameSite=Lax`. For an HTTPS deployment, set `SESSION_COOKIE_SECURE=1` in the server environment so browsers send session cookies only over TLS. Leave this unset for local `http://127.0.0.1:5000` development.
- Set a stable, random `SECRET_KEY` in the deployment environment. If omitted, the app generates an unpredictable key at startup; sessions will be invalidated when the app restarts.
- Public registration only permits buyer, farmer, and supplier roles; admin accounts must be provisioned by an administrator.

Example PowerShell settings for a TLS-terminated deployment (configure these in the service environment rather than committing secrets):

```powershell
$env:SECRET_KEY = "<set-a-random-secret-in-your-deployment-environment>"
$env:SESSION_COOKIE_SECURE = "1"
```

## Testing

Run tests with:

```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Troubleshooting

### Module errors

If you see import errors, reinstall dependencies:

```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Database issues

Delete the local SQLite database and restart the app if the database is corrupted:

```

```powershell
Remove-Item .\agriconnect.db
python app.py
```

### Port already in use

If port 5000 is already in use, stop the existing process or change the port in `app.py`.

## Academic documentation

The `docs/` folder contains chapter files and project diagrams that are preserved for the assignment. The application code is separate and is meant to support the project implementation described in the academic documentation.

## AI and market insights

The dashboard now uses the shared AI services in `ai/models.py`:

- Seasonal crop price regression for tomatoes, maize, potatoes, beans, groundnuts, onions, and cabbage, trained against `ai/market_price_history.csv`.
- Demand scoring from active listing stock and actual pending/accepted order activity, with transparent lower-confidence demo priors when no orders have been recorded.
- Crop suitability ranking from entered rainfall, temperature, season, and province.
- Market trend comparison from the bundled monthly sample price series.

These are demonstration decision-support estimates, not live market quotes or verified agronomic advice. The included history is illustrative because verified monthly source data is not supplied with the project. Replace it with documented, local market observations before drawing real-world conclusions.

All three scripts call the same shared model code as the dashboard and can be run from the project root:

```powershell
.\.venv\Scripts\python.exe ai\price_prediction.py --month 11
.\.venv\Scripts\python.exe ai\crop_recommendation.py --rainfall 650 --temperature 24 --season summer --province Midlands
.\.venv\Scripts\python.exe ai\demand_forecasting.py --season summer
```

## Demo marketplace data

On initialization, the app safely seeds 50 realistic sample listings: ten produce/input types across Harare, Gweru, Mutare, Masvingo, and Bulawayo. A tracking table prevents duplicates on subsequent launches. Existing app users and listings are preserved. Demo seller accounts have randomly generated, undisclosed passwords and are not intended for login.
