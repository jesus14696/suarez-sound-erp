import streamlit as st
import pandas as pd
from datetime import date
import io
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Suárez Sound - Panel de Control",
    page_icon="🔊",
    layout="wide"
)

# Estilos visuales personalizados (CSS)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 2.5em;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACIÓN DE SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# PERFILES DE EMISORES (AMIGO vs PADRE)
# ==========================================
EMISOR_AMIGO = {
    "nombre": "SUÁREZ SOUND (Amigo)",
    "nif": "00000000X",
    "email": "contacto@suarezsound.com",
    "direccion": "Dirección Comercial / Local",
    "actividad": "Sonorización y Proformas"
}

EMISOR_PADRE = {
    "nombre": "EMISOR FISCAL (Padre)",
    "nif": "11111111Y",
    "email": "facturacion@suarezsound.com",
    "direccion": "Dirección Fiscal Oficial",
    "actividad": "Servicios Técnicos / Facturación Oficial"
}

# ==========================================
# FUNCIONES AUXILIARES Y GENERACIÓN DE PDF
# ==========================================
def obtener_o_inicializar_productos():
    res = supabase.table("productos").select("*").order("nombre").execute()
    return res.data if res.data else []

def generar_pdf_presupuesto(cliente_nombre, cliente_nif, items, num_presupuesto, fecha_generacion, validez_dias, datos_emisor, notas="", total_final_custom=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    style_header = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#333333"))
    style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#1e3d59"), alignment=2)
    
    story = []

    # Encabezado Empresa (Emisor Dinámico: Padre o Amigo)
    empresa_text = (
        f"<b>{datos_emisor.get('nombre', 'SUÁREZ SOUND')}</b><br/>"
        f"NIF/CIF: {datos_emisor.get('nif', 'N/A')}<br/>"
        f"{datos_emisor.get('direccion', '')}<br/>"
        f"{datos_emisor.get('email', '')}"
    )
    
    tipo_doc_label = "PRESUPUESTO"
    if num_presupuesto.startswith("FAC"):
        tipo_doc_label = "FACTURA OFICIAL"
    elif num_presupuesto.startswith("PRO"):
        tipo_doc_label = "PROFORMA / RECIBO"

    doc_text = f"<b>{tipo_doc_label}</b><br/>Nº: {num_presupuesto}<br/>Fecha: {fecha_generacion}"
    if validez_dias > 0:
        doc_text += f"<br/>Validez: {validez_dias} días"
    
    table_head = Table([
        [Paragraph(empresa_text, style_header), Paragraph(doc_text, style_title)]
    ], colWidths=[250, 280])
    table_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(table_head)
    story.append(Spacer(1, 20))

    # Datos del Cliente Receptor
    cli_text = f"<b>CLIENTE RECEPTOR:</b><br/><b>Nombre / Razón Social:</b> {cliente_nombre}<br/><b>NIF/CIF:</b> {cliente_nif or 'N/A'}"
    table_cli = Table([[Paragraph(cli_text, style_header)]], colWidths=[530])
    table_cli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
    ]))
    story.append(table_cli)
    story.append(Spacer(1, 20))

    # Tabla de Items / Conceptos
    data_items = [["Concepto / Producto", "Cant.", "Precio Unit.", "Subtotal"]]
    total_calculado = 0.0

    for item in items:
        p_name = item.get("producto") or item.get("nombre") or "Servicio / Producto"
        cant = float(item.get("cantidad", 1))
        precio = float(item.get("precio_unitario", 0.0))
        subt = cant * precio
        total_calculado += subt
        
        data_items.append([
            Paragraph(p_name, styles['Normal']),
            str(cant),
            f"{precio:,.2f} €",
            f"{subt:,.2f} €"
        ])

    tot_final = total_final_custom if total_final_custom is not None else total_calculado
    data_items.append(["", "", "TOTAL:", f"{tot_final:,.2f} €"])

    t_items = Table(data_items, colWidths=[280, 50, 100, 100])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3d59")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (-2,-1), (-1,-1), colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 20))

    if notas:
        story.append(Paragraph(f"<b>Notas / Observaciones:</b><br/>{notas}", style_header))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generar_pdf_documento(doc_data):
    cli = doc_data.get("clientes") or {}
    items = doc_data.get("items") or []
    num_doc = doc_data.get("numero_factura", "DOC-0001")
    
    # Asignar emisor según el tipo de documento si no viene especificado
    emisor_usar = EMISOR_PADRE if num_doc.startswith("FAC") else EMISOR_AMIGO
    if doc_data.get("emisor_tipo") == "Padre":
        emisor_usar = EMISOR_PADRE
    elif doc_data.get("emisor_tipo") == "Amigo":
        emisor_usar = EMISOR_AMIGO

    return generar_pdf_presupuesto(
        cliente_nombre=cli.get("nombre", "Cliente General"),
        cliente_nif=cli.get("nif", ""),
        items=items,
        num_presupuesto=num_doc,
        fecha_generacion=doc_data.get("fecha_emision", str(date.today())),
        validez_dias=0,
        datos_emisor=emisor_usar,
        notas="Documento oficial / Recibo emitido.",
        total_final_custom=float(doc_data.get("total", 0.0))
    )

