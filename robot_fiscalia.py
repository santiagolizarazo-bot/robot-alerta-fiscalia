import requests, re, os, spacy, unicodedata, holidays
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import urllib3 

# Apagamos alarmas de conexión por el Firewall corporativo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# ⚙️ CONFIGURACIONES PRINCIPALES
# ==========================================
ID_DRIVE = "1ImDGv9bO-5cg6LjpAIP-kkRKzkuglI9B" 
NOMBRE_EXCEL_SALIDA = "Alerta_Fiscalia.xlsx"

# ==========================================
# 🛑 DICCIONARIO UIAF: DELITOS FUENTE DE LA/FT
# ==========================================
DELITOS_LAFT = [
    "trafico de migrantes", "trata de personas", "extorsion", "enriquecimiento ilicito",
    "secuestro", "rebelion", "trafico de armas", "porte de armas", "financiacion del terrorismo",
    "terrorismo", "narcotrafico", "estupefacientes", "sicotropicas", "sistema financiero",
    "administracion publica", "contrabando", "fraude aduanero", "concierto para delinquir",
    "lavado de activos", "testaferrato", "explotacion sexual", "prostitucion", "peculado",
    "omision del agente retenedor", "fraude a subvenciones", "concusion", "cohecho",
    "celebracion de contratos", "acuerdos restrictivos", "trafico de influencias",
    "prevaricato", "abuso de autoridad", "usurpacion de funciones", "soborno transnacional",
    "evasion tributaria", "defraudacion", "hidrocarburos", "captacion masiva", "droga"
]

# ==========================================
# 🧠 PARTE 1: EL MOTOR DE EXTRACCIÓN (SCRAPING)
# ==========================================
print("🔥 INICIANDO SÚPER ROBOT: GITHUB EDITION (MODO TURBO + FILTRO UIAF) 🔥")
nlp = spacy.load("es_core_news_sm")
cl = lambda t: unicodedata.normalize('NFKD', str(t)).encode('ASCII', 'ignore').decode('utf-8').upper() if t else ""

prohibidas = [
    "fiscalia", "policia", "juez", "jueces", "gobierno", "alias", "tecnico", "cti", 
    "fiscal", "fiscales", "director", "magistrado", "procuraduria", "nacion", "hermanos",
    "medicina", "legal", "forense", "ciencias", "instituto", "hospital", "clinica", 
    "juzgado", "ejercito", "armada", "fuerza", "fuerzas", "armadas", "perpetuo", "alcaldia", 
    "gobernacion", "ministerio", "secretaria", "departamento", "municipio", "barrio", 
    "vereda", "corregimiento", "carcel", "penitenciaria", "san", "santa", "santo", 
    "cristo", "rey", "palermo", "iglesia", "colegio", "escuela", "parroquia", "avenida", 
    "calle", "carrera", "juan de acosta", "soledad", "malambo", "defensoria", 
    "tunja", "boyaca", "puerto", "berrio", "asis", "putumayo", "establecimiento", 
    "victima", "victimas", "procesado", "procesados", "seccional", "santander", "huila", 
    "vias", "quindio", "cundinamarca", "valle", "cali", "bolivar", "tolima", "colombia", "bogota",
    "reaccion", "inmediata", "arboleda", "campestre", "empleo", "empresarial", "activos", "especiales",
    "bienestar", "proteccion", "animal", "grupo", "especial", "maltrato", "olaya", 
    "herrera", "aurora", "alta", "delito", "delitos", "hurto", "homicidio", 
    "tentativa", "feminicidio", "sexual", "acceso", "carnal", "acto", "violencia", 
    "intrafamiliar", "armas", "fuego", "hechiza", "blanca", "letal", "cuchillo", 
    "motocicleta", "vehiculo", "unidad", "sijin", "dijin", "gaula", "metropolitana", 
    "estacion", "direccion", "especializada", "familia", "pio", "torcoroma", "segun",
    "banda", "estructura", "criminal", "frente", "bloque", "comision", "clan", "golfo",
    "red", "delincuencial", "organizado", "narcotrafico", "narcotraficantes", "sociedad", "asociacion",
    "alertas", "tempranas", "ciudad", "verde", "jerarquia", "responsabilidad", "penal", 
    "corte", "suprema", "correo", "institucional", "notificaciones", "judiciales", 
    "republica", "dominicana", "emiratos", "arabes", "unidos", "peru", "usa", "marquetalia", 
    "pueblo", "nuevo", "luis carlos galan", "miguel uribe", "uribe turbay", "fijo", "viejo",
    "farc", "gaor", "zarco", "aldinever", "chalo", "rusbel", "rumba",
    "kennedy", "cristobal", "simiti", "orquideas", "estado mayor", "puente nacional", 
    "villa flor", "bonilla aragon", "orden", "economico", "funcion", "publica", 
    "gestion", "contable", "fe", "patrimonio", "decision", "judicial", "saber", 
    "pro", "tyt", "icfes", "seguridad", "maxima", "mediana", "dona", "juana", 
    "jovenes", "millonarios", 
    "finanzas", "criminales", "corrupcion", "extincion", "dominio", "lavado", "impuestos", "aduanas", "dian",
    "hirio", "causo", "provoco", "lesiono", "disparo", "ataco", "nego", "acepto", "declaro", 
    "afirmo", "aseguro", "rechazo", "expreso", "indico", "habia", "habian", "sucedido", 
    "adicionalmente", "ademas", "tambien", "asimismo", "igualmente", "posteriormente", 
    "finalmente", "entonces", "luego", "mientras", "durante", "este", "esta", "estos", 
    "estas", "aquel", "porque", "cuando", "donde", "quien", "quienes", "enero", "febrero", 
    "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", 
    "diciembre", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", 
    "mes", "meses", "dia", "dias", "hora", "horas",
    "costa rica", "moneda", "falsa", "falso", "charco", "azul", "almendra", "madre", "padre",
    "pondaje", "hato", "corozal", "falsificacion", "billetes", "dolares", "pesos",
    "derechos", "humanos", "tribunal", "superior",
    
    # --- NUEVOS FILTROS MAYO 2026 ---
    "movil", "turquia", "identificacion", "preliminar", "homologada", 
    "detencion", "domiciliaria", "callejon", "manhattan", "bugalagrande", 
    "zarzal", "liberacion", "nacional", "la mesa"
]

