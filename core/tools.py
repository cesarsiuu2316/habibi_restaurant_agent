from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field
from datetime import datetime

# --- Base de Datos ---
MENU = {
    "hummus": {"precio": 5.00, "categoria": "entrada", "nombre": "Hummus"},
    "shawarma": {"precio": 12.00, "categoria": "principal", "nombre": "Shawarma"},
    "falafel": {"precio": 10.00, "categoria": "entrada", "nombre": "Falafel"},
    "baklava": {"precio": 4.50, "categoria": "postre", "nombre": "Baklava"},
    "refresco": {"precio": 2.50, "categoria": "bebida", "nombre": "Refresco"},
    "agua": {"precio": 1.00, "categoria": "bebida", "nombre": "Agua"}
}
HORARIO = "Lunes a Domingo: 10:00 AM - 10:00 PM"
HORA_APERTURA = 16  # 10:00 AM CST but GMT+0 is 16:00
HORA_CIERRE = 6    # 10:00 PM CST but GMT+0 is 04:00 next day

@tool
def check_current_time() -> str:
    """
    Verificar la hora actual y si el restaurante está abierto. SIEMPRE llamar esta herramienta primero antes de cualquier otra acción.
    """
    now = datetime.now()
    hora_actual = now.hour
    
    # ajustar validaciones para horario GMT+0
    if (HORA_APERTURA <= hora_actual < 24) or (0 <= hora_actual < HORA_CIERRE):
        return "ABIERTO"
    else:
        return f"CERRADO. Lo sentimos, estamos cerrados en este momento. Puedes visitarnos en nuestro horario: {HORARIO}."

# --- Esquemas de Entrada ---
class MenuInput(BaseModel):
    query: str = Field(description="Nombre del platillo a buscar o 'todo' para ver el menú completo.")

class AddOrderInput(BaseModel):
    item_name: str = Field(description="Nombre del platillo a agregar.")
    quantity: int = Field(description="Cantidad a agregar.")

class FinalizeInput(BaseModel):
    customer_name: str = Field(description="Nombre completo.")
    email: str = Field(description="Correo electrónico.")
    address: str = Field(description="Dirección de entrega.")
    phone: str = Field(description="Número de teléfono.")

# --- Tools ---

@tool(args_schema=MenuInput)
def get_menu_info(query: str) -> str:
    """
    Buscar platillos en el menú, precios y disponibilidad.
    """
    if query.lower() in ["all", "todo", "todos", "menu", "menú"]:
        items = [f"- {v['nombre']}: ${v['precio']:.2f}" for k, v in MENU.items()]
        return "Menú Actual:\n" + "\n".join(items)
    
    q = query.lower()
    # Búsqueda flexible
    found = [f"- {v['nombre']}: ${v['precio']:.2f}" for k, v in MENU.items() if q in k or q in v['nombre'].lower()]
    if found:
        return "Platillos encontrados:\n" + "\n".join(found)
    return f"Lo siento, '{query}' no está en nuestro menú."

@tool
def check_store_hours() -> str:
    """Consultar el horario del restaurante."""
    return f"Estamos abiertos: {HORARIO}."

@tool(args_schema=AddOrderInput)
def add_to_order(item_name: str, quantity: int, runtime: ToolRuntime) -> Command:
    """
    Agregar platillos a la orden.
    """
    item_key = item_name.lower()
    tool_call_id = runtime.tool_call_id
    
    if item_key not in MENU:
        return Command(
            update={
                "messages": [ToolMessage(content=f"Error: {item_name} no se encuentra en el menú.", tool_call_id=tool_call_id)]
            }
        )
    
    price = MENU[item_key]["precio"]
    total = price * quantity
    nombre = MENU[item_key]["nombre"]
    
    current_order = runtime.state.get("order_items", [])
    new_item = {"item": item_key, "nombre": nombre, "precio": price, "quantity": quantity, "total": total}
    updated_list = current_order + [new_item]
    
    output_msg = f"Se agregó {quantity} x {nombre} a tu carrito. (${total:.2f})"
    
    return Command(
        update={
            "order_items": updated_list,
            "messages": [ToolMessage(content=output_msg, tool_call_id=tool_call_id)]
        }
    )

@tool
def get_current_order_summary(runtime: ToolRuntime) -> str:
    """Obtener resumen del carrito y total."""
    order = runtime.state.get("order_items", [])
    if not order:
        return "El carrito está vacío."
    
    lines = [f"{x['quantity']}x {x.get('nombre', x['item'].title())} (${x['total']:.2f})" for x in order]
    grand_total = sum(x['total'] for x in order)
    return "Resumen del Carrito:\n" + "\n".join(lines) + f"\n\nTotal: ${grand_total:.2f}"

@tool(args_schema=FinalizeInput)
def finalize_order(customer_name: str, email: str, address: str, phone: str, runtime: ToolRuntime) -> Command:
    """
    Finalizar la orden. Usar SOLO después de confirmación.
    """
    order = runtime.state.get("order_items", [])
    tool_call_id = runtime.tool_call_id
    
    if not order:
        return Command(
             update={"messages": [ToolMessage(content="No se puede finalizar una orden vacía.", tool_call_id=tool_call_id)]}
        )

    print(f"\n--- ENVIANDO ORDEN DE {customer_name} A {email} ---\nDirección: {address}\nPlatillos: {order}\n")
    
    return Command(
        update={
            "order_items": [],
            "messages": [ToolMessage(content=f"¡Orden confirmada! Recibo enviado a {email}.", tool_call_id=tool_call_id)]
        }
    )