# ==========================================
# MENÚ NAVEGACIÓN LATERAL
# ==========================================
st.sidebar.title("🔊 Suárez Sound")
st.sidebar.markdown("Sistema Integrado de Gestión")
menu = st.sidebar.radio("Navegación", [
    "📋 Presupuestos y Catálogo",
    "👤 CRM Clientes",
    "➕ Registros / Facturas",
    "📄 Historial Trabajos",
    "💸 Gastos"
])

# ==========================================
# SECCIÓN: PRESUPUESTOS Y CATÁLOGO
# ==========================================
if menu == "📋 Presupuestos y Catálogo":
    st.title("📋 Presupuestos y Catálogo")
    st.markdown("Generación de presupuestos comerciales, gestión de catálogo e historial.")
    st.markdown("---")

    tab_nuevo_p, tab_hist_p, tab_catalogo = st.tabs(["➕ Nuevo Presupuesto", "📚 Historial Presupuestos", "📦 Catálogo"])

    # Pestaña Nuevo Presupuesto
    with tab_nuevo_p:
        st.subheader("Crear Presupuesto Comercial")
        try:
            res_cli = supabase.table("clientes").select("id, nombre, nif").order("nombre").execute()
            clientes_p = res_cli.data or []

            if not clientes_p:
                st.warning("⚠️ Debes dar de alta al menos un cliente antes de crear un presupuesto.")
            else:
                dict_cli_p = {c["nombre"]: c for c in clientes_p}
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    cli_p_sel = st.selectbox("Cliente Receptor", list(dict_cli_p.keys()))
                    fecha_p = st.date_input("Fecha Emisión", value=date.today())
                with col_p2:
                    emisor_p_sel = st.selectbox("Emisor del Presupuesto", ["Amigo (Proformas / Comercial)", "Padre (Oficial)"])
                    validez_p = st.number_input("Validez (días)", min_value=1, value=15)

                notas_p = st.text_area("Observaciones/Notas", "Condiciones estándar de montaje y desmontaje.")

                st.markdown("---")
                st.markdown("#### Líneas de Concepto / Servicios")

                productos_db = obtener_o_inicializar_productos()
                lista_nombres_prod = [p["nombre"] for p in productos_db] if productos_db else ["Servicio Estándar"]

                if "items_presupuesto" not in st.session_state:
                    st.session_state.items_presupuesto = []

                with st.form("form_add_item"):
                    c_i1, c_i2, c_i3, c_i4 = st.columns([3, 1, 1, 1])
                    with c_i1:
                        prod_item = st.selectbox("Producto / Servicio", lista_nombres_prod)
                    with c_i2:
                        cant_item = st.number_input("Cantidad", min_value=1, value=1)
                    with c_i3:
                        precio_item = st.number_input("Precio Unit (€)", min_value=0.0, value=100.0, step=10.0)
                    with c_i4:
                        btn_add = st.form_submit_button("➕ Añadir Línea")

                    if btn_add:
                        st.session_state.items_presupuesto.append({
                            "producto": prod_item,
                            "cantidad": cant_item,
                            "precio_unitario": precio_item,
                            "subtotal": cant_item * precio_item
                        })

                if st.session_state.items_presupuesto:
                    df_items_p = pd.DataFrame(st.session_state.items_presupuesto)
                    st.dataframe(df_items_p, use_container_width=True)
                    
                    total_p_calc = df_items_p["subtotal"].sum()
                    st.markdown(f"### **Total Calculado:** `{total_p_calc:,.2f} €`")

                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        if st.button("🗑️ Limpiar Líneas"):
                            st.session_state.items_presupuesto = []
                            st.rerun()

                    with c_act2:
                        if st.button("💾 Guardar y Generar Presupuesto"):
                            count_p = supabase.table("presupuestos").select("id", count="exact").execute()
                            next_id_p = (count_p.count or 0) + 1
                            num_pres_gen = f"PRES-{date.today().strftime('%Y')}-{next_id_p:04d}"
                            
                            tipo_e = "Padre" if "Padre" in emisor_p_sel else "Amigo"

                            data_insert_p = {
                                "numero_presupuesto": num_pres_gen,
                                "cliente_id": dict_cli_p[cli_p_sel]["id"],
                                "fecha_emision": str(fecha_p),
                                "validez_dias": validez_p,
                                "total": total_p_calc,
                                "estado": "Pendiente de aprobación",
                                "items": st.session_state.items_presupuesto,
                                "notas": notas_p,
                                "emisor_tipo": tipo_e
                            }
                            supabase.table("presupuestos").insert(data_insert_p).execute()
                            st.session_state.items_presupuesto = []
                            st.success(f"Presupuesto {num_pres_gen} registrado correctamente con emisor: {tipo_e}.")
                            st.rerun()
        except Exception as err:
            st.error(f"Error cargando creador de presupuestos: {err}")

    # Pestaña Historial Presupuestos
    with tab_hist_p:
        try:
            res_p = supabase.table("presupuestos").select("id, numero_presupuesto, cliente_id, fecha_emision, total, estado, validez_dias, notas, items, emisor_tipo, clientes(nombre, nif)").order("id", desc=True).execute()
            if res_p.data:
                raw_p = res_p.data
                filas_p = []
                for p in raw_p:
                    c = p.get("clientes") or {}
                    filas_p.append({
                        "ID": p["id"],
                        "Número": p["numero_presupuesto"],
                        "Emisor": p.get("emisor_tipo", "Amigo"),
                        "Cliente": c.get("nombre", "N/A"),
                        "Fecha": p["fecha_emision"],
                        "Total (€)": p["total"],
                        "Estado": p.get("estado", "Pendiente de aprobación")
                    })
                df_pres = pd.DataFrame(filas_p)
                
                f_est = st.selectbox("Filtrar por Estado", ["Todos", "Pendiente de aprobación", "Enviado", "Aceptado", "Rechazado"])
                if f_est != "Todos":
                    df_pres = df_pres[df_pres["Estado"] == f_est]

                st.dataframe(df_pres, use_container_width=True)

                st.markdown("---")
                st.subheader("⚙️ Acciones sobre Presupuestos")
                
                codigos_pres = [p["numero_presupuesto"] for p in raw_p]
                pres_sel_code = st.selectbox("Selecciona un Presupuesto para gestionar", codigos_pres)
                
                pres_actual = next((item for item in raw_p if item["numero_presupuesto"] == pres_sel_code), None)

                if pres_actual:
                    col_act1, col_act2, col_act3 = st.columns(3)

                    # Cambiar Estado
                    with col_act1:
                        nuevo_estado = st.selectbox(
                            "Estado Actual",
                            ["Pendiente de aprobación", "Enviado", "Aceptado", "Rechazado"],
                            index=["Pendiente de aprobación", "Enviado", "Aceptado", "Rechazado"].index(
                                pres_actual.get("estado", "Pendiente de aprobación")
                            ),
                            key=f"est_{pres_actual['id']}"
                        )
                        if st.button("Actualizar Estado", key=f"btn_est_{pres_actual['id']}"):
                            try:
                                supabase.table("presupuestos").update({"estado": nuevo_estado}).eq("id", pres_actual["id"]).execute()
                                st.success(f"Estado actualizado a: {nuevo_estado}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar estado: {e}")

                    # Regenerar PDF
                    with col_act2:
                        cli_p = pres_actual.get("clientes") or {}
                        emisor_obj = EMISOR_PADRE if pres_actual.get("emisor_tipo") == "Padre" else EMISOR_AMIGO
                        
                        pdf_re = generar_pdf_presupuesto(
                            cliente_nombre=cli_p.get("nombre", "Cliente General"),
                            cliente_nif=cli_p.get("nif", ""),
                            items=pres_actual.get("items") or [],
                            num_presupuesto=pres_actual["numero_presupuesto"],
                            fecha_generacion=pres_actual["fecha_emision"],
                            validez_dias=pres_actual.get("validez_dias", 15),
                            datos_emisor=emisor_obj,
                            notas=pres_actual.get("notas", ""),
                            total_final_custom=float(pres_actual.get("total", 0.0))
                        )
                        st.download_button(
                            label="📄 Descargar PDF",
                            data=pdf_re,
                            file_name=f"{pres_actual['numero_presupuesto']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{pres_actual['id']}"
                        )

                    # Convertir a Factura / Proforma
                    with col_act3:
                        tipo_conv = st.selectbox("Convertir a", ["Factura Oficial (FAC)", "Proforma (PRO)"], key=f"conv_typ_{pres_actual['id']}")
                        if st.button("🔄 Convertir Documento", key=f"btn_conv_{pres_actual['id']}"):
                            try:
                                is_fac = "Oficial" in tipo_conv
                                prefix = "FAC" if is_fac else "PRO"
                                emisor_conv = "Padre" if is_fac else "Amigo"
                                
                                count_res = supabase.table("facturas").select("id", count="exact").execute()
                                next_id = (count_res.count or 0) + 1
                                num_doc = f"{prefix}-{date.today().strftime('%Y')}-{next_id:04d}"

                                nueva_factura = {
                                    "numero_factura": num_doc,
                                    "cliente_id": pres_actual["cliente_id"],
                                    "fecha_emision": str(date.today()),
                                    "total": pres_actual["total"],
                                    "estado": "Pendiente",
                                    "items": pres_actual.get("items"),
                                    "emisor_tipo": emisor_conv
                                }

                                supabase.table("facturas").insert(nueva_factura).execute()
                                supabase.table("presupuestos").update({"estado": "Aceptado"}).eq("id", pres_actual["id"]).execute()
                                st.success(f"Presupuesto convertido a {num_doc} (Emisor: {emisor_conv}).")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al convertir el presupuesto: {e}")

            else:
                st.info("No hay presupuestos registrados en el historial.")

        except Exception as err:
            st.error(f"Error cargando el historial de presupuestos: {err}")

    # Pestaña Catálogo
    with tab_catalogo:
        st.subheader("📦 Gestión del Catálogo de Productos y Servicios")
        
        try:
            prods = obtener_o_inicializar_productos()
            if prods:
                df_cat = pd.DataFrame(prods)
                st.dataframe(df_cat[["id", "nombre"]], use_container_width=True)

            with st.form("form_nuevo_producto"):
                st.markdown("### ➕ Añadir Nuevo Producto / Servicio al Catálogo")
                nuevo_prod_nombre = st.text_input("Nombre del producto o servicio")
                btn_guardar_prod = st.form_submit_button("Guardar Producto")

                if btn_guardar_prod:
                    if nuevo_prod_nombre.strip():
                        supabase.table("productos").insert({"nombre": nuevo_prod_nombre.strip()}).execute()
                        st.success(f"Producto '{nuevo_prod_nombre}' añadido con éxito.")
                        st.rerun()
                    else:
                        st.warning("Escribe un nombre válido.")
        except Exception as err:
            st.error(f"Error gestionando el catálogo: {err}")

