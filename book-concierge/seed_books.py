import sys
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-b5e9e11cd71a"

SEEDED_BOOKS = [
    {
        "id": "project-hail-mary",
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "genre": "Science Fiction",
        "synopsis": "A lone astronaut must save the earth from disaster using science, wit, and an unexpected ally.",
        "pages": 496,
        "rating": 4.8,
        "status": "want_to_read",
        "notes": "Highly recommended for fans of The Martian.",
    },
    {
        "id": "tomorrow-and-tomorrow",
        "title": "Tomorrow, and Tomorrow, and Tomorrow",
        "author": "Gabrielle Zevin",
        "genre": "Contemporary Fiction",
        "synopsis": "Two childhood friends partner up as video game creators and navigate fame, love, and tragedy over three decades.",
        "pages": 416,
        "rating": 4.6,
        "status": "reading",
        "notes": "Current favorite reading club pick.",
    },
    {
        "id": "the-name-of-the-wind",
        "title": "The Name of the Wind",
        "author": "Patrick Rothfuss",
        "genre": "Fantasy",
        "synopsis": "The tale of Kvothe, from his childhood in a troupe of traveling players to his years at the University learning magic.",
        "pages": 662,
        "rating": 4.7,
        "status": "read",
        "notes": "Beautiful prose and immersive worldbuilding.",
    },
    {
        "id": "atomic-habits",
        "title": "Atomic Habits",
        "author": "James Clear",
        "genre": "Self-Help",
        "synopsis": "An easy and proven way to build good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.",
        "pages": 320,
        "rating": 4.8,
        "status": "read",
        "notes": "Practical habit stacking framework.",
    },
    {
        "id": "the-silent-patient",
        "title": "The Silent Patient",
        "author": "Alex Michaelides",
        "genre": "Psychological Thriller",
        "synopsis": "A famous painter shoots her husband and never speaks another word; a psychotherapist becomes obsessed with uncovering her motive.",
        "pages": 336,
        "rating": 4.5,
        "status": "want_to_read",
        "notes": "Exciting plot twist.",
    },
]

def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("books")

    for book in SEEDED_BOOKS:
        doc_id = book["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(book)
        print(f"✓ Seeded book: '{book['title']}' by {book['author']} (ID: {doc_id})")

    print("\n✅ Successfully seeded Firestore 'books' collection!")

if __name__ == "__main__":
    seed_database()
