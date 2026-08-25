import io
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="Suárez Sound - ERP & Dashboard",
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
# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================
SUPABASE_URL = "https://igvireifhqgotfrfamvs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlndmlyZWlmaHFnb3RmcmZhbXZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc2ODE3MTcsImV4cCI6MjEwMzI1NzcxN30.UN_KFNPPgrf4TIIcqWHAENaOIFhCCYsWxSnJcngRZ_0"

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# CLASE NATIVA GENERADORA DE PDF (FPDF2)
# ==========================================
class InvoicePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(30, 41, 59)
        self.cell(120, 10, "SUAREZ SOUND", ln=False)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(37, 99, 235)
        self.cell(70, 10, "FACTURA", ln=True, align="R")
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(120, 5, "Servicios Profesionales de Sonido e Iluminacion", ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "Suarez Sound S.L. - Gracias por confiar en nuestros servicios.", align="C")

def generar_pdf_factura(factura_info):
    num_factura = factura_info.get("numero_factura", "FAC-0000")
    fecha = str(factura_info.get("fecha_emision", date.today()))
    total = float(factura_info.get("total", 0.0))
    base_imponible = total / 1.21
    iva = total - base_imponible
    
    cliente_data = factura_info.get("clientes") or {}
    nombre_cliente = cliente_data.get("nombre", "Cliente General")
    nif_cliente = cliente_data.get("nif", "N/A")
    email_cliente = cliente_data.get("email", "N/A")
    telefono_cliente = cliente_data.get("telefono", "N/A")

    pdf = InvoicePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Bloque Datos Emisor / Cliente
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(95, 6, "EMISOR:", ln=False)
    pdf.cell(95, 6, "CLIENTE:", ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(95, 5, "Suarez Sound S.L.", ln=False)
    pdf.cell(95, 5, f"{nombre_cliente}", ln=True)
    
    pdf.cell(95, 5, "NIF: B-12345678", ln=False)
    pdf.cell(95, 5, f"NIF/CIF: {nif_cliente}", ln=True)
    
    pdf.cell(95, 5, "info@suarezsound.com", ln=False)
    pdf.cell(95, 5, f"Email: {email_cliente}", ln=True)
    
    pdf.cell(95, 5, "", ln=False)
    pdf.cell(95, 5, f"Tel: {telefono_cliente}", ln=True)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Numero de Factura: {num_factura}   |   Fecha de Emision: {fecha}", ln=True)
    pdf.ln(6)
    
    # Tabla de Productos / Servicios
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(140, 8, "Descripcion del Servicio", border=1, fill=True)
    pdf.cell(50, 8, "Importe", border=1, align="R", fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(140, 10, "Servicios tecnicos de sonorizacion, montaje y produccion de eventos", border=1)
    pdf.cell(50, 10, f"{base_imponible:,.2f} EUR", border=1, align="R", ln=True)
    
    pdf.ln(6)
    
    # Cuadro de Totales
    pdf.cell(120, 6, "", ln=False)
    pdf.cell(35, 6, "Base Imponible:", ln=False)
    pdf.cell(35, 6, f"{base_imponible:,.2f} EUR", align="R", ln=True)
    
    pdf.cell(120, 6, "", ln=False)
    pdf.cell(35, 6, "IVA (21%):", ln=False)
    pdf.cell(35, 6, f"{iva:,.2f} EUR", align="R", ln=True)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 8, "", ln=False)
    pdf.cell(35, 8, "TOTAL:", ln=False)
    pdf.cell(35, 8, f"{total:,.2f} EUR", align="R", ln=True)
    
    return bytes(pdf.output())

# ==========================================
# NAVEGACIÓN LATERAL
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #818cf8;'>🔊 Suárez Sound</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menú Principal", 
    ["📊 Dashboard", "📄 Historial Facturas", "➕ Nueva Factura", "👤 Clientes", "💸 Gastos"]
)

