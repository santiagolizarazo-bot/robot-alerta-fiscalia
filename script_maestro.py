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
# 1. Tu ID del archivo Parquet en Google Drive
ID_DRIVE = "17YlH0VZrW-j6mseo_411eZYjJVXHrFh2" 
RUTA_BASE_NUBE = f'https://drive.google.com/uc?id={ID_DRIVE}'

# 2. La URL de tu Webhook en n8n
URL_N8N = "https://n8n.ops.dev.rappipay.com/webhook/alerta-fiscalia"

# ==========================================
# 🧠 PARTE 1: EL MOTOR DE EXTRACCIÓN (SCRAPING)
# ==========================================
print("🔥 INICIANDO SÚPER ROBOT: EXTRACCIÓN + CRUCE AUTOMÁTICO 🔥")
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
    "mes", "meses", "dia", "dias", "hora", "horas"
]

def analizar_noticia(txt):
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

    dels = re.findall(r"(?:(?:el\s+|los\s+)?delito[s]?(?:\s+de)?|presunta\s+participaci[oó]n(?:\s+en)?|responsable\s+de)\s+([^\.]+)", txt, re.I)
    return {p for p in pers_finales if len(p.split()) >= 2}, cl(", ".join(d.strip() for d in dels)) if dels else "DELITO NO ESPECIFICADO"

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
                        for p in pers: datos_extraidos.append({'FECHA': cl(fecha.strftime('%Y-%m-%d')), 'NOMBRE': cl(p), 'DELITO': dels})
                        print(f" -> ¡EXTRAÍDO! ({f_str}): {', '.join([cl(p) for p in pers])}")
                except Exception: pass
            pag += 1
        except Exception as e: 
            print(f"Error en página {pag}: {e}"); break
            
    return pd.DataFrame(datos_extraidos) if datos_extraidos else pd.DataFrame()

# ==========================================
# 🕵️‍♂️ PARTE 2: EL MOTOR DE CRUCE
# ==========================================
def limpiar_texto(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().strip()
    return re.sub(r"[^A-Z0-9\s]", "", "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"))

def buscar_coincidencia(df_contrapartes, nombre_noticia):
    palabras_noticia = limpiar_texto(nombre_noticia).split() 
    if len(palabras_noticia) < 2: return pd.DataFrame() 

    def coincide_ordenado(nombre_db):
        if pd.isna(nombre_db): return False
        palabras_db = str(nombre_db).split()
        if len(palabras_db) < 2: return False
        
        corta, larga = (palabras_noticia, palabras_db) if len(palabras_noticia) <= len(palabras_db) else (palabras_db, palabras_noticia)
        iterador = iter(larga)
        return all(palabra in iterador for palabra in corta)

    return df_contrapartes[df_contrapartes["NOMBRE"].apply(coincide_ordenado)]

# ==========================================
# 🚀 PARTE 3: EJECUCIÓN MAESTRA (REFORZADA)
# ==========================================
def ejecutar_pipeline():
    # 1. Extracción (En Memoria)
    df_noticias = extraer_noticias()
    if df_noticias.empty:
        print("\n✅ Proceso Terminado. No se encontraron noticias válidas hoy.")
        return

    # 2. Descargar Parquet desde Drive (Versión reforzada)
    print(f"\nIntentando descargar Base de Contrapartes desde Google Drive...")
    
    # Ruta temporal donde guardaremos el archivo
    archivo_temporal = "Contrapartes_Temp.parquet"
    
    try:
        # Usamos una sesión para manejar posibles cookies de seguridad de Google
        session = requests.Session()
        
        # Primero hacemos una petición para ver si hay aviso de virus (archivos grandes)
        response = session.get(RUTA_BASE_NUBE, params={'confirm': 't'}, stream=True, verify=False)
        
        # Si la respuesta es exitosa (200), guardamos el contenido
        if response.status_code == 200:
            with open(archivo_temporal, 'wb') as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
            print("✅ Descarga completada.")
        else:
            print(f"❌ Error en la descarga. Código de estado: {response.status_code}")
            return

        # 3. Leer el archivo descargado
        if os.path.exists(archivo_temporal):
            print("Leyendo archivo Parquet...")
            df_base = pd.read_parquet(archivo_temporal)
            df_base["NOMBRE"] = df_base["NOMBRE"].astype(str).apply(limpiar_texto)
        else:
            print("❌ El archivo no se encontró en el disco después de la descarga.")
            return

    except Exception as e:
        print(f"❌ Error crítico en el proceso de descarga/lectura: {e}")
        return

    # 4. Cruce de Datos
    hallazgos_totales = []
    print(f"\nIniciando cruce de {len(df_noticias)} nombres extraídos...")
    
    for index, row in df_noticias.iterrows():
        nombre_buscar = str(row["NOMBRE"]).strip()
        print(f"Buscando: {nombre_buscar}...")
        coincidencias = buscar_coincidencia(df_base, nombre_buscar)
        
        if not coincidencias.empty:
            print(f"  [!] ALERTA ROJA: {len(coincidencias)} posibles contrapartes encontradas.")
            for _, coincidencia_row in coincidencias.iterrows():
                hallazgos_totales.append({
                    'Nombre_Buscado_Noticia': nombre_buscar,
                    'Contraparte_Encontrada': coincidencia_row["NOMBRE"]
                })

    # Guardamos resultados si existen
    if hallazgos_totales:
        pd.DataFrame(hallazgos_totales).to_excel("Cruce_Resultados.xlsx", index=False)
        print(f"\n[OK] Cruce terminado. Se encontraron {len(hallazgos_totales)} alertas.")
    else:
        print("\n[OK] Cruce terminado. Excelente, ninguna contraparte apareció en las noticias.")

    # 5. Envío a n8n
    datos_para_n8n = {
        "fecha": pd.Timestamp.now().strftime('%Y-%m-%d'),
        "alertas_encontradas": len(hallazgos_totales) > 0,
        "total_alertas": len(hallazgos_totales),
        "lista_hallazgos": hallazgos_totales
    }

    try:
        print("\nEnviando reporte a n8n...")
        res_n8n = requests.post(URL_N8N, json=datos_para_n8n, verify=False)
        if res_n8n.status_code == 200:
            print("🚀 ¡Reporte atrapado por n8n con éxito!")
        else:
            print(f"⚠️ n8n respondió con código: {res_n8n.status_code}")
    except Exception as e:
        print(f"❌ No se pudo conectar con n8n: {e}")
        
    # Limpieza final
    if os.path.exists(archivo_temporal):
        try:
            os.remove(archivo_temporal)
        except:
            pass

if __name__ == "__main__":
    ejecutar_pipeline()