def analizar_noticia(txt):
    txt_limpio_busqueda = cl(txt).lower()
    delitos_detectados = [d.upper() for d in DELITOS_LAFT if d in txt_limpio_busqueda]
    
    if not delitos_detectados:
        return set(), ""
        
    dels_final = ", ".join(delitos_detectados)

    ents = []
    txt = re.sub(r"(?i)\balias\s+['\"‘“]?(?:[A-ZÁÉÍÓÚÑ0-9][^\s,.;:()]*|el|la|los|las|o|y|del?)(?:\s+(?:[A-ZÁÉÍÓÚÑ0-9][^\s,.;:()]*|el|la|los|las|o|y|del?)){0,4}['\"’”]?", " ", txt)
    
    patron_hermanos = r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñüA-ZÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñüA-ZÁÉÍÓÚÑ]+)?)\s+[yeY]\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñüA-ZÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñüA-ZÁÉÍÓÚÑ]+){1,3})\b"
    for match in re.finditer(patron_hermanos, txt):
        h1, h2 = match.group(1), match.group(2)
        start_idx = match.start()
        if start_idx > 0:
            text_before = txt[:start_idx].strip()
            if text_before:
                last_word_before = text_before.split()[-1]
                if last_word_before and last_word_before[0].isupper() and last_word_before.lower() not in ["el", "la", "los", "las", "un", "una", "del", "al"]:
                    continue 
        p2 = h2.split()
        if len(p2) >= 3: ents.extend([f"{h1} {' '.join(p2[-2:])}", h2]) 
        elif len(p2) == 2: ents.extend([f"{h1} {p2[-1]}", h2]) 

    for e in nlp(txt).ents:
        if e.label_ == "PER":
            n_crudo = re.sub(r"(?i)^(los\s+hermanos\s+|los\s+se[ñn]ores\s+|el\s+se[ñn]or\s+|la\s+se[ñn]ora\s+)", "", e.text.strip().replace("\n", " "))
            ents.append(n_crudo)

    for n in re.findall(r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+){1,3})\b", txt):
        ents.append(re.sub(r"^(El|La|Los|Las|Un|Una|Del|Al|Por|Para|Con|En)\s+", "", n, flags=re.IGNORECASE).strip())

    triggers_victima = ["asesinato de", "asesinato del", "homicidio de", "homicidio del", "muerte de", "muerte del", "victima", "víctima", "cuerpo de", "cuerpo del", "atentado contra", "ataque contra", "abuso de", "abuso del", "secuestro de", "secuestro del", "magnicidio de", "magnicidio del", "senador", "precandidato", "candidato", "lider", "líder", "crimen contra"]
    triggers_autoridad = ["director", "directora", "comandante", "general", "defensor", "defensora", "procurador", "procuradora", "asesor", "asesora", "alcalde", "alcaldesa", "gobernador", "gobernadora", "coronel", "ministro", "ministra", "gerente", "personero", "personera", "patrullero", "intendente", "vocero", "secretario", "secretaria", "jefe", "instituciones"]
    triggers_lugar = ["barrio", "vereda", "corregimiento", "municipio", "sector", "ciudad", "departamento", "hospital", "clinica", "clínica", "carcel", "cárcel", "colegio", "escuela", "parque", "avenida", "calle", "carrera", "via", "vía", "estacion", "estación", "aeropuerto", "terminal", "finca", "hacienda", "edificio", "conjunto", "localidad", "centro comercial", "plaza", "puente", "universidad", "cementerio"]
    salvavidas = ["capturado", "capturada", "capturados", "condenado", "condenada", "condenados", "imputado", "imputada", "imputados", "procesado", "procesada", "procesados", "judicializado", "judicializada", "judicializados", "cárcel", "carcel", "prisión", "prision", "aseguramiento", "responsable", "extraditado", "extraditada", "extraditados", "presunto", "presunta", "presuntos", "presuntas", "investigado", "investigada", "investigados", "señalado", "señalada", "señalados"]

    ents_filtradas = []
    for n in ents:
        idx = txt.find(n)
        descartar = False
        if idx != -1:
            ctx_antes, ctx_despues = txt[max(0, idx-120):idx].lower(), txt[idx+len(n):idx+len(n)+120].lower()
            ctx_total = ctx_antes + " " + ctx_despues
            if any(t in ctx_antes for t in triggers_victima): descartar = True
            if any(t in ctx_total.replace("fiscalía general", "").replace("fiscalia general", "") for t in triggers_autoridad) and not any(re.search(rf"\b{s}\b", ctx_total) for s in salvavidas): descartar = True
            if any(re.search(rf"\b{lugar}\b\s*(de\s+|del\s+|la\s+|el\s+|los\s+|las\s+)?\s*$", txt[max(0, idx-40):idx].lower()) for lugar in triggers_lugar): descartar = True
        if not descartar: ents_filtradas.append(n)

    pers_limpias = [cl(p) for p in ents_filtradas if not any(re.search(rf"\b{x}\b", cl(p).lower()) for x in prohibidas) and not any(char.isdigit() for char in cl(p)) and "." not in p and "," not in p and len(cl(p)) >= 5 and len(cl(p).split()) <= 4 and not re.search(r"\b[A-Z]\b", cl(p).replace(" Y ", " "))]

    pers_finales = set()
    for p1 in pers_limpias:
        es_version_corta, es_frankenstein = False, False
        palabras_p1 = set(p1.split())
        for p2 in pers_limpias:
            if p1 != p2 and palabras_p1.issubset(set(p2.split())): es_version_corta = True; break
        if not es_version_corta and len(palabras_p1) >= 3:
            palabras_en_otros = set()
            for p2 in pers_limpias:
                if p1 != p2 and not set(p2.split()).issubset(palabras_p1): palabras_en_otros.update(p2.split())
            if palabras_p1.issubset(palabras_en_otros): es_frankenstein = True
        if not es_version_corta and not es_frankenstein: pers_finales.add(p1)

    return {p for p in pers_finales if len(p.split()) >= 2}, dels_final

