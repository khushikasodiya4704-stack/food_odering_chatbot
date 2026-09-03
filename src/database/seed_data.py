"""
Seed script to initialize realistic menu items and sample order history
for the FlavorCraft Bistro restaurant database.
"""

from datetime import datetime, timedelta, timezone
import random
from src.database.connection import init_db, get_db
from src.database.models import MenuItem, Customer, Order, OrderItem, OrderStatus

SAMPLE_MENU_ITEMS = [
    # Appetizers
    {
        "name": "Truffle Parmesan Fries",
        "category": "Appetizers",
        "description": "Crispy golden french fries tossed in white truffle oil, shaved aged parmesan, and fresh rosemary with garlic aioli.",
        "price": 8.99,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": True,
        "allergens": "Dairy, Eggs",
        "spicy_level": 0,
        "calories": 480,
        "prep_time_mins": 10,
    },
    {
        "name": "Crispy Buffalo Cauliflower Bites",
        "category": "Appetizers",
        "description": "Tempura-battered cauliflower florets glazed in zesty buffalo sauce, served with vegan ranch dressing and celery sticks.",
        "price": 9.50,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "Soy",
        "spicy_level": 2,
        "calories": 320,
        "prep_time_mins": 12,
    },
    {
        "name": "Smoked Salmon Crostini",
        "category": "Appetizers",
        "description": "Artisan toasted sourdough topped with herbed cream cheese, wild smoked salmon, capers, and dill.",
        "price": 12.99,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Fish, Dairy, Gluten",
        "spicy_level": 0,
        "calories": 360,
        "prep_time_mins": 10,
    },
    {
        "name": "Cheesy Garlic Dough Knots",
        "category": "Appetizers",
        "description": "Freshly baked pizza dough knots drenched in roasted garlic butter, parsley, and melted mozzarella with marinara dip.",
        "price": 7.99,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy",
        "spicy_level": 0,
        "calories": 520,
        "prep_time_mins": 12,
    },

    # Burgers & Sandwiches
    {
        "name": "The Classic Artisan Cheeseburger",
        "category": "Burgers",
        "description": "6oz Black Angus beef patty, melted aged cheddar, butter lettuce, ripe tomato, house pickles, and secret bistro sauce on a brioche bun.",
        "price": 14.99,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy, Eggs",
        "spicy_level": 0,
        "calories": 780,
        "prep_time_mins": 15,
    },
    {
        "name": "Smoky BBQ Bacon Burger",
        "category": "Burgers",
        "description": "Angus beef patty with crispy smoked bacon, onion rings, smoked gouda, and hickory chipotle barbecue sauce on a brioche bun.",
        "price": 16.50,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy, Eggs",
        "spicy_level": 1,
        "calories": 920,
        "prep_time_mins": 15,
    },
    {
        "name": "Beyond Plant Power Burger",
        "category": "Burgers",
        "description": "100% plant-based Beyond Meat patty, vegan cheddar, creamy avocado, crisp lettuce, tomato, and vegan herb aioli on a gluten-free bun.",
        "price": 15.99,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 590,
        "prep_time_mins": 15,
    },
    {
        "name": "Crispy Nashville Hot Chicken Sandwich",
        "category": "Burgers",
        "description": "Spicy buttermilk fried chicken breast dipped in Nashville hot oil, topped with creamy coleslaw and dill pickles on toasted brioche.",
        "price": 15.50,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy, Eggs",
        "spicy_level": 3,
        "calories": 840,
        "prep_time_mins": 15,
    },

    # Artisanal Pizzas
    {
        "name": "Margherita Classica Pizza",
        "category": "Pizzas",
        "description": "San Marzano tomato sauce, fresh buffalo mozzarella, fragrant sweet basil, and extra virgin olive oil on hand-stretched wood-fired dough.",
        "price": 14.50,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy",
        "spicy_level": 0,
        "calories": 720,
        "prep_time_mins": 18,
    },
    {
        "name": "Double Pepperoni Feast Pizza",
        "category": "Pizzas",
        "description": "Loaded with classic artisanal pepperoni, spicy cupping pepperoni, mozzarella blend, and hot honey drizzle.",
        "price": 17.00,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy",
        "spicy_level": 1,
        "calories": 910,
        "prep_time_mins": 18,
    },
    {
        "name": "Wild Mushroom & Truffle Pizza",
        "category": "Pizzas",
        "description": "Roasted cremini & shiitake mushrooms, fontina & mozzarella, caramelized shallots, baby arugula, and white truffle oil.",
        "price": 18.00,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy",
        "spicy_level": 0,
        "calories": 790,
        "prep_time_mins": 18,
    },
    {
        "name": "Vegan Garden Harvest Pizza",
        "category": "Pizzas",
        "description": "Nut-free vegan mozzarella, roasted bell peppers, zucchini, kalamata olives, red onions, and spinach on gluten-free crust.",
        "price": 16.50,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 610,
        "prep_time_mins": 18,
    },

    # Pastas & Mains
    {
        "name": "Fettuccine Alfredo with Grilled Chicken",
        "category": "Pastas",
        "description": "Fresh egg fettuccine tossed in a velvety garlic-parmesan cream sauce, topped with herb-marinated grilled chicken breast.",
        "price": 16.99,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy, Eggs",
        "spicy_level": 0,
        "calories": 890,
        "prep_time_mins": 16,
    },
    {
        "name": "Spicy Arrabbiata Penne",
        "category": "Pastas",
        "description": "Al dente penne pasta in a fiery crushed San Marzano tomato sauce with garlic, chili flakes, kalamata olives, and fresh basil.",
        "price": 13.99,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": False,
        "allergens": "Gluten",
        "spicy_level": 2,
        "calories": 540,
        "prep_time_mins": 14,
    },
    {
        "name": "Slow-Cooked Beef Bolognese Rigatoni",
        "category": "Pastas",
        "description": "Hearty 6-hour braised beef and pork ragu simmered with red wine, mirepoix, and fresh herbs over ribbed rigatoni with pecorino.",
        "price": 17.50,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Gluten, Dairy",
        "spicy_level": 0,
        "calories": 820,
        "prep_time_mins": 16,
    },

    # Beverages & Drinks
    {
        "name": "Fresh Mint Limeade",
        "category": "Beverages",
        "description": "Freshly squeezed limes muddled with organic mint leaves, pure cane syrup, and sparkling mineral water.",
        "price": 4.50,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 110,
        "prep_time_mins": 3,
    },
    {
        "name": "Artisanal Iced Peach Tea",
        "category": "Beverages",
        "description": "Cold brewed black Ceylon tea infused with real peach nectar and a hint of wild honey.",
        "price": 3.99,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 90,
        "prep_time_mins": 2,
    },
    {
        "name": "Classic Coca Cola (Can)",
        "category": "Beverages",
        "description": "Ice-cold 330ml can of original Coca Cola, served with a cup of ice and lemon wedge.",
        "price": 2.50,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 140,
        "prep_time_mins": 1,
    },
    {
        "name": "Diet Coke (Can)",
        "category": "Beverages",
        "description": "Ice-cold 330ml can of sugar-free Diet Coke, served with ice.",
        "price": 2.50,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 0,
        "prep_time_mins": 1,
    },
    {
        "name": "Cold Brew Hazelnut Latte",
        "category": "Beverages",
        "description": "Slow-steeped single-origin Colombian cold brew with oat milk and roasted hazelnut essence.",
        "price": 5.25,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "Tree Nuts (Hazelnut)",
        "spicy_level": 0,
        "calories": 160,
        "prep_time_mins": 3,
    },

    # Desserts
    {
        "name": "Warm Molten Lava Chocolate Cake",
        "category": "Desserts",
        "description": "Decadent dark Belgian chocolate cake with a gooey warm liquid center, served with Madagascan vanilla bean ice cream.",
        "price": 8.50,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Dairy, Eggs, Gluten",
        "spicy_level": 0,
        "calories": 620,
        "prep_time_mins": 10,
    },
    {
        "name": "Classic New York Cheesecake",
        "category": "Desserts",
        "description": "Rich and silky cream cheese filling on a buttery graham cracker crust, topped with fresh strawberry compote.",
        "price": 7.99,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": False,
        "allergens": "Dairy, Eggs, Gluten",
        "spicy_level": 0,
        "calories": 540,
        "prep_time_mins": 5,
    },
    {
        "name": "Vegan Chia Berry Parfait",
        "category": "Desserts",
        "description": "Organic coconut milk chia seed pudding layered with wild berry coulis and crunchy gluten-free granola.",
        "price": 6.99,
        "is_vegetarian": True,
        "is_vegan": True,
        "is_gluten_free": True,
        "allergens": "None",
        "spicy_level": 0,
        "calories": 280,
        "prep_time_mins": 5,
    },
]

