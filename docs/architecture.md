# Arquitectura: pipeline Saber 11 Bogotá

Fase 2 del proceso Nexcraft.

## Forma

Pipeline batch en Python 3.12 con un solo proceso y un solo comando. No expone HTTP: las reglas de rutas
del canon (autenticación, rate limit, endpoint de salud) **no aplican**. Lo demás sí:
arquitectura por capas, TDD, contrato de errores, configuración por entorno e imagen no-root.

```
saber11/
  configs/pipeline/pipeline_config.py        # typed settings from env, validated once
  core/errors/pipeline_errors.py             # PipelineError + domain sentinels
  models/dataset/dataset_models.py           # canonical columns, groups, labels
  models/analysis/*_models.py                # result dataclasses (the contract between layers)
  models/spatial/spatial_models.py
  models/report/report_models.py             # PipelineResults: everything the PDF needs
  repositories/socrata/socrata_repository.py # datos.gov.co API (paging, retries, token)
  repositories/dataicfes/dataicfes_repository.py  # flat file reader (chunked, delimiter sniffing)
  repositories/directory/school_directory_repository.py  # SED directory (CKAN latest GeoJSON)
  services/ingestion/ingestion_service.py    # Bogotá population, departments, sample
  services/descriptive/descriptive_service.py
  services/assumptions/assumptions_service.py   # Mahalanobis, Mardia, Box's M
  services/inference/manova_service.py       # MANOVA (Pillai, Wilks, Hotelling-Lawley, Roy)
  services/inference/hotelling_service.py    # pairwise Hotelling T² (Bonferroni)
  services/pca/pca_service.py                # PCA on correlation + CP1 ANOVA
  services/spatial/spatial_service.py        # department ranking, locality join
  services/spatial/locality_test_service.py  # Shapiro-Wilk -> ANOVA / Welch / Kruskal-Wallis
  services/groups/shift_groups.py           # per-shift matrices and within-shift residuals
  services/sensitivity/sensitivity_service.py # MANOVA without outliers and public schools only
  services/conclusions/conclusions_service.py # narrative findings from results
  renderers/report/pdf_renderer.py           # ReportLab: tables, text and figures
  renderers/charts/*_charts.py               # matplotlib, fixed color per shift, PNG bytes
  pipelines/run/run_pipeline.py              # orchestration, writes outputs
  __main__.py                                # CLI: python -m saber11 run
tests/  (mirrors saber11/)
```

## Decisiones

| Decisión | Elegida | Descartadas y por qué |
|---|---|---|
| Lenguaje | Python 3.12 (instalado, cumple el piso) | R: el equipo trabaja en Colab y Python |
| Binding | `engineering-canon` con `derived_from: fastapi-senior` | `fastapi-senior` completo: no hay API HTTP |
| MANOVA | `statsmodels.MANOVA` | Implementación propia: más riesgo sin beneficio |
| Mardia, Box M, Hotelling | Implementación propia con numpy/scipy, verificada por pruebas | `pingouin`: dependencia pesada y Box M sin corrección uniforme |
| PCA | Eigen-descomposición de la matriz de correlación (numpy) | sklearn sobre datos estandarizados: equivalente, pero con menos control de las cargas |
| PDF | ReportLab (tablas y texto) + matplotlib (gráficos a color con paleta validada para daltonismo; cada jornada siempre con el mismo color; incrustados como PNG) | WeasyPrint: requiere librerías de sistema; LaTeX: pesado en la imagen |
| Datos 2025 | Archivo local de DataIcfes con adaptador | Las tablas públicas del Icfes son agregadas, sin jornada: no sirven para MANOVA |
| Directorio de colegios | API CKAN → recurso GeoJSON más reciente | URL fija del xlsx: ya dio 404 |
| Localidad | `COD_LOCA` del directorio + catálogo oficial de 20 localidades | Nombres normalizados: frágiles |
| Registros repetidos | Un registro por `estu_consecutivo` (el periodo 20224 de la API trae 1.065.888 filas y 532.792 estudiantes; las copias son idénticas). En la API, los departamentos cuentan `count(distinct estu_consecutivo)` | Contar filas: duplica las poblaciones |
| Ranking de departamentos | Mismos filtros que Bogotá (4 jornadas, sin puntajes faltantes, estudiantes únicos) | Todas las filas: mezcla Noche y Sabatina, que se excluyen en Bogotá |
| Atípicos y Mardia | Se reportan dos versiones: la de la guía (covarianza total, reproduce sus 15 atípicos) y la intra-jornada (residuos y covarianza combinada, que es el supuesto del MANOVA) | Solo la de la guía: confunde diferencias entre jornadas con no normalidad |
| Naturaleza del colegio | Sensibilidad: MANOVA y Hotelling con muestra estratificada solo de colegios oficiales; tabla de % privados por jornada | Ignorarla: Completa es ~99 % privada, el efecto de jornada queda confundido |
| Sensibilidad a atípicos | MANOVA repetido sin los atípicos intra-jornada | Eliminarlos del análisis principal: cambia la muestra de la guía |
| Prueba entre localidades | Shapiro-Wilk por localidad (Bonferroni); normal + Levene no rechaza → ANOVA; normal + Levene rechaza → ANOVA de Welch; no normal → Kruskal-Wallis. α de la configuración | ANOVA clásico con varianzas distintas: infla el error tipo I |
| Lectura DataIcfes | Codificación detectada (UTF-8 o Latin-1, o `SABER11_DATAICFES_ENCODING`); el separador `¬` se cambia por `\x1f` al leer para usar el parser C (~27 veces más rápido) | `engine="python"`: muy lento con millones de filas |
| Salidas | Se escriben con sufijo `.tmp` y se mueven al final: si algo falla no quedan archivos a medias | Escritura directa: deja `results.json` sin PDF |
| CLI | stdout solo lleva la ruta del PDF; las etapas y los errores van a stderr; `SABER11_DEBUG=1` muestra el traceback | Mezclar logs JSON y la ruta en stdout |

