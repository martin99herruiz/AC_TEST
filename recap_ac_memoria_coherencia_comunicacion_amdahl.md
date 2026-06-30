# Recap de Arquitectura de Computadores: memoria, coherencia y comunicación

> Documento vivo para ir actualizando con nuevas tablas, conceptos y ejemplos de tipo test.

---

# 1. Tabla de memoria, arquitecturas y modelos de paralelismo

| Concepto | Significado | Tipo de memoria | Comunicación | ¿Es multiprocesador? | Idea clave | Uso típico / ejemplo |
|---|---|---|---|---|---|---|
| **UMA** | **Uniform Memory Access** | Memoria compartida | Implícita, mediante variables compartidas | **Sí** | Todos los procesadores acceden a la memoria con el mismo tiempo de acceso | Multiprocesadores pequeños o medianos con memoria común |
| **NUMA** | **Non-Uniform Memory Access** | Memoria compartida físicamente distribuida | Implícita, mediante variables compartidas | **Sí** | Hay memoria compartida, pero acceder a memoria local es más rápido que acceder a memoria remota | Multiprocesadores grandes, normalmente con coherencia mediante directorios |
| **NORMA** | **NO Remote Memory Access** | Memoria distribuida, no compartida | Explícita, mediante paso de mensajes | **No** | Cada nodo tiene su propia memoria y no puede acceder directamente a la memoria de otro nodo | Multicomputadores y clusters |
| **Cluster** | Conjunto de computadores conectados por red | Memoria distribuida | Explícita, normalmente paso de mensajes | **No** | Cada computador trabaja como nodo independiente y se comunica por red | Sistemas distribuidos, HPC, servidores conectados |
| **SIMD** | **Single Instruction, Multiple Data** | Depende de la arquitectura | Misma instrucción aplicada a varios datos | No necesariamente | Una única instrucción opera sobre muchos datos a la vez | Procesamiento vectorial, GPU, instrucciones vectoriales |
| **MIMD** | **Multiple Instruction, Multiple Data** | Puede ser compartida o distribuida | Puede ser por memoria compartida o mensajes | Puede ser **sí** o **no** | Varios procesadores ejecutan instrucciones distintas sobre datos distintos | UMA, NUMA, clusters y multicomputadores |

## 1.1 Resumen rápido de memoria

| Si el sistema tiene... | Entonces suele ser... |
|---|---|
| Memoria compartida y mismo tiempo de acceso | **UMA** |
| Memoria compartida, pero acceso local más rápido que remoto | **NUMA** |
| Memoria no compartida y paso de mensajes | **NORMA** |
| Varios computadores conectados por red | **Cluster** |
| Misma instrucción sobre muchos datos | **SIMD** |
| Instrucciones distintas sobre datos distintos | **MIMD** |

## 1.2 Multiprocesador vs multicomputador

| Tipo | Memoria | Comunicación | Ejemplos |
|---|---|---|---|
| **Multiprocesador** | Compartida | Implícita mediante memoria común | **UMA**, **NUMA** |
| **Multicomputador** | Distribuida, no compartida | Explícita mediante mensajes | **NORMA**, **Cluster** |

---

# 2. Tabla de protocolos de comunicación/coherencia de caché

> En este bloque, “protocolos de comunicación” se refiere a cómo se comunican las cachés/procesadores para mantener la coherencia de memoria.

## 2.1 Estados de coherencia

| Estado | Nombre | Significado | Aparece en |
|---|---|---|---|
| **M** | Modified / Modificado | El bloque está modificado en una caché y no coincide con memoria principal. Solo esa caché tiene la copia válida | **MSI**, **MESI** |
| **E** | Exclusive / Exclusivo | El bloque está solo en una caché y coincide con memoria principal | **MESI** |
| **S** | Shared / Compartido | El bloque puede estar en varias cachés y coincide con memoria principal | **MSI**, **MESI** |
| **I** | Invalid / Inválido | La copia del bloque no es válida | **MSI**, **MESI** |

## 2.2 Mensajes principales

| Mensaje | Significado | Para qué sirve |
|---|---|---|
| **PtLec** | Petición de lectura | Un procesador pide un bloque para leerlo |
| **PtEx** | Petición exclusiva | Un procesador pide un bloque en exclusiva para poder escribir |
| **RpBloque** | Respuesta con bloque | Se devuelve el bloque solicitado |
| **Invalidación** | Orden de invalidar una copia | Hace que otras cachés pasen el bloque a estado **I** |
| **Actualización / escritura en memoria** | Volcado del dato modificado | Ocurre cuando un bloque en **M** debe hacerse visible a memoria u otra caché |

