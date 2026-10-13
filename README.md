# Automatizador de Reportes de Ventas

Herramienta en Python que toma un CSV con datos de ventas, **detecta y descarta
filas incorrectas**, calcula indicadores clave y exporta reportes ejecutivos en
**Excel formateado** y **PDF**, junto con gráficas individuales en PNG.

## Características

| Funcionalidad | Detalle |
|---|---|
| Carga de CSV | Lee archivos UTF-8 con el esquema de columnas estándar |
| Validación de datos | Detecta 7 tipos de errores por fila (IDs duplicados, fechas inválidas, valores vacíos, numéricos negativos/cero, emails mal formados, productos ausentes) |
| Limpieza | Conserva solo filas válidas y devuelve las rechazadas con su motivo |
| KPIs | Ingresos totales, órdenes únicas, unidades, ticket medio, precio medio, período |
| Análisis | Por producto, categoría, región, vendedor, mes y top clientes |
| Gráficas | 5 imágenes PNG: serie mensual, top productos, pie de categorías, ventas por región, ranking de vendedores |
| Excel | 8 hojas con formato, KPIs, calidad de datos y todas las tablas |
| PDF | Portada con KPIs, motivos de rechazo, detalle por dimensión y todas las gráficas |
| CLI | Argumentos para archivo de entrada, salida, nombre de empresa, top-N, generar/saltar PDF |

## Requisitos

- Python 3.10+
- Dependencias: `pandas`, `openpyxl`, `matplotlib`, `reportlab`

```bash
pip install pandas openpyxl matplotlib reportlab
```

## Estructura del proyecto

```
.
├── sales_report_automator.py   # CLI principal (entry point)
├── validator.py                # Carga y validación del CSV
├── analytics.py                # Cálculo de KPIs y tablas de análisis
├── charts.py                   # Gráficas con matplotlib
├── excel_exporter.py           # Generador del Excel formateado
├── pdf_exporter.py             # Generador del PDF ejecutivo
├── data/
│   └── sample_sales_data.csv   # CSV de muestra (140 filas, 10 inválidas)
├── tests/
│   └── test_validator.py       # Tests unitarios del validador
└── output/                     # Reportes generados (se crea al ejecutar)
    ├── charts/                 # Gráficas PNG individuales
    ├── reporte_ventas.xlsx
    └── reporte_ventas.pdf
```

## Esquema esperado del CSV

Cabecera obligatoria (orden indiferente):

```
order_id, date, product, category, quantity, unit_price, region, seller, customer_email
```

Reglas de validación aplicadas:

1. `order_id` no vacío y único en el archivo
2. `date` en formato `YYYY-MM-DD`, `YYYY/MM/DD`, `DD/MM/YYYY` o `DD-MM-YYYY`
3. `product`, `region`, `seller`, `customer_email` no vacíos
4. `quantity` entero `> 0`
5. `unit_price` numérico `> 0`
6. `customer_email` con formato válido (regex)

Las filas que rompen alguna regla se descartan y se reportan en la hoja
`Resumen` del Excel y en la portada del PDF con su motivo.

## Uso

### Ejecución rápida con datos de muestra

```bash
python sales_report_automator.py -i data/sample_sales_data.csv -o output
```

### Opciones del CLI

```text
-i, --input        Ruta al CSV de ventas (obligatorio)
-o, --output       Carpeta de salida (por defecto: ./output)
--company          Título que aparece en la portada del PDF
--no-pdf           Omite la generación del PDF
--top-customers    Cantidad de clientes top a listar (por defecto: 10)
--top-products     Cantidad de productos top a graficar (por defecto: 10)
```

### Ejemplos

```bash
# Reporte con título personalizado y solo Excel
python sales_report_automator.py -i ventas_q1.csv -o ./reportes_q1 \
    --company "Mi Empresa S.A." --no-pdf

# Reporte completo con top 15 productos y 20 clientes
python sales_report_automator.py -i ventas_2024.csv -o ./reportes_2024 \
    --top-products 15 --top-customers 20
```

## Salidas

Tras la ejecución, en la carpeta indicada encontrarás:

- `reporte_ventas_YYYYMMDD_HHMMSS.xlsx` — copia con marca de tiempo
- `reporte_ventas.xlsx` — última versión, sin marca
- `reporte_ventas_YYYYMMDD_HHMMSS.pdf` y `reporte_ventas.pdf` (idem)
- `charts/01_ventas_mensuales.png` — serie mensual de ingresos
- `charts/02_top_productos.png` — top productos por ingresos
- `charts/03_categorias.png` — pie de distribución por categoría
- `charts/04_regiones.png` — ventas por región
- `charts/05_vendedores.png` — top vendedores

## Resultados con datos de muestra

Sobre `data/sample_sales_data.csv` (140 filas originales):

- **130 filas aceptadas** (92.86 %)
- **10 filas rechazadas**, desglosadas así:
  | Motivo | Filas |
  |---|---|
  | order_id duplicado | 8 |
  | quantity <= 0 | 2 |
  | fecha inválida | 2 |
  | unit_price <= 0 | 2 |
  | product vacío | 1 |
  | unit_price no numérico | 1 |
  | email inválido | 1 |

- **KPIs del dataset limpio:**
  - Ingresos totales: `$165,251.44`
  - Órdenes únicas: `130`
  - Unidades vendidas: `758`
  - Ticket medio: `$1,271.16`
  - Período: `2024-01-05 a 2024-12-30`

## Tests

```bash
python -m unittest tests.test_validator -v
```

## Notas

- La codificación de caracteres se asume UTF-8 tanto para entrada como para
  los reportes generados. En Windows, si ves acentos rotos en la consola,
  no afecta a los archivos: ejecútalo desde una terminal con `chcp 65001`.
- Si una categoría tiene un valor muy dominante, el pie chart puede verse
  desbalanceado; es algo esperado y refleja la realidad de los datos.
- Las imágenes del Excel se vinculan como objetos; al copiar o imprimir la
  hoja se mantienen en su posición.
