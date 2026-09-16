# nespressoDispenserExtension

## Objetivo

Extensión de capacidad para un dispensador de cápsulas Nespresso. **Dos piezas
independientes de 150 mm cada una**, que se acoplan entre sí y alargan el chute
para apilar más cápsulas.

| Pieza | Función |
|---|---|
| **A_base** | Se **inserta** en la boca del holder. Su exterior está atado a esa boca, así que no se puede ensanchar. |
| **B_acople** | Se **acopla** encima de A. No entra en ningún hueco, así que es libre por fuera. Lleva un **zócalo local** en su extremo inferior que recibe el extremo de A. |

Las cápsulas bajan **de lado** (acostadas), no de plano.

Cada pieza lleva un **corte de inspección** de 20 mm de ancho en una de sus
caras de 39,5 mm (las normales al eje Y), para ver cuántas cápsulas quedan.

## Estado

✅ **Geometría lista, sin imprimir.** Ambas piezas pasan los gates topológicos y
las cotas están verificadas sobre los STL exportados.

⚠️ **El margen del reborde es +0,00 mm.** Ver [Advertencia](#advertencia-el-margen-es-cero).

## Archivos

| Archivo | Qué es |
|---|---|
| `macros/nespresso_dispenser_extension.py` | script build123d que genera **las dos** piezas |
| `nespressoDispenserExtension_A_base.step` / `.stl` | pieza A, la que se inserta |
| `nespressoDispenserExtension_B_acople.step` / `.stl` | pieza B, la que se acopla |

Regenerar ambas:

```
python projects\nespressoDispenserExtension\macros\nespresso_dispenser_extension.py
```

## Dimensiones

Todo en mm. Medido sobre los STL exportados, no sobre el código.

| | A_base | B_acople |
|---|---|---|
| Exterior | 39,50 × 37,00 | 40,70 × 37,00 |
| Zócalo | — | 42,40 × 39,90, de z=0 a z=12 |
| Chute interior | 37,10 × 33,40 | 37,10 × 33,40 |
| Pared, caras de 39,5 | 1,80 (3 × 0,6) | 1,80 (3 × 0,6) |
| Pared, caras de 37,0 | 1,20 (2 × 0,6) | 1,80 (3 × 0,6) |
| Altura | 150,00 | 150,00 |
| Volumen | 28,4 cm³ | 35,1 cm³ |

El chute interior es **idéntico en ambas**, para que no haya escalón donde una
cápsula pueda trabarse en la junta.

### Cápsula

De la ficha técnica en `sources/nespressoDispenserExtension/capsuleDimensions.webp`:

| Cota | Valor | Peor caso |
|---|---|---|
| Reborde | Ø37 +0,1 / −0,2 | **37,10** |
| Cuerpo | Ø29,4 ±0,25 | 29,65 |
| Alto | 27,2 ±0,35 | **27,55** |

Como baja de lado, el **reborde manda en el eje X** y el **alto en el eje Y**:

| | disponible | necesita | margen |
|---|---|---|---|
| eje X | 37,10 | 37,10 | **+0,00** |
| eje Y | 33,40 | 27,55 | +5,85 |

## Decisiones de diseño, y por qué

### La pared de A es asimétrica

El holder mide 40 × 37,5 internos, así que A no puede pasar de 39,50 × 37,00
por fuera. Con 1,8 mm en las cuatro caras el interior quedaría en 35,90 y el
reborde de 37,10 **no pasaría**. Por eso las dos caras **normales al eje X**
(las que miden 37,0 de ancho) bajan a 1,2 mm: su espesor es lo que se resta en
X, que es el eje por donde tiene que pasar el reborde.

| pared en las caras de 37,0 | interior X | margen |
|---|---|---|
| 1,8 | 35,90 | −1,20 no pasa |
| **1,2** | **37,10** | **+0,00** |
| 0,6 | 38,30 | +1,20 |

Separar el proyecto en dos piezas **no libera a A** — sigue atada al holder.
Lo que libera es a B, que por eso conserva 1,8 mm en las cuatro caras.

### La cápsula no puede voltearse

De plano necesitaría 37,10 en **ambos** ejes, y el eje Y solo da 33,40. La
geometría obliga físicamente a que bajen de lado, que es lo que se quiere.

### El zócalo va en B, y es local

B es la más ancha, así que la hembra va ahí. El ensanchamiento ocupa solo los
12 mm del extremo inferior; por encima B vuelve a 40,70 × 37,00.

| | |
|---|---|
| Hueco del zócalo | 40,00 × 37,50 |
| Pared de A que entra | 39,50 × 37,00 |
| Holgura | 0,25 por cara |
| Profundidad | 12,0 |
| Mordaza exterior | 1,2 |

### Los cortes no tienen ningún tramo horizontal

Se imprime **sin soportes**, así que el corte no puede tener un techo plano.

- **A**: el corte **sale por el borde superior**, así que no hay nada que
  rematar arriba. Abajo termina en arco (r=10).
- **B**: conserva marco arriba y abajo. El arco inferior se autosoporta porque
  mira hacia arriba. El remate superior es un **pico a 45°** (V invertida), no
  un arco.

**Por qué no un arco arriba:** un semicírculo es horizontal en su cúspide. La
superficie solo supera los 45° a 7,07 mm del centro, dejando **14,1 mm de techo
casi plano** que el extrusor tendría que puentear. Dos rectas a 45° que se
juntan en un pico no tienen ningún tramo horizontal.

Medido sobre el STL: ángulo mínimo de esa superficie **45,0°**, y el error
contra un modelo de pico es 0,60 frente a 60,07 contra uno de arco.

## Verificación

```
python tools\render_check.py projects\nespressoDispenserExtension\nespressoDispenserExtension_A_base.stl --views iso
python tools\render_check.py projects\nespressoDispenserExtension\nespressoDispenserExtension_B_acople.stl --views iso
```

Ambas: `body_count = 1`, watertight, winding consistente.

Más allá de los gates, medido punto por punto sobre los STL:

- **Espesor real de pared**: 1,78 mm donde se declara 1,8.
- **El zócalo es local**: termina exactamente en z=12,000; por encima el
  cuerpo mide 40,70 × 37,00.
- **El encaje no interfiere**: 17 732 puntos de A muestreados en la zona de
  solape, **0** dentro del material de B.
- **El corte está en la cara correcta**: hueco en +Y, material en −Y, +X y −X.
- **A está abierta arriba**: hueco a z=149,5, sin barra cruzando.
- **El remate de B es un pico**, no un arco (ver arriba).

Una render no es una medición: las renders `_iso.png` muestran la forma, pero
las cotas salen del muestreo del mesh.

## Advertencia: el margen es cero

El chute mide **37,10** y el reborde en su peor caso mide **37,10**. Margen
**+0,00**.

| cápsula | margen |
|---|---|
| peor caso Ø37,10 | +0,00 |
| nominal Ø37,00 | +0,10 |
| mínimo Ø36,80 | +0,30 |

Decisión tomada por el usuario sabiéndolo. El FDM suele cerrar el interior
0,1–0,2 mm respecto a lo modelado, lo que puede volverlo interferencia.

**Antes de imprimir los 150 mm completos, imprime un cupón corto** (≈20 mm de
alto) con la sección exacta y prueba que una cápsula real desliza.

## Impresión

- **Boquilla 0,6.** Todos los espesores son múltiplos limpios: 1,2 = 2 × 0,6 y
  1,8 = 3 × 0,6.
- **De pie**, 150 mm en vertical, sin soportes.
- La carga es compresión pura (peso de las cápsulas) y paralela al eje, que es
  el caso favorable en FDM. `print-tolerance-expert` calculó margen de pandeo de
  ~24 000× con pared 1,8 a 150 mm — estructuralmente sobra.
- Conviene un **chaflán de 0,8–1,0 mm a 45°** en el extremo que se inserta: el
  *elephant's foot* de la primera capa (0,1–0,3 mm por cara) se come la holgura
  de inserción. **Todavía no está modelado.**

## Origen de las medidas

`sources/nespressoDispenserExtension/`:

| Archivo | Qué es |
|---|---|
| `mockupofholder.jpeg` | El holder, boceto isométrico. **Solo referencia**, no se imprime. |
| `mockupofmodel.jpeg` | La sección a imprimir, boceto acotado. |
| `capsuleDimensions.webp` | Ficha técnica de la cápsula. |

Los bocetos tienen cotas corregidas a mano. Lo que vale:

| Cota del boceto | Qué pasa con ella |
|---|---|
| "15mm" de altura | **Error de escritura**: son 15 cm = 150 mm |
| "20mm" | **Corte de material**, no una lengüeta |
| "8,75mm" | **Ignorar**, está tachada |
| 40 × 37,5 | Boca **interna** del holder, con calibre |

La boca de 40 × 37,5 fue medida por el usuario con calibre. El diámetro de la
cápsula viene de su ficha técnica, con tolerancia declarada.

## Relación con NespressoPodDispenser

Proyecto **independiente**. `projects/NespressoPodDispenser` es una jaula cuyo
chute interior mide **56,2 × 105,2 mm** — medido de sus propias constantes. Eso
no coincide con la boca de 40 × 37,5 de este holder, así que esta extensión
**no** monta sobre esa jaula y **no** importa sus constantes.

## Pendiente

- Chaflán de inserción en el extremo de A.
- Cupón de prueba antes de imprimir completo.
