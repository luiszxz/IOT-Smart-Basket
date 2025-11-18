import tkinter as tk
from PIL import Image, ImageTk
import qrcode
import threading
import time
import os
import customtkinter

# Import the backend logic from the separate file
import firestore
from firestore import scan_barcode, get_product_info

# --- IMPORTANT SETUP NOTES ---
# 1. This script requires a local image file named 'savers.png' for the logo.
# 2. It requires a local image file named 'warning.jpg' for the error box.
# 3. It expects a directory structure 'items/item_name.png' for product images.
# 4. The 'firestore_py.py' file must be in the same directory.
# -----------------------------

# Global variables for basket state and UI elements
global items, total, budget, total_label, budget_label_display, rows_frame, button_frame
items = {}  # Stores items: {unique_key: {'price': p, 'quantity': q, 'itemName': n}}
total = 0.0  # Current basket total
budget = 0.0  # Set budget amount

IMAGE_PATH = "items"  # Directory where item images are stored


def init(root):
    """Initializes the main application window and GUI components."""
    root.title("Sentinels Smart Basket")
    # Fixed size for kiosk/device screen simulation
    root.geometry("800x480")
    root.configure(bg="#FFC4C4")

    # Configure grid weights for responsive layout
    root.grid_rowconfigure(0, weight=1)  # Title row
    root.grid_rowconfigure(1, weight=1)  # Placeholder row (now combined with 2)
    root.grid_rowconfigure(2, weight=3)  # Main content area (list + buttons)
    root.grid_rowconfigure(3, weight=0)  # Footer/Bottom row

    # --- Header/Title Frame ---
    title_frame = tk.Frame(root, bg="#FFC4C4")
    title_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10)
    title_frame.grid_columnconfigure(0, weight=1)  # Center content

    # Load and display the logo image
    try:
        logo_image = Image.open("savers.png")
        logo_image = logo_image.resize((200, 50), Image.Resampling.LANCZOS)
        logo_tk = ImageTk.PhotoImage(logo_image)

        global logoImage  # Keep a reference to prevent garbage collection
        logoImage = logo_tk

        image_label = tk.Label(title_frame, image=logoImage, bg="#FFC4C4")
        image_label.pack(side=tk.LEFT, padx=10, pady=5)
    except FileNotFoundError:
        tk.Label(title_frame, text="Sentinels Smart Basket", bg="#FFC4C4", font=("Arial", 20, "bold")).pack(
            side=tk.LEFT, padx=10, pady=5)
        print("Warning: 'savers.png' not found. Using text title instead.")

    # --- Main Content Frame (List and Buttons) ---
    global bottom_frame
    bottom_frame = tk.Frame(root, bg="#FFC4C4")
    bottom_frame.grid(row=1, column=0, columnspan=2, rowspan=2, sticky="nsew")  # Spans across rows 1 and 2
    bottom_frame.grid_rowconfigure(0, weight=1)
    bottom_frame.grid_columnconfigure(0, weight=3)  # List column wider
    bottom_frame.grid_columnconfigure(1, weight=1)  # Button column narrower

    # --- Item List Frame (Scrollable) ---
    global table_frame
    table_frame = customtkinter.CTkScrollableFrame(
        bottom_frame,
        height=300,
        width=450,
        label_text="Shopping List",
        label_font=("Arial", 14, "bold"),
        fg_color="#F0F0F0",
    )
    table_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    table_frame.grid_columnconfigure(0, weight=1)  # Item Name (Wide)
    table_frame.grid_columnconfigure(1, weight=0)  # Price (Fixed)
    table_frame.grid_columnconfigure(2, weight=0)  # Quantity (Fixed)

    # Table Headers
    tk.Label(table_frame, text="Item", bg="#F0F0F0", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w",
                                                                                      padx=(10, 5), pady=(8, 5))
    tk.Label(table_frame, text="Price", bg="#F0F0F0", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w",
                                                                                       padx=(5, 5), pady=(8, 5))
    tk.Label(table_frame, text="Qty", bg="#F0F0F0", font=("Arial", 12, "bold")).grid(row=0, column=2, sticky="w",
                                                                                     padx=(5, 10), pady=(8, 5))

    underline_frame = tk.Frame(table_frame, height=2, bg="#CB4949")
    underline_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10), padx=8)

    # Frame to hold the actual item rows
    global rows_frame
    rows_frame = tk.Frame(table_frame, bg="#F0F0F0")
    rows_frame.grid(row=2, column=0, columnspan=3, sticky="nsew")
    # Note: Column configurations should ideally be inside update_display for dynamic layout,
    # but we set them here for initial structure.
    rows_frame.grid_columnconfigure(0, weight=1)
    rows_frame.grid_columnconfigure(1, weight=0)
    rows_frame.grid_columnconfigure(2, weight=0)

    # --- Control Buttons and Total Frame ---
    global button_frame
    button_frame = tk.Frame(bottom_frame, bg="#FFC4C4")
    button_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # Configure button frame layout
    for i in range(7):
        button_frame.grid_rowconfigure(i, weight=1)
    button_frame.grid_columnconfigure(0, weight=1)

    # Budget Display
    global budget_label_display
    budget_label_display = tk.Label(button_frame, text="Budget: ₱0.00", bg="#FFC4C4", fg="#555555",
                                    font=("Arial", 12, "bold"))
    budget_label_display.grid(row=2, column=0, sticky="s", padx=5, pady=(5, 2))

    # Set Budget Button
    global set_budget_button
    set_budget_button = tk.Button(button_frame, text="Set Budget", command=show_budget_entry, bd=0, fg="white",
                                  bg="#CB4949", font=("Sans-Serif", 12, "bold"), height=2)
    set_budget_button.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)

    # Separator
    tk.Label(button_frame, text="—", bg="#FFC4C4").grid(row=4, column=0, pady=5)

    # Total Label
    global total_label
    total_label = tk.Label(
        button_frame,
        text=f"₱0.00",
        bg="#FFC8C8",
        fg="#B30000",
        font=("Arial", 18, "bold"),
        bd=2,
        relief="solid"
    )
    total_label.grid(row=5, column=0, sticky="nsew", padx=5, pady=2)

    # Checkout Button
    qr_button = tk.Button(button_frame, text="Checkout", command=checkout, bd=0, fg="white", bg="#4C78A8",
                          font=("Sans-Serif", 12, "bold"), height=2)
    qr_button.grid(row=6, column=0, sticky="nsew", padx=5, pady=(10, 5))

    # Start the continuous scanning loop after a short delay
    root.after(500, auto_scan)


