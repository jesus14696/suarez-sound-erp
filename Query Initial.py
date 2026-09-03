import io
import json
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="Suárez Sound - CRM & Gestión",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1, h2, h3 { font-family: 'Inter', system-ui, -apple-system, sans-serif; font-weight: 600; color: #f1f5f9; }
    
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-title { font-size: 0.875rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .kpi-value { font-size: 1.875rem; font-weight: 700; color: #f8fafc; }
    .kpi-sub { font-size: 0.75rem; margin-top: 6px; }
    .text-green { color: #34d399; }
    .text-amber { color: #fbbf24; }
    .text-red { color: #f87171; }
    .text-blue { color: #60a5fa; }
    
    div[data-testid="stForm"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================
SUPABASE_URL = "https://igvireifhqgotfrfamvs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlndmlyZWlmaHFnb3RmcmZhbXZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc2ODE3MTcsImV4cCI6MjEwMzI1NzcxN30.UN_KFNPPgrf4TIIcqWHAENaOIFhCCYsWxSnJcngRZ_0"
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")

# Carga inicial de catálogo de productos
def obtener_o_inicializar_productos():
    try:
        res = supabase.table("productos").select("id, nombre, precio").order("id").execute()
        if not res.data:
            prod_iniciales = [
                {"nombre": "Producto 1: 2 Subwoofers", "precio": 150.0},
                {"nombre": "Producto 2: 4 Subwoofers", "precio": 280.0},
                {"nombre": "Producto 3: 6 Subwoofers", "precio": 400.0},
                {"nombre": "Producto 4: 2 Altavoces", "precio": 120.0},
                {"nombre": "Producto 5: 4 Altavoces", "precio": 220.0},
                {"nombre": "Producto 6: 6 Altavoces", "precio": 320.0},
                {"nombre": "Producto 7: Cabina DJ", "precio": 200.0}
            ]
            supabase.table("productos").insert(prod_iniciales).execute()
            res = supabase.table("productos").select("id, nombre, precio").order("id").execute()
        return res.data
    except Exception:
        return []

# ==========================================
# GENERADOR DE PDF (Facturas y Presupuestos)
# ==========================================
class InvoicePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(30, 41, 59)
        self.cell(110, 10, "SUAREZ SOUND", ln=False)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(37, 99, 235)
        self.cell(80, 10, getattr(self, 'doc_title', 'COMPROBANTE'), ln=True, align="R")
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(110, 5, "Servicios Profesionales de Sonido e Iluminacion", ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "Suarez Sound S.L. - Gracias por confiar en nuestros servicios.", align="C")

def generar_pdf_documento(registro_info):
    num_doc = registro_info.get("numero_factura", "DOC-0000")
    es_factura = num_doc.startswith("FAC")
    fecha = str(registro_info.get("fecha_emision", date.today()))
    total = float(registro_info.get("total", 0.0))
    
    cliente_data = registro_info.get("clientes") or {}
    nombre_cliente = cliente_data.get("nombre", "Cliente General")
    nif_cliente = cliente_data.get("nif") or "No especificado"
    email_cliente = cliente_data.get("email") or "No especificado"
    telefono_cliente = cliente_data.get("telefono") or "No especificado"

    pdf = InvoicePDF()
    pdf.doc_title = "FACTURA OFICIAL" if es_factura else "FACTURA PROFORMA"
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(95, 6, "EMISOR:", ln=False)
    pdf.cell(95, 6, "CLIENTE:", ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(95, 5, "Suarez Sound S.L.", ln=False)
    pdf.cell(95, 5, f"{nombre_cliente}", ln=True)
    
    pdf.cell(95, 5, "NIF: B-12345678", ln=False)
    pdf.cell(95, 5, f"DNI/NIF: {nif_cliente}", ln=True)
    
    pdf.cell(95, 5, "info@suarezsound.com", ln=False)
    pdf.cell(95, 5, f"Email: {email_cliente}", ln=True)
    
    pdf.cell(95, 5, "", ln=False)
    pdf.cell(95, 5, f"Tel: {telefono_cliente}", ln=True)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Numero de Documento: {num_doc}   |   Fecha de Emision: {fecha}", ln=True)
    pdf.ln(6)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(140, 8, "Descripcion del Servicio", border=1, fill=True)
    pdf.cell(50, 8, "Importe", border=1, align="R", fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    
    if es_factura:
        base_imponible = total / 1.21
        iva = total - base_imponible
        
        pdf.cell(140, 10, "Servicios tecnicos de sonorizacion, montaje y produccion (Con Factura)", border=1)
        pdf.cell(50, 10, f"{base_imponible:,.2f} EUR", border=1, align="R", ln=True)
        pdf.ln(6)
        
        pdf.cell(120, 6, "", ln=False)
        pdf.cell(35, 6, "Base Imponible:", ln=False)
        pdf.cell(35, 6, f"{base_imponible:,.2f} EUR", align="R", ln=True)
        
        pdf.cell(120, 6, "", ln=False)
        pdf.cell(35, 6, "IVA (21%):", ln=False)
        pdf.cell(35, 6, f"{iva:,.2f} EUR", align="R", ln=True)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(120, 8, "", ln=False)
        pdf.cell(35, 8, "TOTAL FACTURA:", ln=False)
        pdf.cell(35, 8, f"{total:,.2f} EUR", align="R", ln=True)
    else:
        pdf.cell(140, 10, "Servicios tecnicos de sonorizacion y montaje (Factura Proforma / Recibo)", border=1)
        pdf.cell(50, 10, f"{total:,.2f} EUR", border=1, align="R", ln=True)
        pdf.ln(6)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(120, 8, "", ln=False)
        pdf.cell(35, 8, "TOTAL NETO:", ln=False)
        pdf.cell(35, 8, f"{total:,.2f} EUR", align="R", ln=True)
    
    return bytes(pdf.output())

def generar_pdf_presupuesto(cliente_nombre, cliente_nif, items, num_presupuesto, fecha_generacion, validez_dias, notas):
    pdf = InvoicePDF()
    pdf.doc_title = "PRESUPUESTO"
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(95, 6, "EMISOR:", ln=False)
    pdf.cell(95, 6, "CLIENTE:", ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(95, 5, "Suarez Sound S.L.", ln=False)
    pdf.cell(95, 5, f"{cliente_nombre}", ln=True)
    
    pdf.cell(95, 5, "NIF: B-12345678", ln=False)
    pdf.cell(95, 5, f"DNI/NIF: {cliente_nif or 'No especificado'}", ln=True)
    pdf.cell(95, 5, "info@suarezsound.com", ln=True)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    fecha_dt = date.fromisoformat(str(fecha_generacion))
    fecha_validez = fecha_dt + timedelta(days=validez_dias)
    pdf.cell(0, 6, f"Numero Presupuesto: {num_presupuesto}", ln=True)
    pdf.cell(0, 6, f"Fecha de Generacion: {fecha_dt.strftime('%d/%m/%Y')}   |   Valido hasta: {fecha_validez.strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(6)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(95, 8, "Producto / Equipamiento", border=1, fill=True)
    pdf.cell(25, 8, "Cant.", border=1, align="C", fill=True)
    pdf.cell(35, 8, "Precio Un.", border=1, align="R", fill=True)
    pdf.cell(35, 8, "Total", border=1, align="R", fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    total_presupuesto = 0.0
    for item in items:
        prod = item["producto"]
        cant = item["cantidad"]
        pu = float(item["precio_unitario"])
        subtotal = cant * pu
        total_presupuesto += subtotal
        
        pdf.cell(95, 8, prod, border=1)
        pdf.cell(25, 8, str(cant), border=1, align="C")
        pdf.cell(35, 8, f"{pu:,.2f} EUR", border=1, align="R")
        pdf.cell(35, 8, f"{subtotal:,.2f} EUR", border=1, align="R", ln=True)
        
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 8, "", ln=False)
    pdf.cell(35, 8, "TOTAL ESTIMADO:", ln=False)
    pdf.cell(35, 8, f"{total_presupuesto:,.2f} EUR", align="R", ln=True)
    
    if notas:
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "Notas y Condiciones:", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4, notas)

    return bytes(pdf.output())

# ==========================================
# NAVEGACIÓN LATERAL
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #818cf8;'>🔊 Suárez Sound</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menú Principal", 
    ["📊 Dashboard KPI", "📈 Analítica y Gráficas", "📋 Presupuestos", "👤 CRM Clientes", "➕ Registros / Facturas", "📄 Historial Trabajos", "💸 Gastos"]
)

if "items_presupuesto" not in st.session_state:
    st.session_state.items_presupuesto = []

# ==========================================
# SECCIÓN: DASHBOARD KPI
# ==========================================
if menu == "📊 Dashboard KPI":
    st.title("📊 Dashboard General")
    st.markdown("Visión global del rendimiento financiero de **Suárez Sound**.")
    st.markdown("---")
    
    try:
        res_facturas = supabase.table("facturas").select("total, estado, fecha_emision").execute()
        res_gastos = supabase.table("gastos").select("total, fecha").execute()
        
        df_fac = pd.DataFrame(res_facturas.data) if res_facturas.data else pd.DataFrame(columns=["total", "estado", "fecha_emision"])
        df_gas = pd.DataFrame(res_gastos.data) if res_gastos.data else pd.DataFrame(columns=["total", "fecha"])
        
        total_facturado = df_fac["total"].sum() if not df_fac.empty else 0.0
        total_cobrado = df_fac[df_fac["estado"] == "Cobrada"]["total"].sum() if not df_fac.empty else 0.0
        total_pendiente = df_fac[df_fac["estado"] == "Pendiente"]["total"].sum() if not df_fac.empty else 0.0
        total_gastos = df_gas["total"].sum() if not df_gas.empty else 0.0
        beneficio_real = total_cobrado - total_gastos

        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Ingresos Totales</div>
                <div class="kpi-value">{total_facturado:,.2f} €</div>
                <div class="kpi-sub text-blue">Bruto Generado</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Cobrado</div>
                <div class="kpi-value text-green">{total_cobrado:,.2f} €</div>
                <div class="kpi-sub text-green">Liquidez Real</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Pendiente Cobro</div>
                <div class="kpi-value text-amber">{total_pendiente:,.2f} €</div>
                <div class="kpi-sub text-amber">Por Cobrar</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Gastos Totales</div>
                <div class="kpi-value text-red">{total_gastos:,.2f} €</div>
                <div class="kpi-sub text-red">Salidas Caja</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            color_class = "text-green" if beneficio_real >= 0 else "text-red"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Beneficio Neto</div>
                <div class="kpi-value {color_class}">{beneficio_real:,.2f} €</div>
                <div class="kpi-sub">Cobrado - Gastos</div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as err:
        st.error(f"Error al cargar datos del Dashboard: {err}")

# ==========================================
# SECCIÓN: ANALÍTICA Y GRÁFICAS AVANZADAS
# ==========================================
elif menu == "📈 Analítica y Gráficas":
    st.title("📈 Analítica Visual y Rendimiento")
    st.markdown("Análisis detallado sobre tendencias de facturación, estado de cobros y principales clientes.")
    st.markdown("---")
    
    try:
        res_fac = supabase.table("facturas").select("numero_factura, fecha_emision, total, estado, clientes(nombre)").execute()
        res_gas = supabase.table("gastos").select("fecha, total").execute()
        
        if res_fac.data or res_gas.data:
            if res_fac.data:
                raw_fac = res_fac.data
                fac_list = []
                for item in raw_fac:
                    tipo = "Factura Oficial" if item["numero_factura"].startswith("FAC") else "Proforma / Recibo"
                    cliente = item["clientes"]["nombre"] if item.get("clientes") else "Sin Cliente"
                    fac_list.append({
                        "numero": item["numero_factura"],
                        "fecha": pd.to_datetime(item["fecha_emision"]),
                        "mes_año": pd.to_datetime(item["fecha_emision"]).strftime('%Y-%m'),
                        "total": float(item["total"]),
                        "estado": item["estado"],
                        "tipo": tipo,
                        "cliente": cliente
                    })
                df_fac = pd.DataFrame(fac_list)
            else:
                df_fac = pd.DataFrame()

            if res_gas.data:
                raw_gas = res_gas.data
                gas_list = [{
                    "fecha": pd.to_datetime(g["fecha"]),
                    "mes_año": pd.to_datetime(g["fecha"]).strftime('%Y-%m'),
                    "total": float(g["total"])
                } for g in raw_gas]
                df_gas = pd.DataFrame(gas_list)
            else:
                df_gas = pd.DataFrame()

            st.subheader("📅 Evolución Mensual: Ingresos vs Gastos")
            if not df_fac.empty or not df_gas.empty:
                df_fac_mensual = df_fac.groupby("mes_año")["total"].sum().reset_index(name="Ingresos") if not df_fac.empty else pd.DataFrame(columns=["mes_año", "Ingresos"])
                df_gas_mensual = df_gas.groupby("mes_año")["total"].sum().reset_index(name="Gastos") if not df_gas.empty else pd.DataFrame(columns=["mes_año", "Gastos"])
                
                df_mensual = pd.merge(df_fac_mensual, df_gas_mensual, on="mes_año", how="outer").fillna(0).sort_values("mes_año")
                df_mensual = df_mensual.set_index("mes_año")
                st.line_chart(df_mensual)
            else:
                st.info("Insuficientes datos para la gráfica temporal.")

            st.markdown("---")
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.subheader("💳 Estado de Cobros")
                if not df_fac.empty:
                    df_estado = df_fac.groupby("estado")["total"].sum()
                    st.bar_chart(df_estado)

            with col_g2:
                st.subheader("📄 Distribución: Factura vs Proforma")
                if not df_fac.empty:
                    df_tipo = df_fac.groupby("tipo")["total"].sum()
                    st.bar_chart(df_tipo)

            st.markdown("---")
            st.subheader("🏆 Top Clientes por Volumen de Ingresos")
            if not df_fac.empty:
                df_top_clientes = df_fac.groupby("cliente")["total"].sum().sort_values(ascending=False).head(10)
                st.bar_chart(df_top_clientes)

        else:
            st.info("Aún no existen suficientes datos de facturas o gastos registrados para generar las gráficas.")

    except Exception as err:
        st.error(f"Error procesando la analítica: {err}")

# ==========================================
# SECCIÓN: PRESUPUESTOS (NUEVO & MEJORADO)
# ==========================================
elif menu == "📋 Presupuestos":
    st.title("📋 Módulo de Presupuestos y Catálogo")
    st.markdown("Genera presupuestos con la fecha de emisión e independízate agregando nuevos productos al catálogo.")
    st.markdown("---")

    tab_crear, tab_catalogo, tab_historial = st.tabs(["⚡ Crear Presupuesto", "📦 Gestión de Productos / Catálogo", "📄 Historial Presupuestos"])

    # 1. GENERAR PRESUPUESTO
    with tab_crear:
        try:
            res_clientes = supabase.table("clientes").select("id, nombre, nif").order("nombre").execute()
            clientes = res_clientes.data
            
            lista_productos_db = obtener_o_inicializar_productos()
            dict_productos = {p["nombre"]: float(p["precio"]) for p in lista_productos_db}

            if not clientes:
                st.warning("⚠️ Primero debes dar de alta al menos un cliente en 'CRM Clientes'.")
            elif not dict_productos:
                st.warning("⚠️ No hay productos disponibles en el catálogo.")
            else:
                dict_clientes = {c["nombre"]: c for c in clientes}

                col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                with col_p1:
                    cliente_sel = st.selectbox("Cliente Destinatario *", list(dict_clientes.keys()))
                with col_p2:
                    fecha_pres = st.date_input("Fecha de Generación", value=date.today())
                with col_p3:
                    validez = st.number_input("Validez (Días)", min_value=1, value=15)

                st.markdown("---")
                st.subheader("🛠️ Seleccionar Equipamientos / Productos")

                col_i1, col_i2, col_i3, col_i4 = st.columns([3, 1, 1.5, 1])
                with col_i1:
                    prod_sel = st.selectbox("Seleccionar Producto", list(dict_productos.keys()))
                with col_i2:
                    cant_prod = st.number_input("Cantidad", min_value=1, value=1)
                with col_i3:
                    precio_def = dict_productos.get(prod_sel, 0.0)
                    precio_unitario = st.number_input("Precio Unitario (€)", min_value=0.0, value=precio_def, step=10.0, format="%.2f")
                with col_i4:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("➕ Añadir", use_container_width=True):
                        st.session_state.items_presupuesto.append({
                            "producto": prod_sel,
                            "cantidad": cant_prod,
                            "precio_unitario": precio_unitario,
                            "subtotal": cant_prod * precio_unitario
                        })
                        st.rerun()

                if st.session_state.items_presupuesto:
                    st.markdown("#### Lista de Ítems del Presupuesto")
                    df_pres = pd.DataFrame(st.session_state.items_presupuesto)
                    st.dataframe(df_pres, use_container_width=True)

                    total_presupuesto = df_pres["subtotal"].sum()
                    st.success(f"💰 **Total Presupuesto:** `{total_presupuesto:,.2f} €`")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        notas = st.text_area("Notas o Condiciones del Presupuesto", "Ejemplo: Transporte e instalación incluidos. Validez 15 días.")
                    with col_b2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Limpiar Ítems", use_container_width=True):
                            st.session_state.items_presupuesto = []
                            st.rerun()

                        cliente_info = dict_clientes[cliente_sel]
                        num_pres_code = f"PRES-{date.today().strftime('%Y%m%d')}-{cliente_info['id']}"

                        pdf_bytes = generar_pdf_presupuesto(
                            cliente_nombre=cliente_info["nombre"],
                            cliente_nif=cliente_info["nif"],
                            items=st.session_state.items_presupuesto,
                            num_presupuesto=num_pres_code,
                            fecha_generacion=fecha_pres,
                            validez_dias=validez,
                            notas=notas
                        )

                        if st.button("💾 Guardar en Sistema y Preparar PDF", use_container_width=True):
                            try:
                                data_pres = {
                                    "numero_presupuesto": num_pres_code,
                                    "cliente_id": cliente_info["id"],
                                    "fecha_emision": str(fecha_pres),
                                    "validez_dias": validez,
                                    "items": st.session_state.items_presupuesto,
                                    "total": total_presupuesto,
                                    "notas": notas
                                }
                                supabase.table("presupuestos").insert(data_pres).execute()
                                st.success("¡Presupuesto guardado con éxito!")
                            except Exception as ex:
                                st.warning(f"Aviso al guardar en BD: {ex}")

                        st.download_button(
                            label="📄 Descargar Presupuesto en PDF",
                            data=pdf_bytes,
                            file_name=f"{num_pres_code}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.info("Añade productos de la lista superior para construir el presupuesto.")

        except Exception as err:
            st.error(f"Error generando presupuesto: {err}")

    # 2. GESTIÓN DEL CATÁLOGO
    with tab_catalogo:
        st.subheader("➕ Añadir Nuevo Producto / Servicio al Catálogo")
        with st.form("nuevo_producto_form", clear_on_submit=True):
            col_np1, col_np2 = st.columns([3, 1])
            with col_np1:
                nuevo_prod_nombre = st.text_input("Nombre / Descripción del Producto *")
            with col_np2:
                nuevo_prod_precio = st.number_input("Precio Estándar (€)", min_value=0.0, step=10.0, format="%.2f")
            
            sub_prod = st.form_submit_button("Guardar en Catálogo")
            if sub_prod:
                if not nuevo_prod_nombre:
                    st.error("El nombre del producto no puede estar vacío.")
                else:
                    try:
                        supabase.table("productos").insert({"nombre": nuevo_prod_nombre, "precio": nuevo_prod_precio}).execute()
                        st.success(f"Producto '{nuevo_prod_nombre}' añadido con éxito al catálogo.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al guardar producto: {ex}")

        st.markdown("---")
        st.subheader("📦 Productos Actualmente Registrados")
        prods_db = obtener_o_inicializar_productos()
        if prods_db:
            df_prods = pd.DataFrame(prods_db)
            st.dataframe(df_prods[["id", "nombre", "precio"]], use_container_width=True)
            
            st.markdown("##### 🗑️ Eliminar Producto")
            prod_a_eliminar = st.selectbox("Seleccionar producto a eliminar", [p["nombre"] for p in prods_db])
            if st.button("Eliminar del Catálogo"):
                p_obj = next((p for p in prods_db if p["nombre"] == prod_a_eliminar), None)
                if p_obj:
                    supabase.table("productos").delete().eq("id", p_obj["id"]).execute()
                    st.success("Producto eliminado.")
                    st.rerun()
        else:
            st.info("No hay productos en el catálogo.")

    # 3. HISTORIAL DE PRESUPUESTOS
    with tab_historial:
        st.subheader("📄 Historial de Presupuestos Generados")
        try:
            res_p = supabase.table("presupuestos").select("id, numero_presupuesto, fecha_emision, total, validez_dias, notas, items, clientes(nombre, nif)").order("id", desc=True).execute()
            if res_p.data:
                raw_p = res_p.data
                filas_p = []
                for p in raw_p:
                    cliente_n = p["clientes"]["nombre"] if p.get("clientes") else "Sin Cliente"
                    filas_p.append({
                        "Código": p["numero_presupuesto"],
                        "Cliente": cliente_n,
                        "Fecha Generación": p["fecha_emision"],
                        "Total (€)": p["total"]
                    })
                st.dataframe(pd.DataFrame(filas_p), use_container_width=True)
                
                pres_sel_code = st.selectbox("Seleccionar Presupuesto para Re-descargar PDF", [p["numero_presupuesto"] for p in raw_p])
                p_selected = next((p for p in raw_p if p["numero_presupuesto"] == pres_sel_code), None)
                
                if p_selected:
                    cli_data = p_selected.get("clientes") or {}
                    pdf_h = generar_pdf_presupuesto(
                        cliente_nombre=cli_data.get("nombre", "Cliente General"),
                        cliente_nif=cli_data.get("nif", ""),
                        items=p_selected["items"],
                        num_presupuesto=p_selected["numero_presupuesto"],
                        fecha_generacion=p_selected["fecha_emision"],
                        validez_dias=p_selected["validez_dias"],
                        notas=p_selected.get("notas", "")
                    )
                    st.download_button(
                        label=f"📥 Re-descargar {pres_sel_code}.pdf",
                        data=pdf_h,
                        file_name=f"{pres_sel_code}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.info("Aún no se han guardado presupuestos en el historial.")
        except Exception as err:
            st.error(f"Error consultando historial: {err}")

# ==========================================
# SECCIÓN: CRM CLIENTES
# ==========================================
elif menu == "👤 CRM Clientes":
    st.title("👤 CRM - Gestión de Clientes")
    st.markdown("Gestión ágil de la cartera de clientes. **DNI/NIF opcional.**")
    st.markdown("---")
    
    with st.form("nuevo_cliente", clear_on_submit=True):
        st.subheader("➕ Alta Rápida de Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nombre = st.text_input("Nombre / Empresa *")
            telefono = st.text_input("Móvil / Teléfono")
        with col_c2:
            email = st.text_input("Gmail / Email")
            nif = st.text_input("DNI / NIF (Opcional)")
            
        submit = st.form_submit_button("Guardar en CRM", use_container_width=True)
        
        if submit:
            if not nombre:
                st.error("El nombre del cliente es obligatorio.")
            else:
                data = {
                    "nombre": nombre,
                    "telefono": telefono if telefono else None,
                    "email": email if email else None,
                    "nif": nif if nif else None
                }
                supabase.table("clientes").insert(data).execute()
                st.success(f"Cliente '{nombre}' guardado correctamente.")
                st.rerun()

    st.subheader("📋 Lista de Contactos")
    try:
        response = supabase.table("clientes").select("id, nombre, telefono, email, nif").order("id", desc=True).execute()
        if response.data:
            df_clientes = pd.DataFrame(response.data)
            df_clientes["nif"] = df_clientes["nif"].fillna("Sin DNI")
            st.dataframe(df_clientes[["nombre", "telefono", "email", "nif"]], use_container_width=True)
        else:
            st.info("No hay clientes registrados.")
    except Exception as err:
        st.error(f"Error cargando clientes: {err}")

# ==========================================
# SECCIÓN: REGISTRAR TRABAJO / FACTURA
# ==========================================
elif menu == "➕ Registros / Facturas":
    st.title("➕ Crear Registro de Servicio / Factura")
    st.markdown("Registra un trabajo para un cliente calculando IVA solo cuando se requiera factura oficial.")
    st.markdown("---")
    
    try:
        res_clientes = supabase.table("clientes").select("id, nombre").order("nombre").execute()
        clientes = res_clientes.data
        
        if not clientes:
            st.warning("⚠️ Primero debes dar de alta al menos un cliente en 'CRM Clientes'.")
        else:
            dict_clientes = {c["nombre"]: c["id"] for c in clientes}
            
            res_facturas = supabase.table("facturas").select("numero_factura").order("id", desc=True).limit(1).execute()
            if res_facturas.data:
                last_code = res_facturas.data[0]["numero_factura"]
                try:
                    num_seq = int(last_code.split("-")[1]) + 1
                    siguiente_num = f"{num_seq:04d}"
                except Exception:
                    siguiente_num = "0001"
            else:
                siguiente_num = "0001"

            col_a, col_b = st.columns(2)
            with col_a:
                cliente_sel = st.selectbox("Seleccionar Cliente *", list(dict_clientes.keys()))
                quiere_factura = st.radio("¿Requiere Factura Oficial?", ["No (Proforma / Recibo sin IVA)", "Sí (Factura Oficial + 21% IVA)"])
                fecha_emision = st.date_input("Fecha de Emisión", value=date.today())
                
            with col_b:
                importe_base = st.number_input("Importe Base del Servicio (€) *", min_value=0.0, step=10.0, format="%.2f")
                estado_inicial = st.selectbox("Estado del Cobro", ["Pendiente", "Cobrada"])
                
                if "Sí" in quiere_factura:
                    num_final = f"FAC-{siguiente_num}"
                    iva_calculado = importe_base * 0.21
                    total_calculado = importe_base + iva_calculado
                    st.info(f"💡 **Base:** {importe_base:,.2f} € | **IVA (21%):** {iva_calculado:,.2f} € | **Total Factura:** {total_calculado:,.2f} €")
                else:
                    num_final = f"REC-{siguiente_num}"
                    total_calculado = importe_base
                    st.success(f"💡 **Total Neto Proforma:** {total_calculado:,.2f} € (Sin IVA)")

            if st.button("🚀 Guardar Registro", use_container_width=True):
                if importe_base <= 0:
                    st.error("Introduce un importe válido mayor que 0.")
                else:
                    cliente_id = dict_clientes[cliente_sel]
                    data_factura = {
                        "numero_factura": num_final,
                        "cliente_id": cliente_id,
                        "fecha_emision": str(fecha_emision),
                        "total": total_calculado,
                        "estado": estado_inicial
                    }
                    supabase.table("facturas").insert(data_factura).execute()
                    st.success(f"Registro '{num_final}' guardado con éxito por un total de {total_calculado:,.2f} €.")
                    st.rerun()

    except Exception as err:
        st.error(f"Error cargando el formulario: {err}")

# ==========================================
# SECCIÓN: HISTORIAL DE TRABAJOS / FACTURAS
# ==========================================
elif menu == "📄 Historial Trabajos":
    st.title("📄 Historial General de Servicios, Proformas y Facturas")
    st.markdown("Consulta registros y descarga documentos PDF.")
    st.markdown("---")
    
    try:
        res = supabase.table("facturas").select("id, numero_factura, fecha_emision, total, estado, clientes(nombre, nif, email, telefono)").order("id", desc=True).execute()
        
        if res.data:
            raw_facturas = res.data
            filas = []
            for item in raw_facturas:
                es_fac = "Factura Oficial" if item["numero_factura"].startswith("FAC") else "Proforma / Recibo"
                filas.append({
                    "ID": item["id"],
                    "Código": item["numero_factura"],
                    "Tipo Documento": es_fac,
                    "Cliente": item["clientes"]["nombre"] if item.get("clientes") else "Sin Cliente",
                    "Fecha": item["fecha_emision"],
                    "Total (€)": item["total"],
                    "Estado": item["estado"]
                })
            
            df_all = pd.DataFrame(filas)
            
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                filtro_estado = st.selectbox("Filtrar por Estado", ["Todas", "Pendiente", "Cobrada"])
            with col_f2:
                busqueda = st.text_input("🔍 Buscar por Cliente o Código", "")

            df_filtered = df_all.copy()
            if filtro_estado != "Todas":
                df_filtered = df_filtered[df_filtered["Estado"] == filtro_estado]
            if busqueda:
                df_filtered = df_filtered[
                    df_filtered["Cliente"].str.contains(busqueda, case=False, na=False) |
                    df_filtered["Código"].str.contains(busqueda, case=False, na=False)
                ]

            st.dataframe(
                df_filtered[["Código", "Tipo Documento", "Cliente", "Fecha", "Total (€)", "Estado"]], 
                use_container_width=True,
                height=300
            )
            
            st.markdown(f"**Total acumulado en selección:** `{df_filtered['Total (€)'].sum():,.2f} €`")
            st.markdown("---")
            
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                st.subheader("⚡ Estado de Pago")
                factura_sel_estado = st.selectbox("Seleccionar Registro", df_all["Código"].tolist(), key="sel_est")
                nuevo_estado = st.selectbox("Nuevo Estado", ["Cobrada", "Pendiente"])
                if st.button("Actualizar Estado", use_container_width=True):
                    supabase.table("facturas").update({"estado": nuevo_estado}).eq("numero_factura", factura_sel_estado).execute()
                    st.success(f"Registro {factura_sel_estado} actualizado a '{nuevo_estado}'.")
                    st.rerun()

            with col_m2:
                st.subheader("📥 Generar Documento PDF")
                factura_sel_pdf = st.selectbox("Seleccionar para Descargar PDF", df_all["Código"].tolist(), key="sel_pdf")
                
                factura_obj = next((f for f in raw_facturas if f["numero_factura"] == factura_sel_pdf), None)
                
                if factura_obj:
                    pdf_data = generar_pdf_documento(factura_obj)
                    st.download_button(
                        label=f"📄 Descargar {factura_sel_pdf}.pdf",
                        data=pdf_data,
                        file_name=f"{factura_sel_pdf}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.info("No hay registros todavía.")
    except Exception as err:
        st.error(f"Error consultando el historial: {err}")

# ==========================================
# SECCIÓN: GASTOS
# ==========================================
elif menu == "💸 Gastos":
    st.title("💸 Control de Gastos")
    st.markdown("Registra las salidas de dinero para calcular el Beneficio Neto.")
    st.markdown("---")
    
    with st.form("nuevo_gasto", clear_on_submit=True):
        st.subheader("➕ Registrar Nuevo Gasto")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            concepto = st.text_input("Concepto / Detalle *")
            proveedor = st.text_input("Proveedor (Opcional)")
        with col_g2:
            fecha = st.date_input("Fecha Gasto", value=date.today())
            total = st.number_input("Total (€) *", min_value=0.0, step=5.0, format="%.2f")
            
        submit = st.form_submit_button("Guardar Gasto", use_container_width=True)
        
        if submit:
            if not concepto:
                st.error("El concepto del gasto es obligatorio.")
            else:
                data_gasto = {
                    "concepto": concepto,
                    "proveedor": proveedor if proveedor else None,
                    "fecha": str(fecha),
                    "total": total
                }
                supabase.table("gastos").insert(data_gasto).execute()
                st.success("Gasto guardado correctamente.")
                st.rerun()

    st.subheader("📋 Historial de Gastos")
    try:
        res_gastos = supabase.table("gastos").select("id, concepto, proveedor, fecha, total").order("id", desc=True).execute()
        if res_gastos.data:
            df_gastos = pd.DataFrame(res_gastos.data)
            st.dataframe(df_gastos[["concepto", "proveedor", "fecha", "total"]], use_container_width=True)
        else:
            st.info("No hay gastos registrados.")
    except Exception as err:
        st.error(f"Error cargando gastos: {err}")