---

## 2.3 Protocolo MSI

| Aspecto | MSI |
|---|---|
| Estados | **M, S, I** |
| Estado exclusivo | No tiene estado **E** |
| Escritura sobre bloque compartido | Necesita lanzar **PtEx** e invalidar otras copias |
| Lectura de un bloque inválido | Lanza **PtLec** y pasa normalmente a **S** |
| Idea clave | Simple, pero genera más tráfico que MESI porque no distingue el caso “solo yo tengo el bloque limpio” |

### Transiciones MSI por operación propia

| Estado actual | Operación propia | Acción | Nuevo estado |
|---|---|---|---|
| **I** | Lectura | Lanza **PtLec** y recibe **RpBloque** | **S** |
| **I** | Escritura | Lanza **PtEx**, recibe **RpBloque** e invalida otras copias | **M** |
| **S** | Lectura | Lee directamente de caché | **S** |
| **S** | Escritura | Lanza **PtEx** para invalidar otras copias | **M** |
| **M** | Lectura | Lee directamente de caché | **M** |
| **M** | Escritura | Escribe directamente en caché | **M** |

### Transiciones MSI por operación de otro procesador

| Mi estado actual | Otro procesador hace... | Acción en mi caché | Mi nuevo estado |
|---|---|---|---|
| **I** | **PtLec** | No hago nada | **I** |
| **I** | **PtEx** | No hago nada | **I** |
| **S** | **PtLec** | No hago nada; el bloque puede seguir compartido | **S** |
| **S** | **PtEx** | Invalido mi copia | **I** |
| **M** | **PtLec** | Entrego/actualizo el bloque con **RpBloque** | **S** |
| **M** | **PtEx** | Entrego/actualizo el bloque y me invalido | **I** |

---

## 2.4 MSI con difusión y MSI sin difusión

| Tipo | Cómo funciona | Quién recibe las peticiones | Uso típico | Ventaja | Problema |
|---|---|---|---|---|---|
| **MSI con difusión** | Las peticiones se difunden por el bus | Todas las cachés escuchan | Sistemas pequeños/medianos, normalmente **UMA** | Simple | Mucho tráfico; escala mal |
| **MSI sin difusión / con directorio** | Se consulta un directorio que sabe quién tiene cada bloque | Solo las cachés implicadas | Sistemas grandes, normalmente **NUMA** | Menos tráfico; escala mejor | Más complejo; necesita directorio |

### Idea clave

| Pregunta | Respuesta |
|---|---|
| ¿Cambian los estados entre MSI con difusión y MSI con directorio? | **No**. Los estados siguen siendo **M, S, I** |
| ¿Qué cambia? | Cambia cómo se avisa a las cachés |
| Con difusión | Todos escuchan todas las peticiones |
| Sin difusión / directorio | Solo se avisa a quienes tienen copia del bloque |

### Ejemplo: bloque en S y quiero escribir

| Caso | Qué ocurre |
|---|---|
| **MSI con difusión** | Lanzo **PtEx** al bus. Todas las cachés lo ven. Las que tengan el bloque lo invalidan. Yo paso a **M** |
| **MSI con directorio** | Pido exclusiva al directorio. El directorio invalida solo a las cachés que tienen copia. Yo paso a **M** |

---

## 2.5 Protocolo MESI

| Aspecto | MESI |
|---|---|
| Estados | **M, E, S, I** |
| Diferencia con MSI | Añade el estado **E - Exclusive** |
| Ventaja del estado E | Si tengo el bloque en exclusiva, puedo escribir sin lanzar **PtEx** |
| Idea clave | Reduce tráfico respecto a MSI |

### Transiciones MESI por operación propia

| Estado actual | Operación propia | Acción | Nuevo estado |
|---|---|---|---|
| **I** | Lectura | Lanza **PtLec** | **E** si nadie más lo tiene / **S** si alguien lo tiene |
| **I** | Escritura | Lanza **PtEx** y recibe **RpBloque** | **M** |
| **E** | Lectura | Lee directamente de caché | **E** |
| **E** | Escritura | Escribe directamente, sin avisar | **M** |
| **S** | Lectura | Lee directamente de caché | **S** |
| **S** | Escritura | Lanza **PtEx** e invalida otras copias | **M** |
| **M** | Lectura | Lee directamente de caché | **M** |
| **M** | Escritura | Escribe directamente en caché | **M** |

### Transiciones MESI por operación de otro procesador

