"""
Test script for the Habibi Restaurant Agent.
Tests various scenarios with new and existing session IDs.
"""
import requests
import uuid

BASE_URL = "http://localhost:5000"

def chat(message: str, session_id: str = None) -> dict:
    """Send a chat message to the agent."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    return response.json()

def test_new_session_direct_question():
    """Test: New session, direct question without greeting."""
    print("\n" + "="*60)
    print("TEST: Nueva sesión - Pregunta directa (sin saludo)")
    print("="*60)
    
    result = chat("¿Qué hay en el menú?")
    print(f"Session ID: {result.get('session_id')}")
    print(f"Respuesta: {result.get('response')}")
    print(f"Respuesta vacía: {result.get('response') == ''}")
    return result

def test_new_session_with_greeting():
    """Test: New session with greeting first."""
    print("\n" + "="*60)
    print("TEST: Nueva sesión - Con saludo")
    print("="*60)
    
    result = chat("¡Hola!")
    session_id = result.get('session_id')
    print(f"Session ID: {session_id}")
    print(f"Respuesta: {result.get('response')}")
    return result

def test_conversation_flow():
    """Test: Full conversation flow with same session."""
    print("\n" + "="*60)
    print("TEST: Flujo de conversación completo")
    print("="*60)
    
    session_id = str(uuid.uuid4())
    
    messages = [
        "¡Hola!",
        "¿Qué tienen en el menú?",
        "Agrega 2 shawarma a mi orden",
        "¿Qué hay en mi carrito?",
        "¿Están abiertos ahorita?"
    ]
    
    for msg in messages:
        print(f"\n> Usuario: {msg}")
        result = chat(msg, session_id)
        response = result.get('response', '')
        print(f"< Habibi: {response}")
        if response == '':
            print("⚠️  ADVERTENCIA: ¡Respuesta vacía detectada!")
    
    return session_id

def test_specific_session(session_id: str, message: str):
    """Test with a specific session ID."""
    print("\n" + "="*60)
    print(f"TEST: Specific session - {session_id[:8]}...")
    print("="*60)
    
    print(f"> User: {message}")
    result = chat(message, session_id)
    print(f"< Agent: {result.get('response')}")
    return result

def interactive_mode():
    """Interactive testing mode."""
    print("\n" + "="*60)
    print("MODO INTERACTIVO")
    print("="*60)
    print("Comandos:")
    print("  /nuevo   - Iniciar nueva sesión")
    print("  /sesion  - Mostrar ID de sesión actual")
    print("  /salir   - Salir del modo interactivo")
    print("="*60)
    
    session_id = None
    
    while True:
        user_input = input("\nTú: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == "/salir":
            print("Saliendo del modo interactivo.")
            break
        
        if user_input.lower() == "/nuevo":
            session_id = str(uuid.uuid4())
            print(f"Nueva sesión iniciada: {session_id}")
            continue
        
        if user_input.lower() == "/sesion":
            print(f"Sesión actual: {session_id or 'Ninguna (se creará una nueva)'}")
            continue
        
        result = chat(user_input, session_id)
        session_id = result.get('session_id')  # Keep the session
        response = result.get('response', '')
        
        if response == '':
            print("Habibi: ⚠️ [RESPUESTA VACÍA]")
        else:
            print(f"Habibi: {response}")

def main():
    print("="*60)
    print("HABIBI RESTAURANTE - PRUEBAS")
    print("="*60)
    print(f"Probando contra: {BASE_URL}")
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=3)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: ¡El servidor no está corriendo!")
        print("Primero inicia el servidor con: python api/index.py")
        return
    
    print("\nSelecciona modo de prueba:")
    print("1. Ejecutar todas las pruebas automáticas")
    print("2. Probar nueva sesión con pregunta directa")
    print("3. Probar flujo de conversación completo")
    print("4. Modo interactivo")
    print("5. Salir")
    
    choice = input("\nOpción (1-5): ").strip()
    
    if choice == "1":
        test_new_session_direct_question()
        test_new_session_with_greeting()
        test_conversation_flow()
        print("\n" + "="*60)
        print("TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
    
    elif choice == "2":
        test_new_session_direct_question()
    
    elif choice == "3":
        test_conversation_flow()
    
    elif choice == "4":
        interactive_mode()
    
    elif choice == "5":
        print("¡Hasta luego!")
    
    else:
        print("Opción inválida.")

if __name__ == "__main__":
    main()
