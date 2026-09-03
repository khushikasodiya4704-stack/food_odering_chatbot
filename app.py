"""
FlavorCraft Bistro - AI Food Ordering Chatbot & Sales Analytics Dashboard
Developed with Streamlit, LangChain, RAG, SQLite, and Plotly.
"""

import os
import re
from typing import Any
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.messages import HumanMessage, AIMessage

from config import settings
from src.database.connection import init_db, get_db
from src.database.seed_data import seed_database
from src.database.repository import MenuItemRepository, OrderRepository
from src.agent.chatbot_agent import create_ordering_agent, FallbackAgent
from src.analytics.metrics import RestaurantAnalytics


def format_markdown_display(text: Any) -> str:
    """
    Sanitize text for clean display in Streamlit:
    - Unwraps raw JSON/list-of-dict representations from LLM responses
    - Strips emoji characters and Mojibake artifacts (ð, ï, ¸, µ, ¢, â)
    - Removes LaTeX math mode delimiters (\\( and \\)) to prevent KaTeX letter spacing distortions
    """
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Clean raw stringified list-of-dict representations if any
    if text.strip().startswith("[{") and "'text':" in text:
        match = re.search(r"['\"]text['\"]\s*:\s*['\"](.*?)['\"]\s*(?:,\s*['\"]extras|\}\])", text, re.DOTALL)
        if match:
            try:
                text = match.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
            except Exception:
                text = match.group(1)

    # Remove emoji characters
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\U0001f300-\U0001f9ff\U0001fa00-\U0001faff]",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)

    # Remove Windows CP1252 Mojibake corrupted bytes (ð, ï, ¸, µ, ¢, â, etc.)
    text = re.sub(r"[ðï¸¢µâ\ufffd]", "", text)

    # Remove LaTeX inline math delimiters \( and \) that cause Streamlit KaTeX distortions
    text = text.replace(r"\(", "(").replace(r"\)", ")")
    text = text.replace(r"\[", "[").replace(r"\]", "]")
    text = text.replace(r"\$", "$")

    # Clean redundant blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------
# Page Configuration & Theming
# ---------------------------------------------------------
st.set_page_config(
    page_title="FlavorCraft Bistro | AI Food Ordering",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, modern UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 20px;
    }
    .menu-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out;
    }
    .menu-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .badge-veg { background-color: #DEF7EC; color: #03543F; }
    .badge-vegan { background-color: #E1EFFE; color: #1E429F; }
    .badge-gf { background-color: #FEF08A; color: #713F12; }
    .badge-spicy { background-color: #FDE8E8; color: #9B1C1C; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database & Seed Initialization
# ---------------------------------------------------------
@st.cache_resource
def setup_database_and_rag():
    init_db()
    seed_database()
    return True

setup_database_and_rag()

# ---------------------------------------------------------
# Session State Management
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": format_markdown_display(
                "**Welcome to FlavorCraft Bistro.** I am your AI food ordering assistant.\n\n"
                "I can assist you with:\n"
                "- Browsing our menu and checking ingredients, allergens, and dietary options\n"
                "- Placing orders with multiple items in a single message\n"
                "- Tracking real-time status and estimated delivery times\n\n"
                "*Example: 'I want to order 2 Classic Burgers and 1 Truffle Fries for David at 742 Evergreen Terrace, phone 555-0102'*"
            )
        }
    ]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## **FlavorCraft Bistro**")
    st.caption("AI Food Ordering & Restaurant Analytics")
    st.markdown("---")

    st.markdown("### **Restaurant Information**")
    st.markdown(f"**Hours:** {settings.RESTAURANT_HOURS}")
    st.markdown(f"**Phone:** {settings.RESTAURANT_PHONE}")
    st.markdown(f"**Delivery:** $3.99 (*Free on orders over $40*)")
    st.markdown(f"**Address:** {settings.RESTAURANT_ADDRESS}")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Reset Chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": format_markdown_display("Chat reset. How can I assist you with your order today?")
                }
            ]
            st.session_state.chat_history = []
            st.rerun()
    with col_s2:
        if st.button("Reseed DB", use_container_width=True):
            seed_database()
            st.success("Database re-seeded successfully.")
            st.rerun()