| Mi estado actual | Otro procesador hace... | Acción en mi caché | Mi nuevo estado |
|---|---|---|---|
| **I** | **PtLec** | No hago nada | **I** |
| **I** | **PtEx** | No hago nada | **I** |
| **S** | **PtLec** | No hago nada | **S** |
| **S** | **PtEx** | Invalido mi copia | **I** |
| **E** | **PtLec** | El bloque pasa a estar compartido | **S** |
| **E** | **PtEx** | Invalido mi copia | **I** |
| **M** | **PtLec** | Entrego/actualizo el bloque | **S** |
| **M** | **PtEx** | Entrego/actualizo el bloque y me invalido | **I** |

### Caso típico MESI

| Situación | Resultado |
|---|---|
| Caché de **N1** tiene bloque **B** en estado **E** |
| Otro procesador en **N2** intenta leer un dato de **B** |
| **N1** detecta la petición de lectura |
| **N1** pasa de **E** a **S** |
| **N2** recibe el bloque en **S** |
| Resultado final | El bloque queda en estado **S** en **N1** y **N2** |

---

## 2.6 Directorios

| Aspecto | Directorios |
|---|---|
| Qué son | Una técnica para mantener coherencia de caché sin difundir a todos |
| Qué guardan | Información sobre qué cachés tienen copia de cada bloque |
| Uso típico | Sistemas grandes, especialmente **NUMA** |
| Ventaja | Reducen tráfico porque solo se avisa a los nodos implicados |
| Problema | Aumentan la complejidad y requieren memoria para almacenar el directorio |
| Relación con MSI/MESI | Un sistema con directorios puede implementar MSI, MESI u otros protocolos |

### Comparación difusión vs directorio

| Aspecto | Difusión / Snooping | Directorio |
|---|---|---|
| Comunicación | Se avisa a todas las cachés | Se avisa solo a las cachés implicadas |
| Tráfico | Alto | Menor |
| Escalabilidad | Peor | Mejor |
| Complejidad | Menor | Mayor |
| Uso típico | UMA pequeños/medianos | NUMA grandes |

---

## 2.7 Resumen tipo test: coherencia

| Pregunta | Respuesta |
|---|---|
| ¿Qué significa MSI? | Modified, Shared, Invalid |
| ¿Qué significa MESI? | Modified, Exclusive, Shared, Invalid |
| ¿Qué añade MESI respecto a MSI? | El estado **E - Exclusive** |
| ¿Qué permite el estado E? | Escribir sin lanzar una petición de exclusividad si nadie más tiene el bloque |
| Si estoy en **S** y quiero escribir, ¿qué hago? | Lanzo **PtEx**, invalido otras copias y paso a **M** |
| Si estoy en **E** y quiero escribir, ¿qué hago? | Paso a **M** sin tráfico de bus |
| Si estoy en **M** y otro lee, ¿qué ocurre? | Entrego/actualizo el bloque y paso a **S** |
| Si estoy en **M** y otro quiere escribir, ¿qué ocurre? | Entrego/actualizo el bloque y paso a **I** |
| ¿Qué es difusión? | Enviar las peticiones a todas las cachés |
| ¿Qué es un directorio? | Una tabla que indica qué cachés tienen copia de cada bloque |
| ¿Qué escala mejor? | Directorios |
| ¿Qué es más simple? | Difusión / snooping |

---

# 3. Tabla de comunicación colectiva

## 3.1 Comunicación según arquitectura

| Tipo de sistema | Comunicación | Cómo se hace | Ejemplo |
|---|---|---|---|
| **Multiprocesador** | Implícita | Variables compartidas en memoria común | UMA, NUMA |
| **Multicomputador** | Explícita | Paso de mensajes | NORMA, cluster |

---

## 3.2 Tipos principales de comunicación

