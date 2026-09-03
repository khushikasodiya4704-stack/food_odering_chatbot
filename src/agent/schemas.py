"""
Pydantic schemas for Agent input validation and custom tool interfaces.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemInput(BaseModel):
    item_name: str = Field(..., description="The exact or approximate name of the food or drink item (e.g. 'Smoky BBQ Bacon Burger', 'Margherita Classica Pizza').")
    quantity: int = Field(default=1, ge=1, description="The quantity of this item to order (must be 1 or greater).")
    special_instructions: Optional[str] = Field(
        default="",
        description="Any customer customizations or special instructions (e.g. 'No onions', 'Extra crispy', 'Dressing on the side')."
    )


class PlaceOrderInput(BaseModel):
    customer_name: str = Field(..., description="The full name of the customer placing the order.")
    customer_phone: str = Field(..., description="The phone number of the customer for delivery updates.")
    delivery_address: str = Field(..., description="The full street delivery address for the order.")
    items: List[OrderItemInput] = Field(
        ...,
        min_length=1,
        description="List of one or more items being ordered. Multiple different items should all be included in this list."
    )
    special_notes: Optional[str] = Field(
        default="",
        description="General order delivery instructions (e.g., 'Ring doorbell twice', 'Leave at front porch')."
    )


class OrderStatusInput(BaseModel):
    order_code: str = Field(..., description="The unique order tracking code, e.g. 'ORD-7492' or 'ORD-SEED-1001'.")


class CancelOrderInput(BaseModel):
    order_code: str = Field(..., description="The order code to be cancelled, e.g. 'ORD-7492'.")
    reason: Optional[str] = Field(default="Customer requested cancellation", description="Reason for the cancellation.")


class MenuSearchInput(BaseModel):
    query: str = Field(..., description="Search query regarding menu items, ingredients, allergens, prices, combos, or restaurant policies.")
    category: Optional[str] = Field(default=None, description="Optional category filter e.g. 'Appetizers', 'Burgers', 'Pizzas', 'Pastas', 'Beverages', 'Desserts'.")