# ==========================================
# SECCIÓN: DASHBOARD ANALÍTICO
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Dashboard General")
    st.markdown("Visión global del rendimiento financiero de **Suárez Sound**.")
    st.markdown("---")
    
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
            <div class="kpi-title">Total Facturado</div>
            <div class="kpi-value">{total_facturado:,.2f} €</div>
            <div class="kpi-sub text-blue">Bruto emitido</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Cobrado</div>
            <div class="kpi-value text-green">{total_cobrado:,.2f} €</div>
            <div class="kpi-sub text-green">Liquidez real</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Pendiente Cobro</div>
            <div class="kpi-value text-amber">{total_pendiente:,.2f} €</div>
            <div class="kpi-sub text-amber">Por cobrar</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Gastos Totales</div>
            <div class="kpi-value text-red">{total_gastos:,.2f} €</div>
            <div class="kpi-sub text-red">Salidas caja</div>
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

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns([2, 1])
    with col_chart1:
        st.subheader("📈 Distribución de Facturación")
        if not df_fac.empty:
            estado_counts = df_fac.groupby("estado")["total"].sum().reset_index()
            st.bar_chart(estado_counts.set_index("estado"), y="total", color="#818cf8")
        else:
            st.info("No hay suficiente información.")
            
    with col_chart2:
        st.subheader("📌 Estado de Cobros")
        if not df_fac.empty:
            cantidades = df_fac["estado"].value_counts()
            st.dataframe(cantidades, use_container_width=True)
        else:
            st.info("Sin registros.")

