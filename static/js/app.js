"use strict";

const sampleSentence = document.getElementById("sampleSentence");
const textInput = document.getElementById("textInput");
const analyzeButton = document.getElementById("analyzeButton");
const counter = document.getElementById("counter");
const message = document.getElementById("message");
const results = document.getElementById("results");

sampleSentence.addEventListener("change", () => {
    if (sampleSentence.value) {
        textInput.value = sampleSentence.value;
        updateCounter();
    }
});
textInput.addEventListener("input", updateCounter);
analyzeButton.addEventListener("click", analyze);
textInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") analyze();
});

function updateCounter() {
    counter.textContent = `${textInput.value.length} / 1500`;
}

function setMessage(text, type = "warning") {
    message.textContent = text;
    message.className = `message ${type === "error" ? "error" : ""}`;
}

function clearMessage() {
    message.textContent = "";
    message.className = "message hidden";
}

function escapeText(value) {
    return String(value ?? "");
}

function statusBadge(label, status) {
    const span = document.createElement("span");
    span.className = `status ${status.available ? "ok" : "error"}`;
    span.textContent = `${label}: ${status.available ? "disponible" : "no disponible"}`;
    span.title = status.error || "Herramienta lista";
    return span;
}

async function loadHealth() {
    const health = document.getElementById("health");
    try {
        const response = await fetch("/health");
        const data = await response.json();
        health.replaceChildren(statusBadge("spaCy", data.spacy), statusBadge("CoreNLP", data.corenlp));
    } catch (error) {
        health.innerHTML = '<span class="status error">No se pudo consultar el estado</span>';
    }
}

