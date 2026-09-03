# FlavorCraft Bistro - AI Food Ordering Chatbot & Sales Analytics

An enterprise-grade, scalable, and reliable AI food ordering and restaurant management platform. Built with **LangChain / LangGraph**, **RAG (Retrieval-Augmented Generation)**, **Custom Database Tools** (without generic SQL agents), **SQLite & SQLAlchemy ORM**, and a full-featured **Streamlit Web Application & Sales Analytics Dashboard**.

---

## Key Features

### 1. Conversational AI Agent (LangChain / LangGraph)
- **Multi-Item Natural Language Ordering**: Parses and places complex orders containing multiple items, quantities, and customizations in a single message (e.g. *"I would like 2 Classic Cheeseburgers with no onions, 1 Truffle Fries, and 2 Diet Cokes for David at 742 Evergreen Terrace, phone 555-0102"*).
- **Custom Tool Calling**: Uses purpose-built, strictly typed custom tools (`place_food_order`, `get_order_status`, `cancel_food_order`, `search_restaurant_knowledge`, `get_full_restaurant_menu`).
- **Strictly No Direct SQL Agent**: Pure Python typed validation and atomic database transactions using SQLAlchemy.
- **Multi-Provider LLM Support**: Compatible with **OpenAI** (`gpt-4o-mini`, `gpt-4o`), **Google Gemini** (`gemini-1.5-flash`, `gemini-2.0-flash`), **Groq** (`llama-3.1-70b`), and an **Offline Demo Mode**.

### 2. RAG (Retrieval-Augmented Generation) Knowledge Base
- **Menu & Ingredient Catalog**: Semantic retrieval for dish descriptions, calorie counts, preparation times, and pairing recommendations.
- **Dietary & Allergen Filtering**: Direct answers on vegan, vegetarian, gluten-free dishes, and allergen warnings (dairy, nuts, gluten, soy).
- **Restaurant Policies & FAQs**: Information on operating hours (10 AM - 11 PM), delivery fees (\$3.99 flat, free over \$40), cancellation rules, and promotions.

### 3. Database Layer (SQLAlchemy & SQLite)
- **Relational Schema**: `MenuItem`, `Customer`, `Order`, `OrderItem`, and `OrderStatus` enum.
- **Atomic Transactions**: Calculates subtotal, tax (8%), delivery fees, discounts, and line items atomically.
- **Seed Data**: Pre-loaded with 25+ realistic dishes and past order history for testing and analytics exploration.

### 4. Sales Performance & Best-Sellers Dashboard
- **Executive KPIs**: Total Sales Revenue, Total Orders Placed, Average Order Value (AOV), and Active Orders.
- **Interactive Visualizations**:
  - **Top Best-Selling Items** (Horizontal Bar Chart by Volume & Revenue)
  - **Category Revenue Distribution** (Donut Chart)
  - **Daily Revenue Trends** (Line Chart)
  - **Order Pipeline Status** (Pie Chart)
  - **Recent Orders Data Table**

### 5. Real-Time Order Tracking & Management
- Look up any order by its tracking code (e.g. `ORD-SEED-1001` or generated codes like `ORD-A1B2C3`).
- Progress bar showing order stages: `CONFIRMED` -> `PREPARING` -> `OUT_FOR_DELIVERY` -> `DELIVERED`.
- In-flight cancellation option for eligible orders (`PENDING`/`CONFIRMED`).

---

## Project Architecture

```
chatbot/
├── config.py                   # Central configuration & environment loader
├── app.py                      # Main Streamlit web application & dashboard
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── README.md                   # Project overview & quickstart guide
├── ARCHITECTURE.md             # In-depth architectural documentation
├── src/
│   ├── database/               # Relational database models, connections & repository
│   │   ├── models.py           # SQLAlchemy models (MenuItem, Customer, Order, OrderItem)
│   │   ├── connection.py       # Engine & transactional session management
│   │   ├── seed_data.py        # 25+ menu items & historical orders seeder
│   │   └── repository.py       # Data access layer for menu, orders & analytics
│   ├── rag/                    # RAG vector store, documents & semantic retriever
│   │   ├── vector_store.py     # Document indexing & scoring engine
│   │   ├── retriever.py        # Markdown contextual retrieval formatting
│   │   └── documents/          # Knowledge base (menu catalog & policies)
│   ├── agent/                  # LangChain Agent, custom tools & prompts
│   │   ├── schemas.py          # Pydantic schemas for structured tool inputs
│   │   ├── tools.py            # Custom DB tools (place order, status, cancel, RAG)
│   │   ├── prompts.py          # Agent system prompt & multi-item guidelines
│   │   └── chatbot_agent.py    # Agent executor & multi-provider LLM factory
│   └── analytics/              # Aggregation engine for sales metrics & charts
│       └── metrics.py          # Business intelligence and DataFrame generators
└── tests/                      # Automated test suite
    ├── test_database.py        # Database transactions & models tests
    ├── test_rag.py             # Knowledge ingestion & semantic search tests
    └── test_agent_tools.py     # Custom tools & multi-item order tests
```

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10 to 3.13 recommended.

### 2. Installation
```bash
# Clone repository
cd chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env` and configure keys if desired:
```bash
cp .env.example .env
```
*(You can also configure API keys directly inside the Streamlit sidebar at runtime or use Offline Demo Mode without any API keys)*

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
pytest tests/ -v
```

---

## Sample Conversational Prompts

1. **Dietary Inquiry (RAG)**:
   > *"What vegan and gluten-free options do you have on the menu?"*
2. **Multi-Item Food Ordering**:
   > *"I would like to order 2 Margherita Classica Pizzas and 1 Truffle Parmesan Fries for Sophia Chang, phone 555-0103, address 88 Pine Crest Blvd."*
3. **Menu & Policies**:
   > *"What are your delivery hours and what is the policy for free delivery?"*
4. **Order Status Tracking**:
   > *"Can you check the status of order ORD-SEED-1001?"*
5. **Pairing Suggestions**:
   > *"What drink pairs well with the Smoky BBQ Bacon Burger?"*
