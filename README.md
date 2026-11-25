# AutoTraffic ITS 2026

Prototipo de escritorio para explorar demanda vehicular y predecir el volumen de los siguientes 60 minutos. Incluye selección de vialidad, día y hora, reproducción del día y comparación con la referencia histórica.

## Ejecutar

Requiere Python 3.12 con Tkinter. Cada integrante autorizado debe obtener los datos del organizador y colocar `trafico_desarrollo.csv` en `data/`.

```powershell
python main.py train
python main.py app
```

En Windows también puede abrirse `Abrir AutoTraffic.cmd` después del entrenamiento. Las predicciones y el modelo se generan localmente. Cambiar los filtros no reentrena.

Para los experimentos de aprendizaje automático:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-training.txt
```

## Método

Perfil semanal por vialidad y franja con corrección de la observación actual. Selección temporal de parámetros, validación posterior y entrenamiento final separados. Se predice la suma de los cuatro intervalos siguientes. El modelo actual es estadístico; no es deep learning. El volumen mide demanda, no confirma congestión.

Antes de liberar el reservado, registrar código y modelo en el canal autorizado del comité. No reentrenar después del congelamiento. Para evaluar:

```powershell
python main.py final --reservado data/trafico_reservado.csv
```

Comprobar el archivo generado con el evaluador original del organizador. Los datos, modelos entrenados, resultados y presentación se conservan localmente y no se publican.

## Colaboración

Crear una rama por tarea y proponer cambios mediante pull request:

```
git switch main
git pull --ff-only
git switch -c feature/nombre-del-cambio
python -m unittest test_model.py
git diff
git status
```

Agregar solo archivos revisados, crear un commit descriptivo y subir la rama. Otro integrante revisa antes de integrar a main. No incluir datos, métricas reales, capturas del evento ni credenciales en archivos, commits o incidencias. Las pruebas utilizan datos sintéticos.

Ser público permite leer el código; los permisos para subir cambios requieren invitación de colaborador. Nunca compartir credenciales.

## Herramientas

Python, Tkinter y asistencia de OpenAI Codex para desarrollo y pruebas. pandas y NumPy para análisis local; scikit-learn instalado para experimentos posteriores. No se usan modelos preentrenados. Los datos y el protocolo de evaluación pertenecen al paquete del organizador, no redistribuido aquí.
