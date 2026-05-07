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
    "evasion tributaria", "defraudacion", "hidrocarburos", "captacion masiva", "droga",
    "hurto calificado"
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
    
    # --- FILTROS ADICIONALES ---
    "movil", "turquia", "identificacion", "preliminar", "homologada", 
    "detencion", "domiciliaria", "callejon", "manhattan", "bugalagrande", 
    "zarzal", "liberacion", "nacional", "la mesa", "mosquera"
]

def analizar_noticia(txt):
    txt_limpio_busqueda = cl(txt).lower()
    delitos_detectados = [d.upper() for d in DELITOS_LAFT if d in txt_limpio_busqueda]
    
    if not delitos_detectados:
        return set(), ""
        
    dels_final = ", ".join(delitos_detectados)
    ents = []

    # 1. Limpieza de Alias
    txt = re.sub(r"(?i)\balias\s+['\"‘“]?(?:[A-ZÁÉÍÓÚÑ0-9][^\s,.;:()]*|el|la|los|las|o|y|del?)(?:\s+(?:[A-ZÁÉÍÓÚÑ0-9][^\s,.;:()]*|el|la|los|las|o|y|del?)){0,4}['\"’”]?", " ", txt)

    # 2. DETECTOR DE LISTAS DE NOMBRES (Mejora para leer listas como la de Medellín)
    # Busca grupos de palabras que empiecen en mayúscula, aceptando conectores como "de"
    patron_lista = r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+(?:de\s+|la\s+|del\s+)? [A-ZÁÉÍÓÚÑ][a-záéíóúñü]+){1,3})\b"
    for n in re.findall(patron_lista, txt):
        ents.append(n.strip())

    # 3. REGLA DE HERMANOS MEJORADA (Evita unir municipios)
    patron_hermanos = r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+)?)\s+[yeY]\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+){1,3})\b"
    for match in re.finditer(patron_hermanos, txt):
        h1, h2 = match.group(1), match.group(2)
        p2 = h2.split()
        if len(p2) >= 2: 
            ents.extend([f"{h1} {' '.join(p2[-2:])}", h2]) 

    # 4. Spacy para reconocimiento de entidades
    for e in nlp(txt).ents:
        if e.label_ == "PER":
            n_crudo = re.sub(r"(?i)^(los\s+hermanos\s+|los\s+se[ñn]ores\s+|el\s+se[ñn]or\s+|la\s+se[ñn]ora\s+)", "", e.text.strip().replace("\n", " "))
            ents.append(n_crudo)

    # 🛑 5. FILTROS DE CONTEXTO REFORZADOS (Para descartar lugares y víctimas)
    triggers_victima = ["asesinato de", "homicidio de", "muerte de", "victima", "víctima", "golpeaban a", "intimidaban a", "pertenencias de", "claves de"]
    triggers_lugar = ["barrio", "vereda", "municipio", "sector", "ciudad", "entre", "desde", "hacia", "en el", "en la"]
    salvavidas = ["capturado", "judicializado", "aseguramiento", "imputó", "responsables", "procesado", "detención", "flagrancia"]

    ents_filtradas = []
    for n in ents:
        n_cl = cl(n)
        # Filtro de lista negra y longitud
        if len(n_cl.split()) < 2 or any(re.search(rf"\b{x}\b", n_cl.lower()) for x in prohibidas):
            continue
            
        idx = txt.find(n)
        descartar = False
        if idx != -1:
            ctx_antes = txt[max(0, idx-100):idx].lower()
            
            # Bloqueo por lugar (Ej: "Entre Mosquera y...")
            if any(re.search(rf"\b{l}\b", ctx_antes) for l in triggers_lugar) and not any(s in ctx_antes for s in salvavidas):
                descartar = True
            
            # Bloqueo por víctima
            if any(v in ctx_antes for v in triggers_victima):
                descartar = True
        
        if not descartar:
            ents_filtradas.append(n_cl)

    # Deduplicación inteligente
    final_set = set()
    sorted_ents = sorted(list(set(ents_filtradas)), key=len, reverse=True)
    for nombre in sorted_ents:
        if not any(nombre in otro for otro in final_set):
            final_set.add(nombre)

    return final_set, dels_final

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
                        print(f" -> Extraído ({f_str}): {', '.join([cl(p) for p in pers])} | Delitos: {dels}")
                except Exception: pass
            pag += 1
        except Exception as e: 
            print(f"Error en página {pag}: {e}"); break
            
    return pd.DataFrame(datos_extraidos) if datos_extraidos else pd.DataFrame()

# ==========================================
# 🕵️‍♂️ PARTE 2: EL MOTOR DE CRUCE ESTRICTO
# ==========================================
def limpiar_texto(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().strip()
    return re.sub(r"[^A-Z0-9\s]", "", "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"))

