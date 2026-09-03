"""
Analytics engine for restaurant sales performance and best-seller insights.
"""

from typing import Dict, Any, List
import pandas as pd
from src.database.connection import get_db
from src.database.repository import AnalyticsRepository, OrderRepository


class RestaurantAnalytics:
    @staticmethod
    def get_kpi_summary() -> Dict[str, Any]:
        """Fetch high-level business KPIs."""
        with get_db() as session:
            return AnalyticsRepository.get_sales_summary(session)

    @staticmethod
    def get_best_sellers_df(limit: int = 10) -> pd.DataFrame:
        """Return DataFrame of best-selling items by quantity and revenue."""
        with get_db() as session:
            data = AnalyticsRepository.get_best_selling_items(session, limit=limit)
        if not data:
            return pd.DataFrame(columns=["item_name", "category", "total_quantity", "total_revenue"])
        df = pd.DataFrame(data)
        df.columns = ["Item Name", "Category", "Quantity Sold", "Total Revenue ($)"]
        return df

    @staticmethod
    def get_category_sales_df() -> pd.DataFrame:
        """Return category-wise revenue distribution."""
        with get_db() as session:
            data = AnalyticsRepository.get_sales_by_category(session)
        if not data:
            return pd.DataFrame(columns=["Category", "Items Sold", "Revenue ($)"])
        df = pd.DataFrame(data)
        df.columns = ["Category", "Items Sold", "Revenue ($)"]
        return df

    @staticmethod
    def get_order_status_df() -> pd.DataFrame:
        """Return distribution of order statuses."""
        with get_db() as session:
            data = AnalyticsRepository.get_orders_by_status(session)
        if not data:
            return pd.DataFrame(columns=["Status", "Count"])
        df = pd.DataFrame(data)
        df.columns = ["Status", "Count"]
        return df

    @staticmethod
    def get_revenue_trend_df(days: int = 7) -> pd.DataFrame:
        """Return daily revenue trend over the past N days."""
        with get_db() as session:
            data = AnalyticsRepository.get_daily_revenue_trend(session, days=days)
        if not data:
            return pd.DataFrame(columns=["Date", "Orders", "Revenue ($)"])
        df = pd.DataFrame(data)
        df.columns = ["Date", "Orders", "Revenue ($)"]
        return df

    @staticmethod
    def get_recent_orders_df(limit: int = 20) -> pd.DataFrame:
        """Return recent orders formatted for tabular view."""
        with get_db() as session:
            orders = OrderRepository.list_recent_orders(session, limit=limit)
        if not orders:
            return pd.DataFrame()
        
        flat_list = []
        for o in orders:
            items_str = ", ".join([f"{it['quantity']}x {it['item_name']}" for it in o["items"]])
            flat_list.append({
                "Order Code": o["order_code"],
                "Customer": o["customer_name"],
                "Phone": o["customer_phone"],
                "Items": items_str,
                "Total ($)": f"${o['total_amount']:.2f}",
                "Status": o["status"],
                "Ordered At": o["created_at"],
            })
        return pd.DataFrame(flat_list)
