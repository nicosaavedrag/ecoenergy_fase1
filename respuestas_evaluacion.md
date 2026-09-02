# Respuestas de Evaluación

## Pregunta 1

Cuando alguien ingresa a la URL /resumen-zonas/, Django revisa el archivo de rutas [monitoreo/urls.py](monitoreo/urls.py) y encuentra que esa ruta está registrada con la vista `resumen_zonas`. Esa función, definida en [monitoreo/views.py](monitoreo/views.py), es la view que se ejecuta cuando la ruta se activa. Dentro de ella se cargan los archivos JSON de [data/zonas.json](data/zonas.json) y [data/dispositivos.json](data/dispositivos.json), se calculan los totales generales y el resumen por cada zona, y luego se arma un diccionario llamado `context` con esos valores. Finalmente, la view ejecuta `return render(request, 'monitoreo/resumen_zonas.html', context)`, y Django renderiza la plantilla [templates/monitoreo/resumen_zonas.html](templates/monitoreo/resumen_zonas.html) con ese contexto para devolver el HTML final al navegador.

## Pregunta 2

El archivo donde se cuenta la cantidad de dispositivos y se suma el campo `consumo_kwh` por zona es [monitoreo/views.py](monitoreo/views.py), dentro de la función `resumen_zonas`. La parte clave del código es el recorrido `for zona in zonas`, donde se filtran los dispositivos de cada zona con `disp_zona = [d for d in dispositivos if d.get('zona_id') == zona.get('id')]`, luego se cuenta con `cantidad = len(disp_zona)` y se suma el consumo con `consumo_total = sum(float(d.get('consumo_kwh', 0.0)) for d in disp_zona)`. De esta forma, por cada zona se obtiene cuántos dispositivos tiene y cuánto consume en total, para luego comparar ese valor con el límite de la zona.

## Pregunta 3

La condición utilizada para definir el estado de una zona es la siguiente: si `consumo_total <= limite`, entonces la zona recibe el texto `DENTRO DEL LÍMITE` y la clase de Bootstrap `bg-success text-white`; en caso contrario, si `consumo_total > limite`, se asigna el texto `LÍMITE SUPERADO` y la clase `bg-danger text-white`. Cuando una zona no tiene dispositivos, la lista de dispositivos de esa zona queda vacía, por lo que `cantidad` vale 0 y `consumo_total` queda en 0. En ese caso, si el límite es mayor o igual a cero, la condición se cumple y la zona se considera `DENTRO DEL LÍMITE`, evitando así errores o fallos en la aplicación.
