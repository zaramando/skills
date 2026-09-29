# skills

Skills propias para Claude Code. Cada directorio de la raíz es una skill (`<nombre>/SKILL.md`, más
`references/`, `assets/` o `scripts/` cuando los necesita). Se instalan con un symlink en
`~/.claude/skills/`.

| Skill | Para qué |
|-------|----------|
| `skill-author` | Crear o reconstruir una skill |
| `prompt-review` | Auditar un prompt, CLAUDE.md o SKILL.md existente |
| `ux-benchmark` | Comparar un flujo de producto entre competidores a partir de videos |
| `youtube-search`, `youtube-transcript`, `youtube-screenshot` | Buscar videos, bajar transcripciones y capturar fotogramas |
| `storm-*` | Event Storming socrático (ver abajo) |

## Event Storming socrático (`storm-*`)

### Qué es

Una suite de seis skills para destilar el dominio de un negocio preguntándole a quienes lo conocen
(las **voces**). La IA facilita: hace una pregunta por vez, devuelve lo que entendió con las
palabras de quien respondió y solo escribe después de un "sí" explícito. No completa el modelo: no
propone eventos, nombres, actores ni reglas que nadie dijo.

El resultado queda en el repo del proyecto, no en el de las skills:

```
docs/domain/<slug>/
  eventstorm.yaml    # fuente de verdad, pensada para agentes
  eventstorm.html    # tablero generado para humanos; nunca se edita a mano
```

### Instalación

Se instala con un symlink por skill desde tu clon del repo. Se usan symlinks y no copias para que
un `git pull` en el clon actualice las skills instaladas.

1. Clona el repo en la carpeta que prefieras. La ruta es libre; `~/src/skills` es solo un ejemplo:

   ```bash
   git clone https://github.com/zaramando/skills.git ~/src/skills
   ```

2. Entra a la carpeta clonada (los symlinks se crean desde acá):

   ```bash
   cd ~/src/skills
   ```

3. Crea `~/.claude/skills` si no existe:

   ```bash
   mkdir -p ~/.claude/skills
   ```

4. Crea los seis symlinks apuntando a tu clon (`$PWD` es la ruta real donde lo clonaste):

   ```bash
   for s in storm-start storm-big-picture storm-process storm-design storm-render storm-verify; do ln -s "$PWD/$s" ~/.claude/skills/$s; done
   ```

5. Verifica que los seis apunten a tu clon:

   ```bash
   ls -l ~/.claude/skills | grep storm-
   ```

`storm-start` es obligatoria: las otras cinco la leen como carpeta hermana (`../storm-start`) para
el protocolo, el esquema, la paleta y los scripts. Por eso los seis symlinks deben apuntar al mismo
clon. Si mueves o borras el clon, los symlinks quedan rotos: bórralos y vuelve a crearlos desde la
nueva ubicación.

Los scripts necesitan Python 3 y PyYAML (solo biblioteca estándar más PyYAML). Sin PyYAML salen con
código 2 y lo dicen; la skill te pide permiso antes de instalarlo.

```bash
python3 -m pip install pyyaml
```

Para desinstalar, borra los symlinks (esto no toca tu clon):

```bash
for s in storm-start storm-big-picture storm-process storm-design storm-render storm-verify; do rm ~/.claude/skills/$s; done
```

### Cómo se invocan

Las seis tienen `disable-model-invocation: true`: el modelo no las carga solo ni puede encadenarlas.
Se escribe el comando al inicio del mensaje, no dentro de una frase:

```
/storm-start biblioteca
```

El slug es opcional. Sin él, la skill busca `docs/domain/*/eventstorm.yaml`: si hay uno lo usa, si
hay varios pregunta cuál, si no hay ninguno solo `storm-start` crea el espacio de trabajo. Cada
skill termina diciéndote qué comando correr después.

### El flujo

```
storm-start → storm-big-picture → storm-process → storm-design
                  storm-render y storm-verify: en cualquier momento
```