def auto_scan():
    """
    Starts the continuous scanning thread and defines the callback for updates.
    """

    # The callback function called by the threaded scanner (firestore_py.scan_barcode)
    def update_display_from_scan(product, tag):
        """Processes a single scan event (add or remove) and updates the basket state."""
        global items

        if not product:
            print("Product not found in the database. Ignoring scan.")
            return

        name = product['itemName']
        price = float(product['itemPrice'])
        unique_key = tag  # The full tag is the unique key (e.g., RT101_U12345...)

        # Check if the unique tag is already in the 'items' dictionary
        if unique_key in items:
            # Item exists, this means the scanner *removed* the tag.
            # In our simulation, the backend only reports a scan. The GUI logic
            # for adding/removing items based on tag is complex for this structure.
            # A simple implementation: if the tag exists, remove it. If it doesn't, add it.

            # --- REMOVAL LOGIC ---
            # Remove the item completely from the unique items dictionary
            del items[unique_key]
            print(f"Removed unique tag: {unique_key}. Item: {name}")

        else:
            # --- ADDITION LOGIC ---
            # Item doesn't exist, add it to the unique items dictionary
            items[unique_key] = {'price': price, 'quantity': 1, 'itemName': name}
            print(f"Added unique tag: {unique_key}. Item: {name}")

        # Re-aggregate the items by name for display purposes
        aggregate_items = {}
        for details in items.values():
            item_name = details['itemName']
            item_price = details['price']

            if item_name not in aggregate_items:
                # Use the price from the current item as the list price
                aggregate_items[item_name] = {'price': item_price, 'quantity': 1,
                                              'image_path': os.path.join(IMAGE_PATH, f"{item_name}.png")}
            else:
                aggregate_items[item_name]['quantity'] += 1

        # Update the display using the aggregated item names and quantities
        root.after(0, lambda: update_display(aggregate_items))

    # Start barcode scanning in a separate, non-blocking thread
    # The scan_barcode function needs to be passed the callback.
    scanning_thread = threading.Thread(target=scan_barcode, args=(update_display_from_scan,))
    scanning_thread.daemon = True  # Allows the thread to exit when the main program does
    scanning_thread.start()


