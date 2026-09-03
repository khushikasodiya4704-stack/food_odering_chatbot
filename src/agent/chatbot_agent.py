"""
LangChain / LangGraph Agent implementation for food ordering with multi-provider support (OpenAI, Gemini, Groq, Fallback).
"""

import os
import re
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from config import settings
from src.agent.tools import ALL_CUSTOM_TOOLS
from src.agent.prompts import SYSTEM_PROMPT


def clean_text_content(content: Any) -> str:
    """
    Extracts and sanitizes text from raw message content:
    - Unwraps raw JSON/list-of-dict content representations from Gemini/OpenAI
    - Strips emojis and Windows CP1252 Mojibake corruption characters (like ð, ï¸, µ, ¢, â)
    - Removes LaTeX math mode delimiters (\\( and \\)) that cause KaTeX letter spacing distortions
    """
    if not content:
        return ""

    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if "text" in block:
                    parts.append(str(block["text"]))
                elif "content" in block:
                    parts.append(str(block["content"]))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        text = "\n".join(parts)
    elif isinstance(content, dict):
        text = content.get("text", content.get("content", str(content)))
    else:
        text = str(content)

    # Clean raw stringified list-of-dict representations if any
    if text.strip().startswith("[{") and "'text':" in text:
        match = re.search(r"['\"]text['\"]\s*:\s*['\"](.*?)['\"]\s*(?:,\s*['\"]extras|\}\])", text, re.DOTALL)
        if match:
            try:
                text = match.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
            except Exception:
                text = match.group(1)

    # Remove all Unicode emojis
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\U0001f300-\U0001f9ff\U0001fa00-\U0001faff]",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)

    # Remove Windows CP1252 Mojibake corrupted characters (ð, ï, ¸, µ, ¢, â, etc.)
    text = re.sub(r"[ðï¸¢µâ\ufffd]", "", text)

    # Remove LaTeX inline math delimiters \( and \) so Streamlit doesn't render text in math mode
    text = text.replace(r"\(", "(").replace(r"\)", ")")
    text = text.replace(r"\[", "[").replace(r"\]", "]")
    text = text.replace(r"\$", "$")

    # Clean redundant blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def get_llm(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
):
    """
    Factory function returning an initialized LLM ChatModel.
    Supports OpenAI, Google Gemini, and Groq with graceful fallback.
    """
    selected_provider = (provider or settings.LLM_PROVIDER or "openai").lower()
    
    # 1. OpenAI
    if selected_provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not key:
            raise ValueError("OpenAI API Key is missing. Please provide OPENAI_API_KEY in .env.")
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name or settings.OPENAI_MODEL_NAME or "gpt-5.4-nano",
                api_key=key,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError("langchain-openai is not installed. Run `pip install langchain-openai`.")

    # 2. Google Gemini
    elif selected_provider in ["gemini", "google"]:
        key = api_key or os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
        if not key:
            raise ValueError("Google Gemini API Key is missing. Please provide GOOGLE_API_KEY in .env.")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model_name or settings.GEMINI_MODEL_NAME or "gemini-3.5-flash",
                google_api_key=key,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError("langchain-google-genai is not installed. Run `pip install langchain-google-genai`.")

    # 3. Groq
    elif selected_provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        if not key:
            raise ValueError("Groq API Key is missing. Please provide GROQ_API_KEY in .env.")
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=model_name or settings.GROQ_MODEL_NAME or "llama-3.3-70b-versatile",
                groq_api_key=key,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError("langchain-groq is not installed. Run `pip install langchain-groq`.")

    else:
        raise ValueError(f"Unsupported LLM provider: {selected_provider}. Choose 'openai', 'gemini', or 'groq'.")


class LangGraphOrderingAgent:
    """
    Agent wrapper encapsulating LangGraph / LangChain tool execution and conversational memory.
    """
    def __init__(self, llm):
        from langgraph.prebuilt import create_react_agent
        self.agent = create_react_agent(
            model=llm,
            tools=ALL_CUSTOM_TOOLS,
            prompt=SYSTEM_PROMPT,
        )

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        user_input = inputs.get("input", "")
        chat_history = inputs.get("chat_history", [])

        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_input))

        result = self.agent.invoke({"messages": messages})
        
        final_msgs = result.get("messages", [])
        output_text = "I have processed your request."
        if final_msgs:
            output_text = clean_text_content(final_msgs[-1].content)

        return {"output": output_text}


def create_ordering_agent(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
):
    """
    Creates a LangGraph / LangChain Agent equipped with custom DB and RAG tools.
    """
    llm = get_llm(provider=provider, api_key=api_key, model_name=model_name)
    return LangGraphOrderingAgent(llm=llm)


class FallbackAgent:
    """
    Simulated agent fallback when no API key is provided yet,
    allowing users to explore menu, check status, and place orders offline.
    """
    def __init__(self):
        from src.rag.retriever import retriever
        self.retriever = retriever

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        user_msg = inputs.get("input", "").strip()
        user_msg_lower = user_msg.lower()

        # Check for menu inquiry
        if any(w in user_msg_lower for w in ["menu", "food", "what do you have", "dishes", "options"]):
            response = self.retriever.get_full_menu_summary()
            return {"output": clean_text_content(f"Here is our complete menu:\n\n{response}\n\n*To place an order, specify the items you would like along with your name, phone number, and delivery address.*")}

        # Check for status inquiry
        if "ord-" in user_msg_lower or "track" in user_msg_lower or "status" in user_msg_lower:
            words = user_msg.replace(":", " ").replace(",", " ").split()
            found_code = None
            for w in words:
                if w.upper().startswith("ORD-"):
                    found_code = w.upper()
                    break
            
            if found_code:
                from src.agent.tools import get_order_status
                return {"output": clean_text_content(get_order_status.invoke({"order_code": found_code}))}
            else:
                return {"output": "Please provide your Order Tracking Code (e.g. `ORD-SEED-1001` or `ORD-XXXX`) to check your status."}

        # Check for RAG search (vegan, gluten, allergens, hours, delivery)
        if any(w in user_msg_lower for w in ["vegan", "gluten", "vegetarian", "allergen", "hours", "delivery", "policy", "price", "spicy", "burger", "pizza", "pasta"]):
            rag_info = self.retriever.query(user_msg)
            return {"output": clean_text_content(f"Information from FlavorCraft Bistro knowledge base:\n\n{rag_info}\n\nWould you like to place an order for any of these items?")}

        # Default greeting / assistance
        return {
            "output": clean_text_content(
                "**Welcome to FlavorCraft Bistro.** I am your AI dining assistant.\n\n"
                "I can assist you with:\n"
                "- Browsing our menu (burgers, pizzas, pastas, desserts, beverages)\n"
                "- Dietary recommendations (Vegan, Vegetarian, Gluten-Free, Allergens)\n"
                "- Ordering food (accepts multiple items in a single message)\n"
                "- Real-time order tracking and status checks\n\n"
                "*(Note: LLM provider, models, and API keys are configured via backend .env)*"
            )
        }
