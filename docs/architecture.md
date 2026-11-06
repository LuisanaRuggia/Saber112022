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
  services/inference/manova_service.py       # MANOVA + follow-up ANOVAs (Bonferroni)
  services/inference/hotelling_service.py    # pairwise Hotelling T² (Bonferroni)
  services/pca/pca_service.py                # PCA on correlation + CP1 ANOVA
  services/spatial/spatial_service.py        # department ranking, locality join
  services/conclusions/conclusions_service.py # narrative findings from results
  renderers/report/pdf_renderer.py           # ReportLab: tables + text, no figures
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
| PDF | ReportLab (tablas y texto) | WeasyPrint: requiere librerías de sistema; LaTeX: pesado en la imagen |
| Datos 2025 | Archivo local de DataIcfes con adaptador | Las tablas públicas del Icfes son agregadas, sin jornada: no sirven para MANOVA |
| Directorio de colegios | API CKAN → recurso GeoJSON más reciente | URL fija del xlsx: ya dio 404 |
| Localidad | `COD_LOCA` del directorio + catálogo oficial de 20 localidades | Nombres normalizados: frágiles |

## Configuración (variables de entorno)

| Variable | Defecto | Uso |
|---|---|---|
| `SABER11_SOURCE` | `api` | `api` o `dataicfes` |
| `SABER11_PERIOD` | `20224` | Periodo (texto) |
| `SABER11_DATAICFES_PATH` | — | Obligatoria si la fuente es `dataicfes` |
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
| D-07 | Supuestos | Fixture 2022: 15 atípicos; Box p ≈ 0,238; Mardia rechaza |
| D-08 | MANOVA + ANOVAs | Fixture 2022: Pillai ≈ 0,202; η² ≈ 0,067 |
| D-09 | Hotelling por pares | Fixture 2022: Completa difiere de las otras 3 (p_bonf < 0,001) y las otras 3 no difieren entre sí |
| D-10 | PCA + ANOVA CP1 | Fixture 2022: CP1 ≈ 76,5 %, cargas entre 0,84 y 0,91 |
| D-11 | Espacial | Ranking de departamentos; tabla de localidades con tasa de cruce |
| D-12 | Conclusiones | Texto derivado de los resultados, sin números escritos a mano |
| D-13 | Informe PDF | Abre, sin figuras, contiene todas las secciones de HU-07 |
| D-14 | Orquestación + CLI | `python -m saber11 run` produce CSV, JSON y PDF |
| D-15 | Imagen Docker | Construye, no-root, HEALTHCHECK (import del paquete), salida por volumen |
| D-16 | README | Instalación, configuración, cómo obtener los datos de DataIcfes, ejecución, resultados |

## Imagen

Una sola imagen (`saber11-pipeline`) porque es un solo proceso batch. No publica puertos.
