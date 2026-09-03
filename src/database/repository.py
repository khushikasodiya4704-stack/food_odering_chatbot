"""
Repository layer for database operations (Menu, Customer, Orders, Analytics).
Provides safe, structured data access without exposing direct SQL execution.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from config import settings
from src.database.models import (
    MenuItem,
    Customer,
    Order,
    OrderItem,
    OrderStatus,
)
from src.database.connection import get_db


class MenuItemRepository:
    @staticmethod
    def get_all(session: Session, category: Optional[str] = None, only_available: bool = True) -> List[MenuItem]:
        query = session.query(MenuItem)
        if category:
            query = query.filter(MenuItem.category.ilike(f"%{category}%"))
        if only_available:
            query = query.filter(MenuItem.is_available == True)
        return query.order_by(MenuItem.category, MenuItem.name).all()

    @staticmethod
    def get_all_dict(session: Session, category: Optional[str] = None, only_available: bool = True) -> List[Dict[str, Any]]:
        items = MenuItemRepository.get_all(session, category=category, only_available=only_available)
        return [item.to_dict() for item in items]

    @staticmethod
    def get_by_id(session: Session, item_id: int) -> Optional[MenuItem]:
        return session.query(MenuItem).filter(MenuItem.id == item_id).first()

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[MenuItem]:
        clean_name = name.strip()
        # Direct exact match
        item = session.query(MenuItem).filter(func.lower(MenuItem.name) == clean_name.lower()).first()
        if item:
            return item
        # Fuzzy / partial match
        return session.query(MenuItem).filter(MenuItem.name.ilike(f"%{clean_name}%")).first()

    @staticmethod
    def search_items(session: Session, keyword: str) -> List[MenuItem]:
        search = f"%{keyword.strip()}%"
        return session.query(MenuItem).filter(
            (MenuItem.name.ilike(search)) |
            (MenuItem.description.ilike(search)) |
            (MenuItem.category.ilike(search))
        ).all()


class CustomerRepository:
    @staticmethod
    def get_or_create(session: Session, name: str, phone: str, address: str, email: Optional[str] = None) -> Customer:
        phone_clean = phone.strip()
        customer = session.query(Customer).filter(Customer.phone == phone_clean).first()
        if customer:
            # Update address and name if updated
            customer.name = name.strip() or customer.name
            if address:
                customer.address = address.strip()
            if email:
                customer.email = email.strip()
            session.flush()
            return customer
        
        customer = Customer(
            name=name.strip(),
            phone=phone_clean,
            address=address.strip(),
            email=email.strip() if email else None,
        )
        session.add(customer)
        session.flush()
        return customer


class OrderRepository:
    @staticmethod
    def generate_order_code() -> str:
        """Generate unique human-readable order code e.g. ORD-7492"""
        short_id = str(uuid.uuid4().hex[:6]).upper()
        return f"ORD-{short_id}"

    @classmethod
    def create_order(
        cls,
        session: Session,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        items: List[Dict[str, Any]],
        special_notes: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates an atomic order with multiple items.
        Items format: [{'item_name': 'Margherita Pizza', 'quantity': 2, 'special_instructions': 'Extra crispy'}]
        """
        if not items:
            raise ValueError("An order must contain at least one item.")

        # 1. Customer
        customer = CustomerRepository.get_or_create(
            session=session,
            name=customer_name,
            phone=customer_phone,
            address=delivery_address,
            email=customer_email,
        )

        # 2. Process Order Items & Calculate Pricing
        subtotal = 0.0
        validated_items = []

        for item_data in items:
            raw_name = item_data.get("item_name", "").strip()
            quantity = int(item_data.get("quantity", 1))
            instructions = item_data.get("special_instructions", "")

            if quantity <= 0:
                continue

            menu_item = MenuItemRepository.get_by_name(session, raw_name)
            if not menu_item:
                raise ValueError(f"Menu item '{raw_name}' not found in our catalog.")
            
            if not menu_item.is_available:
                raise ValueError(f"Menu item '{menu_item.name}' is currently out of stock.")

            line_total = menu_item.price * quantity
            subtotal += line_total

            validated_items.append({
                "menu_item": menu_item,
                "quantity": quantity,
                "unit_price": menu_item.price,
                "line_total": line_total,
                "special_instructions": instructions,
            })

        if not validated_items:
            raise ValueError("No valid items in the order.")

        # 3. Calculate Tax, Delivery, and Total
        tax = subtotal * settings.TAX_RATE
        delivery_fee = 0.0 if subtotal >= settings.FREE_DELIVERY_THRESHOLD else settings.DELIVERY_FEE
        discount = 0.0
        total_amount = subtotal + tax + delivery_fee - discount

        # 4. Create Order Record
        order_code = cls.generate_order_code()
        order = Order(
            order_code=order_code,
            customer_id=customer.id,
            status=OrderStatus.CONFIRMED,
            subtotal=round(subtotal, 2),
            tax=round(tax, 2),
            delivery_fee=round(delivery_fee, 2),
            discount=round(discount, 2),
            total_amount=round(total_amount, 2),
            special_notes=special_notes,
            delivery_address=delivery_address,
            estimated_delivery_mins=35,
        )
        session.add(order)
        session.flush()

        # 5. Create Order Items
        for item_info in validated_items:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_info["menu_item"].id,
                item_name=item_info["menu_item"].name,
                quantity=item_info["quantity"],
                unit_price=item_info["unit_price"],
                line_total=item_info["line_total"],
                special_instructions=item_info["special_instructions"],
            )
            session.add(order_item)

        session.flush()
        return order.to_dict()

    @staticmethod
    def get_order_by_code(session: Session, order_code: str) -> Optional[Dict[str, Any]]:
        order = session.query(Order).filter(func.upper(Order.order_code) == order_code.strip().upper()).first()
        return order.to_dict() if order else None

    @staticmethod
    def get_orders_by_phone(session: Session, phone: str) -> List[Dict[str, Any]]:
        customer = session.query(Customer).filter(Customer.phone == phone.strip()).first()
        if not customer:
            return []
        orders = session.query(Order).filter(Order.customer_id == customer.id).order_by(desc(Order.created_at)).all()
        return [o.to_dict() for o in orders]

    @staticmethod
    def cancel_order(session: Session, order_code: str, reason: Optional[str] = None) -> Dict[str, Any]:
        order = session.query(Order).filter(func.upper(Order.order_code) == order_code.strip().upper()).first()
        if not order:
            raise ValueError(f"Order '{order_code}' was not found.")

        if order.status in [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel order '{order_code}' because it is already {order.status.value}.")

        if order.status == OrderStatus.CANCELLED:
            raise ValueError(f"Order '{order_code}' is already cancelled.")

        order.status = OrderStatus.CANCELLED
        if reason:
            order.special_notes = f"{order.special_notes or ''} [Cancelled: {reason}]".strip()
        session.flush()
        return order.to_dict()

    @staticmethod
    def update_status(session: Session, order_code: str, new_status: OrderStatus) -> Dict[str, Any]:
        order = session.query(Order).filter(func.upper(Order.order_code) == order_code.strip().upper()).first()
        if not order:
            raise ValueError(f"Order '{order_code}' not found.")
        order.status = new_status
        session.flush()
        return order.to_dict()

    @staticmethod
    def list_recent_orders(session: Session, limit: int = 20) -> List[Dict[str, Any]]:
        orders = session.query(Order).order_by(desc(Order.created_at)).limit(limit).all()
        return [o.to_dict() for o in orders]


class AnalyticsRepository:
    @staticmethod
    def get_sales_summary(session: Session) -> Dict[str, Any]:
        total_orders = session.query(func.count(Order.id)).scalar() or 0
        active_orders = session.query(func.count(Order.id)).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.OUT_FOR_DELIVERY])
        ).scalar() or 0
        total_revenue = session.query(func.sum(Order.total_amount)).filter(Order.status != OrderStatus.CANCELLED).scalar() or 0.0
        avg_order_value = session.query(func.avg(Order.total_amount)).filter(Order.status != OrderStatus.CANCELLED).scalar() or 0.0
        
        return {
            "total_orders": int(total_orders),
            "active_orders": int(active_orders),
            "total_revenue": round(float(total_revenue), 2),
            "avg_order_value": round(float(avg_order_value), 2),
        }

    @staticmethod
    def get_best_selling_items(session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        results = (
            session.query(
                OrderItem.item_name,
                MenuItem.category,
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.line_total).label("total_revenue"),
            )
            .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.status != OrderStatus.CANCELLED)
            .group_by(OrderItem.item_name, MenuItem.category)
            .order_by(desc("total_quantity"))
            .limit(limit)
            .all()
        )
        return [
            {
                "item_name": r.item_name,
                "category": r.category,
                "total_quantity": int(r.total_quantity),
                "total_revenue": round(float(r.total_revenue), 2),
            }
            for r in results
        ]

    @staticmethod
    def get_sales_by_category(session: Session) -> List[Dict[str, Any]]:
        results = (
            session.query(
                MenuItem.category,
                func.sum(OrderItem.quantity).label("items_sold"),
                func.sum(OrderItem.line_total).label("category_revenue"),
            )
            .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.status != OrderStatus.CANCELLED)
            .group_by(MenuItem.category)
            .order_by(desc("category_revenue"))
            .all()
        )
        return [
            {
                "category": r.category,
                "items_sold": int(r.items_sold),
                "revenue": round(float(r.category_revenue), 2),
            }
            for r in results
        ]

    @staticmethod
    def get_orders_by_status(session: Session) -> List[Dict[str, Any]]:
        results = (
            session.query(Order.status, func.count(Order.id).label("count"))
            .group_by(Order.status)
            .all()
        )
        return [
            {
                "status": r.status.value if isinstance(r.status, OrderStatus) else str(r.status),
                "count": int(r.count),
            }
            for r in results
        ]

    @staticmethod
    def get_daily_revenue_trend(session: Session, days: int = 7) -> List[Dict[str, Any]]:
        start_date = datetime.utcnow() - timedelta(days=days)
        results = (
            session.query(
                func.date(Order.created_at).label("order_date"),
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("daily_revenue"),
            )
            .filter(Order.created_at >= start_date)
            .filter(Order.status != OrderStatus.CANCELLED)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )
        return [
            {
                "date": str(r.order_date),
                "orders": int(r.order_count),
                "revenue": round(float(r.daily_revenue), 2),
            }
            for r in results
        ]