## Configuración (variables de entorno)

| Variable | Defecto | Uso |
|---|---|---|
| `SABER11_SOURCE` | `api` | `api` o `dataicfes` |
| `SABER11_PERIOD` | `20224` | Periodo (texto) |
| `SABER11_DATAICFES_PATH` | — | Obligatoria si la fuente es `dataicfes` |
| `SABER11_DATAICFES_ENCODING` | — | Codificación del archivo; si falta se detecta (UTF-8 o Latin-1) |
| `SABER11_DIRECTORY_PATH` | — | GeoJSON local del directorio de colegios |
| `SABER11_DEBUG` | — | Con `1`, muestra el traceback de errores inesperados |
| `SABER11_SAMPLE_PER_GROUP` | `100` | Tamaño por jornada |
| `SABER11_SEED` | `123` | Semilla |
| `SABER11_OUTPUT_DIR` | `output` | Carpeta de salida |
| `SOCRATA_APP_TOKEN` | — | Token opcional de datos.gov.co |

## Entregables

| ID | Entregable | Aceptación |
|---|---|---|
| D-01 | Config y errores | Falla al arrancar si `dataicfes` no tiene ruta; pruebas |
| D-02 | Repositorio Socrata | Pagina, reintenta 429/5xx, filtra con comillas; pruebas con transporte falso |
| D-03 | Repositorio DataIcfes | Detecta delimitador, normaliza columnas a minúsculas, filtra periodo y Bogotá por bloques |
| D-04 | Repositorio de directorio | Resuelve el recurso GeoJSON más reciente vía CKAN; devuelve dane_sede, dane_est, cod_localidad |
| D-05 | Ingesta y muestra | Población Bogotá limpia + muestra estratificada reproducible |
| D-06 | Descriptivo | Coincide con pandas en la fixture |
| D-07 | Supuestos | Fixture 2022: 15 atípicos (método de la guía); Box p ≈ 0,238; Mardia rechaza; versión intra-jornada inmune a diferencias de medias |
| D-08 | MANOVA + ANOVAs | Fixture 2022: Pillai ≈ 0,202; η² ≈ 0,067 |
| D-09 | Hotelling por pares | Fixture 2022: Completa difiere de las otras 3 (p_bonf < 0,001) y las otras 3 no difieren entre sí |
| D-10 | PCA + ANOVA CP1 | Fixture 2022: CP1 ≈ 76,5 %, cargas entre 0,84 y 0,91 |
| D-11 | Espacial | Ranking de departamentos; tabla de localidades con tasa de cruce |
| D-12 | Conclusiones | Texto derivado de los resultados, sin números escritos a mano |
| D-13 | Informe PDF | Abre; tablas en blanco y negro y gráficos a color, Arial (o Liberation Sans), texto justificado, sin nombres de participantes; portada, método breve, descriptivo, supuestos, explicativo, sensibilidad, espacial, conclusiones y fuentes |
| D-14 | Orquestación + CLI | `python -m saber11 run` produce CSV, JSON y PDF |
| D-15 | Imagen Docker | Construye, no-root, salida por volumen; sin HEALTHCHECK porque es un proceso batch que termina |
| D-16 | README | Instalación, configuración, cómo obtener los datos de DataIcfes, ejecución, resultados |

## Imagen

Una sola imagen (`saber11-pipeline`) porque es un solo proceso batch. No publica puertos.
