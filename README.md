AI-Finance-System/
│
├── django_backend/
│   │
│   ├── banking_system/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── finance/
│   │   ├── migrations/
│   │   │
│   │   ├── management/
│   │   │   └── commands/
│   │   │       ├── generate_users.py
│   │   │       ├── generate_accounts.py
│   │   │       └── generate_transactions.py
│   │   │
│   │   ├── services/
│   │   │   ├── fraud_service.py
│   │   │   ├── forecast_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── gemini_service.py
│   │   │
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tests.py
│   │   └── admin.py
│   │
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── .gitignore
└── README.md