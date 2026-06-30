# Revisión del banco de preguntas de Arquitectura de Computadores

## Resultado

- Banco final: **317 preguntas** (51 originales + 266 incorporadas).
- Clasificación: **Teoría/Prácticas**, tema, lección/subtema, tipo y fuente.
- Las **252 preguntas de teoría** están ordenadas según el temario oficial: 91 del Tema 1, 83 del Tema 2 y 78 del Tema 3. El banco actual no contiene preguntas teóricas específicas del Tema 4.
- Las **65 preguntas de prácticas** se han recuperado en la interfaz y reorganizado conforme a los cinco PDF de `2. Seminarios`.
- Los dos archivos `Parcial1-AC.pdf` son versiones duplicadas del mismo cuestionario; se ha incorporado una sola copia.
- Se han eliminado duplicados por enunciado y se han ordenado todas las preguntas antes de reasignar sus identificadores.

## Incorporación por PDF

| PDF | Preguntas nuevas | Observaciones |
|---|---:|---|
| `wuolah-free-AC-TEST-TM3.pdf` | 16 | Transcritas, normalizadas y revisadas. |
| `wuolah-free-Algunos-test-AC-anos-anteriores.pdf` | 0 | Manuscrito de muy baja resolución; no permite recuperar de forma fiable pares completos de enunciado y solución. |
| `wuolah-free-BP3testconsoluciones.pdf` | 20 | Incorporadas con sus cuatro opciones. |
| `wuolah-free-Parcial1-AC.pdf` y copia `(1)` | 94 | 96 entradas originales; una se excluyó por contradicción y otra era duplicada. |
| `wuolah-free-TEST-Tema-2-soluciones-al-final.pdf` | 50 | Tres fórmulas ilegibles se excluyeron. |
| `wuolah-free-TEST-Tema-3-soluciones-al-final.pdf` | 52 | Cinco entradas dependían de figuras o fragmentos cortados. |
| `wuolah-free-tipotestbp4.pdf` | 10 | Incorporadas y revisadas. |
| `wuolah-free-TODAS-LAS-PREGUNTAS-TEMA-2-TEORIA.pdf` | 24 | Incorporadas con deduplicación. |

## Soluciones incorrectas o imprecisas detectadas

1. **Examen Final Prácticas 2023-24, ejercicio 2 — `omp_get_wtime()`**. El solucionario marcaba “timestamp”. Se corrigió a tiempo de reloj de pared, en segundos, desde un origen arbitrario estable.
2. **AC Test Tema 3, pregunta 1 — multicore frente a CMP**. El solucionario marcaba la opción c, pero *chip multiprocessor* y procesador multicore describen esencialmente varios núcleos integrados en un chip. Se corrigió a la opción d normalizada.
3. **Parcial 1, pregunta 25 — dependencias por `r1`**. Se marcaba falso; aparecen dependencias WAW y RAW, sin WAR por `r1`. Se corrigió a verdadero.
4. **Parcial 1, pregunta 57 — dependencia RAW entre i2 e i3 por `r4`**. Se marcaba falso; i2 escribe `r4` e i3 lo lee. Se corrigió a verdadero.
5. **Parcial 1, pregunta 68 — unidades**. El documento respondía “20 TFLOPS” a una pregunta expresada en GFLOPS. Se normalizó a **20 000 GFLOPS**.
6. **Parcial 1, pregunta 85 — fórmula de MIPS**. Se normalizó a **`F / (CPI × 10^6)`** cuando `F` está expresada en Hz.
7. **Parcial 1, pregunta 90 — aceleración**. El resultado “1,3” era un redondeo prematuro; se guardó el valor exacto **`4/3`**.
8. **Todas las preguntas Tema 2, pregunta 6 — `all-scatter`**. Se marcaba falso, pero la lección 4 muestra que cada flujo recibe un vector compuesto con partes de los vectores de entrada. Se corrigió a **verdadero**.
9. **Test Tema 3, pregunta 40 — transición MSI ante lectura remota**. Se marcaba que un bloque en `M` pasa a `I`. La tabla de la lección 8 establece **`M → S` ante `PtLec`**, por lo que la afirmación se corrigió a **falso**.
10. **Bloque Práctico II, ejercicio 10 — acumulación sobre `v2` sin inicializar**. `atomic` evita actualizaciones perdidas, pero no inicializa el acumulador. Como el enunciado solo inicializa `M` y `v1`, se corrigió la solución a **código no eficiente y resultado indefinido**.

