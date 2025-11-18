# OpenCV (cv2) and Pyzbar are used for camera access and barcode scanning,
# but they are commented out for testing in environments without a physical camera.
# import cv2
# import pyzbar.pyzbar as pyzbar
import cv2
import pyzbar.pyzbar as pyzbar

# Firebase Admin SDK for interacting with Firestore.
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# easygui is used for simple GUI elements, but it's often best replaced by a
# standard terminal interface (print) for cross-environment compatibility.
import easygui as e

# Firebase Initialization
# WARNING: Storing the service account JSON key directly in the code is
# not secure for production. Use environment variables or a dedicated
# authentication service in a real deployment.
try:
    # Load the service account credentials from the JSON file.
    cred = credentials.Certificate(
        "smart-basket-90f82-firebase-adminsdk-jns92-99b59e40f0.json"
        )
    # Initialize the Firebase app with the loaded credentials.
    firebase_admin.initialize_app(cred)
    # Get a Firestore client instance.
    db = firestore.client()
    # Reference to the 'items' collection in the Firestore database.
    doc_ref = db.collection("items")
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    # In a real application, you'd want to handle this error
    # to prevent the app from crashing.


# Barcode Scanning Logic (Currently Mocked)
def scan_barcode():
    """
    Attempts to scan a barcode using the webcam (cv2).

    In this current version, the webcam logic is commented out, and a
    hardcoded ID is returned for testing the Firestore lookup functionality.

    Returns:
        str or None: The barcode data string (e.g., product ID) if found,
                     otherwise returns None.
    """

    # --- REAL-WORLD WEBCAM LOGIC (Commented out for sandbox testing) ---
    # cap = cv2.VideoCapture(0)  # Open the default camera (index 0)
    # if not cap.isOpened():
    #     print("Error: Could not open camera.")
    #     return None
    #
    # ret, frame = cap.read() # Capture a single frame
    # if ret:
    #     barcodes = pyzbar.decode(frame) # Decode barcodes in the frame
    #     for barcode in barcodes:
    #         barcode_data = barcode.data.decode("utf-8")
    #         cap.release() # Release the camera hardware
    #         cv2.destroyAllWindows()
    #         return barcode_data
    #
    # cap.release()
    # cv2.destroyAllWindows()

    # MOCKED DATA FOR TESTING
    print("--- Simulating Barcode Scan ---")
    barcode_data = "rtSK21qfunPHD9CFULuu"  # Hardcoded ID corresponding to a Firestore document
    return barcode_data
    # return None # Uncomment to test failure case


def sample():
    """
    Provides a different sample barcode data for alternative testing.

    Returns:
        str: A sample barcode string.
    """
    print("Simulating Secondary Barcode Scan")
    barcode_data1 = "15235253435"  # Example of a non-existent/different product ID
    return barcode_data1


# Firestore Data Retrieval
def get_product_info(data):
    """
    Retrieves product information from Firestore based on the barcode data (document ID).

    Args:
        data (str): The barcode data, which is used as the Firestore document ID.

    Returns:
        tuple (str, float) or (None, None): A tuple containing (itemName, itemPrice)
        if the product is found, otherwise (None, None).
    """
    print(f"Attempting to look up product with ID: {data}")
    try:
        # Get the specific document using the barcode data as the ID.
        query = doc_ref.document(data).get()
    except Exception as e:
        print(f"Firestore query failed: {e}")
        return None, None

    # Check if the document exists in the database.
    if query.exists:
        item_data = query.to_dict()
        # Extract fields, using .get() for safety against missing keys.
        itemName = item_data.get("itemName", "Unknown Item")
        itemPrice = item_data.get("itemPrice", 0.0) # Default to 0.0 if price is missing
        print(f"Found Item: {itemName}, Price: {itemPrice}")
        return itemName, itemPrice
    else:
        print(f"Error: Product ID '{data}' not found in database.")
        return None, None

# Main Execution Block
if __name__ == "__main__":
    # The main block executes when the script is run directly.

    # Simulate the primary barcode scan
    barcode = scan_barcode()

    if barcode:
        # Look up the product info using the scanned barcode
        name, price = get_product_info(barcode)

        if name and price:
            print("\n--- SUCCESSFULLY SCANNED PRODUCT ---")
            print(f"Product Name: {name}")
            print(f"Product Price: ${price:.2f}")
            print("------------------------------------")

            # Here, you would typically add the item to a shopping basket or display it in the UI.
        else:
            print("\nProduct lookup failed. The ID may not exist in the database.")
    else:
        print("\nBarcode scanning failed. No data was captured.")
