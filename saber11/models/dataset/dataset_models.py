"""Canonical dataset vocabulary shared by every layer."""

PERIOD = "periodo"
STUDENT_ID = "estu_consecutivo"
DEPARTMENT = "cole_depto_ubicacion"
SHIFT = "cole_jornada"
DANE_SITE = "cole_cod_dane_sede"
DANE_SCHOOL = "cole_cod_dane_establecimiento"
NATURE = "cole_naturaleza"
LOCALITY = "localidad"
OFFICIAL = "OFICIAL"

SCORES = (
    "punt_matematicas",
    "punt_lectura_critica",
    "punt_c_naturales",
    "punt_sociales_ciudadanas",
    "punt_ingles",
)

SCORE_LABELS = {
    "punt_matematicas": "Matemáticas",
    "punt_lectura_critica": "Lectura Crítica",
    "punt_c_naturales": "Ciencias Naturales",
    "punt_sociales_ciudadanas": "Sociales y Ciudadanas",
    "punt_ingles": "Inglés",
}

SCORE_SHORT_LABELS = {
    "punt_matematicas": "Mat.",
    "punt_lectura_critica": "Lect.",
    "punt_c_naturales": "Nat.",
    "punt_sociales_ciudadanas": "Soc.",
    "punt_ingles": "Ing.",
}

# Shifts compared in the study; NOCHE and SABATINA (adult education) are excluded.
SHIFTS = ("COMPLETA", "MAÑANA", "TARDE", "UNICA")

SHIFT_LABELS = {"COMPLETA": "Completa", "MAÑANA": "Mañana", "TARDE": "Tarde", "UNICA": "Única"}

# The source repeats some students; STUDENT_ID lets ingestion keep one row per student.
STUDENT_COLUMNS = (PERIOD, STUDENT_ID, DEPARTMENT, SHIFT, DANE_SITE, DANE_SCHOOL, NATURE, *SCORES)

# Official codes of Bogotá's 20 localities (COD_LOCA in the SED school directory).
LOCALITIES = {
    "01": "Usaquén", "02": "Chapinero", "03": "Santa Fe", "04": "San Cristóbal",
    "05": "Usme", "06": "Tunjuelito", "07": "Bosa", "08": "Kennedy",
    "09": "Fontibón", "10": "Engativá", "11": "Suba", "12": "Barrios Unidos",
    "13": "Teusaquillo", "14": "Los Mártires", "15": "Antonio Nariño",
    "16": "Puente Aranda", "17": "La Candelaria", "18": "Rafael Uribe Uribe",
    "19": "Ciudad Bolívar", "20": "Sumapaz",
}