## Organización de las preguntas teóricas

- **Tema 1 — Arquitecturas paralelas: clasificación y prestaciones**: paralelismo implícito; dependencias RAW/WAR/WAW; clasificación de Flynn; UMA/NUMA/NORMA; tiempo de CPU y métricas; ley de Amdahl.
- **Tema 2 — Programación paralela**: herramientas, estilos y estructuras; comunicación colectiva; proceso de paralelización y equilibrio de carga; prestaciones y escalabilidad.
- **Tema 3 — Arquitecturas con TLP**: multicores y SMT; coherencia MSI/MESI; directorios NUMA; consistencia de memoria; sincronización y cerrojos.

La clasificación usa los títulos y la numeración de las lecciones oficiales incorporadas al repositorio. Las dependencias RAW/WAR/WAW permanecen en el Tema 1 porque aparecen expresamente en los objetivos de su lección 1, aunque vuelvan a utilizarse al estudiar los riesgos ILP del Tema 4.

## Organización de las preguntas prácticas

La comparación con la versión anterior confirmó que seguían existiendo las mismas 65 preguntas prácticas y que no faltaba ninguna fuente. Se sustituyó la clasificación antigua por bloques por la estructura del temario de seminarios:

- **Seminario 0 — Entorno de programación**: 1 pregunta sobre el clúster `atcgrid` y el gestor de carga.
- **Seminario 1 — Directivas OpenMP**: 6 preguntas sobre la API, regiones paralelas, trabajo compartido y sincronización.
- **Seminario 2 — Cláusulas OpenMP**: 12 preguntas sobre ámbito de datos, `reduction` y `copyprivate`.
- **Seminario 3 — Interacción con el entorno en OpenMP**: 31 preguntas sobre variables de control, funciones, tiempos y `schedule`.
- **Seminario 4 — Optimización de código en arquitecturas ILP**: 15 preguntas sobre compilación, ejecución, memoria y saltos.

## Erratas reparadas para que la pregunta sea válida

- Examen Final Prácticas, ejercicio 4: `pos[500]` se cambió a `pos[1000]` porque el bucle recorre 1000 posiciones.
- Examen Final Prácticas, ejercicio 7: `reduction(*n)` se corrigió a `reduction(*:n)`.
- Examen Final Prácticas, ejercicio 11: se explicitó la hipótesis usada para contar saltos.
- Bloque Práctico II, ejercicio 4: se explicitó que `v2` parte de cero; sin esa condición el resultado no está definido.
- Examen de Teoría Tema 3, ejercicios 8 y 10: se restauraron los bucles y comparaciones truncados por caracteres `<`; también se corrigió la errata `sum`/`sm` para que el código coincida con los accesos indicados por el enunciado.
- Examen Final de Prácticas, ejercicios 6 y 18: se restauraron las cabeceras `stdio.h`/`omp.h`, la directiva `#define` y la declaración de `n` que habían quedado dañadas al importar HTML.
- Examen Final de Prácticas, ejercicio 5: se reconstruyó la explicación, que estaba cortada después de `if (n`.
- Bloque Práctico II, ejercicio 3: se reformuló el enunciado de `firstprivate` para dejar claro que copia el valor original a cada instancia privada, no valores entre hebras.
- Test de Bloque Práctico IV, pregunta 2: se limpiaron las opciones de compilación (`-O0`, `-O1`, `-O2`, `-g`).

## Preguntas excluidas por falta de información fiable

- Parcial 1, pregunta 13: la instrucción y su comentario escriben registros distintos, por lo que la respuesta cambia según cuál se considere correcto.
- Test Tema 2, preguntas 44, 46 y 51: las fórmulas no se conservan de forma legible en el escaneo.
- Test Tema 3, preguntas 17, 20, 21, 22 y 41: faltan diagramas, instrucciones o estados esenciales.
- `Algunos-test-AC-anos-anteriores.pdf`: las páginas manuscritas no tienen resolución suficiente para una transcripción responsable.

Estas exclusiones son deliberadas: no se han inventado operandos, fórmulas ni opciones ausentes.
