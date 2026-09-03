# Technical Architecture & Design Document

## 1. Executive Summary

The **FlavorCraft Bistro AI Ordering System** is built from the ground up as a decoupled, modular, and resilient micro-architecture designed to bridge conversational AI with structured relational transactions and real-time business analytics.

```mermaid
flowchart TD
    subgraph UI_Layer [Presentation Layer (Streamlit)]
        UI_Chat[AI Order Assistant]
        UI_Menu[Interactive Menu Browser]
        UI_Tracker[Live Order Tracker]
        UI_Dashboard[Sales & Performance Analytics]
    end

    subgraph Agent_Layer [Agent & Tool-Calling Pipeline (LangChain)]
        Prompt[System Prompt & Memory Buffer]
        LLM[Multi-Provider LLM: OpenAI / Gemini / Groq]
        AgentCore[LangChain Tool-Calling Agent]
        
        subgraph Custom_Tools [Custom Agent Tools (No Direct SQL Agent)]
            Tool_Order[place_food_order]
            Tool_Status[get_order_status]
            Tool_Cancel[cancel_food_order]
            Tool_Menu[get_full_restaurant_menu]
            Tool_RAG[search_restaurant_knowledge]
        end
    end

    subgraph RAG_Layer [Knowledge & Retrieval Engine]
        RAG_Catalog[(menu_catalog.json)]
        RAG_Policies[(restaurant_info.md)]
        VectorEngine[Semantic & Lexical Knowledge Indexer]
    end

    subgraph Storage_Layer [Persistence & Data Access Layer]
        Repo_Menu[MenuItemRepository]
        Repo_Customer[CustomerRepository]
        Repo_Order[OrderRepository]
        Repo_Analytics[AnalyticsRepository]
        SQLite_DB[(SQLite Database / SQLAlchemy ORM)]
    end

    UI_Chat --> AgentCore
    AgentCore --> Prompt
    AgentCore --> LLM
    AgentCore --> Custom_Tools

    Tool_RAG --> VectorEngine
    VectorEngine --> RAG_Catalog
    VectorEngine --> RAG_Policies

    Tool_Order --> Repo_Order
    Tool_Status --> Repo_Order
    Tool_Cancel --> Repo_Order
    Tool_Menu --> VectorEngine

    Repo_Order --> SQLite_DB
    Repo_Customer --> SQLite_DB
    Repo_Menu --> SQLite_DB
    Repo_Analytics --> SQLite_DB

    UI_Menu --> Repo_Menu
    UI_Tracker --> Repo_Order
    UI_Dashboard --> Repo_Analytics
```

---

## 2. Component Breakdown

### 2.1 LangChain Agent & Custom Tool System
- **Constraint Satisfaction**: As required by candidate instructions, the system **explicitly avoids generic SQL agents** (such as `create_sql_agent`), which can cause unintended schema mutations, SQL injections, or unconstrained queries.
- **Custom Tools**: All database mutations and queries pass through strictly validated Pydantic schemas:
  - `PlaceOrderInput`: Validates `customer_name`, `customer_phone`, `delivery_address`, and a `List[OrderItemInput]`.
  - `OrderItemInput`: Enforces `item_name`, `quantity >= 1`, and optional `special_instructions`.
  - `OrderStatusInput`: Validates order codes.
  - `CancelOrderInput`: Validates order codes and reasons.
- **Multi-Item Parsing**: The LLM system prompt directs the model to extract all line items from a customer's prompt into the `items` list in a single tool call invocation.

### 2.2 RAG (Retrieval-Augmented Generation) Architecture
- **Knowledge Sources**:
  - `menu_catalog.json`: Contains granular structured attributes including title, category, price, dietary flags (`Vegetarian`, `Vegan`, `Gluten-Free`), allergens (`Dairy`, `Eggs`, `Nuts`, `Gluten`, `Soy`), calories, and chef pairings.
  - `restaurant_info.md`: Documents delivery rules, minimum order thresholds, sales tax rates (8%), kitchen operating hours, and cancellation terms.
- **Indexing & Retrieval Pipeline**:
  - Documents are converted into structured passage chunks.
  - Search engine uses composite scoring (exact title matching, token overlap, dietary keywords, and category filters).
  - Contextual responses format retrieved documents into clean, readable markdown snippets for the LLM.

### 2.3 Data Storage & Transactions (SQLAlchemy)
- **Data Models**:
  - `MenuItem`: Represents dishes, prices, categories, calorie counts, preparation times, and dietary flags.
  - `Customer`: Persists customer contact details and delivery addresses.
  - `Order`: Represents the master order record (`order_code`, `status`, `subtotal`, `tax`, `delivery_fee`, `total_amount`, `estimated_delivery_mins`, `created_at`).
  - `OrderItem`: Line items associated with an order (`quantity`, `unit_price`, `line_total`, `special_instructions`).
- **Atomic Operations**: All calculations (subtotal calculation, free delivery thresholds, 8% tax calculation, foreign key associations) are executed in a single atomic database session with automatic rollbacks upon validation failures.

### 2.4 Sales Analytics Engine
- **Aggregations**:
  - `AnalyticsRepository.get_sales_summary()` calculates Total Revenue, Total Orders, Active Orders, and Average Order Value (AOV).
  - `AnalyticsRepository.get_best_selling_items()` aggregates order items by total quantity sold and revenue generated.
  - `AnalyticsRepository.get_sales_by_category()` computes revenue shares across appetizers, burgers, pizzas, pastas, desserts, and beverages.
  - `AnalyticsRepository.get_daily_revenue_trend()` tracks day-by-day sales trajectory.

---

## 3. Reliability & Scalability Strategies

1. **Decoupled Architecture**: Each layer (UI, Agent, Database, RAG, Analytics) is independently testable and isolated from external dependencies.
2. **Provider Agnostic**: Seamlessly switches between OpenAI, Google Gemini, Groq, and an internal Fallback Agent without code changes.
3. **Thread Safety**: SQLite is configured with `check_same_thread=False` and scoped session management to ensure concurrent Streamlit worker threads do not collide.
4. **Comprehensive Test Suite**: Every component is backed by unit and integration tests under `tests/`.
