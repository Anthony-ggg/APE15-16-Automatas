# Cambios realizados frente al repositorio original

1. Se agregó el anotador `parse` para obtener el árbol sintáctico de CoreNLP.
2. Se corrigió la detección de conectores mediante límites de palabra; ya no se confunde la letra `o` de “Pedro” con una disyunción.
3. Se separó correctamente la clasificación en coordinada o subordinada y se usan relaciones en singular.
4. Se añadieron lemas y dependencias en una sola tabla para cada herramienta.
5. Se implementó el conteo y detalle de proposiciones.
6. Se implementó sujeto, verbo y objeto directo con spaCy y CoreNLP.
7. Se agregó la visualización displaCy exigida por APE 15.
8. Se añadió el árbol de constituyentes exigido por APE 16.
9. Se incorporó la comparación de tiempo, POS, árboles, dependencias, facilidad y memoria.
10. Se corrigieron las oraciones de prueba con sus tildes originales.
11. Se mejoró el manejo de errores para que una herramienta pueda funcionar aunque la otra esté apagada.
12. Se eliminó la dependencia no utilizada `stanza` y se añadieron pruebas automáticas.
13. Se incorporaron scripts para iniciar, detener y revisar Stanford CoreNLP.
14. Se agregó documentación para instalación, demostración e informe.

## Mejora visual de árboles

- displaCy se genera por oración para evitar gráficos demasiado anchos.
- Los árboles tienen controles de zoom, ajuste al ancho y pantalla completa.
- CoreNLP ya no se muestra únicamente como texto entre paréntesis: se transforma en un árbol gráfico con líneas y nodos.
- Los nodos de CoreNLP se pueden contraer y desplegar pulsándolos.
- Se añadieron colores y leyendas para diferenciar raíz, grupos sintácticos, etiquetas POS y palabras.
- La estructura original de CoreNLP permanece disponible en un panel desplegable.

## Corrección semántica y SVO

- Se corrigió el caso «El carro del vecino vuela»: spaCy ya no toma `carro` como verbo principal cuando `vuela` fue etiquetado incorrectamente.
- Se incorporó un respaldo léxico de formas verbales frecuentes y se informa el método de extracción usado.
- Se agregó análisis de compatibilidad semántica literal por restricciones de selección.
- Se muestran el núcleo y categoría del sujeto, el lema verbal, el objeto y una explicación transparente.
- Se agregaron ejemplos compatibles y una advertencia sobre metáforas y contextos fantásticos.
- Se añadieron pruebas unitarias para el error observado y para la coherencia de «El avión vuela».