# ==========================================
# SECCIÓN: CRM CLIENTES
# ==========================================
elif menu == "👤 CRM Clientes":
    st.title("👤 Gestión de Clientes (CRM)")
    st.markdown("Base de datos de clientes receptores para asociar presupuestos, servicios y facturación.")
    st.markdown("---")

    tab_c_lista, tab_c_crear = st.tabs(["📋 Lista de Clientes", "➕ Dar de Alta Cliente"])

    with tab_c_lista:
        try:
            res_c = supabase.table("clientes").select("*").order("nombre").execute()
            if res_c.data:
                df_c = pd.DataFrame(res_c.data)
                st.dataframe(df_c, use_container_width=True)
            else:
                st.info("No hay clientes registrados en la base de datos.")
        except Exception as err:
            st.error(f"Error obteniendo clientes: {err}")

    with tab_c_crear:
        with st.form("form_nuevo_cliente"):
            c_nom = st.text_input("Nombre o Razón Social *")
            c_nif = st.text_input("DNI / NIF / CIF")
            c_email = st.text_input("Correo Electrónico")
            c_tel = st.text_input("Teléfono de Contacto")
            c_dir = st.text_area("Dirección Completa")
            
            btn_c_save = st.form_submit_button("💾 Guardar Cliente")

            if btn_c_save:
                if c_nom.strip():
                    nuevo_c = {
                        "nombre": c_nom.strip(),
                        "nif": c_nif.strip(),
                        "email": c_email.strip(),
                        "telefono": c_tel.strip(),
                        "direccion": c_dir.strip()
                    }
                    try:
                        supabase.table("clientes").insert(nuevo_c).execute()
                        st.success(f"Cliente '{c_nom}' registrado correctamente.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al registrar cliente: {err}")
                else:
                    st.warning("El campo Nombre es obligatorio.")

