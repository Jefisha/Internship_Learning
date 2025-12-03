from pymongo import MongoClient
from urllib.parse import quote_plus

# ===========================
# REQUIRED CONFIG
# ===========================

USERNAME = "your_db_user"
PASSWORD = "your password"  
CLUSTER_URL = "cluster0.r1tnwlw.mongodb.net"

# Escape password properly
escaped_password = quote_plus(PASSWORD)

# Build the correct MongoDB URI
uri = f"mongodb+srv://{USERNAME}:{escaped_password}@{CLUSTER_URL}/?retryWrites=true&w=majority"

# Connect to MongoDB Atlas
client = MongoClient(uri)
db = client["testdb"]
students = db["students"]

print("Connected to MongoDB Atlas!")


# --------------------
# CREATE
# --------------------
def create_student(name, email):
    doc = {"name": name, "email": email}
    result = students.insert_one(doc)
    print("Created student with ID:", result.inserted_id)


# --------------------
# READ
# --------------------
def read_students():
    print("All students:")
    for s in students.find():
        print(s)


# --------------------
# UPDATE
# --------------------
def update_student(name, new_email):
    result = students.update_one({"name": name}, {"$set": {"email": new_email}})
    print("Updated count:", result.modified_count)


# --------------------
# DELETE
# --------------------
def delete_student(name):
    result = students.delete_one({"name": name})
    print("Deleted count:", result.deleted_count)

while True:
    print("\n----- MENU -----")
    print("1. Create student")
    print("2. Read all students")
    print("3. Update student")
    print("4. Delete student")
    print("5. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        name = input("Enter name: ")
        email = input("Enter email: ")
        create_student(name, email)

    elif choice == "2":
        read_students()

    elif choice == "3":
        name = input("Enter name to update: ")
        new_email = input("Enter new email: ")
        update_student(name, new_email)

    elif choice == "4":
        name = input("Enter name to delete: ")
        delete_student(name)

    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")



