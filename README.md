
# ✅ **A) README.md (Production Quality)**

Create a file at:
# **ConvoNest – WhatsApp SaaS Platform (Django + Next.js + PostgreSQL)**

ConvoNest is a modern WhatsApp Automation & Messaging SaaS platform designed for MSMEs, startups, and enterprises.
It provides end-to-end messaging automation, template management, campaign workflows, and multi-channel customer engagement.

This monorepo includes:

* **Backend:** Django + Django REST Framework
* **Frontend:** Next.js (App Router)
* **Database:** PostgreSQL
* **Messaging:** WhatsApp Cloud API (Meta)
* **Architecture:** Modular, scalable, API-driven

---

## 🚀 Tech Stack

### **Backend**

* Python 3.11
* Django 5.x
* Django REST Framework
* PostgreSQL
* psycopg
* CORS + JWT Authentication

### **Frontend**

* Next.js 14 (App Router)
* TypeScript
* Axios
* TailwindCSS
* App directory routing
* API layer with axios client

### **Integration**

* WhatsApp Cloud API
* Webhooks (real-time message handling)
* Template Management (Meta Business APIs)
* Campaign Engine (bulk message dispatcher)

---

## 📂 Project Structure

```
convonest/
│
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── contacts/
│   │   ├── messaging/
│   │   ├── templates/
│   │   ├── campaigns/
│   │   ├── webhooks/
│   │   └── calls/
│   ├── convonest/
│   └── manage.py
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── (auth)/login/page.tsx
    │   │   ├── (auth)/signup/page.tsx
    │   │   ├── dashboard/page.tsx
    │   │   ├── templates/page.tsx
    │   │   ├── campaigns/page.tsx
    │   │   ├── contacts/page.tsx
    │   │   └── settings/page.tsx
    │   ├── components/
    │   ├── lib/apiClient.ts
    │   └── styles/
    └── package.json
```

---

## 🛠 Backend Setup (Django)

### Create virtual environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set up PostgreSQL

Update `backend/convonest/settings.py`:

```python
DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "convonest",
    "USER": "convonest_user",
    "PASSWORD": "your_password",
    "HOST": "localhost",
    "PORT": "5432",
  }
}
```

### Run migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 💻 Frontend Setup (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:
**[http://localhost:3000](http://localhost:3000)**

---

## 🔗 WhatsApp Cloud API Integration

ConvoNest supports:

* Send Text Messages
* Send Templates
* Media Messages
* Interactive Buttons
* Lists
* Carousels
* Location Request
* Mark-as-read
* Typing Indicators
* Webhooks
* Template Preview API
* Campaign Sending

Incoming messages are handled by the webhook module.

---

## 🧩 Environment Variables

Example `.env` (backend):

```
WHATSAPP_VERIFY_TOKEN=xxxx
WHATSAPP_ACCESS_TOKEN=xxxx
WHATSAPP_PHONE_ID=xxxx
WHATSAPP_BUSINESS_ID=xxxx
```

---

## 📈 Development Status

| Module          | Status        |
| --------------- | ------------- |
| User Auth       | ✔ In progress |
| Contacts        | ✔ MVP ready   |
| Templates       | ⏳ ongoing     |
| Messaging       | ⏳ ongoing     |
| Campaign Engine | 🔜 planned    |
| Webhooks        | ⏳ ongoing     |
| Calls API       | 🔜 planned    |

---

## 🤝 Contributing

1. Create feature branch
2. Commit changes
3. Open PR into `dev`
4. Once reviewed → merge into `main`

---

## 📜 License

Private SaaS repository. All rights reserved.

---

# ⭐ **B) GitHub Branch Strategy (Professional SaaS Workflow)**

This is the cleanest, real-world strategy for SaaS:

---

# **🌳 Branch Structure**

```
main        → Production (stable)
dev         → Development (active work)
feature/*   → Individual features
fix/*       → Bug fixes
hotfix/*    → Urgent production issues
```

---

## 🔥 **1. main (production-ready)**

* Contains only tested, stable, deployable code
* You merge into `main` **only via Pull Request from dev**

---

## 🧪 **2. dev (active development)**

* Developers merge features here
* CI/CD tests run here
* When dev is stable → merge into `main`

Create dev:

```bash
git checkout -b dev
git push -u origin dev
```

---

## 🧩 **3. feature branches**

For every feature/module:

```
feature/auth-login
feature/contacts-api
feature/templates-builder
feature/send-message
feature/campaign-engine
```

Create:

```bash
git checkout -b feature/contacts-api
```

After finishing:

```bash
git add .
git commit -m "Contacts API done"
git push origin feature/contacts-api
```

Open PR into **dev**.

---

## 🛠 **4. fix branches**

For bugs:

```
fix/template-preview-bug
fix/postgres-permission
```

---

## 🔥 **5. hotfix branches**

For emergencies on production:

```
hotfix/broken-send-template
```

PR → main
Then PR → dev (to sync fixes)


