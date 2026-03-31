# -
markdown
# 🛍️ Zain Store - Multi-Vendor E-Commerce Platform

A complete e-commerce solution with web interface (HTML/CSS/JS) and desktop application (Python/Tkinter), powered by Firebase.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Technologies Used](#technologies-used)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Usage](#usage)
7. [Firebase Configuration](#firebase-configuration)
8. [Screenshots](#screenshots)
9. [Future Improvements](#future-improvements)
10. [License](#license)
11. [Contact](#contact)

---

## 📖 Overview

Zain Store is a **multi-vendor e-commerce platform** that allows:

- **Customers** to browse and purchase products from multiple vendors
- **Vendors** to manage their own products and orders
- **Admin/Owner** to control the entire platform, manage users, and view analytics

The project has **two versions**:
- 🌐 **Web Version**: HTML/CSS/JS with Firebase (PWA ready)
- 💻 **Desktop Version**: Python/Tkinter application (EXE)

---

## ✨ Features

### 👤 For Customers
- Browse products from multiple vendors
- Filter products by category and vendor
- Add products to cart
- Track orders
- WhatsApp order confirmation

### 🏪 For Vendors
- Add, edit, and delete products
- View orders for their products
- Update order status
- Store analytics and statistics

### 👑 For Admin/Owner
- Complete user management (upgrade, suspend, delete)
- Product management (all products)
- Service management
- Sales analytics and statistics
- Backup system (JSON export)
- Commission system (ready)

### 🛠️ General Features
- PWA support (installable on mobile)
- Push notifications (OneSignal)
- Order tracking
- Professional services section
- Subscription plans (monthly, yearly, lifetime)

---

## 💻 Technologies Used

| Component | Technology |
|-----------|------------|
| **Frontend (Web)** | HTML5, CSS3, JavaScript |
| **Backend (Web)** | Firebase (Auth, Database, Hosting) |
| **Desktop App** | Python, Tkinter |
| **Database** | Firebase Realtime Database |
| **Authentication** | Firebase Auth |
| **Notifications** | OneSignal |
| **PWA** | Manifest, Service Worker |
| **Version Control** | Git, GitHub |

---

## 📁 Project Structure
test_research/
├── public/ # Web files (Firebase Hosting)
│ ├── index.html # Main store page
│ ├── my-store.html # Vendor dashboard
│ ├── sellers.html # Sellers management (admin)
│ ├── product.html # Product details page
│ ├── upgrade.html # Subscription upgrade
│ ├── services.html # Professional services
│ ├── manifest.json # PWA manifest
│ ├── service-worker.js # PWA service worker
│ └── icons/ # App icons (192px, 512px)
│
├── main.py # Desktop application (Python)
├── config.py # Firebase configuration
├── license_manager.py # License management
├── serviceAccountKey.json # Firebase service account (private)
├── requirements.txt # Python dependencies
├── README.md # This file
└── .gitignore # Git ignore file

text

---

## 🚀 Installation & Setup

### Web Version

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/test_research.git
   cd test_research/public
Set up Firebase

Create a Firebase project

Enable Authentication (Email/Password)

Enable Realtime Database

Update Firebase config in index.html and other files

Deploy to Firebase Hosting

bash
firebase init hosting
firebase deploy --only hosting
Access your store

text
https://your-project.web.app
Desktop Version (Python EXE)
Install Python 3.9+

Create virtual environment

bash
conda create -n myenv python=3.9
conda activate myenv
Install dependencies

bash
pip install -r requirements.txt
Run the application

bash
python main.py
Build EXE (optional)

bash
pyinstaller --onefile --name "ZainStore" --add-data "serviceAccountKey.json;." --add-data "config.json;." --hidden-import firebase_admin --hidden-import cryptography --hidden-import PIL --noconsole main.py
🔧 Firebase Configuration
Required Firebase Services
Authentication: Email/Password

Realtime Database: Data storage

Hosting: Web deployment (optional)

Storage: Product images (optional)

Database Structure
json
{
  "Products": { ... },           // Main products (admin)
  "VendorProducts": {            // Vendor products
    "vendor_uid": {
      "product_id": { ... }
    }
  },
  "users": {                     // User data
    "uid": {
      "email": "...",
      "role": "user/seller_monthly/seller_yearly/owner/trial",
      "phone": "...",
      "storeName": "..."
    }
  },
  "Services": { ... },           // Professional services
  "Orders": { ... }              // Order history
}
Security Rules
Firebase Rules are configured for:

Users can read their own data, admins can read all

Products are publicly readable

VendorProducts writable only by vendors

Orders writable by customers and admins

📱 Usage
Web Version
Open https://your-project.web.app

Register as a new user

Browse products and add to cart

Checkout and confirm via WhatsApp

Track orders using order ID

Desktop Version
Run python main.py

Login with your account

Vendors: Manage products in "My Store" section

Admin: Access "Security" and "Backup" panels

📸 Screenshots
(Add your screenshots here)

Home page with products

Vendor dashboard

Admin panel

Cart and checkout

🔮 Future Improvements
Implement commission system (10% for owner)

Add product ratings and reviews

Export reports to Excel

Multi-language support (Arabic/English)

Advanced analytics dashboard

Telegram bot for customer support

Privacy policy and terms of service pages

Payment gateway integration (Stripe/PayPal)

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

📞 Contact
Developer: Mr. Zain
Email: zain.koda@gmail.com
WhatsApp: +20 100 503 2186
Project Link: https://g10-sovereign.web.app

🙏 Acknowledgments
Firebase for backend services

Tkinter for desktop GUI

OneSignal for push notifications

All contributors and testers

Built with ❤️ by Mr. Zain


