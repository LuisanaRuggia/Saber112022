# Requisitos: pipeline Saber 11 Bogotá

Fase 1 del proceso Nexcraft. Fecha: 2026-11-06.

## Problema

Comparar el rendimiento en las cinco pruebas del Saber 11 (Matemáticas, Lectura Crítica,
Ciencias Naturales, Sociales y Ciudadanas, Inglés) entre las jornadas Completa, Mañana,
Tarde y Única en Bogotá. El periodo objetivo es el más reciente con microdatos por estudiante
(2025, de DataIcfes). La salida es un informe PDF reproducible, generado por un pipeline de
datos y sin figuras.

## Actores

- **Analista** (equipo: Juan Sebastián Rueda, David Florez, Luisana Gutiérrez Ruggia): ejecuta el
  pipeline y usa el informe para armar el póster.
- **Fuentes externas**: API Socrata de datos.gov.co, archivo plano de DataIcfes, directorio de
  colegios de Datos Abiertos Bogotá y GeoJSON de localidades.

## Historias de usuario

| ID | Historia | Criterio de aceptación |
|---|---|---|
| HU-01 | Como analista, quiero ingerir el periodo elegido desde la API o desde un archivo de DataIcfes | `SABER11_SOURCE=api` descarga Bogotá por páginas; `SABER11_SOURCE=dataicfes` lee el .txt/.csv (delimitador `¬`, `\|`, `;` o `,`) y deja el mismo esquema canónico |
| HU-02 | Como analista, quiero una muestra reproducible | 100 estudiantes por jornada (Completa, Mañana, Tarde, Única) con semilla 123, ambos configurables, guardada como CSV |
| HU-03 | Como analista, quiero el análisis descriptivo | Tamaño por grupo, vector de medias, desviaciones, covarianzas y correlaciones (muestra), además de medias de la población por jornada |
| HU-04 | Como analista, quiero validar los supuestos | Atípicos por Mahalanobis (χ² al 97,5 %), normalidad multivariada de Mardia (asimetría y curtosis) y M de Box |
| HU-05 | Como analista, quiero el análisis explicativo | MANOVA (Pillai, Wilks, Hotelling-Lawley, Roy; η² parcial con Pillai), ANOVA por prueba con Bonferroni, T² de Hotelling por pares con Bonferroni, PCA sobre la matriz de correlación y ANOVA del CP1 por jornada |
| HU-06 | Como analista, quiero el análisis espacial | Ranking de departamentos (n ≥ 30) por promedio de Matemáticas + Lectura y por las 5 pruebas; resultados por localidad de Bogotá cruzando por código DANE con el directorio vigente y tasa de cruce |
| HU-07 | Como analista, quiero un informe PDF | El PDF tiene portada, metodología, secciones descriptiva, de supuestos, explicativa y espacial, conclusiones redactadas a partir de los resultados y fuentes; solo tablas y texto |
| HU-08 | Como analista, quiero ejecutar todo con un comando | `python -m saber11 run` (o `docker run`) produce CSV, `results.json` y el PDF en `output/<periodo>/` |

## Requisitos no funcionales

| ID | Requisito | Meta |
|---|---|---|
| RNF-01 | Reproducibilidad | Misma entrada y semilla producen los mismos números |
| RNF-02 | Corrección estadística | Con la muestra 2022 de la guía (`tests/fixtures`) se reproducen: Pillai 0,202; η² 0,067; Box p 0,238; 15 atípicos; CP1 76,5 % |
| RNF-03 | Robustez de red | Reintentos con espera ante 429/5xx; token de Socrata opcional (`SOCRATA_APP_TOKEN`) |
| RNF-04 | Memoria | El archivo de DataIcfes se lee por bloques, filtrando Bogotá y las columnas necesarias |
| RNF-05 | Calidad | TDD con pytest; archivos ≤ 200 líneas; funciones ≤ 30 líneas; código y comentarios en inglés |
| RNF-06 | Portabilidad | Imagen Docker no-root, base `python:3.12-slim` |

## Reglas de negocio

- El campo `periodo` es texto en la API: se filtra con comillas (`periodo='20224'`).
- Bogotá se identifica con `upper(cole_depto_ubicacion) like '%BOGOT%'`.
- Se excluyen las jornadas Noche y Sabatina (educación de adultos) y las filas con puntajes faltantes.
- El cruce espacial usa el código DANE de 12 dígitos (sede y, si no aparece, establecimiento), no el DIVIPOLA.
- Corrección de Bonferroni: α = 0,05 dividido por el número de comparaciones.

## Supuestos y restricciones

- Los microdatos 2025 requieren registro en DataIcfes. Mientras llega el archivo, el pipeline
  se valida con 2022 (API). El periodo se elige por configuración, sin cambiar el código.
- No se generan figuras (decisión de la usuaria); el póster se arma aparte.
- Cualquier prueba estadística que no esté en la guía se consulta antes de agregarla.

## Backlog priorizado (MoSCoW)

- **Must:** HU-01 a HU-08.
- **Must (aprobado el 2026-11-06):** comparación entre localidades: Shapiro-Wilk por localidad; ANOVA si se cumple la normalidad, Kruskal-Wallis si no.
- **Could:** I de Moran (autocorrelación espacial); no solicitado.
- **Won't (ahora):** figuras y póster.
