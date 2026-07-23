# APE 15 y 16 — spaCy + Stanford CoreNLP

Proyecto corregido para cumplir las actividades de las prácticas 15 y 16 de Teoría de Autómatas y Computabilidad Avanzada.

## Funciones incluidas

- Entrada obligatoria desde un front-end.
- Token, lema, categoría POS, dependencia y gobernante con spaCy y CoreNLP.
- Extracción de sujeto, verbo principal y objeto directo.
- Identificación y conteo de proposiciones.
- Clasificación de oraciones simples, coordinadas y subordinadas.
- Análisis semántico literal mediante categorías, roles y restricciones de selección.
- Detección explicable de combinaciones posiblemente incompatibles, por ejemplo «El carro del vecino vuela».
- Respaldo léxico para recuperar verbos que el modelo pequeño de spaCy etiquete incorrectamente.
- Relaciones: copulativa, disyuntiva, adversativa, causal, condicional, concesiva, temporal, final y consecutiva.
- Visualización del árbol de dependencias con displaCy, separada por oración y con zoom.
- Árbol gráfico de constituyentes de Stanford CoreNLP con nodos desplegables.
- Controles para acercar, alejar, ajustar y ampliar ambos árboles.
- Leyendas visuales y acceso opcional al árbol original entre paréntesis.
- Comparación de tiempo, acuerdo POS, árboles, dependencias, facilidad y memoria.
- Manejo independiente de errores: la aplicación puede mostrar spaCy aunque CoreNLP esté apagado.

## 1. Requisitos en Ubuntu

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip openjdk-17-jre unzip curl
```

Verifique:

```bash
python3 --version
java -version
```

## 2. Preparar Python

```bash
cd APE15-16-Automatas
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

## 3. Preparar Stanford CoreNLP en español

1. Descargue y descomprima Stanford CoreNLP.
2. Descargue el JAR de modelos españoles de la **misma versión**.
3. Copie el archivo `*-models-spanish.jar` dentro de la carpeta descomprimida de CoreNLP.
4. Defina la ubicación:

```bash
export CORENLP_HOME="$HOME/Descargas/stanford-corenlp-4.x.x"
```

5. Inicie el servidor:

```bash
chmod +x scripts/*.sh
./scripts/start_corenlp.sh
```

Cuando termine de cargar debe responder:

```bash
curl http://localhost:9000/ready
```

La primera carga puede tardar porque se inicializan los modelos. El script usa las propiedades españolas y precarga `tokenize,ssplit,pos,lemma,parse,depparse`.

## 4. Ejecutar la aplicación

En otra terminal:

```bash
cd APE15-16-Automatas
source .venv/bin/activate
python app.py
```

Abra:

```text
http://localhost:5000
```

## 5. Comprobar el entorno

```bash
./scripts/check_environment.sh
```

## 6. Ejecutar pruebas

```bash
pytest -q
```

Las pruebas verifican especialmente que letras como `o`, `e` o `y` no se detecten dentro de palabras como “Pedro” o “automóvil”. También comprueban que:

- «El carro del vecino vuela» produzca sujeto **El carro del vecino** y verbo **vuela**.
- El lema recuperado sea **volar**, aunque spaCy etiquete `vuela` como sustantivo.
- Un vehículo terrestre que “vuela” se marque como posible anomalía literal.
- «El avión vuela» se considere compatible con las reglas disponibles.

## 7. Detener CoreNLP

```bash
./scripts/stop_corenlp.sh
```

## Estructura

```text
.
├── app.py
├── config.py
├── analyzers/
│   ├── common.py
│   ├── corenlp_analyzer.py
│   └── spacy_analyzer.py
├── services/
│   ├── classifier.py
│   ├── comparison.py
│   ├── linguistic_rules.py
│   └── semantic_analyzer.py
├── templates/index.html
├── static/css/app.css
├── static/js/app.js
├── scripts/
├── tests/
└── docs/
```

## Observación sobre la “precisión POS”

La interfaz presenta un acuerdo referencial entre las etiquetas POS de ambas herramientas. Este dato no es una precisión científica porque para calcularla correctamente se necesita un corpus de referencia etiquetado manualmente. La aplicación lo aclara para evitar reportar un porcentaje engañoso.

## Reemplazar el contenido del repositorio actual

Desde la carpeta clonada del repositorio, conserve `.git` y reemplace los demás archivos:

```bash
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a /ruta/APE15-16-Automatas/. .
git add .
git commit -m "Corrige e integra APE 15 y APE 16"
git push origin main
```

Revise `docs/GUIA_DEMO.md` para la exposición y `docs/INFORME_BASE_APE15_16.md` para el documento.

## Análisis semántico implementado

El proyecto diferencia dos niveles:

1. **Relación semántica entre proposiciones:** causal, condicional, temporal, concesiva, copulativa, disyuntiva, etc., determinada por conectores.
2. **Coherencia semántica literal:** compara la categoría del sujeto y del objeto con las restricciones del verbo.

Ejemplo esperado:

```text
Entrada: El carro del vecino vuela.
Sujeto: El carro del vecino
Núcleo del sujeto: carro
Verbo principal: vuela
Lema: volar
Categoría del sujeto: vehículo terrestre
Resultado: Posible anomalía semántica literal
Explicación: volar normalmente requiere un animal volador o una aeronave.
```

La advertencia no declara que la oración sea absolutamente falsa. Puede ser válida en una metáfora, una historia fantástica o un contexto especial. Esta limitación se muestra también en el front-end.
