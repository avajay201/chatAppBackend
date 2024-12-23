# import firebase_admin
# from firebase_admin import credentials, firestore

# # Initialize Firebase Admin SDK
# cred = credentials.Certificate("/home/ameo/Pictures/chatAppBackend/metrichat-adb11-firebase-adminsdk-6wuid-6b766e39b2.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# def delete_subcollection(doc_path, subcollection_name):
#     """Delete all documents in a specific subcollection."""
#     subcollection_ref = db.document(doc_path).collection(subcollection_name)
#     docs = subcollection_ref.stream()

#     for doc in docs:
#         print(f"Deleting document {doc.id} from subcollection {subcollection_name}")
#         subcollection_ref.document(doc.id).delete()

# def fetch_and_delete_subcollections():
#     """Fetch subcollections of a document and delete them."""
#     doc_ref = db.collection('meet').document('chatId')
#     subcollections = doc_ref.collections()

#     for subcollection in subcollections:
#         print(f"Deleting subcollection: {subcollection.id}")
#         if subcollection.id == 'test202':
#             delete_subcollection('meet/chatId', subcollection.id)

# # Call the function to fetch and delete subcollections
# fetch_and_delete_subcollections()


import turtle

# Set up the screen
screen = turtle.Screen()
screen.bgcolor("white")

# Create the turtle object
star = turtle.Turtle()
star.shape("turtle")
star.color("blue")
star.speed(3)

# Function to draw a star
def draw_star(size):
    for i in range(5):
        star.forward(size)
        star.right(144)

# Draw the star
draw_star(100)

# Hide the turtle after drawing
star.hideturtle()

# Keep the window open until it is clicked
screen.exitonclick()
