import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configurar la página
st.set_page_config(
    page_title="GASGUARIBE - Sistema de Gas",
    page_icon="🪔",
    layout="wide"
)

# Título principal en español
st.title("🪔 GASGUARIBE")
st.subheader("Sistema de Administración y Reparto de Gas Doméstico")
st.markdown("---")

# URL de tu API (la que ya desplegaste)
API_URL = "https://gas-guaribe.onrender.com"

# Sidebar para navegación
st.sidebar.image("https://img.icons8.com/fluency/96/000000/gas-station.png")
st.sidebar.title("📋 Menú")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["🏠 Inicio", "📦 Nuevo Pedido", "📊 Mis Pedidos", "📈 Estadísticas", "📋 Reportes"]
)

# --- SECCIÓN INICIO ---
if opcion == "🏠 Inicio":
    st.header("Bienvenido a GASGUARIBE")
    st.write("""
    Esta aplicación te permite solicitar gas doméstico a domicilio, 
    realizar seguimiento de tus pedidos y consultar estadísticas.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Pedidos Hoy", "12", "+2")
    with col2:
        st.metric("🚚 Repartidores Activos", "5", "✓")
    with col3:
        st.metric("🏫 Escuelas Exoneradas", "3", "✓")

# --- SECCIÓN NUEVO PEDIDO ---
elif opcion == "📦 Nuevo Pedido":
    st.header("Solicitar Nuevo Pedido")
    
    with st.form("pedido_form"):
        st.subheader("Datos del Cliente")
        cliente_id = st.number_input("ID del Cliente", min_value=1, value=1)
        
        st.subheader("Detalles del Pedido")
        tamanio = st.selectbox(
            "Tamaño del Cilindro",
            ["P (5kg)", "M (15kg)", "G (45kg)"]
        )
        cantidad = st.number_input("Cantidad", min_value=1, max_value=10, value=1)
        
        st.subheader("Dirección de Entrega")
        direccion = st.text_input("Dirección", "Calle Principal 123")
        lat = st.number_input("Latitud", value=10.0, format="%.4f")
        lng = st.number_input("Longitud", value=-66.0, format="%.4f")
        
        enviar = st.form_submit_button("🚀 Solicitar Pedido")
        
        if enviar:
            # Convertir tamaño a código
            tamanio_codigo = {"P (5kg)": "P", "M (15kg)": "M", "G (45kg)": "G"}[tamanio]
            
            # Datos para la API
            data = {
                "cliente_id": cliente_id,
                "tamanio": tamanio_codigo,
                "cantidad": cantidad,
                "direccion": direccion,
                "lat": lat,
                "lng": lng
            }
            
            try:
                response = requests.post(f"{API_URL}/pedidos/solicitar", data=data)
                if response.status_code == 200:
                    resultado = response.json()
                    st.success(f"✅ Pedido creado exitosamente!")
                    st.json(resultado)
                else:
                    st.error(f"❌ Error: {response.text}")
            except:
                st.error("❌ No se pudo conectar con el servidor. ¿Está en línea?")

# --- SECCIÓN MIS PEDIDOS ---
elif opcion == "📊 Mis Pedidos":
    st.header("Historial de Pedidos")
    
    cliente_id = st.number_input("ID del Cliente", min_value=1, value=1)
    if st.button("Ver Pedidos"):
        try:
            response = requests.get(f"{API_URL}/pedidos/mis-pedidos/{cliente_id}")
            if response.status_code == 200:
                pedidos = response.json()
                if pedidos:
                    df = pd.DataFrame(pedidos)
                    st.dataframe(df)
                else:
                    st.info("No hay pedidos para este cliente")
            else:
                st.error("❌ Error al obtener pedidos")
        except:
            st.error("❌ No se pudo conectar con el servidor")

# --- SECCIÓN ESTADÍSTICAS ---
elif opcion == "📈 Estadísticas":
    st.header("Estadísticas en Tiempo Real")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resumen Diario")
        try:
            response = requests.get(f"{API_URL}/reportes/resumen-diario")
            if response.status_code == 200:
                datos = response.json()
                st.metric("📦 Total Pedidos", datos.get("total_pedidos", 0))
                st.metric("💰 Ingresos del Día", f"${datos.get('ingresos_del_dia', 0):.2f}")
                st.metric("🎓 Cilindros Exonerados", datos.get("cilindros_exonerados_hoy", 0))
            else:
                st.warning("No se pudieron obtener estadísticas")
        except:
            st.warning("Servidor no disponible")
    
    with col2:
        st.subheader("Utilidad Acumulada")
        try:
            response = requests.get(f"{API_URL}/reportes/utilidad-acumulada")
            if response.status_code == 200:
                datos = response.json()
                st.metric("💰 Ingresos Totales", f"${datos.get('ingresos_totales', 0):.2f}")
                st.metric("📊 Utilidad Bruta", f"${datos.get('utilidad_bruta', 0):.2f}")
                st.metric("📈 Utilidad Neta", f"${datos.get('utilidad_neta', 0):.2f}")
            else:
                st.warning("No se pudieron obtener estadísticas")
        except:
            st.warning("Servidor no disponible")

# --- SECCIÓN REPORTES ---
elif opcion == "📋 Reportes":
    st.header("Generar Reportes")
    st.info("Próximamente: Generación de reportes en PDF y Excel")

# Pie de página
st.sidebar.markdown("---")
st.sidebar.caption("🇻🇪 GASGUARIBE v1.0")
st.sidebar.caption("Municipio Guaribe")
