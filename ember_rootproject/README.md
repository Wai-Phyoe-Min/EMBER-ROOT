# 🔥 EMBER & ROOT — Wood-Fired Pizza Restaurant Website
## Full-Stack Django + Bootstrap 5 Project

---

## 📁 Project Structure
EMBER-ROOT/
├── manage.py
├── requirements.txt
├── README.md
│
├── ember_rootproject/ # Django project config
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
│
├── ember_rootapp/ # Main Django app
│ ├── models.py # DB models (User, Pizza, Order, etc.)
│ ├── views.py # All views + REST-like API endpoints
│ ├── urls.py # URL routing
│ ├── forms.py # Django forms (Contact, Auth, etc.)
│ ├── admin.py # Admin panel config
│ ├── decorators.py # Custom decorators
│ ├── migrations/
│ └── templates/ember_rootapp/
│ ├── base.html # Master layout (navbar, footer, modals)
│ ├── index.html # Landing page (hero, featured, philosophy)
│ ├── menu.html # Full menu with category filters
│ ├── story.html # Founder story + farm partners
│ ├── distance.html # Interactive 120km farm map
│ ├── visit.html # Location, hours, transportation
│ ├── contact.html # Contact form + FAQ
│ ├── faq.html # FAQs with dynamic counts
│ ├── dashboard.html # User dashboard (orders, favorites)
│ ├── auth.html # Login/Registration (AJAX)
│ ├── privacy.html # Privacy policy
│ ├── terms.html # Terms of service
│ └── admin/
│ └── dashboard.html # Admin dashboard (CRUD, orders)
│
├── static/
│ ├── css/
│ │ └── style.css # Full custom stylesheet
│ └── js/
│ └── main.js # Frontend logic (cart, auth, modals)
│
└── media/ # Uploaded images (pizzas, pairings)

text

---

## 🚀 Quick Start

### 1. Clone & create virtual environment
```bash
git clone https://github.com/Wai-Phyoe-Min/EMBER-ROOT.git
cd EMBER-ROOT
python -m venv venv
source venv/bin/activate                    # Windows: venv\Scripts\activate

### 2. Install dependencies
```bash
pip install -r requirements.txt

### 3. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate

### 4. Create admin user
```bash
python manage.py createsuperuser

### 5. Start development server
```bash
python manage.py runserver
Open: http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin

✨ Features
Frontend
Feature	Details
Dynamic content	Farm/pizza counts, hours, closing times via API
Interactive maps	Leaflet maps with draggable farm markers (120km radius)
Real-time cart	Session-based cart with pairing suggestions
AJAX forms	Login, register, contact — no page reload
Real-time validation	Live form validation with visual feedback
Category filters	Menu filtering (All/Classics/Signature/White/Seasonal)
Favorites system	Save favorite pizzas (localStorage + server sync)
Order tracking	Real-time order status updates
Toast notifications	Animated confirmations for cart actions
Responsive design	Mobile-first, Bootstrap 5 grid
Scroll animations	IntersectionObserver fade-in on scroll
Particle background	Animated floating particles on auth page
Password strength meter	Real-time password strength indicator

Backend (Django)
Feature	Details
Custom User Model	Email-based authentication, user types (customer/admin)
Models	User, Pizza, MenuItem, Order, Favorite, ContactMessage, BusinessHours, UserActivity
Session Cart	Add/remove/update cart via localStorage + AJAX sync
Order system	Place orders, status tracking (pending → confirmed → preparing → ready → completed)
Contact messages	Admin reply system with unread indicators
Business hours	Dynamic hours management with live preview
Real-time availability	Open/closed status based on current time
Admin dashboard	Full CRUD for pizzas, menu items, orders, customers, messages, hours
Image upload	Upload pizza images + pairing images with preview
Interactive farm map	Drag/drop markers to set farm coordinates
API endpoints	REST-like JSON endpoints for dynamic data
Export orders	CSV export for order management
Soft delete	Account deletion with confirmation

API Endpoints
Endpoint	Method	Description
/api/pizzas/	GET	Returns all available pizzas
/api/business-hours/	GET	Returns business hours
/api/stats/	GET	Returns farm and pizza counts
/ajax/login/	POST	AJAX login handler
/ajax/register/	POST	AJAX registration handler
/ajax/submit-contact/	POST	Contact form submission
/ajax/place-order/	POST	Order placement
/ajax/favorite/<id>/	POST	Toggle favorite pizza
/ajax/order-history/	GET	User's order history

Pages Overview
Page	URL	Description
Home	/	Hero section, featured pizzas, philosophy cards
Menu	/menu/	Full menu with category filters, diet tags
Story	/story/	Founder story, timeline, farm partners
Distance	/distance/	Interactive farm map (120km sourcing radius)
Visit	/visit/	Location, hours, transportation, ambiance gallery
Contact	/contact/	Contact form with real-time validation
FAQ	/faq/	Frequently asked questions with search
Dashboard	/dashboard/	User orders, favorites, profile management
Auth	/auth/	Login/Registration (AJAX, password strength)
Admin Dashboard	/admin-dashboard/	Full admin panel (CRUD, orders, messages, hours)

Admin Dashboard Features
Feature	Details
Dashboard stats	Revenue, orders, customers, new messages
Pizza management	Create/Edit/Delete pizzas (name, price, description, farm, coordinates, images, pairing)
Menu items	Manage sides and drinks
Order management	Update status, view details, export CSV
Customer management	View and delete customer accounts
Message center	Read and reply to customer inquiries
Business hours	Set daily hours with closed status and notes
Image preview	Upload images with live preview
Interactive map	Drag/drop farm location markers