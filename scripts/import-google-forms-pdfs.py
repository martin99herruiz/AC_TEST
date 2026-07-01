#!/usr/bin/env python3
"""Importa y normaliza los dos formularios PDF a los bancos JSON y HTML."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "banco-preguntas-ac.json"
HTML_PATH = ROOT / "test-ac-arquitectura-computadores.html"

PDFS = {
    "T": ROOT / "AutoTests de AC - Todos los temas - Formularios de Google.pdf",
    "P": ROOT / "Tests de AC - Todas las bps - Formularios de Google.pdf",
}

# Duplicados semánticos del banco actual o preguntas cuyo código no aparece en el PDF.
SKIP = {("T", 24), ("T", 80), ("P", 32), ("P", 42), ("P", 45), ("P", 56)}

TRUE_FALSE = {("T", 19), ("T", 25), ("T", 26), ("T", 28)}


def parse_pdf(pdf: Path, label: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "document.json"
        subprocess.run(
            ["mutool", "draw", "-q", "-F", "stext.json", "-o", str(output), str(pdf)],
            check=True,
        )
        doc = json.loads(output.read_text(encoding="utf-8"))

    questions = []
    for page_number, page in enumerate(doc["pages"], 1):
        blocks = []
        for block in page["blocks"]:
            if block["type"] != "text":
                continue
            lines = block.get("lines", [])
            blocks.append(
                {
                    "x": block["bbox"]["x"],
                    "y": block["bbox"]["y"],
                    "text": " ".join(line.get("text", "").strip() for line in lines).strip(),
                    "lines": lines,
                    "fonts": {line.get("font", {}).get("name", "") for line in lines},
                }
            )

        markers = []
        for block in blocks:
            for line in block["lines"]:
                match = re.fullmatch(r"(\d+)\.", line.get("text", "").strip())
                if match and 60 <= line.get("x", 0) <= 80:
                    markers.append((int(match.group(1)), block["y"]))
                    break

        for number, y_start in markers:
            following = [y for _, y in markers if y > y_start]
            y_end = min(following) if following else 810
            instructions = [
                block
                for block in blocks
                if y_start < block["y"] < y_end
                and (
                    block["text"].startswith("Marca solo")
                    or block["text"].startswith("Selecciona todos")
                )
            ]
            if not instructions:
                continue
            instruction_y = min(block["y"] for block in instructions)
            title_blocks = [
                block
                for block in blocks
                if y_start - 2 <= block["y"] < instruction_y
                and any("Type3" in font for font in block["fonts"])
            ]
            title = " ".join(
                block["text"] for block in sorted(title_blocks, key=lambda item: (item["y"], item["x"]))
            ).strip()
            if not title or title == "[Navegación del cuestionario:]":
                continue

            options = []
            for block in sorted(blocks, key=lambda item: (item["y"], item["x"])):
                if not (instruction_y < block["y"] < y_end) or block["x"] < 100:
                    continue
                if any("Type3" in font or "Roboto-Italic" in font for font in block["fonts"]):
                    continue
                if block["text"] and block["text"] != "1 punto":
                    options.append(block["text"])

            questions.append(
                {
                    "key": (label, number),
                    "number": number,
                    "page": page_number,
                    "multi": instructions[0]["text"].startswith("Selecciona todos"),
                    "question": title,
                    "options": options,
                }
            )
    return questions


MULTI_OPTIONS = {
    ("T", 8): [
        "Se obtiene al extraer la estructura lógica de funciones de una aplicación.",
        "Está relacionado con el paralelismo a nivel de función.",
        "Está implícito en operaciones sobre vectores y matrices.",
        "Está relacionado con el paralelismo a nivel de bucle.",
    ],
    ("T", 9): [
        "Se obtiene al extraer la estructura lógica de funciones de una aplicación.",
        "Está relacionado con el paralelismo a nivel de función.",
        "Está implícito en operaciones sobre vectores y matrices.",
        "Está relacionado con el paralelismo a nivel de bucle.",
    ],
    ("T", 16): [
        "En un multiprocesador los procesadores comparten espacio de direcciones; en un multicomputador, cada nodo dispone del suyo.",
        "En un multiprocesador la ubicación física de los datos es transparente al programador; en un multicomputador debe gestionarse para comunicar.",
        "En un multiprocesador los datos se centralizan necesariamente en memoria secundaria.",
        "Un multiprocesador es MISD y un multicomputador es SISD.",
    ],
    ("T", 17): [
        "El SMP suele ofrecer menor latencia de comunicación que un multicomputador.",
        "El SMP suele escalar peor por la contención de los recursos compartidos.",
        "La comunicación es implícita mediante variables compartidas.",
        "La comunicación exige siempre send/receive y duplicación explícita de datos.",
    ],
    ("T", 59): [
        "Reparto cíclico: `for (i=idT; i<Iter; i+=nT)`.",
        "Reparto por bloques contiguos calculados con `idT`, `nT` e `Iter` antes de ejecutar el bucle.",
        "Reparto bajo demanda mediante un contador protegido por `lock/unlock`.",
        "Cola de tareas donde cada hebra solicita una iteración al terminar la anterior.",
    ],
    ("T", 71): [
        "Toda escritura debe hacerse visible a los demás procesadores en tiempo finito.",
        "Las escrituras sobre una misma dirección deben observarse en el mismo orden por todos los procesadores.",
        "Toda escritura debe propagarse necesariamente por difusión global.",
        "La serialización solo es necesaria para lecturas, no para escrituras.",
    ],
    ("T", 72): [
        "Toda escritura debe hacerse visible a los demás procesadores en tiempo finito.",
        "Las escrituras sobre una misma dirección deben observarse en el mismo orden por todos los procesadores.",
        "La red debe convertir cada escritura en una difusión global para ser escalable.",
        "El nodo home puede serializar las escrituras según el orden de llegada de las peticiones.",
    ],
    ("T", 89): [
        "Las operaciones de cada hebra deben parecer ejecutarse en orden de programa.",
        "Las operaciones de memoria deben poder situarse en un único orden global, como si fueran atómicas.",
        "Cada procesador debe ejecutar físicamente todas sus operaciones sin reordenamiento interno.",
        "La memoria solo necesita preservar el orden de las escrituras, no el de las lecturas.",
    ],
    ("T", 90): [
        "Pueden relajarse ciertos órdenes entre accesos a direcciones distintas, como W→R, W→W o R→W.",
        "Puede relajarse la atomicidad de propagación y permitir que una escritura sea visible antes para unos procesadores que para otros.",
        "Puede cambiarse el algoritmo para que varios procesadores escriban simultáneamente la misma dirección sin sincronización.",
        "Puede enviarse automáticamente cada operación al tipo de procesador que la ejecute mejor.",
    ],
    ("T", 97): [
        "Establecen un orden FIFO de adquisición mediante etiquetas o turnos.",
        "Establecen necesariamente un orden LIFO.",
        "Eliminan cualquier orden entre solicitantes para reducir latencia.",
        "Permiten que varias hebras con la misma etiqueta adquieran el cerrojo a la vez.",
    ],
}


MULTI_CORRECT = {
    ("T", 2): [0, 1, 2],
    ("T", 8): [0, 1],
    ("T", 9): [2, 3],
    ("T", 14): [2, 3],
    ("T", 15): [1, 2],
    ("T", 16): [0, 1],
    ("T", 17): [0, 1, 2],
    ("T", 18): [0, 1, 2],
    ("T", 20): [0, 1, 2, 4, 6],
    ("T", 31): [0, 1],
    ("T", 32): [2, 3],
    ("T", 33): [0, 1],
    ("T", 34): [0, 1],
    ("T", 35): [3, 4, 5],
    ("T", 40): [0, 1, 2],
    ("T", 41): [3],
    ("T", 42): [4],
    ("T", 56): [0, 1],
    ("T", 57): [0, 1, 2],
    ("T", 58): [0, 1],
    ("T", 59): [0, 1],
    ("T", 61): [0, 1, 2],
    ("T", 64): [2, 3, 4],
    ("T", 65): [0, 1, 2, 3, 4],
    ("T", 68): [0, 1],
    ("T", 71): [0, 1],
    ("T", 72): [0, 1, 3],
    ("T", 76): [0, 1],
    ("T", 77): [2, 3],
    ("T", 89): [0, 1],
    ("T", 90): [0, 1],
    ("T", 94): [0, 1, 2],
    ("T", 97): [0],
}


SINGLE_ANSWER = {
    # Teoría
    **{("T", n): a for n, a in {
        3: 3, 4: 0, 5: 0, 6: 1, 7: 2, 10: 0, 11: 0, 12: 0, 13: 1,
        19: 0, 21: 0, 22: 0, 25: 0, 26: 0, 27: 2, 28: 0, 29: 1,
        30: 0, 36: 1, 37: 0, 38: 0, 39: 2, 43: 0, 44: 1, 45: 2,
        46: 3, 47: 4, 48: 0, 49: 1, 50: 1, 51: 0, 52: 3, 53: 3,
        54: 2, 55: 0, 60: 0, 63: 3, 66: 0, 67: 1, 69: 0, 70: 1,
        73: 0, 74: 1, 75: 2, 78: 0, 79: 1, 81: 1, 82: 3, 83: 2,
        84: 0, 85: 1, 86: 2, 87: 3, 88: 0, 91: 0, 92: 0, 93: 0,
        95: 2, 96: 3, 98: 2, 99: 2, 100: 1, 101: 1, 102: 0,
        103: 1, 105: 0, 106: 2, 107: 0, 108: 2, 109: 3, 110: 2, 111: 3,
    }.items()},
    # Prácticas
    **{("P", n): a for n, a in {
        2: 0, 3: 0, 4: 3, 5: 0, 6: 0, 7: 3, 8: 2, 9: 2, 10: 0,
        11: 3, 13: 1, 14: 0, 15: 0, 16: 0, 17: 2, 18: 0, 19: 3,
        20: 1, 21: 0, 22: 0, 23: 0, 24: 1, 26: 1, 27: 1, 28: 3,
        29: 3, 30: 1, 31: 1, 33: 3, 34: 2, 35: 2, 36: 0, 38: 2,
        39: 1, 40: 1, 41: 3, 43: 0, 44: 2, 46: 1, 47: 1, 48: 0,
        49: 3, 51: 2, 52: 1, 53: 3, 54: 1, 55: 0, 57: 1, 58: 0,
    }.items()},
}


CUSTOM_SINGLE_OPTIONS = {
    ("T", 10): [
        "Estudia hardware y software para ejecutar aplicaciones sobre varios cores, procesadores o computadores que se presentan como una unidad de cómputo.",
        "Estudia exclusivamente sistemas distribuidos con recursos autónomos y administraciones independientes.",
        "Se limita a explotar ILP dentro de un único cauce superescalar, sin concurrencia entre flujos.",
        "Exige memoria físicamente compartida; por definición excluye multicomputadores y clústeres.",
    ],
    ("T", 22): [
        "`p=2`, `f=0,75` y `S=2/(1+0,75)=1,14`.",
        "`p=0,5`, `f=0,75` y `S=0,5/(1+0,75)=0,28`.",
        "`p=2`, `f=0,75` y `S=2/(1+0,25)=1,6`.",
        "`p=2`, `f=0,25` y `S=1/(0,25+0,75/2)=1,6`, porque f es la parte mejorada.",
    ],
    ("T", 30): [
        "Compiladores paralelos → abstracción alta; lenguajes paralelos y API con directivas → media; API de funciones → baja.",
        "API de funciones → alta; compiladores paralelos → media; lenguajes con directivas → baja.",
        "Lenguajes con directivas → alta; API de funciones → media; compiladores paralelos → baja.",
        "Los tres mecanismos ofrecen el mismo nivel de abstracción porque generan código paralelo.",
    ],
    ("T", 36): [
        "P0 reparte componentes distintas x0, x1, x2 y x3 entre P0-P3.",
        "P0 envía el mismo valor x a P0-P3.",
        "Todos los procesos intercambian un componente con todos los demás.",
        "P0-P3 envían sus valores a P0, que los concatena.",
    ],
    ("T", 37): [
        "P0-P3 envían x0-x3 a P0, que forma el vector (x0,x1,x2,x3).",
        "P0 envía el mismo valor x a todos los procesos.",
        "Cada proceso recibe el prefijo formado por los procesos anteriores.",
        "Cada proceso envía su valor al siguiente en una permutación circular.",
    ],
    ("T", 38): [
        "Cada Pi entrega xi a P(i+1) módulo p.",
        "P0 difunde x a todos los procesos.",
        "Todos los procesos construyen el mismo vector con los valores de todos.",
        "P0 recibe y concatena un valor procedente de cada proceso.",
    ],
    ("T", 39): [
        "Todos los procesos terminan con el vector completo (x0,x1,x2,x3).",
        "Cada proceso recibe exactamente un valor del proceso anterior.",
        "Pi obtiene f(x0,...,xi), de modo que los resultados contienen prefijos crecientes.",
        "P0 recibe todos los datos y los reduce a un único escalar.",
    ],
    ("T", 50): [
        "Un servidor responde peticiones independientes de varios clientes.",
        "Un maestro reparte tareas a trabajadores y recolecta sus resultados.",
        "Un árbol descompone recursivamente el problema y combina resultados.",
        "Una cadena de etapas aplica transformaciones sucesivas a cada dato.",
    ],
    ("T", 51): [
        "Un servidor responde peticiones independientes de varios clientes.",
        "Un maestro reparte tareas a trabajadores y recolecta sus resultados.",
        "Un árbol descompone recursivamente el problema y combina resultados.",
        "El dominio se divide en regiones vecinas que intercambian fronteras.",
    ],
    ("T", 52): [
        "Un servidor responde peticiones independientes de varios clientes.",
        "Un maestro asigna dinámicamente trabajos de una cola central.",
        "Un árbol descompone recursivamente el problema y combina resultados.",
        "El dominio se divide en regiones asignadas a procesos que cooperan e intercambian fronteras.",
    ],
    ("T", 53): [
        "Un servidor responde peticiones independientes.",
        "Un árbol divide el problema y combina sus hojas.",
        "Un maestro reparte tareas sin dependencias entre trabajadores.",
        "Varias etapas P1-P4 procesan en cauce elementos sucesivos.",
    ],
    ("T", 54): [
        "Un maestro reparte una cola plana de tareas.",
        "Un servidor procesa peticiones de clientes.",
        "Un árbol divide recursivamente el problema y combina los resultados parciales.",
        "Una cadena de etapas procesa un flujo continuo.",
    ],
    ("T", 60): [
        "Crear/terminar: morado; localizar: naranja; comunicar/sincronizar: verde; agrupar/asignar: amarillo.",
        "Crear/terminar: naranja; localizar: morado; comunicar/sincronizar: amarillo; agrupar/asignar: verde.",
        "Crear/terminar: verde; localizar: amarillo; comunicar/sincronizar: morado; agrupar/asignar: naranja.",
        "Crear/terminar: amarillo; localizar: verde; comunicar/sincronizar: naranja; agrupar/asignar: morado.",
    ],
    ("T", 48): [
        "Paso de mensajes explícito entre espacios de direcciones distintos.",
        "Variables compartidas con cargas y almacenamientos remotos transparentes.",
        "Paralelismo SIMD obligado por una única unidad de control.",
        "Memoria transaccional global sin operaciones send/receive.",
    ],
    ("T", 49): [
        "Paso de mensajes como único mecanismo para acceder a datos de otro procesador.",
        "Variables compartidas dentro de un espacio de direcciones común.",
        "Paralelismo de datos sin posibilidad de paralelismo de tareas.",
        "Memoria privada por nodo y comunicación exclusivamente mediante MPI.",
    ],
    ("T", 66): [
        "Cada escritura de caché actualiza también memoria principal.",
        "La memoria principal se actualiza solo al desalojar un bloque modificado.",
        "La escritura se propaga a las demás cachés, pero nunca a memoria principal.",
        "El bloque se invalida localmente y la escritura se difiere hasta una lectura posterior.",
    ],
    ("T", 67): [
        "Cada escritura de caché actualiza inmediatamente memoria principal.",
        "Un bloque modificado se escribe en memoria principal al ser reemplazado o desalojado.",
        "Toda escritura invalida la copia local y conserva las copias remotas.",
        "La memoria se actualiza al recibir cualquier lectura remota, aunque el bloque esté limpio.",
    ],
    ("T", 69): [
        "La nueva palabra se envía a las cachés que conservan copias para que las actualicen.",
        "Antes de escribir se invalidan todas las demás copias y solo queda válida la del escritor.",
        "Solo se actualiza memoria principal; las demás cachés mantienen temporalmente valores antiguos.",
        "Se invalida también la copia del escritor y la operación se repite tras un fallo de caché.",
    ],
    ("T", 70): [
        "La nueva palabra se transmite a todas las cachés que tienen el bloque.",
        "Se invalidan las copias remotas antes de que el procesador complete su modificación local.",
        "Se actualiza exclusivamente memoria principal y no se envía ninguna transacción de coherencia.",
        "Se convierten todas las copias remotas a estado Exclusivo para serializar futuras escrituras.",
    ],
    ("T", 73): [
        "Para buses o redes donde la difusión de cada transacción es eficiente y observable por todas las cachés.",
        "Para redes escalables sin difusión, consultando un directorio home por cada bloque.",
        "Solo para jerarquías de directorios distribuidos sin ningún medio compartido.",
        "Para memorias NORMA, donde no existe caché de datos compartidos.",
    ],
    ("T", 74): [
        "Para buses pequeños, haciendo que todas las cachés espíen cada transacción.",
        "Para redes sin difusión o escalables, manteniendo información sobre propietarios y compartidores.",
        "Solo para redes jerárquicas que combinan obligatoriamente buses y anillos.",
        "Para sustituir la coherencia por consistencia secuencial y evitar estados MSI/MESI.",
    ],
    ("T", 75): [
        "Para un único bus plano con difusión global y sin niveles de interconexión.",
        "Para una red sin difusión usando exclusivamente un directorio central monolítico.",
        "Para combinar coherencia dentro y entre niveles de una jerarquía de buses o redes escalables.",
        "Para desactivar la coherencia entre grupos y confiar solo en barreras de software.",
    ],
    ("T", 81): [
        "Es la única copia válida y difiere de memoria principal.",
        "El bloque está limpio respecto de memoria y puede existir en otras cachés.",
        "La línea no contiene un bloque utilizable por el procesador.",
        "Es la única copia en caché, está limpia y puede escribirse sin transacción previa.",
    ],
    ("T", 83): [
        "Es la única copia válida y está modificada respecto de memoria.",
        "Está limpia y puede estar replicada en varias cachés.",
        "La línea no contiene una copia válida del bloque para atender el acceso.",
        "Es una copia exclusiva limpia pendiente de confirmación del directorio.",
    ],
    ("T", 88): [
        "Puede existir una copia válida en una o varias cachés, según el estado de coherencia.",
        "Debe existir exactamente una copia válida en todo el sistema.",
        "Solo es válido si memoria principal y todas las cachés contienen simultáneamente el mismo dato.",
        "Es válido únicamente cuando ninguna caché lo almacena y se lee desde memoria principal.",
    ],
    ("T", 98): [
        "Atómicamente: `temp=x; x=x+a; return temp;`.",
        "Atómicamente: si `x==a`, intercambiar `x` y `b` y devolver el valor observado.",
        "Atómicamente: `temp=x; x=1; return temp;`.",
        "Atómicamente: `temp=x; x=0; return temp;`.",
    ],
    ("T", 99): [
        "Atómicamente: `temp=x; x=1; return temp;`.",
        "Atómicamente: si `x==a`, sustituirlo por `b`.",
        "Atómicamente: `temp=x; x=x+a; return temp;`.",
        "Atómicamente: devolver `x+a` sin modificar x.",
    ],
    ("T", 100): [
        "Atómicamente: `temp=x; x=1; return temp;`.",
        "Atómicamente: comparar x con a; si coinciden, escribir b y devolver el valor anterior.",
        "Atómicamente: `temp=x; x=x+a; return temp;`.",
        "Atómicamente: intercambiar x y b sin comprobar el valor esperado a.",
    ],
    ("T", 101): [
        "`while (test_and_set(k) == 0) {}`",
        "`while (test_and_set(k) == 1) {}`",
        "`do { test_and_set(k); } while (b == 1);` sin recoger el valor devuelto",
        "`while (test_and_set(k) != k) {}`",
    ],
    ("T", 102): [
        "`while (fetch_or(k, 1) == 1) {}`",
        "`while (fetch_or(k, 1) == 0) {}`",
        "`b=0; do { fetch_or(k,b); } while (b==1);`",
        "`while (fetch_or(k, 0) == 0) {}`",
    ],
    ("T", 103): [
        "`while (compare_swap(0,1,k) == 0) {}` interpretando el retorno como valor anterior.",
        "`b=1; do { compare_swap(0,b,k); } while (b==1);` donde b recibe el valor observado.",
        "`while (compare_swap(0,1,k) == 1) {}` sin recuperar el valor observado.",
        "`b=0; do { compare_swap(1,b,k); } while (b==0);`.",
    ],
    ("P", 15): [
        "El resultado es correcto; la barrera tras `omp for` es redundante, la situada antes de `single` es necesaria y el incremento podría protegerse con `atomic`.",
        "Ambas barreras explícitas pueden eliminarse porque `critical` incluye una barrera global al salir.",
        "La primera barrera es necesaria y la segunda redundante, ya que `single` espera a las demás hebras antes de entrar.",
        "Cambiar `critical` por `atomic` introduce una carrera porque `atomic` no admite actualizaciones de suma.",
    ],
    ("P", 28): [
        "Abrir `parallel private(j)` y hacer que todas las hebras recorran el mismo bucle exterior i compartido; dentro, usar `omp for reduction(+:v2[i])` sobre j.",
        "Usar `parallel for private(j)` sobre el bucle exterior i y ejecutar secuencialmente todas las columnas j de cada fila.",
        "Abrir `parallel private(i,j)` sin `omp for`, de modo que cada hebra recorra por completo las N filas y las N columnas.",
        "Abrir `parallel private(i)`; hacer que todas las hebras avancen coordinadamente por i y, para cada fila, repartir j con `omp for reduction(+:v2[i])`.",
    ],
    ("P", 53): [
        "Recalcular ambos sumatorios completos para cada repetición y seleccionar con un `if`.",
        "Recalcular ambos sumatorios en un único bucle para cada repetición y usar `std::min`.",
        "Precalcular dos vectores auxiliares y volver a recorrerlos completos en cada repetición.",
        "Calcular una vez las sumas invariantes de `a` y `b` y derivar cada resultado mediante una expresión cerrada.",
    ],
    ("P", 54): [
        "Ninguna: `-Os` conserva siempre una multiplicación en C sin generar ensamblador.",
        "`imul $6, %edi, %eax; ret`.",
        "`lea (%rdi,%rdi,2), %eax; add %eax,%eax; ret`.",
        "Prólogo de pila y tres instrucciones `add` para sumar seis copias.",
    ],
    ("P", 57): [
        "Sustituir el bucle por `4*n` usando una sola instrucción `lea`.",
        "Mantener un bucle que calcula `i % 5`, suma el resto más uno y termina al alcanzar n.",
        "Sustituir el bucle por `3*n` usando una sola instrucción `lea`.",
        "Ninguna implementación puede preservar el resultado para todo n.",
    ],
}


QUESTION_SUFFIX = {
    ("T", 5): "\n\nCódigo: `a=b+c; ...; d=a+c;` (el código intermedio no usa a).",
    ("T", 6): "\n\nCódigo: `a=b+c; ...; a=d+e;`.",
    ("T", 7): "\n\nCódigo: `b=a+1; ...; a=d+e;`.",
    ("T", 25): "\n\nLa expresión propuesta es `S = Ts / (Ts/p + p²)`.",
    ("T", 28): "\n\nLa expresión propuesta es `S = p / (1 + f(p-1))`.",
    ("T", 105): "\n\nSecuencia: `1 LD r1,0(r2); 2 MUL r6,r4,r2; 3 LD r8,0(r3); 4 ADD r1,r8,r1; 5 ADD r6,r6,r1; 6 MUL r7,r6,r2; 7 LD r8,0(r4); 8 ADD r9,r8,r1`.",
    ("T", 106): "\n\nUse el cauce y la secuencia de ocho instrucciones descritos en el enunciado: ancho 3, emisión desordenada, LD de dos etapas, ADD de una y MUL de cuatro.",
    ("T", 107): "\n\nUse el cauce y la secuencia de ocho instrucciones descritos en el enunciado: ancho 3, emisión desordenada, LD de dos etapas, ADD de una y MUL de cuatro.",
    ("T", 108): "\n\nUse el cauce y la secuencia de ocho instrucciones descritos en el enunciado: ancho 3, emisión desordenada, LD de dos etapas, ADD de una y MUL de cuatro.",
    ("T", 109): "\n\nUse el cauce y la secuencia de ocho instrucciones descritos en el enunciado: ancho 3, emisión desordenada, LD de dos etapas, ADD de una y MUL de cuatro.",
    ("T", 110): "\n\nCódigo: `for(i=0;i<8;i++) for(j=i;j<8;j++) v2[i] += m[i][j]*v1[j];`.",
    ("T", 111): "\n\nCódigo de referencia: `for(i=0;i<8;i++) for(j=i;j<8;j++) v2[i] += m[i][j]*v1[j];`.",
    ("P", 15): "\n\n```c\n#pragma omp parallel private(sumalocal)\n{\n  sumalocal=0;\n  #pragma omp for\n  for(i=0;i<n;i++) sumalocal += a[i];\n  #pragma omp barrier\n  #pragma omp critical\n  suma += sumalocal;\n  #pragma omp barrier\n  #pragma omp single\n  printf(\"La suma es=%d\\n\", suma);\n}\n```",
    ("P", 16): "\n\n```c\na=0;\nfor(i=0;i<10;i++) b[i]=-1;\n#pragma omp parallel\n{\n  #pragma omp single\n  { a=1; printf(\"Ejecutada por: %d.\", omp_get_thread_num()); }\n  #pragma omp for\n  for(i=0;i<10;i++) b[i]=a;\n}\nprintf(\"b[3]=%d\",b[3]);\n```",
    ("P", 18): "\n\nCódigo: una región `parallel` contiene un `single` que ejecuta `printf(\"x\")`.",
    ("P", 19): "\n\nCódigo: una región `parallel` contiene un `critical` que ejecuta `printf(\"x\")`.",
    ("P", 20): "\n\nEl código calcula sumas locales con `omp for`, las acumula dentro de `critical` y las imprime en `single`; hay una barrera explícita antes de `critical` y otra antes de `single`.",
    ("P", 26): "\n\nCódigo: `int i,n=1; #pragma omp parallel for default(none) private(i) for(i=0;i<5;i++) n+=i;`.",
    ("P", 27): "\n\nCódigo: `int n=6,ret=1; #pragma omp parallel reduction(+:ret) for(i=omp_get_thread_num(); i<omp_get_max_threads(); i+=omp_get_num_threads()) ret+=i;`.",
    ("P", 28): "\n\nSe desea paralelizar el índice de columnas j; el resultado `v2[i]` es compartido y debe combinarse mediante una reducción.",
    ("P", 30): "\n\nCódigo: `int n=1; #pragma omp parallel for firstprivate(n) lastprivate(n) for(int i=0;i<5;i++) n+=1;`.",
    ("P", 31): "\n\nCódigo: `int n=1; #pragma omp parallel for firstprivate(n) lastprivate(n) for(int i=0;i<5;i++) n+=i;`.",
    ("P", 33): "\n\nLas alternativas usan, sin reducción: (a) `parallel for` con `sum+=i`; (b) `parallel` y cada hebra recorre todos los impares; (c) dos `section` que actualizan el mismo `sum`.",
    ("P", 34): "\n\nCódigo: `int n=0; #pragma omp parallel for reduction(*:n) for(int i=n;i<size;i++) n+=i;`.",
    ("P", 35): "\n\nCódigo: `int n=6,ret=1; #pragma omp parallel reduction(+:ret) private(i) for(i=omp_get_thread_num();i<n;i+=omp_get_num_threads()) ret+=i;`.",
    ("P", 40): "\n\nCódigo: `omp_set_num_threads(4); #pragma omp parallel num_threads(2) printf(\"hello\\n\");`.",
    ("P", 44): "\n\nCódigo: `n=omp_get_max_threads()/4; #pragma omp parallel for num_threads(6) if(n>6) for(i=0;i<n;i++) printf(\"h:%d\",omp_get_thread_num());`.",
    ("P", 49): "\n\nCódigo: `N=omp_get_max_threads(); omp_set_num_threads(2); #pragma omp parallel for num_threads(6) if(N>=4) schedule(static) for(i=0;i<12;i++) ...`.",
    ("P", 52): "\n\nEl bucle evalúa `v[i]%3`: si vale cero llama a `foo(v[i])`; si no, un `switch` llama a `foo(v[i]+2)` o `foo(v[i]+1)`.",
    ("P", 53): "\n\nDatos: `N=5000`, `REP=40000`, `struct S {int a,b;} s[N]`; para cada repetición se comparan dos sumas lineales sobre `s[].a` y `s[].b`.",
    ("P", 54): "\n\nFunción fuente: `int f(int x) { return x*6; }`.",
    ("P", 57): "\n\nFunción fuente: `int f(int n) { int s=0; for(int i=0;i<n;i++) s += i%5+1; return s; }`.",
}

QUESTION_REPLACE = {
    ("T", 60): "En el código OpenMP del cálculo de pi, `parallel` aparece en morado, `omp for` en naranja, `reduction` en verde y `schedule(dynamic)` en amarillo. ¿Qué correspondencia con las fases de paralelización es correcta?",
    ("T", 105): "(A) El cauce de un superescalar tiene cuatro etapas: IF (1 ciclo, ancho 3 instrucciones/ciclo), ID (1 ciclo, ancho 3), EX (latencia de 1 a 4 ciclos según la unidad) y WB (1 ciclo, retirada de hasta 3 instrucciones/ciclo desde el ROB). Hay una unidad de carga segmentada en dos etapas, una unidad de almacenamiento de un ciclo, dos unidades ADD de un ciclo, una unidad MUL segmentada en cuatro etapas y una unidad de saltos de un ciclo. La emisión es desordenada, el ROB y la ventana centralizada no limitan el número de entradas y pueden emitirse hasta tres instrucciones por ciclo. ¿Cuántos ciclos tarda en completarse el cauce?",
    ("P", 7): "¿Qué orden crea un único proceso OpenMP con 12 hebras, asignando cada hebra a un core físico distinto de un nodo atcgrid[1-3]?",
    ("P", 36): "¿Qué relación correcta existe entre directivas y cláusulas de OpenMP?",
    ("P", 58): "¿Qué afirmación general sobre la optimización de código es correcta?",
}


def metadata(key: tuple[str, int]) -> tuple[str, str, str]:
    label, number = key
    if label == "P":
        if number <= 11:
            return "Prácticas", "Seminario 0 - Entorno de programación", "SLURM y arquitectura de atcgrid"
        if number <= 24:
            return "Prácticas", "Seminario 1 - Directivas OpenMP", "Regiones, reparto y sincronización"
        if number <= 36:
            return "Prácticas", "Seminario 2 - Cláusulas OpenMP", "Cláusulas de datos y reducciones"
        if number <= 49:
            return "Prácticas", "Seminario 3 - Interacción con el entorno en OpenMP", "ICV, planificación y prestaciones"
        return "Prácticas", "Seminario 4 - Optimización de código en arquitecturas ILP", "Transformaciones y optimización del compilador"

    if number <= 20:
        return "Teoría", "Tema 1 - Arquitecturas paralelas: clasificación y prestaciones", "Lección 1 - Paralelismo implícito y clasificación"
    if number <= 22:
        return "Teoría", "Tema 1 - Arquitecturas paralelas: clasificación y prestaciones", "Lección 3 - Prestaciones y ley de Amdahl"
    if number <= 54:
        return "Teoría", "Tema 2 - Programación paralela", "Lección 4 - Herramientas, estructuras y comunicaciones colectivas"
    if number <= 61:
        return "Teoría", "Tema 2 - Programación paralela", "Lección 5 - Descomposición, asignación y sobrecarga"
    if number <= 88:
        return "Teoría", "Tema 3 - Arquitecturas con paralelismo a nivel de thread (TLP)", "Lección 8 - Coherencia de caché y protocolos"
    if number <= 103:
        return "Teoría", "Tema 3 - Arquitecturas con paralelismo a nivel de thread (TLP)", "Lecciones 9 y 10 - Consistencia y sincronización"
    return "Teoría", "Tema 4 - Arquitecturas con paralelismo a nivel de instrucción (ILP)", "Planificación dinámica y predicción de saltos"


def composite_options(options: list[str], correct: list[int], seed: int) -> tuple[list[str], int]:
    good = [options[index] for index in correct]
    wrong = [option for index, option in enumerate(options) if index not in correct]
    correct_text = "Son correctas exactamente: " + "; ".join(good)
    candidates = [
        correct_text,
        "Es correcta únicamente: " + good[0],
        "Son correctas exactamente: " + "; ".join((good[:-1] or good) + (wrong[:1] or [])),
        "Son correctas todas las afirmaciones propuestas." if wrong else "No es correcta ninguna afirmación propuesta.",
    ]
    shift = seed % 4
    rotated = candidates[shift:] + candidates[:shift]
    return rotated, rotated.index(correct_text)


def normalize_single(key: tuple[str, int], options: list[str], answer: int) -> tuple[list[str], int]:
    if key in TRUE_FALSE:
        return ["Verdadero", "Falso"], answer
    if key in CUSTOM_SINGLE_OPTIONS:
        return CUSTOM_SINGLE_OPTIONS[key], answer
    correct = options[answer]
    if len(options) > 4:
        selected = [correct] + [option for index, option in enumerate(options) if index != answer][:3]
    else:
        selected = list(options)
        extras = [
            "No puede determinarse con la información proporcionada.",
            "Ninguna de las anteriores: se confunden propiedades de modelos distintos.",
            "Todas las opciones anteriores son simultáneamente correctas.",
        ]
        for extra in extras:
            if len(selected) == 4:
                break
            if extra not in selected:
                selected.append(extra)
    shift = key[1] % 4
    selected = selected[shift:] + selected[:shift]
    return selected, selected.index(correct)


def explanation_for(key: tuple[str, int], correct_option: str, subtopic: str) -> str:
    special = {
        ("T", 22): "La parte no mejorada es 0,75 y el recurso mejora por 2: S=2/(1+0,75)=1,14.",
        ("T", 27): "El trabajo secuencial equivalente es 10+5·10=60 ns y el tiempo paralelo 20 ns; S=3.",
        ("T", 29): "En Gustafson f se mide sobre el tiempo paralelo: 10/20=0,5.",
        ("T", 105): "Al calendarizar dependencias y latencias, la última multiplicación completa WB en el ciclo 12.",
        ("T", 106): "Tras decodificar los tres grupos, las ocho instrucciones ya han entrado en el ROB al considerar el ciclo 5.",
        ("T", 107): "La instrucción 5 espera los resultados de la MUL 2 y del ADD 4 y puede emitirse en el ciclo 7.",
        ("T", 108): "La instrucción 8 permanece tres ciclos en la ventana hasta que están disponibles r8 y r1.",
        ("T", 109): "Al terminar el ciclo 5 ya están disponibles los resultados de las dos cargas que alimentan el ADD 4.",
        ("T", 111): "El salto interno se ejecuta 8+7+…+1=36 veces.",
        ("P", 8): "Hay cuatro nodos de cómputo con placa de doble zócalo: ocho sockets en total.",
        ("P", 11): "Cada atcgrid[1-3] tiene dos Xeon E5645 de 12 hebras lógicas: 24 por nodo.",
        ("P", 27): "La reducción suma 0+1+2+3 al valor inicial 1, por lo que ret termina en 7.",
        ("P", 30): "lastprivate copia el valor de la hebra que ejecuta la última iteración; su acumulado depende del reparto y del número de hebras.",
        ("P", 31): "La hebra de la última iteración puede haber ejecutado otras iteraciones; lastprivate hace depender n del reparto.",
        ("P", 34): "La identidad privada de la reducción multiplicativa es 1, pero el valor original compartido es 0 y el resultado combinado permanece 0.",
        ("P", 35): "Las hebras suman exactamente 0+1+…+5=15 y la reducción lo combina con el valor inicial 1: ret=16.",
        ("P", 49): "N vale 4, la cláusula if activa seis hebras y schedule(static) reparte 12 iteraciones: dos para la maestra.",
    }
    reason = special.get(key, f"La distinción aplicada corresponde a {subtopic.lower()} según el temario.")
    return f"Respuesta correcta: «{correct_option}». {reason}"


def build_questions() -> list[dict]:
    extracted = []
    for label, pdf in PDFS.items():
        extracted.extend(parse_pdf(pdf, label))

    result = []
    for item in extracted:
        key = item["key"]
        if key in SKIP:
            continue
        if key in MULTI_OPTIONS:
            item["options"] = MULTI_OPTIONS[key]
        if key in QUESTION_REPLACE:
            item["question"] = QUESTION_REPLACE[key]
        if key in QUESTION_SUFFIX:
            item["question"] += QUESTION_SUFFIX[key]

        if item["multi"]:
            if key not in MULTI_CORRECT:
                raise KeyError(f"Falta solución múltiple para {key}")
            options, answer = composite_options(item["options"], MULTI_CORRECT[key], item["number"])
            question_type = "Opción múltiple combinada"
        else:
            if key not in SINGLE_ANSWER:
                raise KeyError(f"Falta solución para {key}")
            options, answer = normalize_single(key, item["options"], SINGLE_ANSWER[key])
            question_type = "Verdadero/Falso" if key in TRUE_FALSE else "Opción múltiple"

        block, topic, subtopic = metadata(key)
        source_name = "AutoTests de AC - Todos los temas" if key[0] == "T" else "Tests de AC - Todas las bps"
        result.append(
            {
                "bloque": block,
                "tema": topic,
                "subtema": subtopic,
                "dificultad": "Alta",
                "tipo": question_type,
                "question": item["question"],
                "options": options,
                "answer": answer,
                "explanation": explanation_for(key, options[answer], subtopic),
                "source": f"{source_name} · Pregunta {item['number']} · página {item['page']}",
                "_key": key,
            }
        )

    if len(result) != 154:
        raise AssertionError(f"Se esperaban 154 preguntas nuevas y se obtuvieron {len(result)}")
    return result


def adapted_true_false(source: dict) -> dict:
    key = tuple(source.pop("_key"))
    correct = source["answer"] == 0
    statement = source["question"]
    rationales = {
        ("T", 19): [
            "Es verdadera: NORMA es un multicomputador con memorias privadas y comunicación explícita, sin espacio global compartido.",
            "Es falsa: NORMA designa un NUMA coherente cuyo directorio elimina el paso de mensajes.",
            "Es verdadera: NORMA es un UMA distribuido que mantiene latencia uniforme mediante snooping.",
            "Es falsa: todo MIMD con memoria distribuida se clasifica necesariamente como CC-NUMA.",
        ],
        ("T", 25): [
            "Es verdadera: con paralelismo ilimitado el trabajo útil tarda Ts/p y la sobrecarga p² se suma al tiempo paralelo.",
            "Es falsa: la sobrecarga debe multiplicar Ts/p, no sumarse, por lo que S=p/(1+p²).",
            "Es verdadera solo si p² representa trabajo útil; si es overhead debe restarse del numerador.",
            "Es falsa: una fracción secuencial nula obliga a S=p con independencia de cualquier sobrecarga.",
        ],
        ("T", 26): [
            "Es verdadera: mientras p<n hay paralelismo suficiente, no existe parte secuencial ni overhead, y Tp=Ts/p.",
            "Es falsa: el límite n solo se aplica cuando p≤n/2; a partir de ahí la aceleración es n-p.",
            "Es verdadera únicamente para p=n; si p<n quedan tareas sin procesador y S<p.",
            "Es falsa: incluso sin overhead la ley de Amdahl limita S a 1/(1-f)=1 cuando f=0.",
        ],
        ("T", 28): [
            "Es verdadera: `S=p/(1+f(p-1))` es algebraicamente equivalente a `1/(f+(1-f)/p)`.",
            "Es falsa: el denominador correcto es `1+(1-f)(p-1)` porque f representa la parte paralela.",
            "Es verdadera solo para f=0; con f>0 debe usarse la ley escalada de Gustafson.",
            "Es falsa: con paralelismo ilimitado p desaparece y la aceleración siempre es exactamente 1/f.",
        ],
    }
    options = rationales[key]
    if not correct:
        options[0], options[1] = options[1], options[0]
    answer = 0
    adapted = {field: value for field, value in source.items() if field != "id"}
    adapted.update(
        {
            "tipo": "Opción múltiple adaptada",
            "question": "Analiza el enunciado y elige la única valoración técnicamente completa:\n\n«" + statement + "»",
            "options": options,
            "answer": answer,
            "explanation": options[answer],
            "source": source["source"] + " · reformulación de cuatro opciones",
        }
    )
    return adapted


def write_preserving_repository_format(bank: list[dict]) -> None:
    base_json = subprocess.check_output(
        ["git", "show", "HEAD:banco-preguntas-ac.json"], cwd=ROOT, text=True
    )
    base_bank = json.loads(base_json)
    base_count = len(base_bank)
    if base_count < len(bank):
        additions_json = json.dumps(bank[base_count:], ensure_ascii=False, indent=4)
        combined_json = base_json.rstrip()[:-1].rstrip() + ",\n" + additions_json[2:] + "\n"
    elif base_count == len(bank):
        combined_json = base_json
        for old, new in zip(base_bank, bank):
            if old == new:
                continue
            object_text = "\n".join("    " + line for line in json.dumps(new, ensure_ascii=False, indent=4).splitlines())
            id_marker = f'\n        "id": {new["id"]}\n'
            id_position = combined_json.find(id_marker)
            if id_position < 0:
                raise RuntimeError(f"No se pudo actualizar el objeto con id {new['id']}")
            object_start = combined_json.rfind("\n    {", 0, id_position) + 1
            object_end = combined_json.find("\n    }", id_position) + len("\n    }")
            if object_start <= 0 or object_end < len("\n    }"):
                raise RuntimeError(f"No se pudieron delimitar los datos del objeto con id {new['id']}")
            combined_json = combined_json[:object_start] + object_text + combined_json[object_end:]
    else:
        raise RuntimeError(f"HEAD contiene {base_count} preguntas pero el banco solo {len(bank)}")
    JSON_PATH.write_text(combined_json, encoding="utf-8")

    base_html = subprocess.check_output(
        ["git", "show", "HEAD:test-ac-arquitectura-computadores.html"], cwd=ROOT, text=True
    )
    prefix = "const allQuizQuestionsData = "
    suffix = "\n];\n\nlet filteredQuestions"
    start = base_html.index(prefix) + len(prefix)
    end = base_html.index(suffix, start) + 2
    html = base_html[:start] + combined_json.strip() + base_html[end:]
    HTML_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    try:
        bank = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        bank = json.loads(
            subprocess.check_output(
                ["git", "show", "HEAD:banco-preguntas-ac.json"], cwd=ROOT, text=True
            )
        )
    if any("AutoTests de AC - Todos los temas · Pregunta" in q.get("source", "") for q in bank):
        for question in bank:
            for key, title in QUESTION_REPLACE.items():
                source_name = "AutoTests de AC - Todos los temas" if key[0] == "T" else "Tests de AC - Todas las bps"
                if question.get("source", "").startswith(f"{source_name} · Pregunta {key[1]} "):
                    question["question"] = title + QUESTION_SUFFIX.get(key, "")
                    break
            for key, options in CUSTOM_SINGLE_OPTIONS.items():
                source_name = "AutoTests de AC - Todos los temas" if key[0] == "T" else "Tests de AC - Todas las bps"
                if question.get("source", "").startswith(f"{source_name} · Pregunta {key[1]} "):
                    question["options"] = options
                    question["answer"] = SINGLE_ANSWER[key]
                    question["explanation"] = explanation_for(
                        key, options[question["answer"]], question["subtema"]
                    )
                    break
        write_preserving_repository_format(bank)
        print(f"Formato restaurado; total existente: {len(bank)}")
        return

    additions = build_questions()
    tf_sources = [question.copy() for question in additions if tuple(question["_key"]) in TRUE_FALSE]
    for question in additions:
        question.pop("_key", None)
    additions.extend(adapted_true_false(question) for question in tf_sources)

    next_id = max(question["id"] for question in bank) + 1
    for offset, question in enumerate(additions):
        question["id"] = next_id + offset
    bank.extend(additions)

    write_preserving_repository_format(bank)

    print(f"Añadidas {len(additions)} preguntas; total: {len(bank)}")


if __name__ == "__main__":
    main()
