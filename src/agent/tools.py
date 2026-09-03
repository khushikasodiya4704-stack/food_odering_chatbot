"""
Custom LangChain tools for database operations and RAG knowledge retrieval.
Strictly uses custom structured tools for DB interaction without generic SQL agents.
"""

from typing import List, Optional
from langchain.tools import tool

from src.database.connection import get_db
from src.database.repository import OrderRepository, MenuItemRepository
from src.rag.retriever import retriever
from src.agent.schemas import (
    PlaceOrderInput,
    OrderStatusInput,
    CancelOrderInput,
    MenuSearchInput,
)


@tool("search_restaurant_knowledge", args_schema=MenuSearchInput)
def search_restaurant_knowledge(query: str, category: Optional[str] = None) -> str:
    """
    Search the restaurant knowledge base (RAG) for menu item details, ingredients,
    dietary tags (vegan, vegetarian, gluten-free), allergens, calorie counts, prices,
    promotions, combos, operating hours, delivery fees, and restaurant policies.
    """
    try:
        results = retriever.query(query=query, top_k=4, category=category)
        return results
    except Exception as e:
        return f"Error retrieving knowledge base details: {str(e)}"


@tool("get_full_restaurant_menu")
def get_full_restaurant_menu() -> str:
    """
    Retrieve the complete, categorized menu of FlavorCraft Bistro with all items, descriptions, and prices.
    """
    try:
        return retriever.get_full_menu_summary()
    except Exception as e:
        return f"Error retrieving menu: {str(e)}"


@tool("place_food_order", args_schema=PlaceOrderInput)
def place_food_order(
    customer_name: str,
    customer_phone: str,
    delivery_address: str,
    items: List[dict],
    special_notes: Optional[str] = "",
) -> str:
    """
    Custom Database Tool: Atomically places a new food order in the database with multiple items.
    Calculates subtotal, taxes, delivery fee, and creates the order and line items.
    Returns the confirmation details, order ID, items breakdown, and estimated delivery time.
    """
    try:
        with get_db() as session:
            # Convert items if Pydantic objects or dicts
            formatted_items = []
            for item in items:
                if hasattr(item, "model_dump"):
                    formatted_items.append(item.model_dump())
                elif hasattr(item, "dict"):
                    formatted_items.append(item.dict())
                else:
                    formatted_items.append(dict(item))

            order_data = OrderRepository.create_order(
                session=session,
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address=delivery_address,
                items=formatted_items,
                special_notes=special_notes,
            )

        items_summary = "\n".join(
            [f"  - {it['quantity']}x {it['item_name']} (${it['unit_price']:.2f} each) = ${it['line_total']:.2f}" + 
             (f" [{it['special_instructions']}]" if it.get('special_instructions') else "")
             for it in order_data['items']]
        )

        return (
            f"**Order Successfully Placed**\n\n"
            f"- **Order Tracking Code**: `{order_data['order_code']}`\n"
            f"- **Customer**: {order_data['customer_name']} ({order_data['customer_phone']})\n"
            f"- **Delivery Address**: {order_data['delivery_address']}\n"
            f"- **Items Ordered**:\n{items_summary}\n\n"
            f"- **Subtotal**: ${order_data['subtotal']:.2f}\n"
            f"- **Tax (8%)**: ${order_data['tax']:.2f}\n"
            f"- **Delivery Fee**: ${order_data['delivery_fee']:.2f}\n"
            f"- **Total Paid**: **${order_data['total_amount']:.2f}**\n"
            f"- **Status**: {order_data['status']}\n"
            f"- **Estimated Delivery**: {order_data['estimated_delivery_mins']} minutes\n"
            f"- **Notes**: {order_data['special_notes'] or 'None'}\n\n"
            f"Save your Order Code `{order_data['order_code']}` to track your order anytime."
        )
    except ValueError as ve:
        return f"Order placement failed: {str(ve)}. Please check the item names or details."
    except Exception as e:
        return f"System error placing order: {str(e)}"


@tool("get_order_status", args_schema=OrderStatusInput)
def get_order_status(order_code: str) -> str:
    """
    Custom Database Tool: Lookup the current real-time status and details of an existing order by its tracking code.
    """
    try:
        with get_db() as session:
            order = OrderRepository.get_order_by_code(session, order_code)
            if not order:
                return f"No order found with tracking code `{order_code}`. Please verify your order number."

            items_list = "\n".join([f"  - {it['quantity']}x {it['item_name']}" for it in order['items']])
            return (
                f"**Order Status: `{order['order_code']}`**\n\n"
                f"- **Status**: **{order['status']}**\n"
                f"- **Customer**: {order['customer_name']}\n"
                f"- **Delivery Address**: {order['delivery_address']}\n"
                f"- **Items**:\n{items_list}\n"
                f"- **Total Amount**: ${order['total_amount']:.2f}\n"
                f"- **Ordered At**: {order['created_at']}\n"
                f"- **Estimated Delivery**: {order['estimated_delivery_mins']} minutes"
            )
    except Exception as e:
        return f"Error looking up order status: {str(e)}"


@tool("cancel_food_order", args_schema=CancelOrderInput)
def cancel_food_order(order_code: str, reason: Optional[str] = "Customer requested cancellation") -> str:
    """
    Custom Database Tool: Cancel an order if it is still in PENDING or CONFIRMED state.
    Cannot cancel orders that are already PREPARING or OUT FOR DELIVERY.
    """
    try:
        with get_db() as session:
            cancelled_order = OrderRepository.cancel_order(session, order_code, reason)
            return (
                f"**Order `{cancelled_order['order_code']}` has been CANCELLED.**\n"
                f"Reason: {reason}\n"
                f"No charges will be incurred."
            )
    except ValueError as ve:
        return f"Cannot cancel order: {str(ve)}"
    except Exception as e:
        return f"Error cancelling order: {str(e)}"


# Export list of all custom tools
ALL_CUSTOM_TOOLS = [
    search_restaurant_knowledge,
    get_full_restaurant_menu,
    place_food_order,
    get_order_status,
    cancel_food_order,
]
