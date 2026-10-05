# GPS Analyst



GPS Analyst es una herramienta interna para interpretar y analizar datos GPS de flota procedentes de Automatica PLUS.



## Estado



Versión estable: v0.1.0



## Objetivo V0.1



La primera versión se centra exclusivamente en el análisis GPS.



Debe ser capaz de:



- importar archivos Excel oficiales de Automatica PLUS;

- detectar vehículos y días;

- interpretar actividad y días sin actividad;

- reconstruir trayectos y paradas;

- obtener inicio y fin de actividad;

- calcular tiempos de conducción y parada;

- obtener kilómetros, velocidad y localizaciones;

- validar los cálculos contra las hojas Totales y SubTotales;

- presentar una jornada GPS comprensible y verificable.



## Fuera de alcance de V0.1



Todavía no se incluye:



- integración con Woffu;

- cruce con Time Analyst;

- alertas laborales;

- albaranes o facturación;

- identificación mediante iButton;

- modificaciones sobre Automatica PLUS.



## Arquitectura



Las fuentes de datos se mantienen separadas del motor de análisis.



Inicialmente:



Automatica PLUS Excel

→ ExcelSource

→ modelo GPS común

→ servicios de análisis

→ interfaz



Si Automatica PLUS facilita una API:



Automatica PLUS API

→ ApiSource

→ mismo modelo GPS común

→ mismos servicios de análisis

→ misma interfaz



La futura API no debe obligar a reescribir el motor GPS.



## Seguridad y privacidad



El proyecto trabaja en modo de solo lectura respecto a Automatica PLUS.



Los Excel reales, matrículas, nombres, ubicaciones, coordenadas y demás información operativa se consideran datos privados.



Los archivos reales se almacenarán únicamente en:



data/private/



Ese directorio está excluido de Git.



No deben publicarse:



- archivos Excel reales;

- credenciales;

- nombres de empleados;

- matrículas reales;

- posiciones GPS reales;

- datos de clientes;

- rutas o históricos reales.



## Formato Automatica PLUS



Los Excel estudiados contienen las hojas:



- Totales

- SubTotales

- Detalle



Reglas observadas inicialmente:



- `PARA = ??` y `ARRANCA = hora` representa una apertura de bloque y no un trayecto real.

- `PARA = hora` y `ARRANCA = hora` representa una parada intermedia entre trayectos.

- `PARA = hora` y `ARRANCA = ??` representa el último trayecto real del bloque.

- Los valores de kilómetros y velocidad de una fila de apertura pueden estar arrastrados del bloque anterior y deben ignorarse.
- Automatica PLUS puede omitir excepcionalmente la fila de apertura y contaminar el primer detalle con valores arrastrados; en ese caso deben conservarse los valores RAW y normalizarse únicamente los valores utilizables cuando el resumen y la coherencia física permitan demostrar la corrección.
- Las distancias visibles están redondeadas a una decimal; la validación entre suma de detalles y resumen debe admitir la acumulación matemática de ese redondeo en función del número de tramos.

- `--` representa ausencia de actividad en determinados campos de resumen.

- Las duraciones pueden superar las 24 horas y deben tratarse como duraciones, no como horas del reloj.

- Los decimales pueden utilizar coma.

- Un día con 0 km no implica necesariamente ausencia total de actividad.



Estas reglas deberán quedar cubiertas mediante pruebas automatizadas.



## Desarrollo



Python 3.12.



Dependencias iniciales:



- openpyxl

- pytest



## Reconstrucción de jornada

La capa `GpsDayAnalysisService` transforma cada `VehicleDay` normalizado en una cronología explícita y verificable.

Produce:

- trayectos con inicio, fin, duración, kilómetros, velocidad punta y destino;
- paradas con inicio, fin, duración, tipo, dirección y mapa;
- continuidad temporal completa desde el inicio hasta el final de jornada;
- soporte de jornadas sin actividad;
- soporte del caso excepcional en que Automatica PLUS omite la fila `opening`;
- validación de tiempos, kilómetros y estructura contra el resumen normalizado.

Esta capa no modifica el importador ni contiene todavía reglas laborales o integración con Woffu/Time Analyst.


## Presentación de jornada

La capa `GpsDayPresenter` transforma el análisis técnico de una jornada en una representación humana reutilizable.

Incluye:

- resumen de fecha, inicio y fin;
- duración total, conducción y tiempo parado;
- kilómetros y velocidad punta;
- cronología ordenada de trayectos y paradas;
- duración, distancia, velocidad y destino de cada trayecto;
- duración, tipo y ubicación de cada parada;
- conservación de enlaces de mapa cuando están disponibles;
- representación explícita de jornadas sin actividad.

El presenter no modifica ni reinterpreta los datos GPS: únicamente presenta el resultado ya normalizado y validado por las capas anteriores.


## Aplicación local de consulta

GPS Analyst incluye una aplicación local de escritorio construida con PySide6.

Permite:

- abrir exportaciones XLSX de Automatica PLUS en modo de solo lectura;
- buscar y seleccionar vehículos;
- seleccionar fechas disponibles;
- consultar el resumen completo de la jornada;
- visualizar una cronología ordenada de trayectos y paradas;
- distinguir explícitamente origen, destino y ubicación de parada;
- declarar el origen inicial como no disponible cuando la fuente no lo proporciona;
- conservar y abrir enlaces de mapa asociados a los eventos;
- consultar también jornadas sin actividad.

La interfaz consume las capas de importación, análisis y presentación existentes y no contiene lógica específica de Automatica PLUS ni reglas laborales. Esto permite reutilizar el motor GPS en futuras integraciones, incluido el cruce con Time Analyst.


## Tests reproducibles y regresión privada

La suite de tests no depende de datos operativos reales.

Por defecto, `pytest` genera y utiliza fixtures XLSX sintéticos y anónimos compatibles con el formato esperado de Automatica PLUS:

```cmd
python -m pytest -q
```

Esto permite ejecutar la suite completa en un clon limpio del repositorio sin matrículas, empleados, ubicaciones ni exportaciones privadas.

Opcionalmente, durante el desarrollo local puede ejecutarse la misma suite contra exportaciones reales almacenadas fuera de Git en `data/private/fixtures`:

```cmd
set GPS_ANALYST_TEST_DATA=private
python -m pytest -q
set GPS_ANALYST_TEST_DATA=
```

Los datos privados sirven únicamente como regresión local adicional y no son necesarios para desarrollar, validar ni ejecutar la aplicación.


## Distribución Windows

GPS Analyst puede empaquetarse como aplicación de escritorio para Windows mediante PyInstaller en modo `onedir`.

### Preparar dependencias de build

```cmd
python -m pip install -r requirements-build.txt
```

### Generar la distribución

```cmd
BUILD_GPS_ANALYST.cmd
```

El proceso ejecuta primero la suite reproducible de tests y cancela el build si existe algún fallo. Después genera:

```text
dist\\GPS Analyst\\
├── GPS Analyst.exe
└── _internal\\
```

Debe distribuirse la carpeta `GPS Analyst` completa; el ejecutable no debe separarse de `_internal`.

El equipo de destino no necesita Python ni un entorno virtual. Los XLSX de Automatica PLUS se seleccionan externamente desde la aplicación y no se incluyen en la distribución.

El script de build verifica además que no se haya incorporado ningún XLSX ni `data/private` al paquete generado.