def extraer_noticias():
    hoy = datetime.now()
    festivos_colombia = holidays.Colombia(years=hoy.year)
    dias_atras = 1
    fecha_revisar = hoy - timedelta(days=dias_atras)
    while fecha_revisar.weekday() >= 5 or fecha_revisar in festivos_colombia:
        dias_atras += 1 
        fecha_revisar = hoy - timedelta(days=dias_atras)

    lim_inf = fecha_revisar.replace(hour=0, minute=0, second=0, microsecond=0)
    lim_sup = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Buscando estrictamente noticias desde el: {lim_inf.strftime('%Y-%m-%d')} hasta Hoy\n")

    sesion = requests.Session()
    sesion.headers.update({'User-Agent': 'Mozilla/5.0'})
    sesion.verify = False 
    
    datos_extraidos = []
    pag, run = 1, True

    while run:
        print(f"Revisando pág {pag}...")
        try:
            soup = BeautifulSoup(sesion.get(f"https://www.fiscalia.gov.co/colombia/inicio/mas-noticias/page/{pag}/").content, 'html.parser')
            links = [a.get('href') for a in soup.select("h3.entry-title a") if a.get('href')]
            if not links: break

            for l in links:
                try:
                    s_not = BeautifulSoup(sesion.get(l).content, 'html.parser')
                    t = s_not.find("meta", property="article:published_time") or s_not.find("time")
                    f_str = t.get("content", t.get("datetime", ""))[:10] if t else ""
                    fecha = datetime.strptime(f_str, "%Y-%m-%d") if len(f_str) == 10 else None
                    
                    if not fecha or fecha >= lim_sup: continue
                    if fecha < lim_inf: run = False; break
                    
                    txt = re.sub(r"(.*?)(La informaci[oó]n contenida.*)", r"\1", " ".join([p.text for p in s_not.find_all("p")]), flags=re.I)
                    pers, dels = analizar_noticia(txt)
                    
                    if pers:
                        for p in pers: datos_extraidos.append({'FECHA': cl(fecha.strftime('%Y-%m-%d')), 'NOMBRE': cl(p), 'DELITO': dels, 'URL_NOTICIA': l})
                        print(f" -> ¡FILTRO UIAF APROBADO! Extraído ({f_str}): {', '.join([cl(p) for p in pers])} | Delitos: {dels}")
                except Exception: pass
            pag += 1
        except Exception as e: 
            print(f"Error en página {pag}: {e}"); break
            
    return pd.DataFrame(datos_extraidos) if datos_extraidos else pd.DataFrame()

