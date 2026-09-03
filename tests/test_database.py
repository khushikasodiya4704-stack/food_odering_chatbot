"""
Unit tests for Database Models, Connections, and Repositories.
"""

import pytest
from src.database.connection import init_db, get_db
from src.database.seed_data import seed_database
from src.database.models import MenuItem, OrderStatus
from src.database.repository import MenuItemRepository, OrderRepository, CustomerRepository, AnalyticsRepository


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    seed_database()


def test_menu_items_seeded():
    with get_db() as session:
        items = MenuItemRepository.get_all(session)
        assert len(items) >= 20
        burgers = MenuItemRepository.get_all(session, category="Burgers")
        assert len(burgers) >= 3


def test_menu_item_lookup():
    with get_db() as session:
        item = MenuItemRepository.get_by_name(session, "Margherita Classica Pizza")
        assert item is not None
        assert item.price == 14.50
        assert item.is_vegetarian is True


def test_customer_creation():
    with get_db() as session:
        cust = CustomerRepository.get_or_create(
            session=session,
            name="John Tester",
            phone="555-9988",
            address="100 Testing Lane",
            email="tester@example.com",
        )
        assert cust.id is not None
        assert cust.name == "John Tester"


def test_place_multi_item_order():
    with get_db() as session:
        items = [
            {"item_name": "The Classic Artisan Cheeseburger", "quantity": 2, "special_instructions": "No onions"},
            {"item_name": "Truffle Parmesan Fries", "quantity": 1, "special_instructions": "Extra dip"},
            {"item_name": "Classic Coca Cola (Can)", "quantity": 2, "special_instructions": ""},
        ]
        order = OrderRepository.create_order(
            session=session,
            customer_name="John Tester",
            customer_phone="555-9988",
            delivery_address="100 Testing Lane",
            items=items,
            special_notes="Leave at door",
        )

        assert order is not None
        assert order["order_code"].startswith("ORD-")
        assert order["status"] == "CONFIRMED"
        assert len(order["items"]) == 3
        
        # Expected subtotal: 2*14.99 + 8.99 + 2*2.50 = 29.98 + 8.99 + 5.00 = 43.97
        assert order["subtotal"] == 43.97
        # Free delivery over $40
        assert order["delivery_fee"] == 0.0
        assert order["total_amount"] > 43.97


def test_order_status_and_cancellation():
    with get_db() as session:
        items = [{"item_name": "Fresh Mint Limeade", "quantity": 1}]
        order = OrderRepository.create_order(
            session=session,
            customer_name="Alice Cancel",
            customer_phone="555-7766",
            delivery_address="45 Cancel Ave",
            items=items,
        )

        code = order["order_code"]
        fetched = OrderRepository.get_order_by_code(session, code)
        assert fetched is not None
        assert fetched["status"] == "CONFIRMED"

        # Cancel order
        cancelled = OrderRepository.cancel_order(session, code, reason="Changed mind")
        assert cancelled["status"] == "CANCELLED"


def test_analytics_repository():
    with get_db() as session:
        kpi = AnalyticsRepository.get_sales_summary(session)
        assert kpi["total_orders"] > 0
        assert kpi["total_revenue"] > 0

        best_sellers = AnalyticsRepository.get_best_selling_items(session, limit=5)
        assert len(best_sellers) > 0