| Skill | Qué pregunta | Qué llena en el YAML |
|-------|--------------|----------------------|
| `/storm-start` | Nombre del dominio, quiénes responden, qué entra y qué queda fuera (y por qué), si hay material previo; qué nivel sigue | `domain` (nombre, slug, alcance, exclusiones, `sources`), `speakers`, `session`; decisiones de saltar o reabrir un nivel |
| `/storm-big-picture` | Qué pasó, en pasado y en palabras del negocio; en qué orden; qué momento cambia todo; quiénes participan; qué pasa cuando sale mal | `events`, `actors`, `external_systems`, `flows` (con eventos pivote y caminos de falla); fronteras candidatas como hotspots |
| `/storm-process` | Sobre las historias que tú eliges: qué dispara cada evento, quién hace la acción, qué mira para decidir, qué pasa si se rechaza, falla o se demora, qué reacción sigue | `commands`, `policies`, `read_models`, `triggered_by`, `failure_paths`, `walked.process` |
| `/storm-design` | Qué haría que algo deje de ser lo que es (con casos límite), qué reglas deben cumplirse juntas, si una misma palabra en dos áreas es lo mismo, qué deja fuera el modelo; nombres en código solo si aceptas | `invariants`, `aggregates`, `bounded_contexts`, `glossary[].invariants`/`validations`/`bounded_context`, exclusiones |
| `/storm-render` | Nada | Regenera `eventstorm.html`. No valida |
| `/storm-verify` | Nada | Solo reporta: corre los chequeos estructurales y dice qué sesión corrige cada falla. No edita |

Saltar un nivel o reabrir uno cerrado se decide solo en `/storm-start`, como decisión con autores,
motivo y alternativas. Las skills de nivel no lo hacen: te mandan de vuelta ahí.

**Retomar.** Todo el estado vive en el bloque `session` del YAML: nivel actual, estado de cada nivel,
etapa, pregunta pendiente por nivel (`pending_questions.start`, `big-picture`, `process`,
`design`) y siguiente paso. Cada corrida lo escribe al terminar, aunque la cortes a la mitad; la
siguiente empieza por la pregunta pendiente. La excepción es el arranque: hasta que existen nombre y
al menos una voz no hay archivo, y un arranque interrumpido empieza de nuevo.

**Cerrar un nivel.** Solo cierra si `verify.py --close <nivel>` sale con 0. Lo bloquean:

- hotspots bloqueantes abiertos de ese nivel o de uno anterior;
- en `process`, historias elegidas sin recorrer y eventos o comandos del alcance sin disparador o
  sin sus tres caminos de falla resueltos;
- en `big-picture` y `design`, además, lo que la skill revisa antes de correr el gate (eventos sin
  confirmar ni anotados como abiertos; palabras, acciones o reglas sin agrupar).

Cada `FAIL` se convierte en la siguiente pregunta. La lista completa de chequeos está en
`verify.py --list`, que es la única fuente.

### Reglas que conviene conocer