SAMPLE_CUSTOMERS = [
    {"name": "Alice Johnson", "phone": "555-0101", "address": "124 Oak Street, Apt 4B", "email": "alice.j@example.com"},
    {"name": "David Martinez", "phone": "555-0102", "address": "742 Evergreen Terrace", "email": "david.m@example.com"},
    {"name": "Sophia Chang", "phone": "555-0103", "address": "88 Pine Crest Blvd", "email": "sophia.c@example.com"},
    {"name": "Marcus Lee", "phone": "555-0104", "address": "305 Ocean Drive, Suite 12", "email": "marcus.l@example.com"},
    {"name": "Emily Watson", "phone": "555-0105", "address": "19 Elm Street", "email": "emily.w@example.com"},
]


def seed_database():
    """Seed the database with menu items and initial sample sales history."""
    init_db()
    with get_db() as session:
        # 1. Seed Menu Items
        for item_data in SAMPLE_MENU_ITEMS:
            existing = session.query(MenuItem).filter(MenuItem.name == item_data["name"]).first()
            if not existing:
                item = MenuItem(**item_data)
                session.add(item)
        session.flush()

        # Check if we already have orders seeded
        existing_orders_count = session.query(Order).count()
        if existing_orders_count > 0:
            return

        # 2. Seed Customers
        customer_objs = []
        for cust_data in SAMPLE_CUSTOMERS:
            cust = Customer(**cust_data)
            session.add(cust)
            customer_objs.append(cust)
        session.flush()

        # 3. Seed Realistic Historical Orders (Past 5 days)
        menu_items = session.query(MenuItem).all()
        statuses = [
            OrderStatus.DELIVERED,
            OrderStatus.DELIVERED,
            OrderStatus.DELIVERED,
            OrderStatus.PREPARING,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.CONFIRMED,
        ]

        now = datetime.now(timezone.utc)

        for i in range(35):
            cust = random.choice(customer_objs)
            order_code = f"ORD-SEED-{1000 + i}"
            order_date = now - timedelta(
                days=random.randint(0, 5),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            status = random.choice(statuses)

            num_items = random.randint(1, 4)
            chosen_items = random.sample(menu_items, num_items)
            
            subtotal = 0.0
            order_items_to_add = []

            for m_item in chosen_items:
                qty = random.randint(1, 3)
                line_total = m_item.price * qty
                subtotal += line_total
                order_items_to_add.append({
                    "item": m_item,
                    "quantity": qty,
                    "line_total": line_total,
                })

            tax = subtotal * 0.08
            delivery_fee = 0.0 if subtotal >= 40.0 else 3.99
            total = subtotal + tax + delivery_fee

            order = Order(
                order_code=order_code,
                customer_id=cust.id,
                status=status,
                subtotal=round(subtotal, 2),
                tax=round(tax, 2),
                delivery_fee=round(delivery_fee, 2),
                discount=0.0,
                total_amount=round(total, 2),
                special_notes="Sample seeded order",
                delivery_address=cust.address,
                estimated_delivery_mins=35,
                created_at=order_date,
            )
            session.add(order)
            session.flush()

            for item_info in order_items_to_add:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item_info["item"].id,
                    item_name=item_info["item"].name,
                    quantity=item_info["quantity"],
                    unit_price=item_info["item"].price,
                    line_total=item_info["line_total"],
                    special_instructions="None",
                )
                session.add(order_item)

        session.flush()


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully with menu items and orders.")
