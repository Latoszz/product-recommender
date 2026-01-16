import os
from dotenv import load_dotenv
from graph_repository import GraphRepository
import random

load_dotenv()


def seed_database():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    repo = GraphRepository(uri, user, password)
    repo.create_constraints()

    print("Starting database seeding...")

    # Sample users
    users = [
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Eve",
        "Frank",
        "Grace",
        "Henry",
        "Iris",
        "Jack",
        "Kate",
        "Leo",
        "Maria",
        "Nathan",
        "Olivia",
    ]

    # Sample products by category
    products = {
        "Electronics": [
            "Wireless Headphones",
            "Smartphone",
            "Laptop",
            "Smartwatch",
            "Tablet",
            "E-Reader",
        ],
        "Books": [
            "Science Fiction Novel",
            "Programming Guide",
            "Cooking Book",
            "History Book",
            "Biography",
        ],
        "Home": [
            "Coffee Maker",
            "Blender",
            "Vacuum Cleaner",
            "Air Purifier",
            "Standing Desk",
        ],
        "Sports": [
            "Yoga Mat",
            "Running Shoes",
            "Fitness Tracker",
            "Bicycle",
            "Tennis Racket",
        ],
        "Gaming": [
            "Video Game Console",
            "Gaming Mouse",
            "Mechanical Keyboard",
            "VR Headset",
        ],
    }

    # Add users
    print("\nAdding users...")
    for user in users:
        repo.add_user(user)
        print(f"  Added user: {user}")

    # Add products
    print("\nAdding products...")
    for category, product_list in products.items():
        for product in product_list:
            repo.add_product(product, category)
            print(f"  Added product: {product} ({category})")

    # Create follow relationships (social graph)
    print("\nCreating follow relationships...")
    follow_pairs = [
        ("Alice", "Bob"),
        ("Alice", "Charlie"),
        ("Alice", "Diana"),
        ("Bob", "Charlie"),
        ("Bob", "Eve"),
        ("Bob", "Frank"),
        ("Charlie", "Diana"),
        ("Charlie", "Grace"),
        ("Diana", "Eve"),
        ("Diana", "Henry"),
        ("Eve", "Frank"),
        ("Eve", "Iris"),
        ("Frank", "Grace"),
        ("Frank", "Jack"),
        ("Grace", "Henry"),
        ("Grace", "Kate"),
        ("Henry", "Iris"),
        ("Henry", "Leo"),
        ("Iris", "Jack"),
        ("Iris", "Maria"),
        ("Jack", "Kate"),
        ("Jack", "Nathan"),
        ("Kate", "Leo"),
        ("Kate", "Olivia"),
        ("Leo", "Maria"),
        ("Maria", "Nathan"),
        ("Nathan", "Olivia"),
        ("Olivia", "Alice"),
    ]

    for follower, followee in follow_pairs:
        repo.create_follow_relationship(follower, followee)
        print(f"  {follower} follows {followee}")

    # Create product ratings
    print("\nCreating product ratings...")
    all_products = [p for cat_products in products.values() for p in cat_products]

    # Define user preferences (simulating different tastes)
    user_preferences = {
        "Alice": {"Electronics": 5, "Books": 4, "Gaming": 3},
        "Bob": {"Sports": 5, "Home": 4, "Electronics": 3},
        "Charlie": {"Books": 5, "Gaming": 4, "Electronics": 4},
        "Diana": {"Home": 5, "Books": 4, "Sports": 3},
        "Eve": {"Gaming": 5, "Electronics": 5, "Books": 3},
        "Frank": {"Sports": 5, "Home": 4, "Gaming": 3},
        "Grace": {"Books": 5, "Home": 4, "Electronics": 3},
        "Henry": {"Electronics": 5, "Gaming": 4, "Sports": 3},
        "Iris": {"Home": 5, "Books": 5, "Sports": 4},
        "Jack": {"Gaming": 5, "Electronics": 4, "Books": 3},
        "Kate": {"Books": 5, "Sports": 4, "Home": 4},
        "Leo": {"Electronics": 5, "Gaming": 5, "Sports": 3},
        "Maria": {"Home": 5, "Books": 4, "Sports": 4},
        "Nathan": {"Sports": 5, "Gaming": 4, "Electronics": 4},
        "Olivia": {"Books": 5, "Home": 5, "Electronics": 3},
    }

    rating_count = 0
    for user in users:
        prefs = user_preferences.get(user, {})
        num_ratings = random.randint(5, 12)
        rated_products = random.sample(all_products, num_ratings)

        for product in rated_products:
            category = None
            for cat, prods in products.items():
                if product in prods:
                    category = cat
                    break

            base_rating = prefs.get(category, 3)
            rating = max(1, min(5, base_rating + random.randint(-1, 1)))

            if rating >= 4:
                rating_type = "recommends"
            elif rating <= 2:
                rating_type = "discourages"
            else:
                rating_type = "rates"

            repo.rate_product(
                user=user, product=product, rating=rating, rating_type=rating_type
            )
            rating_count += 1
            print(f"  {user} rated {product}: {rating}/5 ({rating_type})")

    print("\nDatabase seeding completed!")
    print(f"  Total users: {len(users)}")
    print(f"  Total products: {len(all_products)}")
    print(f"  Total follow relationships: {len(follow_pairs)}")
    print(f"  Total ratings: {rating_count}")

    repo.close()


if __name__ == "__main__":
    seed_database()