def show_budget_entry():
    """Replaces the 'Set Budget' button with an entry field and opens the keyboard."""
    global budget_entry, keyboard_window, set_budget_button, confirm_budget_button

    # Remove the button
    set_budget_button.grid_forget()

    # Create a new Entry box where the button was
    budget_entry = tk.Entry(button_frame, font=("Arial", 14), width=10, justify='center', bd=1, relief="solid")
    budget_entry.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)

    # Add a new button for confirming budget entry
    confirm_budget_button = tk.Button(button_frame, text="Confirm", command=set_budget_from_entry, bd=0, fg="white",
                                      bg="#64A048", font=("Sans-Serif", 12, "bold"))
    confirm_budget_button.grid(row=4, column=0, sticky="nsew", padx=5, pady=2)

    # Show the on-screen keyboard
    keyboard_window = show_on_screen_keyboard(budget_entry)


def key_press(button_text, entry_widget):
    """Handles key presses from the on-screen keyboard."""
    current_text = entry_widget.get()
    if button_text == "Clear":
        entry_widget.delete(0, tk.END)
    elif button_text == "Backspace":
        entry_widget.delete(len(current_text) - 1, tk.END)
    elif button_text.isdigit() or button_text == ".":
        # Only allow one decimal point
        if button_text == "." and "." in current_text:
            return
        entry_widget.insert(tk.END, button_text)


# Function to show the numerical on-screen keyboard
def show_on_screen_keyboard(entry_widget):
    """Creates a top-level window for the numerical keyboard."""
    keyboard_window = tk.Toplevel(root)
    keyboard_window.title("Enter Budget")
    keyboard_window.geometry("250x300")
    keyboard_window.configure(bg="#F0F0F0")

    # Grid configuration
    for i in range(4):
        keyboard_window.grid_rowconfigure(i, weight=1)
        keyboard_window.grid_columnconfigure(i % 3, weight=1)

    buttons = [
        '1', '2', '3',
        '4', '5', '6',
        '7', '8', '9',
        '.', '0', 'Backspace'
    ]

    for i, button_text in enumerate(buttons):
        if button_text == 'Backspace':
            display_text = 'DEL'
            bg_color = '#CB4949'
        elif button_text == '.':
            display_text = '.'
            bg_color = '#C0C0C0'
        else:
            display_text = button_text
            bg_color = '#FFFFFF'

        button = tk.Button(
            keyboard_window, text=display_text, width=8, height=2, bd=0,
            bg=bg_color, fg="black", font=("Arial", 14, "bold"),
            command=lambda text=button_text: key_press(text, entry_widget)
        )
        button.grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky="nsew")

    clear_button = tk.Button(keyboard_window, text="Clear", bd=0, bg="#4C78A8", fg="white", font=("Arial", 14, "bold"),
                             command=lambda: key_press("Clear", entry_widget))
    clear_button.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=3, pady=3)

    keyboard_window.grab_set()  # Modal behavior
    return keyboard_window


def set_budget_from_entry():
    """Sets the global budget from the entry field and checks for over-budget."""
    global budget
    amount = budget_entry.get()

    if 'keyboard_window' in globals() and keyboard_window:
        keyboard_window.destroy()

    try:
        budget = float(amount)
        budget_label_display.config(text=f"Budget: ₱{budget:.2f}")
        print(f"Budget set to: ₱{budget:.2f}")

        # Remove entry and confirm button
        budget_entry.grid_forget()
        confirm_budget_button.grid_forget()

        # Show the set_budget_button again
        set_budget_button.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)

        # Check if the total exceeds the budget
        if total > budget:
            show_custom_error("Budget Alert", f"Your current total (₱{total:.2f}) exceeds the budget (₱{budget:.2f})!")

    except ValueError:
        show_custom_error("Invalid Input", "Please enter a valid number for the budget.")


