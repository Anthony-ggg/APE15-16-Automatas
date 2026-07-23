# Informe base — APE 15 y APE 16

> Integrantes: Boris Rengel, Estefanía Cale y Anthony Gutiérrez. Complete las capturas, tiempos obtenidos y enlace del video antes de entregar.

## 1. Título

Análisis léxico, sintáctico y clasificación semántica de oraciones en español mediante spaCy y Stanford CoreNLP.

## 2. Objetivo general

Implementar una aplicación web que reciba oraciones en español y ejecute análisis léxico, sintáctico y una clasificación semántica basada en conectores, comparando los resultados producidos por spaCy y Stanford CoreNLP.

## 3. Metodología

El desarrollo se organizó en cinco etapas. Primero se preparó un entorno virtual de Python y se instaló spaCy junto con el modelo `es_core_news_sm`. Después se configuró Stanford CoreNLP como servidor Java local con los modelos para español. En la tercera etapa se construyó un backend Flask que recibe el texto enviado desde el front-end y consulta ambos analizadores. En la cuarta etapa se implementaron reglas para reconocer conectores coordinantes y subordinantes mediante expresiones regulares con límites de palabra. Finalmente se diseñó una interfaz que presenta tokens, lemas, POS, dependencias, proposiciones, árboles sintácticos y la comparación entre herramientas.

## 4. Arquitectura

- **Front-end:** HTML, CSS y JavaScript.
- **Backend:** Flask.
- **APE 15:** módulo `spacy_analyzer.py`.
- **APE 16:** módulo `corenlp_analyzer.py` conectado al servidor Java por HTTP.
- **Clasificación:** `classifier.py`.
- **Comparación:** `comparison.py`.

## 5. Resultados

Inserte aquí capturas de:

1. Pantalla inicial y estado de las herramientas.
2. Oración simple con tabla de tokens, lema, POS y dependencias.
3. Extracción de sujeto, verbo y objeto directo.
4. Oración coordinada y su clasificación.
5. Oración subordinada y su clasificación.
6. Visualización displaCy.
7. Árbol de constituyentes de CoreNLP.
8. Tabla comparativa final.

### Tabla de comparación obtenida

| Aspecto | spaCy | Stanford CoreNLP |
|---|---|---|
| Tiempo de ejecución | Complete con el resultado | Complete con el resultado |
| Precisión/acuerdo POS | Complete con el resultado | Complete con el resultado |
| Árbol sintáctico | Dependencias visuales | Constituyentes |
| Dependencias | Complete con el resultado | Complete con el resultado |
| Facilidad de uso | Alta | Media |
| Consumo de memoria | Complete con el resultado | Complete con el resultado |

## 6. Preguntas de control — APE 15

### ¿Qué diferencia existe entre un token y un lema?

Un token es cada unidad en la que se divide el texto durante la tokenización, mientras que el lema es la forma base o de diccionario asociada a esa unidad. Por ejemplo, “estudiaba” es un token cuyo lema puede ser “estudiar”.

### ¿Qué representa una etiqueta POS?

Una etiqueta POS indica la categoría gramatical que cumple un token en la oración, como sustantivo, verbo, adjetivo, determinante o adverbio.

### ¿Qué es una dependencia sintáctica?

Es una relación dirigida entre dos palabras. Una funciona como gobernante y otra como dependiente. Estas relaciones permiten representar funciones como sujeto, objeto, modificador o raíz verbal.

### ¿Cómo identifica spaCy el sujeto de una oración?

spaCy analiza el árbol de dependencias y asigna etiquetas como `nsubj` o `csubj` a los tokens que funcionan como sujeto respecto de un verbo.

### ¿Qué limitaciones presenta spaCy en el análisis semántico?

El modelo puede equivocarse cuando la oración es ambigua, contiene expresiones poco frecuentes, omite información o se aleja de los datos con los que fue entrenado. Además, una etiqueta sintáctica no equivale por sí sola a una comprensión completa del significado.

## 7. Preguntas de control — APE 16

### ¿Qué diferencias encontró entre spaCy y Stanford CoreNLP?

spaCy se integra directamente con Python y produce análisis con menor complejidad de instalación. CoreNLP funciona como una plataforma Java y ofrece un árbol de constituyentes más explícito, aunque requiere un servidor y modelos adicionales para español.

### ¿Cuál herramienta genera árboles sintácticos más detallados?

Stanford CoreNLP genera un árbol de constituyentes que presenta sintagmas y niveles jerárquicos. spaCy se concentra principalmente en relaciones de dependencia y su visualización mediante displaCy.

### ¿Qué ventajas ofrece Stanford CoreNLP para el análisis lingüístico?

Integra múltiples anotadores dentro de una misma tubería, permite producir árboles de constituyentes y dependencias, dispone de una API HTTP y puede reutilizarse desde diferentes lenguajes de programación.

### ¿Qué limitaciones presenta el enfoque basado en reglas para el análisis semántico?

Las reglas solo reconocen los patrones incluidos previamente. Pueden fallar ante conectores ambiguos, conectores omitidos, múltiples relaciones en una misma oración o estructuras no contempladas.

### ¿Qué mejoras implementaría para aumentar la precisión del clasificador?

Se podría combinar la lista de conectores con dependencias sintácticas, validar que existan al menos dos núcleos verbales, utilizar un corpus etiquetado para evaluar resultados e incorporar un modelo supervisado para los casos ambiguos.

## 8. Conclusiones

1. La integración de spaCy y Stanford CoreNLP permitió observar que ambas herramientas representan la estructura lingüística desde perspectivas complementarias: dependencias y constituyentes.
2. El uso de expresiones regulares con límites de palabra evitó clasificaciones falsas causadas por conectores de una sola letra presentes dentro de otras palabras.
3. El front-end facilitó la ejecución de las actividades porque centralizó la entrada y presentó de forma ordenada los resultados léxicos, sintácticos y semánticos.

## 9. Recomendaciones

1. Iniciar CoreNLP antes del backend Flask y verificar el endpoint `/ready`.
2. Mantener la misma versión entre la distribución CoreNLP y el JAR de modelos españoles.
3. Evaluar la precisión con un conjunto de oraciones etiquetadas manualmente, en lugar de depender únicamente de la comparación entre herramientas.

## 10. Bibliografía

- Material de las semanas 15 y 16 de la asignatura.
- Documentación oficial de spaCy.
- Documentación oficial de Stanford CoreNLP.

## 11. Enlaces

- Repositorio: complete aquí.
- Video de explicación: complete aquí.

## Mejora del análisis semántico

Además de clasificar las relaciones expresadas por conectores, se implementó una capa de análisis semántico basada en restricciones de selección. Esta capa toma los roles sintácticos identificados por spaCy y Stanford CoreNLP, determina una categoría aproximada para el núcleo del sujeto y del objeto, y la compara con los tipos de participantes que normalmente admite el verbo en una interpretación literal.

En la oración “El carro del vecino vuela”, el sistema recupera `vuela` como verbo principal y `volar` como lema incluso cuando el modelo pequeño de spaCy lo etiqueta erróneamente. Luego identifica `carro` como núcleo del sujeto y lo clasifica como vehículo terrestre. Como la regla de `volar` admite principalmente animales voladores y aeronaves, se genera una advertencia de posible anomalía semántica literal. La aplicación aclara que este resultado no es absoluto, puesto que una metáfora o un contexto de ciencia ficción puede cambiar la interpretación.