# ==========================================
# SECCIÓN: HISTORIAL DE FACTURAS + DESCARGA PDF
# ==========================================
elif menu == "📄 Historial Facturas":
    st.title("📄 Historial General de Facturas")
    st.markdown("Consulta facturas, cambia su estado o descarga la factura oficial en PDF.")
    st.markdown("---")
    
    res = supabase.table("facturas").select("id, numero_factura, fecha_emision, total, estado, clientes(nombre, nif, email, telefono)").order("id", desc=True).execute()
    
    if res.data:
        raw_facturas = res.data
        filas = []
        for item in raw_facturas:
            filas.append({
                "ID": item["id"],
                "Nº Factura": item["numero_factura"],
                "Cliente": item["clientes"]["nombre"] if item.get("clientes") else "Sin Cliente",
                "Fecha Emisión": item["fecha_emision"],
                "Total (€)": item["total"],
                "Estado": item["estado"]
            })
        
        df_all = pd.DataFrame(filas)
        
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            filtro_estado = st.selectbox("Filtrar por Estado", ["Todas", "Pendiente", "Cobrada"])
        with col_f2:
            busqueda = st.text_input("🔍 Buscar por Cliente o Nº Factura", "")

        df_filtered = df_all.copy()
        if filtro_estado != "Todas":
            df_filtered = df_filtered[df_filtered["Estado"] == filtro_estado]
        if busqueda:
            df_filtered = df_filtered[
                df_filtered["Cliente"].str.contains(busqueda, case=False, na=False) |
                df_filtered["Nº Factura"].str.contains(busqueda, case=False, na=False)
            ]

        st.dataframe(
            df_filtered[["Nº Factura", "Cliente", "Fecha Emisión", "Total (€)", "Estado"]], 
            use_container_width=True,
            height=300
        )
        
        st.markdown(f"**Total acumulado en la selección:** `{df_filtered['Total (€)'].sum():,.2f} €`")
        st.markdown("---")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.subheader("⚡ Cambiar Estado")
            factura_sel_estado = st.selectbox("Factura para actualizar estado", df_all["Nº Factura"].tolist(), key="sel_est")
            nuevo_estado = st.selectbox("Nuevo Estado", ["Cobrada", "Pendiente"])
            if st.button("Actualizar Estado", use_container_width=True):
                supabase.table("facturas").update({"estado": nuevo_estado}).eq("numero_factura", factura_sel_estado).execute()
                st.success(f"Factura {factura_sel_estado} actualizada a '{nuevo_estado}'.")
                st.rerun()

        with col_m2:
            st.subheader("📥 Generar & Descargar PDF")
            factura_sel_pdf = st.selectbox("Seleccionar Factura para PDF", df_all["Nº Factura"].tolist(), key="sel_pdf")
            
            factura_obj = next((f for f in raw_facturas if f["numero_factura"] == factura_sel_pdf), None)
            
            if factura_obj:
                pdf_data = generar_pdf_factura(factura_obj)
                st.download_button(
                    label=f"📄 Descargar {factura_sel_pdf}.pdf",
                    data=pdf_data,
                    file_name=f"Factura_{factura_sel_pdf}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info("No hay facturas registradas todavía.")

# ==========================================
# SECCIÓN: NUEVA FACTURA
# ==========================================
elif menu == "➕ Nueva Factura":
    st.title("➕ Crear Nueva Factura")
    st.markdown("Genera una nueva factura correlativa asociada a un cliente.")
    st.markdown("---")
    
    res_clientes = supabase.table("clientes").select("id, nombre").order("nombre").execute()
    clientes = res_clientes.data
    
    if not clientes:
        st.warning("⚠️ Primero debes dar de alta un cliente en la sección 'Clientes'.")
    else:
        dict_clientes = {c["nombre"]: c["id"] for c in clientes}
        
        res_facturas = supabase.table("facturas").select("numero_factura").order("id", desc=True).limit(1).execute()
        if res_facturas.data:
            last_code = res_facturas.data[0]["numero_factura"]
            try:
                num_seq = int(last_code.split("-")[1]) + 1
                siguiente_num = f"FAC-{num_seq:04d}"
            except Exception:
                siguiente_num = "FAC-0001"
        else:
            siguiente_num = "FAC-0001"

        with st.form("nueva_factura", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.text_input("Número de Factura", value=siguiente_num, disabled=True)
                cliente_sel = st.selectbox("Cliente *", list(dict_clientes.keys()))
            with col_b:
                fecha_emision = st.date_input("Fecha de Emisión", value=date.today())
                total = st.number_input("Total Factura (€) *", min_value=0.0, step=10.0, format="%.2f")
                
            submit = st.form_submit_button("🚀 Emitir Factura", use_container_width=True)

            if submit:
                cliente_id = dict_clientes[cliente_sel]
                data_factura = {
                    "numero_factura": siguiente_num,
                    "cliente_id": cliente_id,
                    "fecha_emision": str(fecha_emision),
                    "total": total,
                    "estado": "Pendiente"
                }
                supabase.table("facturas").insert(data_factura).execute()
                st.success(f"Factura {siguiente_num} registrada correctamente.")
                st.rerun()

# ==========================================
# SECCIÓN: CLIENTES
# ==========================================
elif menu == "👤 Clientes":
    st.title("👤 Gestión de Clientes")
    st.markdown("Añade y consulta la base de datos de tus clientes.")
    st.markdown("---")
    
    with st.form("nuevo_cliente", clear_on_submit=True):
        st.subheader("➕ Añadir Nuevo Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nombre = st.text_input("Nombre / Empresa *")
            nif = st.text_input("NIF / CIF")
        with col_c2:
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            
        submit = st.form_submit_button("Guardar Cliente", use_container_width=True)
        
        if submit:
            if not nombre:
                st.error("El nombre del cliente es obligatorio.")
            else:
                data = {
                    "nombre": nombre,
                    "nif": nif if nif else None,
                    "email": email if email else None,
                    "telefono": telefono if telefono else None
                }
                supabase.table("clientes").insert(data).execute()
                st.success(f"Cliente '{nombre}' guardado correctamente.")
                st.rerun()

    st.subheader("📋 Listado de Clientes")
    response = supabase.table("clientes").select("id, nombre, nif, email, telefono").order("id", desc=True).execute()
    if response.data:
        df_clientes = pd.DataFrame(response.data)
        st.dataframe(df_clientes[["nombre", "nif", "email", "telefono"]], use_container_width=True)
    else:
        st.info("No hay clientes registrados.")

# ==========================================
# SECCIÓN: GASTOS
# ==========================================
elif menu == "💸 Gastos":
    st.title("💸 Registro de Gastos")
    st.markdown("Controla los costes operativos de Suárez Sound.")
    st.markdown("---")
    
    with st.form("nuevo_gasto", clear_on_submit=True):
        st.subheader("➕ Registrar Nuevo Gasto")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            concepto = st.text_input("Concepto / Descripción *")
            proveedor = st.text_input("Proveedor")
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
    res_gastos = supabase.table("gastos").select("id, concepto, proveedor, fecha, total").order("id", desc=True).execute()
    if res_gastos.data:
        df_gastos = pd.DataFrame(res_gastos.data)
        st.dataframe(df_gastos[["concepto", "proveedor", "fecha", "total"]], use_container_width=True)
    else:
        st.info("No hay gastos registrados.")