# ==========================================
# 🕵️‍♂️ PARTE 2: EL MOTOR DE CRUCE Y GUARDADO
# ==========================================
def limpiar_texto(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().strip()
    return re.sub(r"[^A-Z0-9\s]", "", "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"))

def buscar_coincidencia_rapida(df_contrapartes, nombre_noticia):
    palabras_noticia = limpiar_texto(nombre_noticia).split() 
    if len(palabras_noticia) < 2: return pd.DataFrame() 

    def coincide(palabras_db):
        if len(palabras_db) < 2: return False
        corta, larga = (palabras_noticia, palabras_db) if len(palabras_noticia) <= len(palabras_db) else (palabras_db, palabras_noticia)
        return all(palabra in larga for palabra in corta)

    mask = df_contrapartes['PALABRAS_LISTA'].apply(coincide)
    return df_contrapartes[mask]

# ==========================================
# 🚀 PARTE 3: EJECUCIÓN MAESTRA
# ==========================================
def ejecutar_pipeline():
    columnas_finales = ['NROID', 'ID', 'RAPPIPAY ID', 'NIVEL DE ALERTA', 'CONTRAPARTE (BD)', 'ACUSADO (NOTICIA)', '% DE COINCIDENCIA', 'FECHA', 'DELITO', 'URL_NOTICIA']
    
    df_noticias = extraer_noticias()
    if df_noticias.empty:
        print("\n✅ Proceso Terminado. No se encontraron noticias de delitos fuente LA/FT hoy.")
        try:
            pd.DataFrame(columns=columnas_finales).to_excel(NOMBRE_EXCEL_SALIDA, index=False)
        except PermissionError:
            print(f"\n❌ ERROR: ¡Tienes el archivo '{NOMBRE_EXCEL_SALIDA}' abierto! Ciérralo.")
        return

    print(f"\nIntentando descargar Base de Contrapartes desde Google Drive (>25MB)...")
    archivo_temporal = "Contrapartes_Temp.parquet"
    
    try:
        session = requests.Session()
        URL = f"https://drive.google.com/uc?export=download&id={ID_DRIVE}"
        
        # ⚡ 1. Primera petición inteligente
        response = session.get(URL, stream=True, verify=False)
        content_type = response.headers.get('Content-Type', '')
        
        # ⚡ 2. Detector de Páginas Web (Antivirus o Login bloqueado)
        if 'text/html' in content_type:
            texto_html = response.text
            match = re.search(r'confirm=([a-zA-Z0-9_-]+)', texto_html)
            
            if match:
                token = match.group(1)
                print("Saltando advertencia de Antivirus de Google Drive...")
                response = session.get(URL, params={'confirm': token}, stream=True, verify=False)
            else:
                print("\n❌ ERROR GRAVE: Google Drive no entregó la base de datos, entregó una página web.")
                print("⚠️ Es CASI SEGURO que tu enlace está restringido a 'Solo empleados de la empresa'.")
                print("⚠️ SOLUCIÓN: Ve a Drive -> Compartir -> Cambia a 'Cualquier persona con el enlace'.\n")
                return
        
        # ⚡ 3. Descarga de datos reales
        if response.status_code == 200:
            with open(archivo_temporal, 'wb') as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
            print("✅ Descarga completada correctamente.")
        else:
            print(f"❌ Error en la descarga. Código de estado: {response.status_code}")
            return

        # ⚡ 4. Lector Turbo
        if os.path.exists(archivo_temporal):
            print("Leyendo y optimizando archivo Parquet para velocidad Turbo...")
            df_base = pd.read_parquet(archivo_temporal)
            df_base["NOMBRE"] = df_base["NOMBRE"].astype(str).apply(limpiar_texto)
            df_base["PALABRAS_LISTA"] = df_base["NOMBRE"].str.split()
        else:
            print("❌ El archivo no se encontró en el disco después de la descarga.")
            return

    except Exception as e:
        print(f"❌ Error crítico en el proceso de descarga/lectura: {e}")
        return

    hallazgos_totales = []
    print(f"\nIniciando cruce ultra-rápido de {len(df_noticias)} nombres extraídos...")
    
    for index, row in df_noticias.iterrows():
        nombre_buscar = str(row["NOMBRE"]).strip()
        print(f"Buscando: {nombre_buscar}...")
        coincidencias = buscar_coincidencia_rapida(df_base, nombre_buscar)
        
        if not coincidencias.empty:
            print(f"  [!] ALERTA ROJA: {len(coincidencias)} posibles contrapartes encontradas.")
            for _, coincidencia_row in coincidencias.iterrows():
                
                palabras_n = nombre_buscar.split()
                palabras_c = coincidencia_row["PALABRAS_LISTA"]
                max_len = max(len(palabras_n), len(palabras_c))
                min_len = min(len(palabras_n), len(palabras_c))
                
                porcentaje_raw = (min_len / max_len) * 100 if max_len > 0 else 0
                porcentaje_calc = f"{round(porcentaje_raw, 2)}%"
                
                nroid_extraido = coincidencia_row["NROID"] if "NROID" in coincidencia_row else "NO DISPONIBLE"
                id_extraido = coincidencia_row["ID"] if "ID" in coincidencia_row else "NO DISPONIBLE"
                rappipay_id_extraido = coincidencia_row["RAPPIPAY ID"] if "RAPPIPAY ID" in coincidencia_row else "NO DISPONIBLE"

                if min_len >= 4:
                    nivel_alerta = "🔴 ALERTA CRÍTICA (4+ Palabras)"
                elif min_len == 3:
                    nivel_alerta = "🟠 ALERTA MEDIA (3 Palabras)"
                elif min_len == 2:
                    nivel_alerta = "🟡 ALERTA BAJA (2 Palabras)"
                else:
                    nivel_alerta = "⚪ DESCARTADO (1 Palabra)"

                hallazgos_totales.append({
                    'NROID': nroid_extraido,
                    'ID': id_extraido,                             
                    'RAPPIPAY ID': rappipay_id_extraido,           
                    'NIVEL DE ALERTA': nivel_alerta,             
                    'CONTRAPARTE (BD)': coincidencia_row["NOMBRE"],
                    'ACUSADO (NOTICIA)': nombre_buscar,
                    '% DE COINCIDENCIA': porcentaje_calc,
                    'FECHA': row.get("FECHA", ""),
                    'DELITO': row.get("DELITO", ""),
                    'URL_NOTICIA': row.get("URL_NOTICIA", ""),
                    '_sort_pct': porcentaje_raw,                 
                    '_sort_key': min_len                         
                })

    if hallazgos_totales:
        df_final = pd.DataFrame(hallazgos_totales)
        df_final = df_final.sort_values(by=['_sort_pct', '_sort_key'], ascending=[False, False])
        df_final = df_final.drop(columns=['_sort_key', '_sort_pct'])
        df_final = df_final[columnas_finales]
        
        try:
            df_final.to_excel(NOMBRE_EXCEL_SALIDA, index=False)
            print(f"\n[OK] Cruce terminado. Se encontraron {len(hallazgos_totales)} alertas.")
            print(f"✅ Archivo guardado localmente como: {NOMBRE_EXCEL_SALIDA}")
        except PermissionError:
            print(f"\n❌ ERROR: ¡Tienes el archivo '{NOMBRE_EXCEL_SALIDA}' abierto! Ciérralo.")
    else:
        try:
            pd.DataFrame(columns=columnas_finales).to_excel(NOMBRE_EXCEL_SALIDA, index=False)
            print("\n[OK] Cruce terminado. Excelente, ninguna contraparte apareció en las noticias.")
            print(f"✅ Archivo vacío guardado localmente como: {NOMBRE_EXCEL_SALIDA}")
        except PermissionError:
            print(f"\n❌ ERROR: ¡Tienes el archivo '{NOMBRE_EXCEL_SALIDA}' abierto! Ciérralo.")
            
    if os.path.exists(archivo_temporal):
        try:
            os.remove(archivo_temporal)
        except:
            pass

if __name__ == "__main__":
    ejecutar_pipeline()