- **Nada entra confirmado sin ti.** Cada respuesta tiene una devolución ("lo anotaría así… ¿es
  así?"). Un "más o menos" es un no.
- **"No sé" es una respuesta.** Queda como desconocido visible (`{desconocido: <hs-id>}` más un
  hotspot), nunca como un dato inventado. El resto de la regla que sí diste entra igual.
- **La severidad la fija una regla, no se pregunta.** Un conflicto entre voces y una frontera
  candidata cuyos casos tuvieron veredictos opuestos son siempre bloqueantes, y ninguna voz puede
  bajarlos. Lo demás es no bloqueante salvo que una voz lo suba.
- **Varias voces.** Cada respuesta lleva `speaker`. Si dos voces se contradicen, el elemento queda
  `disputado` y ninguna gana hasta una decisión que ambas acepten.
- **Los términos quedan en el idioma de quien habla**, sin traducir. Un nombre para el código
  (`code_name`) es opcional y siempre una decisión con autor.
- **Material previo** (transcripciones, documentos, código legado) genera preguntas, no respuestas:
  entra como hipótesis sin autor hasta que una voz la adopta.

### Leyenda del tablero

Colores de `storm-start/assets/palette.json`, única fuente; `render.py` dibuja la leyenda desde ahí.

<img src="storm-start/assets/legend.svg" width="768" alt="Leyenda del tablero: una nota de color por tipo (evento naranja, comando azul, política lila, actor amarillo claro y más chico, agregado amarillo, vista verde, sistema externo rosa, punto caliente magenta con texto blanco, oportunidad verde claro, decisión blanca con borde oscuro) y los estados y marcas (hipótesis sin autor con borde punteado, disputado con borde doble, evento pivote con borde izquierdo grueso oscuro, camino de falla con línea roja, no se sabe con etiqueta magenta). El detalle está en las tablas de abajo.">

La imagen se genera desde la paleta; si cambias `palette.json`, regenérala:

```sh
python3 storm-start/scripts/render.py --legend storm-start/assets/legend.svg
```

| Elemento | Color | Significa |
|----------|-------|-----------|
| Evento | naranja `#ff9f43` | Algo que pasó en el dominio, en pasado |
| Comando | azul `#6fa8ff` | Lo que alguien pide que pase |
| Política | lila `#c9a7f5` | Cada vez que X, entonces Y |
| Actor | amarillo claro `#fff4b0` (pequeño) | Quién da la orden |
| Agregado | amarillo `#ffd84d` | Lo que protege las reglas que nunca se rompen |
| Vista | verde `#7ed98b` | Lo que alguien mira para decidir |
| Sistema externo | rosa `#ffa8d0` | Algo fuera del alcance que dispara o recibe |
| Punto caliente | magenta `#e8246f`, texto blanco | Duda, conflicto o ambigüedad sin resolver |
| Oportunidad | verde claro `#c8f2c0` | Algo que se podría mejorar |
| Decisión | blanco con borde oscuro | Elección con autor, motivo y alternativas descartadas |

| Marca o estado | Cómo se ve | Significa |
|----------------|------------|-----------|
| Evento pivote | borde izquierdo grueso oscuro | Después de este evento cambia todo lo que sigue |
| Camino de falla | línea roja `#c0392b`, bajo su historia | Lo que pasa cuando la historia principal sale mal |
| Hipótesis sin autor | borde punteado | Nadie la adoptó; no cuenta como modelo |
| Disputado | borde doble | Dos voces lo dicen distinto; tiene un punto caliente abierto |
| Propuesto / Confirmado | sin borde | Falta o ya tiene la confirmación de la devolución |
| No se sabe | etiqueta "? no se sabe" | El campo apunta a un desconocido; también se listan en la sección "Lo que no se sabe" |

### Scripts a mano

Viven en `storm-start/scripts/`. Chequeos estructurales (con `--close`, además el gate de ese nivel):

```sh
python3 storm-start/scripts/verify.py docs/domain/<slug>/eventstorm.yaml
```

```sh
python3 storm-start/scripts/verify.py docs/domain/<slug>/eventstorm.yaml --close process
```

Listar cada chequeo, cuándo corre, cuándo falla y qué sesión lo corrige:

```sh
python3 storm-start/scripts/verify.py --list
```

Generar el tablero. Sin `-o`, escribe `eventstorm.html` junto al YAML:

```sh
python3 storm-start/scripts/render.py docs/domain/<slug>/eventstorm.yaml
```

```sh
python3 storm-start/scripts/render.py docs/domain/<slug>/eventstorm.yaml -o <salida.html>
```

| Script | 0 | 1 | 2 |
|--------|---|---|---|
| `verify.py` | Todo pasa | Algún chequeo falló (líneas `FAIL`), o YAML mal formado (`error:` sin reporte) | Uso, archivo, falta PyYAML o esquema fuera del subconjunto soportado |
| `render.py` | HTML (o, con `--legend`, SVG) escrito; imprime la ruta | YAML mal formado | Uso, archivo, falta PyYAML |

`verify.py` revisa estructura, no significado: un PASS no dice que el modelo sea correcto.

### Ejemplo y evaluación

- `storm-start/assets/fixtures/biblioteca.eventstorm.yaml`: un dominio ficticio, los préstamos de
  una biblioteca, que sirve de ejemplo del resultado y de prueba de los scripts. Modela préstamo,
  devolución, vencimiento y una multa automática, con dos voces, Big Picture y Process cerrados y
  Design abierto; usa todos los tipos de nota y marcas de la leyenda. Pasa `verify.py` y falla
  `--close design` a propósito: la frontera "libro" vs "ejemplar" queda bloqueante para mostrar que
  Design no cierra con una frontera sin resolver. Para ver su tablero (el HTML se escribe fuera del
  repo), desde la raíz del clon:

  ```bash
  python3 storm-start/scripts/render.py storm-start/assets/fixtures/biblioteca.eventstorm.yaml -o /tmp/biblioteca.html
  ```

  ```bash
  open /tmp/biblioteca.html
  ```

  `open` es de macOS; en Linux usa `xdg-open`.

- `storm-start/assets/fixtures/biblioteca.invalid.eventstorm.yaml`: fixture negativo; debe fallar
  todos los chequeos salvo `schema` y `session`.
- `storm-start/evals/saldo-brief.md`: caso de evaluación de punta a punta con dos voces simuladas
  ("saldo" en crédito y en contabilidad). Las skills no lo leen, para que el facilitador no saque
  respuestas de ahí; un agente facilita y otro hace de voces solo con el brief.

### Limitaciones conocidas

- La integración con Praxis no lee el YAML todavía: `praxis-survey` debería leer
  `docs/domain/<slug>/eventstorm.yaml`, pero hoy hay que pasarle la ruta a mano; `praxis-challenge`
  aún no acepta el modelo como entrada, así que `/storm-verify` no ofrece crítica semántica.
- Las decisiones técnicas (almacenamiento, APIs, frameworks, sincronía) quedan fuera: se anotan en
  `open_questions` con destino `praxis-design` y la sesión vuelve a la pregunta de dominio.