# ==========================================
# SECCIÓN: REGISTROS / FACTURAS
# ==========================================
elif menu == "➕ Registros / Facturas":
    st.title("➕ Alta Directa de Facturas y Proformas")
    st.markdown("Genera un registro oficial o proforma especificando el tipo de emisor e importes.")
    st.markdown("---")

    try:
        res_clientes = supabase.table("clientes").select("id, nombre, nif").order("nombre").execute()
        clientes = res_clientes.data

        if not clientes:
            st.warning("⚠️ Primero debes dar de alta al menos un cliente en 'CRM Clientes'.")
        else:
            dict_clientes = {c["nombre"]: c for c in clientes}

            with st.form("form_alta_factura"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    cli_sel_f = st.selectbox("Cliente Receptor *", list(dict_clientes.keys()))
                    tipo_doc = st.selectbox("Tipo Documento", ["Factura Oficial (FAC)", "Proforma / Recibo (PRO)"])
                with col_f2:
                    fecha_fac = st.date_input("Fecha Emisión / Evento", value=date.today())
                    estado_pago = st.selectbox("Estado del Pago", ["Pendiente", "Cobrada"])

                # Lógica del Emisor según tipo de documento
                default_emisor_idx = 0 if "Oficial" in tipo_doc else 1
                emisor_seleccionado = st.selectbox(
                    "Emisor Fiscal del Documento",
                    ["Padre (Facturación Oficial)", "Amigo (Proformas / Recibos)"],
                    index=default_emisor_idx
                )

                st.markdown("---")
                concepto_serv = st.text_input("Concepto / Servicio Principal", "Servicios técnicos de sonorización y montaje")
                monto_total = st.number_input("Importe Total (€ IVA Incluido si aplica)", min_value=0.0, value=0.0, step=10.0, format="%.2f")

                btn_gen_fac = st.form_submit_button("💾 Emitir Documento")

                if btn_gen_fac:
                    if monto_total > 0:
                        prefix = "FAC" if "Oficial" in tipo_doc else "PRO"
                        tipo_emisor_str = "Padre" if "Padre" in emisor_seleccionado else "Amigo"

                        count_res = supabase.table("facturas").select("id", count="exact").execute()
                        next_id = (count_res.count or 0) + 1
                        num_doc = f"{prefix}-{date.today().strftime('%Y')}-{next_id:04d}"

                        item_data = [{
                            "producto": concepto_serv,
                            "cantidad": 1,
                            "precio_unitario": monto_total,
                            "subtotal": monto_total
                        }]

                        registro_fac = {
                            "numero_factura": num_doc,
                            "cliente_id": dict_clientes[cli_sel_f]["id"],
                            "fecha_emision": str(fecha_fac),
                            "total": monto_total,
                            "estado": estado_pago,
                            "items": item_data,
                            "emisor_tipo": tipo_emisor_str
                        }

                        supabase.table("facturas").insert(registro_fac).execute()
                        st.success(f"Documento {num_doc} generado con éxito con Emisor: {tipo_emisor_str}.")
                        st.rerun()
                    else:
                        st.warning("El importe total debe ser mayor a 0.")

    except Exception as err:
        st.error(f"Error procesando formulario: {err}")

# ==========================================
# SECCIÓN: HISTORIAL TRABAJOS
# ==========================================
elif menu == "📄 Historial Trabajos":
    st.title("📄 Historial General de Trabajos y Documentos")
    st.markdown("Consulta general de facturas y recibos guardados, actualización de estados de cobro y descarga en PDF.")
    st.markdown("---")

    try:
        res_f = supabase.table("facturas").select("id, numero_factura, cliente_id, fecha_emision, total, estado, items, emisor_tipo, clientes(nombre, nif, email, telefono)").order("id", desc=True).execute()

        if res_f.data:
            raw_f = res_f.data
            filas_f = []

            for f in raw_f:
                cli = f.get("clientes") or {}
                filas_f.append({
                    "ID": f["id"],
                    "Número": f["numero_factura"],
                    "Emisor": f.get("emisor_tipo", "Padre" if f["numero_factura"].startswith("FAC") else "Amigo"),
                    "Cliente Receptor": cli.get("nombre", "Sin Cliente"),
                    "Fecha": f["fecha_emision"],
                    "Total (€)": f["total"],
                    "Estado": f["estado"]
                })

            df_f = pd.DataFrame(filas_f)

            col_fil1, col_fil2, col_fil3 = st.columns(3)
            with col_fil1:
                filtro_est_f = st.selectbox("Filtrar por Estado de Pago", ["Todos", "Pendiente", "Cobrada"])
            with col_fil2:
                filtro_tipo_f = st.selectbox("Filtrar por Tipo", ["Todos", "Facturas Oficiales (FAC)", "Proformas (PRO)"])
            with col_fil3:
                filtro_emisor_f = st.selectbox("Filtrar por Emisor", ["Todos", "Padre", "Amigo"])

            if filtro_est_f != "Todos":
                df_f = df_f[df_f["Estado"] == filtro_est_f]
            if filtro_tipo_f != "Todos":
                pfx = "FAC" if "FAC" in filtro_tipo_f else "PRO"
                df_f = df_f[df_f["Número"].str.startswith(pfx)]
            if filtro_emisor_f != "Todos":
                df_f = df_f[df_f["Emisor"] == filtro_emisor_f]

            st.dataframe(df_f, use_container_width=True)

            st.markdown("---")
            st.subheader("🛠️ Gestión de Documento")

            codigos_docs = [doc["numero_factura"] for doc in raw_f]
            doc_sel_code = st.selectbox("Seleccionar Documento para gestionar", codigos_docs)
            
            doc_actual = next((item for item in raw_f if item["numero_factura"] == doc_sel_code), None)

            if doc_actual:
                c_m1, c_m2 = st.columns(2)

                with c_m1:
                    est_actual = doc_actual["estado"]
                    nuevo_est = st.selectbox("Estado de Pago", ["Pendiente", "Cobrada"], index=0 if est_actual == "Pendiente" else 1, key=f"f_est_{doc_actual['id']}")
                    
                    if st.button("Actualizar Estado de Pago", key=f"f_btn_{doc_actual['id']}"):
                        supabase.table("facturas").update({"estado": nuevo_est}).eq("id", doc_actual["id"]).execute()
                        st.success(f"Estado actualizado a: {nuevo_est}")
                        st.rerun()

                with c_m2:
                    pdf_fac_bytes = generar_pdf_documento(doc_actual)
                    st.download_button(
                        label="📄 Descargar PDF de Documento",
                        data=pdf_fac_bytes,
                        file_name=f"{doc_actual['numero_factura']}.pdf",
                        mime="application/pdf",
                        key=f"f_dl_{doc_actual['id']}"
                    )
        else:
            st.info("No existen facturas o recibos registrados en la base de datos.")

    except Exception as err:
        st.error(f"Error al cargar historial: {err}")

# ==========================================
# SECCIÓN: GASTOS
# ==========================================
elif menu == "💸 Gastos":
    st.title("💸 Gestión y Registro de Gastos")
    st.markdown("Control de compras, material, transporte y salidas de caja de **Suárez Sound**.")
    st.markdown("---")

    tab_g1, tab_g2 = st.tabs(["📋 Historial de Gastos", "➕ Registrar Gasto"])

    with tab_g1:
        try:
            res_g = supabase.table("gastos").select("*").order("fecha", desc=True).execute()
            if res_g.data:
                df_g = pd.DataFrame(res_g.data)
                st.dataframe(df_g, use_container_width=True)
                
                tot_g_sum = df_g["total"].sum()
                st.info(f"💰 **Total Acumulado de Gastos:** `{tot_g_sum:,.2f} €`")
            else:
                st.info("No hay gastos registrados.")
        except Exception as err:
            st.error(f"Error al cargar gastos: {err}")

    with tab_g2:
        with st.form("form_nuevo_gasto"):
            g_concepto = st.text_input("Concepto / Proveedor *")
            g_categoria = st.selectbox("Categoría", ["Material / Equipamiento", "Transporte / Combustible", "Personal / Freelance", "Mantenimiento", "Otros"])
            g_fecha = st.date_input("Fecha", value=date.today())
            g_monto = st.number_input("Importe (€)", min_value=0.0, value=0.0, step=5.0, format="%.2f")

            btn_g_save = st.form_submit_button("💾 Guardar Gasto")

            if btn_g_save:
                if g_concepto.strip() and g_monto > 0:
                    nuevo_gasto = {
                        "concepto": g_concepto.strip(),
                        "categoria": g_categoria,
                        "fecha": str(g_fecha),
                        "total": g_monto
                    }
                    try:
                        supabase.table("gastos").insert(nuevo_gasto).execute()
                        st.success("Gasto registrado correctamente.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al guardar gasto: {err}")
                else:
                    st.warning("Proporciona un concepto válido y un importe mayor a 0.")