async function analyze() {
    const texto = textInput.value.trim();
    if (!texto) {
        setMessage("Escriba o seleccione una oración antes de analizar.", "error");
        return;
    }

    clearMessage();
    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analizando…";
    results.classList.add("hidden");

    try {
        const response = await fetch("/analizar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "No se pudo analizar el texto.");
        renderResults(data);
        if (data.warnings?.length) setMessage(data.warnings.join(" "));
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = "Analizar oración";
    }
}

function renderResults(data) {
    renderSummary(data);
    renderClassification(data.classification);
    renderPropositions("spacyPropositions", data.spacy);
    renderPropositions("corePropositions", data.corenlp);
    renderSemantic(data.semantic);
    renderTokenTable("spacyTokens", "spacyError", data.spacy);
    renderTokenTable("coreTokens", "coreError", data.corenlp);
    renderTrees(data);
    renderComparison(data.comparison);
    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSummary(data) {
    const cards = [
        ["Tipo de oración", data.classification.type],
        ["Relación", data.classification.relation],
        ["Conector", data.classification.connector],
        ["Número de proposiciones", data.proposition_count],
        ["Coherencia semántica", data.semantic?.overall?.label || "No disponible"],
    ];
    const container = document.getElementById("summaryCards");
    container.replaceChildren(...cards.map(([label, value]) => {
        const card = document.createElement("div");
        card.className = "summary-card";
        const small = document.createElement("small");
        small.textContent = label;
        const strong = document.createElement("strong");
        strong.textContent = value;
        card.append(small, strong);
        return card;
    }));
}

function renderClassification(classification) {
    const container = document.getElementById("classificationDetails");
    container.replaceChildren();
    const paragraph = document.createElement("p");
    paragraph.textContent = `${classification.type}. Relación ${classification.relation}.`;
    container.appendChild(paragraph);

    const pills = document.createElement("div");
    pills.className = "pills";
    if (!classification.connectors.length) {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = "No se encontraron conectores de la tabla de reglas";
        pills.appendChild(pill);
    } else {
        classification.connectors.forEach((connector) => {
            const pill = document.createElement("span");
            pill.className = "pill";
            pill.textContent = `${connector.found_text} · ${connector.sentence_class} ${connector.relation}`;
            pills.appendChild(pill);
        });
    }
    container.appendChild(pills);
}

function renderPropositions(elementId, result) {
    const container = document.getElementById(elementId);
    container.replaceChildren();
    if (!result.available) {
        const error = document.createElement("div");
        error.className = "inline-error";
        error.textContent = result.error || "Herramienta no disponible";
        container.appendChild(error);
        return;
    }
    if (!result.propositions?.length) {
        container.textContent = "No se detectaron proposiciones.";
        return;
    }
    result.propositions.forEach((item, index) => {
        const card = document.createElement("div");
        card.className = "proposition-card";
        const title = document.createElement("p");
        title.className = "proposition-text";
        title.textContent = `Proposición ${index + 1}: ${item.text}`;
        const subject = document.createElement("p");
        subject.textContent = `Sujeto: ${item.subject}`;
        const verb = document.createElement("p");
        const lemma = item.verb_lemma && item.verb_lemma !== item.verb ? ` · lema: ${item.verb_lemma}` : "";
        verb.textContent = `Verbo principal: ${item.verb}${lemma}`;
        const object = document.createElement("p");
        object.textContent = `Objeto directo: ${item.object}`;
        const method = document.createElement("p");
        method.className = "extraction-method";
        method.textContent = `Método de extracción: ${item.extraction_method || "dependencias del modelo"}`;
        card.append(title, subject, verb, object, method);
        container.appendChild(card);
    });
}


function semanticStatusClass(status) {
    if (status === "coherent") return "semantic-coherent";
    if (status === "warning") return "semantic-warning";
    return "semantic-unknown";
}

function appendSemanticRole(container, label, value, detail = "") {
    const row = document.createElement("div");
    row.className = "semantic-role";
    const term = document.createElement("span");
    term.textContent = label;
    const content = document.createElement("strong");
    content.textContent = value || "No detectado";
    row.append(term, content);
    if (detail) {
        const small = document.createElement("small");
        small.textContent = detail;
        row.appendChild(small);
    }
    container.appendChild(row);
}

function renderSemantic(semantic) {
    const overview = document.getElementById("semanticOverview");
    const propositions = document.getElementById("semanticPropositions");
    const limitations = document.getElementById("semanticLimitations");
    overview.replaceChildren();
    propositions.replaceChildren();

    if (!semantic) {
        overview.textContent = "No se generó el análisis semántico.";
        limitations.textContent = "";
        return;
    }

    const banner = document.createElement("div");
    banner.className = `semantic-banner ${semanticStatusClass(semantic.overall.status)}`;
    const title = document.createElement("strong");
    title.textContent = semantic.overall.label;
    const summary = document.createElement("p");
    summary.textContent = semantic.overall.summary;
    const relation = document.createElement("p");
    relation.className = "semantic-relation";
    relation.textContent = semantic.relation_semantics.explanation;
    banner.append(title, summary, relation);
    overview.appendChild(banner);

    semantic.propositions.forEach((item, index) => {
        const card = document.createElement("article");
        card.className = `semantic-card ${semanticStatusClass(item.status)}`;

        const header = document.createElement("div");
        header.className = "semantic-card-header";
        const heading = document.createElement("h3");
        heading.textContent = `Proposición ${index + 1}`;
        const badge = document.createElement("span");
        badge.className = "semantic-badge";
        badge.textContent = item.label;
        header.append(heading, badge);

        const phrase = document.createElement("p");
        phrase.className = "semantic-phrase";
        phrase.textContent = item.text;

        const roles = document.createElement("div");
        roles.className = "semantic-roles";
        appendSemanticRole(roles, "Sujeto", item.subject, `Núcleo: ${item.subject_head || "—"} · ${item.subject_category_label}`);
        appendSemanticRole(roles, "Verbo", item.verb, `Lema: ${item.verb_lemma}`);
        appendSemanticRole(roles, "Objeto directo", item.object, item.object !== "No detectado" ? `Núcleo: ${item.object_head || "—"} · ${item.object_category_label}` : "No exigido o no presente");

        const explanation = document.createElement("p");
        explanation.className = "semantic-explanation";
        explanation.textContent = item.explanation;

        const source = document.createElement("small");
        source.className = "semantic-source";
        source.textContent = `Estructura base seleccionada: ${item.source || "reglas internas"}`;

        card.append(header, phrase, roles, explanation, source);

        if (item.suggestions?.length) {
            const suggestions = document.createElement("div");
            suggestions.className = "semantic-suggestions";
            const suggestionTitle = document.createElement("strong");
            suggestionTitle.textContent = "Ejemplos compatibles:";
            suggestions.appendChild(suggestionTitle);
            item.suggestions.forEach((value) => {
                const chip = document.createElement("span");
                chip.textContent = value;
                suggestions.appendChild(chip);
            });
            card.appendChild(suggestions);
        }
        propositions.appendChild(card);
    });

    limitations.textContent = semantic.limitations;
}

function renderTokenTable(tableId, errorId, result) {
    const table = document.getElementById(tableId);
    const errorBox = document.getElementById(errorId);
    table.replaceChildren();
    errorBox.replaceChildren();
    if (!result.available) {
        errorBox.className = "inline-error";
        errorBox.textContent = result.error || "Herramienta no disponible";
        return;
    }
    errorBox.className = "";
    const header = document.createElement("thead");
    header.innerHTML = "<tr><th>#</th><th>Token</th><th>Lema</th><th>POS</th><th>Dependencia</th><th>Gobernante</th><th>Observación</th></tr>";
    const body = document.createElement("tbody");
    result.tokens.forEach((token) => {
        const row = document.createElement("tr");
        const observation = token.lexical_verb_backup ? "Verbo recuperado por respaldo léxico" : "—";
        [token.index, token.token, token.lemma, token.pos, token.dependency, token.governor, observation].forEach((value, index) => {
            const cell = document.createElement("td");
            if (index === 3 || index === 4) {
                const code = document.createElement("code");
                code.textContent = escapeText(value);
                cell.appendChild(code);
            } else {
                cell.textContent = escapeText(value);
            }
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
    table.append(header, body);
}

function createTreeViewer(title, subtitle = "") {
    const card = document.createElement("article");
    card.className = "tree-card";

    const header = document.createElement("div");
    header.className = "tree-card-header";

    const headingBox = document.createElement("div");
    const heading = document.createElement("h4");
    heading.textContent = title;
    headingBox.appendChild(heading);
    if (subtitle) {
        const description = document.createElement("p");
        description.className = "tree-card-subtitle";
        description.textContent = subtitle;
        headingBox.appendChild(description);
    }

    const toolbar = document.createElement("div");
    toolbar.className = "tree-toolbar";
    toolbar.setAttribute("aria-label", "Controles del árbol");

    const viewport = document.createElement("div");
    viewport.className = "tree-viewport";

    const content = document.createElement("div");
    content.className = "tree-zoom-content";
    viewport.appendChild(content);

    header.append(headingBox, toolbar);
    card.append(header, viewport);
    installTreeControls(card, viewport, content, toolbar);
    return { card, viewport, content };
}

function treeControl(text, title) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tree-control";
    button.textContent = text;
    button.title = title;
    button.setAttribute("aria-label", title);
    return button;
}

function installTreeControls(card, viewport, content, toolbar) {
    let zoom = 1;
    const minus = treeControl("−", "Alejar");
    const zoomLabel = document.createElement("span");
    zoomLabel.className = "tree-zoom-label";
    const plus = treeControl("+", "Acercar");
    const fit = treeControl("Ajustar", "Ajustar el árbol al ancho disponible");
    const fullscreen = treeControl("Ampliar", "Mostrar el árbol en pantalla completa");

    function updateZoom(nextZoom) {
        zoom = Math.min(1.8, Math.max(0.45, nextZoom));
        content.style.setProperty("--tree-zoom", zoom.toFixed(2));
        zoomLabel.textContent = `${Math.round(zoom * 100)}%`;
    }

    minus.addEventListener("click", () => updateZoom(zoom - 0.15));
    plus.addEventListener("click", () => updateZoom(zoom + 0.15));
    fit.addEventListener("click", () => {
        updateZoom(1);
        requestAnimationFrame(() => {
            const naturalWidth = content.scrollWidth;
            const availableWidth = Math.max(320, viewport.clientWidth - 28);
            updateZoom(naturalWidth > availableWidth ? availableWidth / naturalWidth : 1);
            viewport.scrollTo({ left: 0, top: 0, behavior: "smooth" });
        });
    });
    fullscreen.addEventListener("click", () => {
        const active = card.classList.toggle("is-fullscreen");
        document.body.classList.toggle("tree-fullscreen-open", active);
        fullscreen.textContent = active ? "Cerrar" : "Ampliar";
        fullscreen.title = active ? "Salir de pantalla completa" : "Mostrar el árbol en pantalla completa";
        if (active) viewport.focus({ preventScroll: true });
    });

    toolbar.append(minus, zoomLabel, plus, fit, fullscreen);
    updateZoom(1);
}

function createConstituencyNode(node, depth = 0) {
    const item = document.createElement("li");
    const children = Array.isArray(node.children) ? node.children : [];
    const isTerminal = Boolean(node.terminal) || children.length === 0;
    const isPreterminal = !isTerminal && children.every((child) => child.terminal || !(child.children?.length));

    const label = document.createElement(isTerminal ? "span" : "button");
    if (!isTerminal) label.type = "button";
    label.className = "constituency-node";
    if (isTerminal) label.classList.add("terminal-node");
    else if (depth === 0) label.classList.add("root-node");
    else if (isPreterminal) label.classList.add("pos-node");
    else label.classList.add("group-node");
    label.textContent = node.label || "?";

    item.appendChild(label);
    if (!isTerminal && children.length) {
        label.title = "Pulse para contraer o desplegar";
        label.setAttribute("aria-expanded", "true");
        const childList = document.createElement("ul");
        children.forEach((child) => childList.appendChild(createConstituencyNode(child, depth + 1)));
        item.appendChild(childList);
        label.addEventListener("click", () => {
            const collapsed = item.classList.toggle("collapsed");
            label.setAttribute("aria-expanded", String(!collapsed));
        });
    }
    return item;
}

function renderSpacyTrees(result) {
    const container = document.getElementById("displacyTree");
    container.replaceChildren();
    if (!result.available) {
        const error = document.createElement("div");
        error.className = "inline-error";
        error.textContent = result.error || "spaCy no disponible";
        container.appendChild(error);
        return;
    }

    const trees = result.displacy_trees?.length
        ? result.displacy_trees
        : [{ number: 1, text: "", html: result.displacy_html }];

    trees.forEach((tree) => {
        const viewer = createTreeViewer(`Oración ${tree.number}`, tree.text);
        viewer.content.classList.add("spacy-tree-content");
        viewer.content.innerHTML = tree.html || '<p class="tree-empty">Árbol no disponible.</p>';
        container.appendChild(viewer.card);
    });
}

function renderCoreTrees(result) {
    const container = document.getElementById("coreTrees");
    container.replaceChildren();
    if (!result.available) {
        const error = document.createElement("div");
        error.className = "inline-error";
        error.textContent = result.error || "CoreNLP no disponible";
        container.appendChild(error);
        return;
    }

    const structures = result.parse_tree_structures || [];
    result.parse_trees.forEach((rawTree, index) => {
        const sentenceText = result.sentences?.[index]?.text || "";
        const viewer = createTreeViewer(`Oración ${index + 1}`, sentenceText);
        const structure = structures[index];

        if (structure) {
            viewer.content.classList.add("constituency-tree");
            const rootList = document.createElement("ul");
            rootList.className = "constituency-root-list";
            rootList.appendChild(createConstituencyNode(structure));
            viewer.content.appendChild(rootList);
        } else {
            const fallback = document.createElement("pre");
            fallback.className = "parse-tree";
            fallback.textContent = rawTree || "Árbol no disponible";
            viewer.content.appendChild(fallback);
        }

        const details = document.createElement("details");
        details.className = "raw-tree-details";
        const summary = document.createElement("summary");
        summary.textContent = "Ver estructura original de CoreNLP";
        const pre = document.createElement("pre");
        pre.className = "parse-tree raw-tree";
        pre.textContent = rawTree || "Árbol no disponible";
        details.append(summary, pre);
        viewer.card.appendChild(details);
        container.appendChild(viewer.card);
    });
}

function renderTrees(data) {
    renderSpacyTrees(data.spacy);
    renderCoreTrees(data.corenlp);
}

function renderComparison(comparison) {
    const table = document.getElementById("comparisonTable");
    table.replaceChildren();
    const header = document.createElement("thead");
    header.innerHTML = "<tr><th>Aspecto</th><th>spaCy</th><th>Stanford CoreNLP</th></tr>";
    const body = document.createElement("tbody");
    comparison.rows.forEach((item) => {
        const row = document.createElement("tr");
        [item.aspect, item.spacy, item.corenlp].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
    table.append(header, body);
    document.getElementById("comparisonNote").textContent = comparison.note;
}

document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const fullscreenCard = document.querySelector(".tree-card.is-fullscreen");
    if (!fullscreenCard) return;
    fullscreenCard.classList.remove("is-fullscreen");
    document.body.classList.remove("tree-fullscreen-open");
    const fullscreenButton = [...fullscreenCard.querySelectorAll(".tree-control")].find(
        (button) => button.textContent === "Cerrar"
    );
    if (fullscreenButton) fullscreenButton.textContent = "Ampliar";
});

updateCounter();
loadHealth();
