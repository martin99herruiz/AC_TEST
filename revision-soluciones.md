# Revisión del banco de preguntas de Arquitectura de Computadores

## Resultado

- Banco final: **317 preguntas** (51 originales + 266 incorporadas).
- Clasificación: **Teoría/Prácticas**, tema, subtema, tipo y fuente.
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

## Erratas reparadas para que la pregunta sea válida

- Examen Final Prácticas, ejercicio 4: `pos[500]` se cambió a `pos[1000]` porque el bucle recorre 1000 posiciones.
- Examen Final Prácticas, ejercicio 7: `reduction(*n)` se corrigió a `reduction(*:n)`.
- Examen Final Prácticas, ejercicio 11: se explicitó la hipótesis usada para contar saltos.
- Bloque Práctico II, ejercicio 4: se explicitó que `v2` parte de cero; sin esa condición el resultado no está definido.

## Preguntas excluidas por falta de información fiable

- Parcial 1, pregunta 13: la instrucción y su comentario escriben registros distintos, por lo que la respuesta cambia según cuál se considere correcto.
- Test Tema 2, preguntas 44, 46 y 51: las fórmulas no se conservan de forma legible en el escaneo.
- Test Tema 3, preguntas 17, 20, 21, 22 y 41: faltan diagramas, instrucciones o estados esenciales.
- `Algunos-test-AC-anos-anteriores.pdf`: las páginas manuscritas no tienen resolución suficiente para una transcripción responsable.

Estas exclusiones son deliberadas: no se han inventado operandos, fórmulas ni opciones ausentes.