def show_custom_error(title, message="Error occurred"):
    """Displays a custom modal error/alert message."""
    # Create a new window for the error message
    error_window = tk.Toplevel(root)
    error_window.title(title)
    error_window.geometry("300x150")
    error_window.configure(bg="#FFC4C4")
    error_window.resizable(False, False)

    # Center the window
    x = root.winfo_x() + root.winfo_width() // 2 - 150
    y = root.winfo_y() + root.winfo_height() // 2 - 75
    error_window.geometry(f'+{x}+{y}')

    # Try to load a warning image
    try:
        img = Image.open("warning.jpg")
        img = img.resize((30, 30), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        global warningImage
        warningImage = img_tk
        image_label = tk.Label(error_window, image=warningImage, bg="#FFC4C4")
        image_label.pack(pady=5)
    except Exception:
        tk.Label(error_window, text="⚠️", font=("Arial", 20), bg="#FFC4C4").pack(pady=5)

    # Display the error message
    error_label = tk.Label(error_window, text=message, font=("Arial", 10), wraplength=250, bg="#FFC4C4")
    error_label.pack(pady=5)

    # OK button to close the error window
    ok_button = tk.Button(error_window, text="OK", command=error_window.destroy, bd=0, fg="white", bg="#CB4949")
    ok_button.pack(pady=5)

    error_window.grab_set()  # Modal behavior


def reset_basket():
    """Resets the shopping basket state and updates the display."""
    global items, total
    items = {}
    total = 0.0

    # Re-aggregate an empty list to clear the display
    update_display({})

    if 'qr_window' in globals() and qr_window:
        qr_window.destroy()


def checkout():
    """Generates a QR code containing the final basket contents and total."""
    global qr_window

    if not items:
        show_custom_error("Basket Empty", "Please add items before checking out.")
        return

    # Prepare data for the QR code
    qr_data = "Sentinels Smart Basket Checkout:\n"
    # Re-aggregate for a nice printout (as update_display does)
    aggregate_items = {}
    for details in items.values():
        item_name = details['itemName']
        item_price = details['price']
        if item_name not in aggregate_items:
            aggregate_items[item_name] = {'price': item_price, 'quantity': 1}
        else:
            aggregate_items[item_name]['quantity'] += 1

    for name, details in aggregate_items.items():
        qty = details['quantity']
        price = details['price']
        qr_data += f"{name} ({qty}x) @ ₱{price:.2f} each\n"

    qr_data += f"\nTOTAL: ₱{total:.2f}"

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,  # Smaller box size for better fit on screen
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill='black', back_color='white')
    qr_img.save("basket_qr.png")

    qr_img_tk = ImageTk.PhotoImage(Image.open("basket_qr.png"))

    # Create QR Display Window
    qr_window = tk.Toplevel(root)
    qr_window.title("Checkout QR Code")
    qr_window.configure(bg="#FFC4C4")

    # Center the window
    x = root.winfo_x() + root.winfo_width() // 2 - 150
    y = root.winfo_y() + root.winfo_height() // 2 - 150
    qr_window.geometry(f'300x350+{x}+{y}')

    qr_label = tk.Label(qr_window, image=qr_img_tk, bg="white")
    qr_label.image = qr_img_tk
    qr_label.pack(pady=10)

    tk.Label(qr_window, text="Scan this code at the payment terminal.", bg="#FFC4C4", font=("Arial", 10)).pack()

    # Finish Shopping button
    finish_button = tk.Button(qr_window, text="Finish Shopping / Reset", command=reset_basket, bd=0, fg="white",
                              bg="#4C78A8", font=("Sans-Serif", 12), padx=10, pady=8)
    finish_button.pack(pady=10)

    qr_window.grab_set()


