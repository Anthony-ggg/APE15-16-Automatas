# Guía rápida para la demostración

1. Abra dos terminales en la carpeta del proyecto.
2. Terminal 1: active `CORENLP_HOME` y ejecute `./scripts/start_corenlp.sh`.
3. Terminal 2: active el entorno virtual y ejecute `python app.py`.
4. Abra `http://localhost:5000`.
5. Compruebe que los indicadores de spaCy y CoreNLP aparezcan disponibles.

## Pruebas obligatorias

| Entrada | Resultado principal esperado |
|---|---|
| María estudia todos los días. | Simple, una proposición |
| Pedro compró un automóvil. | Sujeto Pedro, verbo compró, objeto un automóvil |
| Ana cocina la cena. | Sujeto Ana, verbo cocina, objeto la cena |
| Luis juega fútbol. | Sujeto Luis, verbo juega, objeto fútbol |
| María estudia porque mañana tiene un examen. | Compuesta subordinada causal, dos proposiciones |
| Pedro llegó y Ana salió. | Compuesta coordinada copulativa, dos proposiciones |
| Aunque llueve iremos al parque. | Compuesta subordinada concesiva, dos proposiciones |
| Si estudias aprobarás. | Compuesta subordinada condicional, dos proposiciones |
| Juan cocina mientras Ana limpia. | Compuesta subordinada temporal, dos proposiciones |

## Qué explicar

- spaCy realiza la APE 15: tokenización, lema, POS, dependencias y displaCy.
- Stanford CoreNLP realiza la APE 16: tokens, POS, lema, dependencias y árbol de constituyentes.
- La clasificación semántica usa reglas con límites de palabra para no confundir `o` de “Pedro” con el conector disyuntivo.
- El sistema identifica las raíces verbales de cada cláusula para contar proposiciones y extraer sujeto, verbo y objeto.
- La tabla final compara tiempo, acuerdo POS, árboles, dependencias, facilidad y memoria.

## Demostración del análisis semántico

1. Ingrese `El carro del vecino vuela.`
2. Verifique que spaCy muestre:
   - Sujeto: `El carro del vecino`.
   - Verbo principal: `vuela`.
   - Lema: `volar`.
   - Objeto directo: `No detectado`.
3. En “Coherencia de sujeto, verbo y objeto” explique que `carro` se clasifica como vehículo terrestre.
4. El sistema debe advertir que, en sentido literal, `volar` suele seleccionar un animal volador o una aeronave.
5. Luego pruebe `El avión vuela.` para mostrar un resultado compatible.
6. Aclare que el sistema usa reglas explicables y no invalida metáforas, personificación o ciencia ficción.
