# Saber 11 Bogotá: rendimiento por jornada

Pipeline de datos que compara el rendimiento en las cinco pruebas del Saber 11 (Matemáticas,
Lectura Crítica, Ciencias Naturales, Sociales y Ciudadanas, Inglés) entre las jornadas
**Completa, Mañana, Tarde y Única** en Bogotá. Hace la ingesta, el análisis descriptivo, el
explicativo (MANOVA y PCA) y el espacial, y genera un **informe PDF** con los resultados y las
conclusiones (solo tablas y texto, sin figuras).

**Integrantes:** Juan Sebastián Rueda, David Florez, Luisana Gutiérrez Ruggia.

## Qué hace

```
ingesta ─► descriptivo ─► supuestos ─► MANOVA + ANOVA ─► Hotelling ─► PCA ─► espacial ─► sensibilidad ─► conclusiones ─► PDF
```

| Etapa | Contenido |
|---|---|
| Ingesta | Estudiantes de Bogotá del periodo elegido (API de datos.gov.co o archivo de DataIcfes), un registro por estudiante (`estu_consecutivo`: la fuente repite filas), sin Noche ni Sabatina y sin puntajes faltantes. Muestra estratificada de 100 por jornada (semilla 123). Promedios de todos los departamentos con los mismos filtros. |
| Descriptivo | Tamaño por grupo, medias y desviaciones por jornada (muestra y población), matrices de covarianzas y correlaciones. |
| Supuestos | Atípicos por distancia de Mahalanobis (χ² al 97,5 %), normalidad multivariada de Mardia (global y por jornada) y M de Box. Mahalanobis y Mardia también sobre los residuos dentro de cada jornada. |
| Explicativo | MANOVA (Pillai, Wilks, Hotelling-Lawley, Roy; η² parcial), ANOVA por prueba con Bonferroni, T² de Hotelling por pares con Bonferroni, PCA sobre la matriz de correlaciones y ANOVA del CP1. |
| Sensibilidad | MANOVA sin los atípicos intra-jornada, y MANOVA y T² de Hotelling solo con colegios oficiales (la jornada Completa es casi toda privada), con la tabla de % de privados por jornada. |
| Espacial | Ranking de los departamentos (n ≥ 30) por Matemáticas + Lectura y resultados por localidad de Bogotá, cruzando el código DANE con el directorio de colegios de la SED. Comparación entre localidades (muestra de hasta 100 por localidad): Shapiro-Wilk por localidad con Bonferroni; si se cumple la normalidad se usa ANOVA (η²), o ANOVA de Welch si Levene rechaza la igualdad de varianzas, y si no, Kruskal-Wallis (ε²), para el promedio de las 5 pruebas y para cada prueba. |
| Informe | `informe_saber11_<periodo>.pdf` con portada, metodología, resultados, conclusiones y fuentes. |

## Requisitos