| Patrón | Operación | Tipo | Qué ocurre | Resultado |
|---|---|---|---|---|
| **Uno a uno** | Send / Receive | Punto a punto | Un proceso manda a otro proceso concreto | Solo comunica origen y destino |
| **Uno a todos** | Broadcast / Difusión | Colectiva | Uno manda el mismo dato a todos | Todos reciben lo mismo |
| **Uno a todos** | Scatter / Dispersión | Colectiva | Uno reparte datos distintos | Cada proceso recibe una parte |
| **Todos a uno** | Gather / Acumulación | Colectiva | Todos mandan sus datos a un proceso raíz | Un proceso reúne todos los datos |
| **Todos a uno** | Reduce / Reducción | Colectiva | Todos mandan datos y se aplica una operación | Un proceso obtiene el resultado |
| **Todos a todos** | Allgather | Colectiva | Todos mandan su dato y todos reciben los datos de todos | Todos tienen toda la información |
| **Todos a todos** | Allreduce | Colectiva | Se hace una reducción y todos reciben el resultado | Todos tienen el resultado final |
| **Todos a todos** | Alltoall | Colectiva | Cada proceso manda datos distintos a todos los demás | Intercambio completo de datos |
| **Todos a todos** | Gossiping | Colectiva | Todos tienen información inicial y la intercambian hasta que todos conocen la de todos | Todos acaban con toda la información |
| **Múltiple uno a uno** | Permutación | Colectiva | Cada proceso envía a otro según una correspondencia | Los datos cambian de proceso |
| **Múltiple uno a uno** | Rotación | Colectiva | Cada proceso envía al siguiente o anterior | Los datos rotan |
| **Compuesto** | Scan / Recorrido | Colectiva | Se calculan reducciones parciales | Cada proceso obtiene un resultado parcial |
| **Sincronización** | Barrier / Barrera | Colectiva | Todos los procesos esperan a todos | Nadie continúa hasta que todos llegan |

---

## 3.3 Uno a todos

| Operación | Qué hace | Ejemplo |
|---|---|---|
| **Broadcast / Difusión** | Un proceso manda el mismo dato a todos | P0 envía `X` a P0, P1, P2 y P3 |
| **Scatter / Dispersión** | Un proceso reparte partes distintas a cada proceso | P0 tiene `[A, B, C, D]` y reparte una parte a cada proceso |

### Diferencia clave

| Operación | Dato enviado |
|---|---|
| **Broadcast** | El mismo dato para todos |
| **Scatter** | Un trozo distinto para cada proceso |

---

## 3.4 Todos a uno

| Operación | Qué hace | Resultado |
|---|---|---|
| **Gather / Acumulación** | Todos mandan sus datos a un proceso raíz | El proceso raíz reúne una lista/vector |
| **Reduce / Reducción** | Todos mandan datos y se aplica una operación | El proceso raíz obtiene un único resultado |

### Diferencia clave

| Operación | Qué obtiene el proceso raíz |
|---|---|
| **Gather** | Todos los datos juntos |
| **Reduce** | Un resultado combinado: suma, máximo, mínimo, producto, etc. |

---

## 3.5 Todos a todos

| Operación | Qué hace | Resultado |
|---|---|---|
| **Allgather** | Todos reúnen los datos de todos | Todos tienen la lista completa |
| **Allreduce** | Todos hacen una reducción y reciben el resultado | Todos tienen el resultado final |
| **Alltoall** | Todos envían datos personalizados a todos | Cada proceso recibe datos distintos de todos |
| **Gossiping** | Todos van intercambiando información hasta que todos conocen todo | Todos acaban con la información de todos |

### Diferencia entre Allgather, Alltoall y Gossiping

| Operación | Idea clave |
|---|---|
| **Allgather** | Todos acaban teniendo los datos de todos |
| **Alltoall** | Cada proceso manda un dato distinto a cada destino |
| **Gossiping** | La información se propaga mediante intercambios hasta que todos conocen todo |

---

## 3.6 Servicios compuestos

| Operación | Tipo | Qué hace |
|---|---|---|
| **Scan / Recorrido** | Reducción parcial | Cada proceso obtiene el resultado parcial hasta su posición |
| **Barrier / Barrera** | Sincronización colectiva | No necesariamente mueve datos; obliga a esperar a que todos lleguen |

### Ejemplo de scan con suma

| Proceso | Valor inicial | Resultado scan |
|---|---:|---:|
| P0 | 2 | 2 |
| P1 | 5 | 7 |
| P2 | 3 | 10 |
| P3 | 10 | 20 |

---

## 3.7 Resumen tipo test: comunicación colectiva

| Si el enunciado dice... | Operación |
|---|---|
| “Un proceso manda el mismo dato a todos” | **Broadcast / Difusión** |
| “Un proceso reparte partes distintas” | **Scatter / Dispersión** |
| “Todos mandan sus datos a uno” | **Gather / Acumulación** |
| “Todos mandan datos y se calcula suma, máximo, mínimo…” | **Reduce / Reducción** |
| “Todos obtienen todos los datos” | **Allgather** |
| “Todos obtienen el resultado de una reducción” | **Allreduce** |
| “Todos intercambian datos con todos” | **Alltoall** |
| “Todos tienen algo que contar y todos acaban sabiendo lo de todos” | **Gossiping** |
| “Cada proceso espera a que lleguen los demás” | **Barrier / Barrera** |
| “Cada proceso obtiene una suma parcial acumulada” | **Scan / Recorrido** |