def update_display(aggregate_items):
    """
    Clears and redraws the item list based on the aggregated items.

    Args:
        aggregate_items (dict): A dictionary of items aggregated by name,
                                containing total quantity and price.
    """
    global total, total_label, budget, budget_label_display, item_image_references

    # Clear all existing item row widgets
    for widget in rows_frame.winfo_children():
        widget.destroy()

    # Need to keep track of image references to prevent garbage collection
    item_image_references = []
    row_number = 0

    # Sort items alphabetically for better readability
    sorted_items = sorted(aggregate_items.items(), key=lambda item: item[0])

    for name, details in sorted_items:
        quantity = details['quantity']
        price = details['price']

        # --- Row Frame for the item ---
        item_row_frame = tk.Frame(rows_frame, bg="#F0F0F0")
        item_row_frame.grid(row=row_number, column=0, columnspan=3, sticky="ew", padx=5)
        item_row_frame.grid_columnconfigure(0, weight=1)  # Name
        item_row_frame.grid_columnconfigure(1, weight=0)  # Price
        item_row_frame.grid_columnconfigure(2, weight=0)  # Quantity

        # --- Image and Name (Column 0) ---
        product_frame = tk.Frame(item_row_frame, bg="#F0F0F0")
        product_frame.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Load the item image
        image_file = os.path.join(IMAGE_PATH, f"{name.lower().replace(' ', '_')}.png")  # Normalize filename

        item_image_tk = None
        if os.path.exists(image_file):
            try:
                item_image = Image.open(image_file)
                item_image = item_image.resize((40, 40), Image.Resampling.LANCZOS)
                item_image_tk = ImageTk.PhotoImage(item_image)
                item_image_references.append(item_image_tk)  # Store reference

                image_label = tk.Label(product_frame, image=item_image_tk, bg="#F0F0F0")
                image_label.pack(side=tk.LEFT, padx=(5, 10))
            except Exception:
                image_label = tk.Label(product_frame, text="🖼️", font=("Arial", 16), bg="#F0F0F0")
                image_label.pack(side=tk.LEFT, padx=(5, 10))
        else:
            image_label = tk.Label(product_frame, text="📦", font=("Arial", 16), bg="#F0F0F0")
            image_label.pack(side=tk.LEFT, padx=(5, 10))

        # Product name
        name_label = tk.Label(product_frame, text=name, bg="#F0F0F0", font=("Arial", 12, "bold"))
        name_label.pack(side=tk.LEFT)

        # Price (Column 1)
        tk.Label(item_row_frame, text=f"₱{price:.2f}", bg="#F0F0F0", font=("Arial", 12)).grid(row=0, column=1,
                                                                                              sticky="e", padx=(10, 20))

        # Quantity (Column 2)
        quantity_label = tk.Label(item_row_frame, text=f"{quantity}", bg="#F0F0F0", font=("Arial", 12))
        quantity_label.grid(row=0, column=2, sticky="e", padx=(10, 20))

        # Underline for separation
        underline_frame = tk.Frame(rows_frame, height=1, bg="#CB4949")
        underline_frame.grid(row=row_number + 1, column=0, columnspan=3, sticky="ew", padx=10)

        row_number += 2

    # --- Update Total ---
    # Calculate the new total based on the unique items dictionary
    total = sum(details['price'] * details['quantity'] for details in items.values())
    total_label.config(text=f"₱{total:.2f}")

    # Budget Check and Color Change
    if budget > 0 and total > budget:
        total_label.config(bg="#FF7777", fg="white", text=f"₱{total:.2f} (OVER)")  # Danger color
        show_custom_error("Budget Alert", f"Your total (₱{total:.2f}) is over your budget (₱{budget:.2f})!")
    elif budget > 0 and total > (budget * 0.9):
        total_label.config(bg="#FFD700", fg="black")  # Warning color
    else:
        total_label.config(bg="#C8FFC8", fg="#006400")  # Safe color


# Main Application Execution
root = tk.Tk()
try:
    init(root)
    root.mainloop()
except NameError as e:
    print(f"\nFATAL ERROR: A required asset or dependency is missing. Details: {e}")
    print("\nPLEASE ENSURE:")
    print("1. 'savers.png' and 'warning.jpg' are in the same directory.")
    print("2. The 'firestore_py.py' file is in the same directory.")
    print("3. There is an 'items' directory with product images (e.g., 'items/apple.png').")