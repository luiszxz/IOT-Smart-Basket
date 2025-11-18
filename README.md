Smart Basket

IoT-Powered Automated Shopping System

Overview
Smart Basket is an innovative shopping solution that uses RFID technology to automatically detect grocery items when placed into the basket. It displays item name, price, quantity, and total cost in real time. At checkout, the system generates a QR code containing all product details so the cashier can scan everything at once, eliminating long queues and manual item scanning.

Key Features
- RFID Scanning – Automatically identifies items when dropped into the basket.
- Budget Input & Monitoring – Users can enter a spending limit, and the system alerts them when the total cost approaches or exceeds their budget.
- Real-Time Item Tracking – Displays item name, price, quantity, and total cost.
- Quantity & Cost Monitoring – Updates dynamically when items are added or removed.
- QR Code Generation – Displays all product information for fast cashier scanning.
- Faster Checkout – No barcode scanning, no manual entry — just scan the QR code.
- IoT Integration – Uses Raspberry Pi, ESP8266, and Wi-Fi module for communication.
- Firebase Integration – Cloud sync for transaction data, inventory, and user management.

How Firebase Is Used
- Realtime sync: Keep the basket state and totals synchronized to the cloud so multiple devices (e.g., cashier console, admin dashboard) see updates instantly.
- Transactions: Save each checkout (items, quantities, total, timestamp) to Firestore / Realtime DB for reporting and auditing.
- Inventory links: Update inventory counts when items are checked out (if store chooses to sync).
- Authentication & Security: Use Firebase Auth rules to restrict access to admin/cashier features.
- Optional Analytics / Cloud Functions: Trigger server-side functions on checkout for receipts, email notifications, or integration with POS.

How It Works (Process Flow)
- Customer places an item into the basket.
- RFID module detects the product.
- System displays item details & updates total (locally and optionally to Firebase).
- After shopping, user clicks “Generate QR Code.”
- QR code appears with full purchase summary.
- Cashier scans QR code to retrieve all data instantly (can read from Firebase or decode QR).
- Transaction saved to Firebase for records and reporting.

Project Structure
The application logic is cleanly separated into two primary files:
- main.py: Contains all User Interface (UI) and event handling logic (buttons, display updates, budget checking, checkout process). This runs the main Tkinter loop.
- firestore_py.py: Manages all Backend Logic including Firebase initialization, querying the Firestore database, and running the dedicated, continuous scanning thread that signals item changes back to the GUI.

Setup and Installation

Follow these steps to set up the Smart Basket system locally.
1. Prerequisites

You must have Python 3.8+ installed. The project also requires a set of external libraries.

2. Dependencies
Install all necessary Python libraries using pip:

pip install customtkinter pillow qrcode firebase-admin opencv-python pyzbar

Firebase Configuration
The firestore_py.py file requires a secure connection to your Firebase project.
- Get Service Account Key: In your Firebase console, go to Project Settings > Service accounts.
- Click Generate new private key and download the JSON file.
- Rename and Place: Place this downloaded JSON file in the project root directory and ensure its name matches the path used in firestore_py.py:

cred = credentials.Certificate("smart-basket-90f82-firebase-adminsdk-jns92-99b59e40f0.json")

Running the Application
Execute the main GUI file to start the system:

python smart_basket_gui.py