---

# 4. Ideas finales para examen

| Idea | Resumen |
|---|---|
| **UMA y NUMA** | Son multiprocesadores con memoria compartida |
| **NORMA y Cluster** | Son multicomputadores con memoria distribuida |
| **MSI y MESI** | Son protocolos de coherencia de caché |
| **MESI** | Es MSI + estado **Exclusive** |
| **Directorios** | Evitan difundir a todos; escalan mejor |
| **Broadcast** | Uno manda lo mismo a todos |
| **Scatter** | Uno reparte partes distintas |
| **Gather** | Todos mandan a uno |
| **Reduce** | Todos mandan a uno y se calcula algo |
| **Allgather** | Todos acaban con los datos de todos |
| **Gossiping** | Todos difunden su información hasta que todos saben todo |

---

# 5. Fórmulas de rendimiento

## 5.1 Ganancia / Aceleración

| Concepto | Fórmula | Significado |
|---|---|---|
| **Ganancia** o **aceleración** | $G = \dfrac{T_{secuencial}}{T_{paralelo}}$ | Indica cuántas veces es más rápido el sistema paralelo frente al secuencial |
| **Ganancia con p procesadores** | $G(p) = \dfrac{T(1)}{T(p)}$ | Compara el tiempo usando 1 procesador frente al tiempo usando `p` procesadores |
| **Eficiencia** | $E(p) = \dfrac{G(p)}{p}$ | Mide qué porcentaje del rendimiento teórico de los procesadores se aprovecha |

### Interpretación rápida

| Resultado | Interpretación |
|---|---|
| $G = 1$ | No hay mejora |
| $G > 1$ | El sistema paralelo mejora al secuencial |
| $G = p$ | Ganancia ideal con `p` procesadores |
| $G < p$ | Hay pérdidas por comunicación, sincronización, esperas o sobrecarga |
| $E = 1$ | Eficiencia ideal |
| $E < 1$ | Parte de la capacidad de los procesadores se desaprovecha |

### Resumen tipo test

| Si el enunciado pide... | Usa |
|---|---|
| “Ganancia”, “speedup” o “aceleración” | $G = \dfrac{T_{secuencial}}{T_{paralelo}}$ |
| “Ganancia con `p` procesadores” | $G(p) = \dfrac{T(1)}{T(p)}$ |
| “Eficiencia” | $E(p) = \dfrac{G(p)}{p}$ |


## 5.2 Ley de Amdahl

La **Ley de Amdahl** calcula la ganancia máxima posible cuando solo una parte del programa puede paralelizarse.

| Concepto | Fórmula | Significado |
|---|---|---|
| **Ley de Amdahl** | $G(p) = \dfrac{1}{(1 - f) + \dfrac{f}{p}}$ | Ganancia usando `p` procesadores |
| **Límite máximo teórico** | $G_{max} = \dfrac{1}{1 - f}$ | Ganancia máxima cuando el número de procesadores tiende a infinito |

### Variables

| Símbolo | Significado |
|---|---|
| $G(p)$ | Ganancia o aceleración con `p` procesadores |
| $p$ | Número de procesadores |
| $f$ | Fracción paralelizable del programa |
| $1 - f$ | Fracción secuencial del programa, que no puede paralelizarse |

### Interpretación rápida

| Caso | Interpretación |
|---|---|
| $f = 0$ | Nada es paralelizable, por tanto no hay ganancia |
| $f = 1$ | Todo es paralelizable, caso ideal |
| Cuanto mayor es $f$ | Mayor ganancia posible |
| Cuanto mayor es la parte secuencial $1-f$ | Menor ganancia máxima |
| Aunque aumenten mucho los procesadores | La parte secuencial limita la aceleración |

### Resumen tipo test

| Si el enunciado dice... | Usa |
|---|---|
| “Ley de Amdahl” | $G(p) = \dfrac{1}{(1 - f) + \dfrac{f}{p}}$ |
| “Fracción paralelizable” | $f$ |
| “Fracción no paralelizable” o “parte secuencial” | $1 - f$ |
| “Ganancia máxima con infinitos procesadores” | $G_{max} = \dfrac{1}{1 - f}$ |

### Ejemplo rápido

Si el **80%** del programa es paralelizable y usamos **4 procesadores**:

$$
G(4) = \dfrac{1}{(1 - 0.8) + \dfrac{0.8}{4}}
= \dfrac{1}{0.2 + 0.2}
= \dfrac{1}{0.4}
= 2.5
$$

La ganancia sería **2,5**.