def buscar_coincidencia_rapida(df_contrapartes, nombre_noticia):
    palabras_noticia = limpiar_texto(nombre_noticia).split() 
    if len(palabras_noticia) < 2: return pd.DataFrame() 

    def coincide_con_orden(palabras_db):
        if len(palabras_db) < 2: return False
        corta, larga = (palabras_noticia, palabras_db) if len(palabras_noticia) <= len(palabras_db) else (palabras_db, palabras_noticia)
        # Verifica orden estricto de izquierda a derecha
        iterador_larga = iter(larga)
        return all(palabra in iterador_larga for palabra in corta)

    mask = df_contrapartes['PALABRAS_LISTA'].apply(coincide_con_orden)
    return df_contrapartes[mask]

# ==========================================
# 🚀 PARTE 3: EJECUCIÓN MAESTRA
# ==========================================
def ejecutar_pipeline():
    columnas_finales = ['DOCUMENTO', 'PAY_ID', 'NIVEL DE ALERTA', 'CONTRAPARTE (BD)', 'ACUSADO (NOTICIA)', '% DE COINCIDENCIA', 'FECHA', 'DELITO', 'URL_NOTICIA']
    
    df_noticias = extraer_noticias()
    if df_noticias.empty:
        print("\n✅ Proceso Terminado. No se encontraron noticias hoy.")
        try:
            pd.DataFrame(columns=columnas_finales).to_excel(NOMBRE_EXCEL_SALIDA, index=False)
        except: pass
        return

    print(f"\nIntentando descargar Base de Contrapartes...")
    archivo_temporal = "Contrapartes_Temp.parquet"
    
    try:
        session = requests.Session()
        URL = f"https://drive.google.com/uc?export=download&id={ID_DRIVE}"
        response = session.get(URL, stream=True, verify=False)
        
        # Saltador de aviso de virus de Google Drive
        if 'text/html' in response.headers.get('Content-Type', ''):
            match = re.search(r'confirm=([a-zA-Z0-9_-]+)', response.text)
            if match:
                response = session.get(URL, params={'confirm': match.group(1)}, stream=True, verify=False)
        
        if response.status_code == 200:
            with open(archivo_temporal, 'wb') as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk: f.write(chunk)
            
            df_base = pd.read_parquet(archivo_temporal)
            df_base["NOMBRE"] = df_base["NOMBRE"].astype(str).apply(limpiar_texto)
            df_base["PALABRAS_LISTA"] = df_base["NOMBRE"].str.split()
        else: return

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    hallazgos_totales = []
    print(f"\nIniciando cruce estricto de {len(df_noticias)} nombres...")
    
    for index, row in df_noticias.iterrows():
        nombre_buscar = str(row["NOMBRE"]).strip()
        coincidencias = buscar_coincidencia_rapida(df_base, nombre_buscar)
        
        if not coincidencias.empty:
            for _, c_row in coincidencias.iterrows():
                palabras_n = nombre_buscar.split()
                palabras_c = c_row["PALABRAS_LISTA"]
                max_len = max(len(palabras_n), len(palabras_c))
                min_len = min(len(palabras_n), len(palabras_c))
                
                porcentaje_raw = (min_len / max_len) * 100
                
                hallazgos_totales.append({
                    'DOCUMENTO': c_row.get("DOCUMENTO", "NO DISPONIBLE"),
                    'PAY_ID': c_row.get("PAY_ID", "NO DISPONIBLE"),
                    'NIVEL DE ALERTA': f"ALERTA ({min_len} Palabras)",             
                    'CONTRAPARTE (BD)': c_row["NOMBRE"],
                    'ACUSADO (NOTICIA)': nombre_buscar,
                    '% DE COINCIDENCIA': f"{round(porcentaje_raw, 2)}%",
                    'FECHA': row.get("FECHA", ""),
                    'DELITO': row.get("DELITO", ""),
                    'URL_NOTICIA': row.get("URL_NOTICIA", ""),
                    '_sort': porcentaje_raw
                })

    if hallazgos_totales:
        df_final = pd.DataFrame(hallazgos_totales).sort_values(by='_sort', ascending=False).drop(columns='_sort')
        df_final.to_excel(NOMBRE_EXCEL_SALIDA, index=False)
        print(f"\n✅ Terminado. Se encontraron {len(hallazgos_totales)} alertas.")
    else:
        pd.DataFrame(columns=columnas_finales).to_excel(NOMBRE_EXCEL_SALIDA, index=False)
        print("\n✅ Terminado. Sin hallazgos.")
            
    if os.path.exists(archivo_temporal): os.remove(archivo_temporal)

if __name__ == "__main__":
    ejecutar_pipeline()
