from dotenv import load_dotenv
import os
from typing import TypedDict, List

# LangChain Imports
from langchain.agents import create_agent, AgentState
from langchain_groq import ChatGroq
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.checkpoint.memory import MemorySaver 

# Tools
from core.tools import (
    check_current_time,
    get_menu_info, 
    check_store_hours, 
    add_to_order, 
    get_current_order_summary, 
    finalize_order
)

load_dotenv()

# Define State
class RestaurantState(AgentState):
    order_items: List[dict]

# Middleware for Logic Control
@dynamic_prompt
def logic_middleware(request: ModelRequest) -> str:
    """
    Dynamically injects instructions based on the user's cart status.
    """
    state = request.state
    order_items = state.get("order_items", [])
    
    system_prompt = """Eres Habibi, un asistente de restaurante amigable. SIEMPRE responde en español.

    REGLA CRÍTICA: SIEMPRE llama a check_current_time PRIMERO antes de hacer cualquier otra cosa.
    - Si el resultado dice "CERRADO", responde ÚNICAMENTE con el mensaje de cerrado que recibiste. No hagas nada más.
    - Si el resultado dice "ABIERTO", continúa ayudando al usuario normalmente sin mencionar la hora.

    IMPORTANTE: Cuando uses una herramienta y recibas información, SIEMPRE incluye esa información en tu respuesta al usuario.

    Herramientas disponibles:
    - check_current_time: SIEMPRE llámala PRIMERO para verificar si estamos abiertos.
    - get_menu_info: Llámala cuando el usuario pregunte por el menú, comida, platillos o precios.
    - check_store_hours: Llámala cuando pregunten por el horario.
    - add_to_order: Llámala cuando el usuario quiera ordenar/agregar platillos (SOLO si estamos ABIERTOS).
    - get_current_order_summary: Llámala cuando pregunten por su carrito/orden.
    - finalize_order: Llámala cuando el usuario dé nombre, email, dirección y teléfono para pagar.

    Sé amable y conversacional. Siempre comparte los datos reales de las herramientas. RESPONDE SIEMPRE EN ESPAÑOL."""

    if order_items:
        count = sum(i['quantity'] for i in order_items)
        system_prompt += f"\n\nEl cliente tiene {count} artículo(s) en su carrito."
        
    return system_prompt

class OrderAgent:
    def __init__(self):
        print("Initializing Agent with Groq...")

        self.model = ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0, 
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.checkpointer = MemorySaver()

        self.agent = create_agent(
            model=self.model,
            tools=[
                check_current_time,
                get_menu_info, 
                check_store_hours, 
                add_to_order, 
                get_current_order_summary, 
                finalize_order
            ],
            state_schema=RestaurantState,
            middleware=[logic_middleware],
            checkpointer=self.checkpointer
        )

    def get_response(self, user_text: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get message count before invoking to know where new messages start
        try:
            state_before = self.agent.get_state(config)
            msg_count_before = len(state_before.values.get("messages", []))
        except:
            msg_count_before = 0
        
        # Invoke agent
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_text}]},
            config=config
        )
        
        # Get only the NEW messages from this turn
        all_messages = response.get("messages", [])
        new_messages = all_messages[msg_count_before:] if msg_count_before > 0 else all_messages
        
        # Find the last AI message with actual content from new messages
        for msg in reversed(new_messages):
            msg_type = getattr(msg, 'type', None) or msg.__class__.__name__.lower().replace('message', '')
            
            if msg_type not in ('ai', 'aimessage', 'assistant'):
                continue
            
            content = getattr(msg, 'content', None)
            
            if content and content.strip():
                # Clean up any XML function tags that leaked through
                import re
                content = re.sub(r'<function=\w+>.*?</function>', '', content)
                content = re.sub(r'<function=\w+>\{.*?\}', '', content)
                content = content.strip()
                if content:
                    return content
        
        # Fallback: Return tool message content directly
        for msg in reversed(new_messages):
            msg_type = getattr(msg, 'type', None) or msg.__class__.__name__.lower()
            if 'tool' in msg_type:
                content = getattr(msg, 'content', None)
                if content and content.strip():
                    return content
        
        return "Lo siento, no pude procesar eso. ¿Podrías intentarlo de nuevo?"