# ---------------------------------------------------------
# Agent Initialization Helper (Backend ENV Configured)
# ---------------------------------------------------------
def get_active_agent():
    provider = (settings.LLM_PROVIDER or "openai").lower()
    has_key = False
    if provider in ["gemini", "google"] and (settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")):
        has_key = True
    elif provider == "openai" and (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")):
        has_key = True
    elif provider == "groq" and (settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")):
        has_key = True

    if not has_key:
        return FallbackAgent(), False

    try:
        agent_exec = create_ordering_agent(
            provider=settings.LLM_PROVIDER,
            api_key=None,
            model_name=None,
        )
        return agent_exec, True
    except Exception:
        return FallbackAgent(), False


# ---------------------------------------------------------
# Header & Navigation Tabs
# ---------------------------------------------------------
st.markdown('<div class="main-header">FlavorCraft Bistro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Food Ordering, Customer Assistance & Sales Performance Dashboard</div>', unsafe_allow_html=True)

tab_chat, tab_menu, tab_track, tab_analytics = st.tabs([
    "AI Order Assistant",
    "Restaurant Menu",
    "Track & Manage Orders",
    "Sales Performance Dashboard",
])


# =========================================================
# TAB 1: AI Chatbot (Food Ordering & RAG)
# =========================================================
with tab_chat:
    col_chat, col_info = st.columns([2.5, 1.2])

    with col_chat:
        st.markdown("#### **Chat with AI Concierge**")
        st.caption("Place multi-item orders, inquire about dietary options, or verify restaurant details.")

        # Render conversation messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(format_markdown_display(msg["content"]))

        # Chat Input
        user_input = st.chat_input("Type your food order, question, or tracking code...")

        if user_input:
            # Append User Message
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(format_markdown_display(user_input))

            agent, is_live_llm = get_active_agent()

            with st.chat_message("assistant"):
                with st.spinner("Processing request..."):
                    try:
                        if is_live_llm:
                            response = agent.invoke({
                                "input": user_input,
                                "chat_history": st.session_state.chat_history,
                            })
                            agent_reply = response.get("output", "I have processed your request.")
                            st.session_state.chat_history.append(HumanMessage(content=user_input))
                            st.session_state.chat_history.append(AIMessage(content=agent_reply))
                        else:
                            response = agent.invoke({"input": user_input})
                            agent_reply = response["output"]

                        formatted_reply = format_markdown_display(agent_reply)
                        st.markdown(formatted_reply)
                        st.session_state.messages.append({"role": "assistant", "content": formatted_reply})
                    except Exception as err:
                        error_msg = f"Agent Error: {str(err)}. Please verify your API key in .env."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

    with col_info:
        st.markdown("#### **Quick Action Prompts**")
        st.caption("Click any prompt to test sample interactions:")

        quick_prompts = [
            "What vegan and gluten-free options do you have?",
            "Show me your best-selling gourmet burgers and prices",
            "What are your delivery hours and free delivery rules?",
            "I want 2 Margherita Classica Pizza and 1 Truffle Parmesan Fries for Sophia Chang, phone 555-0103, address 88 Pine Crest Blvd",
            "Track order ORD-SEED-1001",
        ]

        for p in quick_prompts:
            if st.button(p, help=p, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": p})
                agent, is_live_llm = get_active_agent()
                if is_live_llm:
                    res = agent.invoke({"input": p, "chat_history": st.session_state.chat_history})
                    reply = res.get("output", "Order processed.")
                    st.session_state.chat_history.append(HumanMessage(content=p))
                    st.session_state.chat_history.append(AIMessage(content=reply))
                else:
                    res = agent.invoke({"input": p})
                    reply = res["output"]
                formatted_reply = format_markdown_display(reply)
                st.session_state.messages.append({"role": "assistant", "content": formatted_reply})
                st.rerun()

        st.markdown("---")
        st.markdown("#### **Current Promotions**")
        st.info("Pizza Party Combo: Order any 2 artisanal pizzas to receive complimentary Cheesy Garlic Knots.\n\nFree Delivery on all orders totaling $40.00 or more.")


# =========================================================
# TAB 2: Live Restaurant Menu
# =========================================================
with tab_menu:
    st.markdown("### **Restaurant Menu**")
    st.caption("Browse items, filter by category or dietary needs, and view allergen information.")

    col_m1, col_m2, col_m3 = st.columns([2, 1.5, 1.5])
    with col_m1:
        search_query = st.text_input("Search Menu Items or Ingredients", "")
    with col_m2:
        selected_category = st.selectbox(
            "Filter by Category",
            options=["All Categories", "Appetizers", "Burgers", "Pizzas", "Pastas", "Beverages", "Desserts"],
            index=0
        )
    with col_m3:
        diet_filter = st.selectbox(
            "Dietary Preference",
            options=["All Diets", "Vegetarian", "Vegan", "Gluten-Free"],
            index=0
        )

    with get_db() as session:
        cat_param = None if selected_category == "All Categories" else selected_category
        items = MenuItemRepository.get_all_dict(session, category=cat_param)

    # Filter by search & dietary
    filtered_items = []
    for it in items:
        if search_query:
            q = search_query.lower()
            if q not in it["name"].lower() and q not in it["description"].lower() and q not in it["category"].lower():
                continue
        if diet_filter == "Vegetarian" and not it["is_vegetarian"]:
            continue
        if diet_filter == "Vegan" and not it["is_vegan"]:
            continue
        if diet_filter == "Gluten-Free" and not it["is_gluten_free"]:
            continue
        filtered_items.append(it)

    st.markdown(f"Showing **{len(filtered_items)}** items")

    # Grid display
    cols = st.columns(3)
    for idx, it in enumerate(filtered_items):
        with cols[idx % 3]:
            badges_html = ""
            if it["is_vegetarian"]:
                badges_html += '<span class="badge badge-veg">Vegetarian</span>'
            if it["is_vegan"]:
                badges_html += '<span class="badge badge-vegan">Vegan</span>'
            if it["is_gluten_free"]:
                badges_html += '<span class="badge badge-gf">Gluten-Free</span>'
            if it["spicy_level"] > 0:
                badges_html += f'<span class="badge badge-spicy">Spicy ({it["spicy_level"]}/3)</span>'

            allergens_text = f"<br><small><b>Allergens:</b> {it['allergens']}</small>" if it["allergens"] != "None" else ""

            st.markdown(f"""
            <div class="menu-card">
                <h4 style="margin: 0 0 5px 0; color: #1E293B;">{it['name']}</h4>
                <div style="font-size: 1.15rem; font-weight: 700; color: #0F766E; margin-bottom: 8px;">${it['price']:.2f}</div>
                <div>{badges_html}</div>
                <p style="color: #475569; font-size: 0.9rem; margin-top: 8px;">{it['description']}</p>
                <div style="font-size: 0.8rem; color: #64748B;">
                    Prep Time: {it['prep_time_mins']} mins | Calories: {it['calories']} kcal {allergens_text}
                </div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# TAB 3: Track & Manage Orders
# =========================================================
with tab_track:
    st.markdown("### **Order Status & Tracking**")
    st.caption("Look up any order by tracking code to check status and line item details.")

    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        track_code = st.text_input("Enter Order Code (e.g. ORD-SEED-1001, ORD-SEED-1005)", value="")
        track_btn = st.button("Track Order", type="primary")

    if track_code or track_btn:
        with get_db() as session:
            order = OrderRepository.get_order_by_code(session, track_code)

        if order:
            st.success(f"Order {order['order_code']} Found")
            
            # Status Progress Bar
            status_map = {
                "PENDING": 10,
                "CONFIRMED": 35,
                "PREPARING": 65,
                "OUT_FOR_DELIVERY": 90,
                "DELIVERED": 100,
                "CANCELLED": 0,
            }
            curr_status = order["status"]
            progress_val = status_map.get(curr_status, 20)

            col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
            with col_p2:
                if curr_status == "CANCELLED":
                    st.error("Order Status: CANCELLED")
                elif curr_status == "DELIVERED":
                    st.success("Order Status: DELIVERED")
                    st.progress(100)
                else:
                    st.info(f"Current Stage: {curr_status} (Est. {order['estimated_delivery_mins']} mins)")
                    st.progress(progress_val)

            # Order Details
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("#### **Customer & Delivery**")
                st.write(f"**Customer Name:** {order['customer_name']}")
                st.write(f"**Phone:** {order['customer_phone']}")
                st.write(f"**Delivery Address:** {order['delivery_address']}")
                st.write(f"**Ordered At:** {order['created_at']}")
                st.write(f"**Special Notes:** {order['special_notes'] or 'None'}")

            with col_d2:
                st.markdown("#### **Items & Financials**")
                for it in order["items"]:
                    note = f" *({it['special_instructions']})*" if it.get("special_instructions") else ""
                    st.write(f"- **{it['quantity']}x** {it['item_name']} - ${it['line_total']:.2f}{note}")
                
                st.markdown("---")
                st.write(f"Subtotal: ${order['subtotal']:.2f}")
                st.write(f"Tax (8%): ${order['tax']:.2f}")
                st.write(f"Delivery Fee: ${order['delivery_fee']:.2f}")
                st.markdown(f"### Total: ${order['total_amount']:.2f}")

            # Cancel Action
            if curr_status in ["PENDING", "CONFIRMED"]:
                st.markdown("---")
                cancel_reason = st.text_input("Reason for cancellation (optional):", "Customer request")
                if st.button("Cancel This Order", type="secondary"):
                    with get_db() as session:
                        OrderRepository.cancel_order(session, order["order_code"], cancel_reason)
                    st.warning("Order has been cancelled.")
                    st.rerun()
        else:
            if track_code:
                st.error(f"No order found with code '{track_code}'. Please verify the order code.")

    st.markdown("---")
    st.markdown("#### **Recent Orders Log**")
    recent_df = RestaurantAnalytics.get_recent_orders_df(limit=10)
    if not recent_df.empty:
        st.dataframe(recent_df, use_container_width=True, hide_index=True)


# =========================================================
# TAB 4: Sales & Best-Sellers Dashboard
# =========================================================
with tab_analytics:
    st.markdown("### **Sales Performance & Best-Sellers Dashboard**")
    st.caption("Insights into best-selling items, revenue distribution, and overall sales performance.")

    # High-level KPI summary cards
    kpis = RestaurantAnalytics.get_kpi_summary()
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric(label="Total Sales Revenue", value=f"${kpis['total_revenue']:,.2f}")
    with col_k2:
        st.metric(label="Total Orders Placed", value=f"{kpis['total_orders']}")
    with col_k3:
        st.metric(label="Average Order Value (AOV)", value=f"${kpis['avg_order_value']:.2f}")
    with col_k4:
        st.metric(label="Active Orders", value=f"{kpis['active_orders']}")

    st.markdown("---")

    # Chart Row 1: Best-Sellers & Category Revenue
    col_c1, col_c2 = st.columns([1.5, 1])

    with col_c1:
        st.markdown("#### **Top Best-Selling Menu Items**")
        best_df = RestaurantAnalytics.get_best_sellers_df(limit=8)
        if not best_df.empty:
            fig_best = px.bar(
                best_df,
                x="Quantity Sold",
                y="Item Name",
                orientation="h",
                color="Category",
                text="Quantity Sold",
                title="Top Dishes by Order Volume",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_best.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=20, r=20, t=40, b=20),
                height=380,
            )
            st.plotly_chart(fig_best, use_container_width=True)
        else:
            st.info("No sales data available yet.")

    with col_c2:
        st.markdown("#### **Revenue by Category**")
        cat_df = RestaurantAnalytics.get_category_sales_df()
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                names="Category",
                values="Revenue ($)",
                hole=0.45,
                title="Sales Share by Food Category",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_cat.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=380,
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No category sales data.")

    st.markdown("---")

    # Chart Row 2: Daily Sales Trend & Order Status Distribution
    col_c3, col_c4 = st.columns([1.5, 1])

    with col_c3:
        st.markdown("#### **Daily Revenue Trend**")
        trend_df = RestaurantAnalytics.get_revenue_trend_df(days=7)
        if not trend_df.empty:
            fig_trend = px.line(
                trend_df,
                x="Date",
                y="Revenue ($)",
                markers=True,
                title="Daily Sales Revenue ($)",
                line_shape="spline",
            )
            fig_trend.update_traces(line_color="#0F766E", line_width=3)
            fig_trend.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No trend data available.")

    with col_c4:
        st.markdown("#### **Order Status Breakdown**")
        status_df = RestaurantAnalytics.get_order_status_df()
        if not status_df.empty:
            fig_status = px.pie(
                status_df,
                names="Status",
                values="Count",
                title="Order Pipeline Status",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_status.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No order status data.")

    st.markdown("---")
    st.markdown("#### **All Time Best Sellers Data Table**")
    st.dataframe(best_df, use_container_width=True, hide_index=True)
