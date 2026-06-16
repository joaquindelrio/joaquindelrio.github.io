# Audio Analysis

Aplicación web para análisis de audio WAV, cálculo de SPL, generación de espectrogramas y creación de informes.

Este proyecto tiene dos modos de despliegue:

- Producción (completa) en quim.obsea.es, con backend activo.
- GitHub Pages (estático), solo para vista web sin backend.

Importante: GitHub Pages no ejecuta PHP ni Python. Para listar WAV y correr análisis debes ejecutar la app en local o en un servidor con PHP + Python.

## Requisitos

- Linux, macOS o Windows con WSL
- Python 3.10 o superior
- pip
- PHP 8 o superior
- Servidor web
  - Opción A: Apache (entorno parecido a producción)
  - Opción B: Servidor local de PHP (rápido para pruebas)

Dependencias Python usadas por el proyecto:

- numpy
- scipy
- matplotlib
- pandas
- reportlab

## Estructura relevante

- Frontend web: web/index.html
- API backend PHP: web/api.php
- Pipeline principal Python: main.py

## Instalación local paso a paso

1. Clona el repositorio y entra a la carpeta de la app.

2. Crea entorno virtual de Python.

	python3 -m venv .venv

3. Activa el entorno virtual.

	source .venv/bin/activate

4. Instala dependencias.

	pip install --upgrade pip
	pip install numpy scipy matplotlib pandas reportlab

5. Verifica que Python ve correctamente los paquetes.

	python -c "import numpy, scipy, matplotlib, pandas, reportlab; print('OK')"

## Ejecutar la app en local

### Opcion A: Apache + PHP (recomendada)

1. Sirve el proyecto con Apache y apunta el DocumentRoot al repositorio (o a la carpeta superior que contenga audio_analysis).

2. Abre en navegador la ruta de la app, por ejemplo:

   http://localhost/audio_analysis/audio_analysis/app/web/index.html

3. Comprueba que la API responde:

   http://localhost/audio_analysis/audio_analysis/app/web/api.php?action=list&path=audio_analysis/audio_analysis/data

Si devuelve JSON, backend operativo.

### Opcion B: Servidor local con PHP (rapida para desarrollo)

Desde la carpeta raiz del repositorio (la que contiene audio_analysis):

	php -S 127.0.0.1:8080

Luego abre:

   http://127.0.0.1:8080/audio_analysis/audio_analysis/app/web/index.html

## Configuracion de Python en la API (muy importante)

En web/api.php, la ejecucion del analisis usa variables internas para invocar Python.
En algunos equipos debes ajustar la ruta del ejecutable Python para que use tu entorno virtual.

Busca estas variables en web/api.php:

- $python
- $pythonPath

Configuracion recomendada en local:

- $python apuntando a tu .venv/bin/python
- $pythonPath vacio o con tu site-packages si lo necesitas

Ejemplo tipico de ruta:

   /ruta/al/proyecto/.venv/bin/python

## Flujo de uso

1. En la web, selecciona la carpeta de audio.
2. Pulsa Buscar carpeta para verificar contenido.
3. Pulsa Ejecutar analisis.
4. Descarga resultados en la carpeta resultados.

## Datos de ejemplo

Ruta usada habitualmente:

   audio_analysis/audio_analysis/data/experimento_001/audio

## Problemas frecuentes

1. No lista WAV o aparece error JSON
- Revisa URL de api.php en navegador.
- Verifica que PHP esta corriendo y que la ruta existe.

2. Error al ejecutar analisis
- Verifica que Python y dependencias estan instaladas en el entorno activo.
- Revisa la ruta configurada en $python dentro de web/api.php.

3. En GitHub Pages no funciona el analisis
- Es esperado. Pages no ejecuta backend.
- Usa entorno local o servidor con PHP + Python.

## Nota sobre despliegue

- En GitHub Pages esta app se comporta como frontend estatico.
- La version funcional completa requiere backend en servidor (como quim.obsea.es o local con PHP + Python).