- Python 3.12 y [uv](https://docs.astral.sh/uv/), o Docker.

## Uso rápido (periodo 2022, sin registro)

```bash
uv sync
uv run python -m saber11 run
```

Las salidas quedan en `output/<periodo>/`:

```
output/20224/
  informe_saber11_20224.pdf
  results.json                       # todos los números del informe
  data/muestra_saber11_20224.csv
  data/bogota_resumen_jornada_20224.csv
  data/departamentos_saber11_20224.csv
  data/localidades_saber11_20224.csv
```

## Configuración

Todo se configura con variables de entorno:

| Variable | Defecto | Descripción |
|---|---|---|
| `SABER11_SOURCE` | `api` | `api` (datos.gov.co) o `dataicfes` (archivo local) |
| `SABER11_PERIOD` | `20224` | Periodo: año + semestre (por ejemplo, `20252`) |
| `SABER11_DATAICFES_PATH` | | Ruta del archivo de DataIcfes (obligatoria si la fuente es `dataicfes`) |
| `SABER11_DATAICFES_ENCODING` | | Codificación del archivo de DataIcfes. Si no se indica, se detecta (UTF-8 o Latin-1) |
| `SABER11_DIRECTORY_PATH` | | GeoJSON local del directorio de colegios. Si no se indica, se descarga la versión más reciente |
| `SABER11_SAMPLE_PER_GROUP` | `100` | Estudiantes por jornada en la muestra |
| `SABER11_SEED` | `123` | Semilla del muestreo |
| `SABER11_OUTPUT_DIR` | `output` | Carpeta de salida |
| `SOCRATA_APP_TOKEN` | | Token opcional de datos.gov.co (evita el error 429) |
| `SABER11_DEBUG` | | Con `1`, muestra el traceback de un error inesperado |

La salida estándar solo trae la ruta del PDF; el avance por etapas (JSON por línea) y los errores van a la
salida de error. Los archivos se escriben al final: si algo falla, no quedan salidas a medias.

## Periodo del proyecto

El proyecto usa **2022-2** (`20224`): es el periodo más reciente con microdatos por estudiante en
datos abiertos, y todo se descarga sin registro. El informe lo justifica en la metodología.

## Datos 2023 en adelante (DataIcfes)

La API abierta de datos.gov.co solo llega hasta **2022-2** (`20224`). Los microdatos por estudiante
de 2023, 2024 y 2025 se obtienen en **DataIcfes**:

1. Registrarse en <https://www.icfes.gov.co/data-icfes/> ("Regístrate al DataIcfes"). Las
   credenciales llegan por correo.
2. Descargar la base de **Saber 11** del periodo deseado (por ejemplo, 2025-2) y descomprimirla.
3. Ejecutar:

```bash
SABER11_SOURCE=dataicfes \
SABER11_PERIOD=20252 \
SABER11_DATAICFES_PATH=~/Descargas/Examen_Saber_11_20252.txt \
uv run python -m saber11 run
```

El lector detecta el delimitador (`¬`, `|`, `;` o `,`) y la codificación (UTF-8 o Latin-1), pasa los
nombres de columna a minúsculas y lee el archivo por bloques.

## Directorio de colegios

El enlace al Excel del directorio que usaba el notebook original ya no existe (404). El pipeline
consulta la API CKAN de Datos Abiertos Bogotá y usa el GeoJSON más reciente (`DANE12_SED`,
`DANE12_EST`, `COD_LOCA`). Si el servidor rechaza la descarga, se puede bajar el archivo a mano e
indicarlo en `SABER11_DIRECTORY_PATH`:

```bash
curl -L -o data/colegios092026.geojson "https://datosabiertos.bogota.gov.co/dataset/d451b52f-e30c-43b3-9066-3a7816638fea/resource/4cb45e38-779b-483b-acc4-5673c5db9505/download/colegios092026.geojson"
SABER11_DIRECTORY_PATH=data/colegios092026.geojson uv run python -m saber11 run
```

Sin directorio, el informe sale igual pero sin la tabla por localidad.

## Docker

```bash
docker build -t saber11-pipeline .
docker run --rm \
  -v "$PWD/output:/app/output" \
  -v "$PWD/data:/data:ro" \
  -e SABER11_DIRECTORY_PATH=/data/colegios092026.geojson \
  saber11-pipeline run
```

Para DataIcfes se pone el archivo en `data/` y se agrega
`-e SABER11_SOURCE=dataicfes -e SABER11_PERIOD=20252 -e SABER11_DATAICFES_PATH=/data/<archivo>`.
La imagen corre con un usuario sin privilegios y no expone puertos: es un proceso batch.

## Pruebas

```bash
uv run pytest -q                  # pruebas unitarias, sin red
uv run pytest -q -m network       # pruebas contra las fuentes reales
```

`tests/fixtures/muestra_saber11_20224.csv` es la muestra 2022 de la guía original. Las pruebas
comprueban que el pipeline reproduce sus resultados: Pillai 0,202; η² parcial 0,067; M de Box
p = 0,238; 15 atípicos (método de la guía); CP1 76,5 %. Esa muestra trae 2 filas repetidas porque la
guía la sacó de la fuente sin quitar duplicados; se deja tal cual para conservar la referencia.

## Estructura

```
saber11/
  configs/      configuración tipada desde el entorno
  core/         contrato de errores y formato de números en español
  models/       contratos de datos y resultados entre capas
  repositories/ fuentes: API Socrata, archivo DataIcfes, directorio de colegios
  services/     ingesta, descriptivo, supuestos, inferencia, PCA, espacial, sensibilidad, conclusiones
  renderers/    informe PDF (ReportLab)
  pipelines/    orquestación y escritura de salidas
docs/           arquitectura y decisiones
tests/          misma estructura que saber11/
```

## Fuentes

- Icfes, Resultados únicos Saber 11: <https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe>
- Icfes, DataIcfes: <https://www.icfes.gov.co/data-icfes/>
- Secretaría de Educación del Distrito, Colegios Bogotá D.C.: <https://datosabiertos.bogota.gov.co/dataset/colegios-bogota-d-c>
