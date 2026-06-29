import os
from groq import Groq
from .database import SessionLocal
from .models import (
    Pedido, Cliente, Planta, Cilindro, DetallePedido, CostoOperativo
)
from sqlalchemy import func
import json
from datetime import datetime, timedelta

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_estadisticas_completas():
    db = SessionLocal()
    try:
        hoy = datetime.now().date()
        inicio_mes = hoy.replace(day=1)

        # --- 1. PEDIDOS ---
        total_pedidos = db.query(Pedido).count()
        pedidos_hoy = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) == hoy).count()
        pedidos_mes = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) >= inicio_mes).count()
        
        pendientes = db.query(Pedido).filter(Pedido.estado == "pendiente").count()
        en_ruta = db.query(Pedido).filter(Pedido.estado == "en_ruta").count()
        entregados = db.query(Pedido).filter(Pedido.estado == "entregado").count()
        cancelados = db.query(Pedido).filter(Pedido.estado == "cancelado").count()

        # --- 2. FINANZAS ---
        pedidos_entregados = db.query(Pedido).filter(Pedido.estado == "entregado").all()
        ingreso_total = sum(float(p.monto_total) for p in pedidos_entregados)
        costo_logistico_total = sum(float(p.costo_logistico) for p in pedidos_entregados)
        costo_admin_total = sum(float(p.costo_administrativo) for p in pedidos_entregados)
        utilidad_bruta = ingreso_total - costo_logistico_total
        utilidad_neta = utilidad_bruta - costo_admin_total

        # --- 3. CILINDROS ---
        total_cilindros = db.query(Cilindro).count()
        disponibles = db.query(Cilindro).filter(Cilindro.estado == "disponible").count()
        en_ruta_cil = db.query(Cilindro).filter(Cilindro.estado == "en_ruta").count()
        vacios = db.query(Cilindro).filter(Cilindro.estado == "vacio").count()
        
        cilindros_por_tamano = {}
        ventas_por_tamano = {"P": 0, "M": 0, "G": 0}
        for tam in ["P", "M", "G"]:
            count = db.query(Cilindro).filter(Cilindro.tamanio == tam).count()
            cilindros_por_tamano[tam] = count

        # --- 4. EXONERACIONES ---
        detalles = db.query(DetallePedido).all()
        exonerados_total = 0
        valor_exoneraciones = 0
        for d in detalles:
            if d.exonerado:
                exonerados_total += d.cantidad
                valor_exoneraciones += float(d.precio_unitario) * d.cantidad

        # --- 5. PLANTAS ---
        plantas = db.query(Planta).all()
        datos_plantas = []
        for p in plantas:
            pedidos_planta = db.query(Pedido).filter(Pedido.planta_asignada_id == p.id).count()
            ingresos_planta = sum(
                float(ped.monto_total) for ped in db.query(Pedido).filter(
                    Pedido.planta_asignada_id == p.id, Pedido.estado == "entregado"
                ).all()
            )
            datos_plantas.append({
                "nombre": p.nombre,
                "pedidos": pedidos_planta,
                "ingresos": round(ingresos_planta, 2)
            })

        # --- 6. COSTOS OPERATIVOS ---
        costos_logisticos = db.query(CostoOperativo).filter(CostoOperativo.tipo == "Logístico").all()
        costos_admin = db.query(CostoOperativo).filter(CostoOperativo.tipo == "Administrativo").all()
        total_logistico = sum(float(c.monto) for c in costos_logisticos)
        total_admin = sum(float(c.monto) for c in costos_admin)

        return {
            "fecha_actual": str(hoy),
            "pedidos": {
                "total": total_pedidos,
                "hoy": pedidos_hoy,
                "este_mes": pedidos_mes,
                "pendientes": pendientes,
                "en_ruta": en_ruta,
                "entregados": entregados,
                "cancelados": cancelados,
            },
            "finanzas": {
                "ingreso_total": round(ingreso_total, 2),
                "costo_logistico": round(costo_logistico_total, 2),
                "costo_administrativo": round(costo_admin_total, 2),
                "utilidad_bruta": round(utilidad_bruta, 2),
                "utilidad_neta": round(utilidad_neta, 2),
            },
            "cilindros": {
                "total": total_cilindros,
                "disponibles": disponibles,
                "en_ruta": en_ruta_cil,
                "vacios": vacios,
                "por_tamano": cilindros_por_tamano,
            },
            "exoneraciones": {
                "total_cilindros": exonerados_total,
                "valor_monetario": round(valor_exoneraciones, 2),
            },
            "plantas": datos_plantas,
            "costos": {
                "logistico": round(total_logistico, 2),
                "administrativo": round(total_admin, 2),
            }
        }
    finally:
        db.close()

def generar_respuesta(pregunta_usuario: str):
    datos = get_estadisticas_completas()
    
    mensajes = [
        {
            "role": "system",
            "content": f"""
            Eres el asistente virtual de 'GASGUARIBE'. 
            Aquí tienes los datos actuales del sistema en formato JSON:
            {json.dumps(datos, indent=2, default=str)}
            
            Responde en español, de forma clara y profesional.
            """
        },
        {
            "role": "user",
            "content": pregunta_usuario
        }
    ]

    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=1500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Lo siento, tuve un problema al procesar tu solicitud: {e}"
