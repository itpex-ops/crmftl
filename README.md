# Parcelex ops

A Django-based logistics and transport management platform for handling enquiries, orders, tracking, fleet coordination, billing, and operations.

## 🚀 Features
* Enquiry Management
* Order Management
* Enquiry to Order Conversion
* Load / Shipment Tracking
* Vehicle Assignment
* Invoice & E-Way Tracking
* Fleet Advance Tracking
* Settlement Workflow
* Admin Dashboard
* Customer Tracking Portal
* Responsive UI

## 🛠️ Tech Stack

* Python
* Django
* HTML / CSS / JavaScript
* Bootstrap
* SQLite (development)
* PostgreSQL (production recommended)
* Nginx
* Gunicorn

## 📦 Installation

```bash
git remote add origin https://github.com/itpex-ops/pex_ops.git
cd yourrepo
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 🌐 Production Deployment

Recommended hosting:

* DigitalOcean Ubuntu Droplet
* PostgreSQL
* Gunicorn
* Nginx
* SSL with Certbot

## 📁 Project Structure

```text
project/
├── app/
├── templates/
├── static/
├── manage.py
└── requirements.txt
```

## ⚙️ Environment Notes

Update `settings.py` for production:

* `DEBUG = False`
* Add domain to `ALLOWED_HOSTS`
* Configure PostgreSQL database

## 🔒 Security

* Use strong admin passwords
* Enable HTTPS
* Restrict server SSH access
* Keep dependencies updated

## 📈 Future Improvements

* API integration
* Customer notifications
* Analytics dashboard
* Role-based access control
* Mobile app support

## 👤 Author

Parcelex ops Team

## 📄 License

Private / Proprietary Project
