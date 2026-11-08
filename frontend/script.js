// ============================================
// PANTALLAS
// ============================================

// Muestra una pantalla y oculta todas las demás
function mostrarPantalla(idPantalla) {

    document.querySelectorAll(".pantalla").forEach(function (pantalla) {
        pantalla.classList.add("oculto");
    });

    document.getElementById(idPantalla).classList.remove("oculto");
    window.scrollTo(0, 0);
}


// ============================================
// SESION (el navegador solo guarda el token y los datos básicos del usuario)
// ============================================

const CLAVE_SESION = "edudebug_sesion";

// Resumen del estudiante que entrega el servidor: diagnóstico, % del curso y errores corregidos
let progresoActual = null;

function obtenerSesion() {
    try {
        return JSON.parse(localStorage.getItem(CLAVE_SESION));
    } catch (e) {
        return null;
    }
}

function guardarSesion(sesion) {
    try {
        localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
    } catch (e) { }
}

function borrarSesion() {
    try {
        localStorage.removeItem(CLAVE_SESION);
    } catch (e) { }
    progresoActual = null;
}

function cerrarSesion() {
    borrarSesion();
    mostrarPantalla("pantallaBienvenida");
}

// Guarda la sesión que devuelve la API al iniciar sesión
function iniciarSesionDesdeRespuesta(datos) {
    guardarSesion({
        id: datos.usuario.id,
        nombre: datos.usuario.nombre,
        email: datos.usuario.email,
        rol: datos.usuario.rol,
        token: datos.token
    });
    progresoActual = datos.progreso;
}

// Lleva al usuario a la pantalla que indica el servidor:
// el profesor al panel, el estudiante nuevo al diagnóstico y el que ya lo hizo al catálogo.
function irA(siguiente) {
    if (siguiente === "panel") {
        mostrarPanelProfesor();
    } else if (siguiente === "catalogo") {
        mostrarCatalogo();
    } else {
        iniciarDiagnostico();
    }
}


// ============================================
// CONEXION CON LA API (Flask)
// ============================================

// Por defecto la API está en la misma dirección que la página (Flask la sirve, o Render).
// Si abres el HTML con Live Server (puerto 55xx) o como archivo, apunta a Flask en el puerto 5000.
const API_URL = window.EDUDEBUG_API ||
    ((location.protocol === "file:" || /^55\d\d$/.test(location.port))
        ? "http://127.0.0.1:5000" : "");

async function api(ruta, opciones) {

    opciones = opciones || {};

    let cabeceras = { "Content-Type": "application/json" };
    let sesion = obtenerSesion();
    if (sesion && sesion.token) {
        cabeceras["Authorization"] = "Bearer " + sesion.token;
    }

    let respuesta;
    try {
        respuesta = await fetch(API_URL + ruta, {
            method: opciones.method || "GET",
            headers: cabeceras,
            body: opciones.body ? JSON.stringify(opciones.body) : undefined
        });
    } catch (e) {
        throw new Error("No se pudo conectar con el servidor. ¿Está encendido?");
    }

    let datos = {};
    try { datos = await respuesta.json(); } catch (e) { }

    if (!respuesta.ok) {

        let error = new Error(datos.error || "Ocurrió un error inesperado.");
        error.estado = respuesta.status;

        // Sesión vencida: se borra y se pide iniciar sesión de nuevo
        if (respuesta.status === 401 && sesion && !opciones.silencioso) {
            borrarSesion();
            mostrarPantalla("pantallaLogin");
        }
        throw error;
    }

    return datos;
}

// Misma regla que el servidor: 8 caracteres o más, con al menos una letra y un número
function contrasenaValida(password) {
    return password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password);
}

// Los botones marcados con "solo-admin" únicamente se ven con el rol administrador
function aplicarRolEnMenus() {
    let sesion = obtenerSesion();
    let esAdmin = !!sesion && sesion.rol === "admin";
    document.querySelectorAll(".solo-admin").forEach(function (boton) {
        boton.classList.toggle("oculto", !esAdmin);
    });
}

function capitalizar(texto) {
    return texto.charAt(0).toUpperCase() + texto.slice(1);
}

// Convierte < > & en texto para que nunca se interpreten como HTML real
function escaparHtml(texto) {
    return String(texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

const NOMBRES_ERROR = {
    etiqueta_sin_cerrar: "Etiqueta sin cerrar",
    atributo_sin_comillas: "Atributo sin comillas",
    etiqueta_en_mayusculas: "Etiqueta en mayúsculas"
};

function nivelTexto() {
    if (progresoActual && progresoActual.diagnostico) {
        return capitalizar(progresoActual.diagnostico.nivel);
    }
    return "Sin evaluar";
}


// ============================================
// FORMULARIO DE LOGIN
// ============================================

document.getElementById("formLogin").addEventListener("submit", async function (event) {

    event.preventDefault();

    let email = document.getElementById("correoLogin").value.trim().toLowerCase();
    let password = document.getElementById("passwordLogin").value;
    let boton = event.submitter;
    if (boton) boton.disabled = true;

    try {
        let datos = await api("/api/auth/login", { method: "POST", body: { email: email, password: password } });
        iniciarSesionDesdeRespuesta(datos);
        document.getElementById("formLogin").reset();
        irA(datos.siguiente);
    } catch (error) {
        alert(error.message);
    } finally {
        if (boton) boton.disabled = false;
    }

});


// ============================================
// FORMULARIO DE REGISTRO
// ============================================

document.getElementById("formRegistro").addEventListener("submit", async function (event) {

    event.preventDefault();

    let nombre = document.getElementById("nombre").value.trim();
    let email = document.getElementById("correo").value.trim().toLowerCase();
    let rol = "estudiante"; // el registro público solo crea estudiantes; profesor y admin los crea un administrador
    let password = document.getElementById("password").value;
    let confirmarPassword = document.getElementById("confirmarPassword").value;

    if (!contrasenaValida(password)) {
        alert("La contraseña debe tener mínimo 8 caracteres, con letras y números.");
        return;
    }

    if (password !== confirmarPassword) {
        alert("Las contraseñas no coinciden.");
        return;
    }

    let boton = event.submitter;
    if (boton) boton.disabled = true;

    try {
        await api("/api/usuarios/registro", {
            method: "POST",
            body: { nombre: nombre, email: email, password: password, rol: rol }
        });
        alert("Cuenta creada correctamente.");
        document.getElementById("formRegistro").reset();
        mostrarPantalla("pantallaLogin");
    } catch (error) {
        alert(error.message);
    } finally {
        if (boton) boton.disabled = false;
    }

});


// ============================================
// DIAGNOSTICO ADAPTATIVO (una pregunta a la vez, desde la API)
// ============================================

let testActual = null;
let ultimoResultado = null;

// Entra con la cuenta de prueba para ver cómo es el test sin registrarse
async function entrarComoDemo() {
    try {
        let datos = await api("/api/auth/login", {
            method: "POST",
            body: { email: "estudiante@edudebug.com", password: "123456" }
        });
        iniciarSesionDesdeRespuesta(datos);
        iniciarDiagnostico();
    } catch (error) {
        alert("No se pudo abrir la demostración: " + error.message);
    }
}

async function iniciarDiagnostico() {

    mostrarPantalla("pantallaDiagnostico");

    let contenedor = document.getElementById("preguntaDiagnostico");
    let boton = document.getElementById("btnEnviarDiagnostico");

    boton.disabled = true;
    contenedor.innerHTML = '<p class="text-muted text-center py-4">Cargando pregunta...</p>';

    try {
        let estado = await api("/api/diagnostico/iniciar", { method: "POST" });
        dibujarPregunta(estado);

    } catch (error) {

        contenedor.innerHTML = "";
        let aviso = document.createElement("p");
        aviso.className = "text-danger text-center py-3";
        aviso.textContent = error.message;
        let reintentar = document.createElement("button");
        reintentar.type = "button";
        reintentar.className = "btn btn-outline-primary w-100 mb-3";
        reintentar.textContent = "Reintentar";
        reintentar.onclick = iniciarDiagnostico;
        contenedor.appendChild(aviso);
        contenedor.appendChild(reintentar);
    }
}

// textContent evita que <h1>, <p>, etc. se interpreten como HTML real
function dibujarPregunta(estado) {

    testActual = estado;
    let pregunta = estado.pregunta;

    document.getElementById("diagnosticoContador").textContent =
        "Pregunta " + estado.numero + " de " + estado.total;

    let porcentaje = Math.round((estado.numero - 1) * 100 / estado.total);
    document.getElementById("diagnosticoPorcentaje").textContent = porcentaje + "%";
    document.getElementById("diagnosticoBarra").style.width = porcentaje + "%";

    let boton = document.getElementById("btnEnviarDiagnostico");
    boton.textContent = estado.numero === estado.total ? "Terminar diagnóstico" : "Responder";
    boton.disabled = true;

    let contenedor = document.getElementById("preguntaDiagnostico");
    contenedor.innerHTML = "";

    let bloque = document.createElement("div");
    bloque.className = "pregunta";

    let titulo = document.createElement("h5");
    titulo.textContent = estado.numero + ". " + pregunta.texto;
    bloque.appendChild(titulo);

    pregunta.opciones.forEach(function (opcion) {

        let idRadio = "opcion_" + opcion.idOpcion;

        let fila = document.createElement("div");
        fila.className = "form-check";

        let radio = document.createElement("input");
        radio.className = "form-check-input";
        radio.type = "radio";
        radio.name = "opcionDiagnostico";
        radio.value = opcion.idOpcion;
        radio.id = idRadio;
        radio.addEventListener("change", function () { boton.disabled = false; });

        let etiqueta = document.createElement("label");
        etiqueta.className = "form-check-label";
        etiqueta.htmlFor = idRadio;
        etiqueta.textContent = opcion.texto;

        fila.appendChild(radio);
        fila.appendChild(etiqueta);
        bloque.appendChild(fila);
    });

    contenedor.appendChild(bloque);
}

document.getElementById("formDiagnostico").addEventListener("submit", async function (event) {

    event.preventDefault();

    let marcada = document.querySelector('input[name="opcionDiagnostico"]:checked');
    if (!marcada || !testActual) return;

    let boton = document.getElementById("btnEnviarDiagnostico");
    boton.disabled = true; // evita el doble clic

    try {
        let estado = await api("/api/diagnostico/responder", {
            method: "POST",
            body: {
                idTest: testActual.idTest,
                idPregunta: testActual.pregunta.idPregunta,
                idOpcion: parseInt(marcada.value, 10)
            }
        });

        if (estado.finalizado) {
            mostrarResultadoDiagnostico(estado);
        } else {
            dibujarPregunta(estado);
        }

    } catch (error) {
        alert(error.message);
        boton.disabled = false;
    }

});

function mostrarResultadoDiagnostico(resultado) {

    ultimoResultado = resultado;
    testActual = null;

    progresoActual = progresoActual || { porcentajeCurso: 0, erroresCorregidos: 0 };
    progresoActual.diagnostico = {
        idTest: resultado.idTest,
        aciertos: resultado.aciertos,
        total: resultado.total,
        nivel: resultado.nivel
    };

    document.getElementById("resultadoPuntaje").textContent =
        resultado.aciertos + " de " + resultado.total;

    let mensajes = {
        alto: "¡Muy bien! Tienes una buena base de HTML.",
        medio: "Tienes conocimientos básicos. Puedes seguir practicando.",
        bajo: "Necesitas reforzar algunos conceptos de HTML."
    };
    document.getElementById("resultadoMensaje").textContent =
        "Nivel " + resultado.nivel + ". " + mensajes[resultado.nivel];

    // Revisión pregunta por pregunta
    let detalle = document.getElementById("resultadoDetalle");
    detalle.innerHTML = "";

    let titulo = document.createElement("h5");
    titulo.className = "mb-3";
    titulo.textContent = "Revisa tus respuestas";
    detalle.appendChild(titulo);

    resultado.detalle.forEach(function (item) {

        let fila = document.createElement("div");
        fila.className = "d-flex gap-2 mb-3";

        let marca = document.createElement("span");
        marca.textContent = item.acerto ? "✓" : "✗";
        marca.style.fontWeight = "bold";
        marca.style.color = item.acerto ? "var(--mint-dark)" : "var(--coral-dark)";

        let texto = document.createElement("div");
        texto.style.fontSize = "14px";

        let enunciado = document.createElement("div");
        enunciado.style.fontWeight = "bold";
        enunciado.textContent = item.texto;
        texto.appendChild(enunciado);

        let respuesta = document.createElement("div");
        respuesta.className = "text-muted";
        respuesta.textContent = item.acerto
            ? "Tu respuesta: " + item.respuestaCorrecta
            : "Tu respuesta: " + item.tuRespuesta + "  ·  Correcta: " + item.respuestaCorrecta;
        texto.appendChild(respuesta);

        fila.appendChild(marca);
        fila.appendChild(texto);
        detalle.appendChild(fila);
    });

    mostrarPantalla("pantallaResultado");
}

function continuarDiagnostico() {

    if (ultimoResultado && ultimoResultado.siguiente === "teoria") {
        reiniciarTeoria();
        mostrarPantalla("pantallaTeoria");
    } else {
        mostrarCatalogo();
    }

}


// ============================================
// TEORIA DE HTML
// ============================================

let temaActual = 1;

function registrarTemaVisto(tema) {
    api("/api/actividad", { method: "POST", body: { tipo: "tema_visto", detalle: { tema: tema } }, silencioso: true })
        .catch(function () { });
}

function siguienteTema() {

    if (temaActual < 5) {
        document.getElementById("tema" + temaActual).classList.add("oculto");
        temaActual++;
        registrarTemaVisto(temaActual);
        document.getElementById("tema" + temaActual).classList.remove("oculto");
        window.scrollTo(0, 0);
    }

}

function reiniciarTeoria() {
    for (let i = 1; i <= 5; i++) {
        document.getElementById("tema" + i).classList.toggle("oculto", i !== 1);
    }
    temaActual = 1;
}

function verTemas() {
    reiniciarTeoria();
    mostrarPantalla("pantallaTeoria");
}

function terminarTeoria() {
    mostrarCatalogo();
}


// ============================================
// CATALOGO DE CURSOS
// ============================================

async function mostrarCatalogo() {

    let cursos;
    try {
        cursos = (await api("/api/cursos")).cursos;
    } catch (error) {
        alert(error.message);
        return;
    }

    let porcentaje = progresoActual ? progresoActual.porcentajeCurso : 0;

    let grid = document.getElementById("catalogoGrid");
    grid.innerHTML = "";

    if (cursos.length === 0) {
        grid.innerHTML = '<p class="text-muted">Todavía no hay cursos disponibles.</p>';
    }

    cursos.forEach(function (curso) {

        let tarjeta = document.createElement("div");
        tarjeta.className = curso.disponible ? "curso-card" : "curso-card curso-card-bloqueado";

        let modulos = curso.totalModulos + (curso.totalModulos === 1 ? " módulo" : " módulos");

        if (curso.disponible) {

            tarjeta.innerHTML =
                '<span class="curso-card-etiqueta etiqueta-disponible">Disponible</span>' +
                "<h3>" + escaparHtml(curso.nombre) + "</h3>" +
                '<p class="curso-card-nivel">Nivel: ' + escaparHtml(nivelTexto()) + " · " + modulos + "</p>" +
                '<div class="barra-progreso-curso"><div class="barra-progreso-curso-relleno" style="width:' + porcentaje + '%"></div></div>' +
                '<p class="curso-card-porcentaje">' + porcentaje + "% completado</p>" +
                '<button type="button" class="btn btn-outline-primary w-100 mb-2" onclick="verTemas()">Ver temas</button>' +
                '<button type="button" class="btn btn-primary w-100" onclick="mostrarPantalla(\'pantallaEditor\')">Practicar en el editor</button>';

        } else {

            tarjeta.innerHTML =
                '<span class="curso-card-etiqueta etiqueta-proximamente">Próximamente</span>' +
                "<h3>" + escaparHtml(curso.nombre) + "</h3>" +
                '<p class="curso-card-nivel">' + escaparHtml(curso.descripcion) + "</p>";
        }

        grid.appendChild(tarjeta);
    });

    mostrarPantalla("pantallaCatalogo");
}


// ============================================
// DEPURADOR DE CODIGO
// ============================================

async function validarCodigo() {

    let codigo = document.getElementById("codigoHTML").value;
    let boton = document.querySelector(".btn-validar");
    boton.disabled = true;

    try {
        let datos = await api("/api/depurador/analizar", { method: "POST", body: { codigoHtml: codigo } });
        progresoActual = datos.progreso;
        dibujarResultadoDepurador(datos);
    } catch (error) {
        alert(error.message);
    } finally {
        boton.disabled = false;
    }
}

function dibujarResultadoDepurador(datos) {

    let resultado = document.getElementById("resultadoEditor");
    let errores = datos.erroresDetectados;
    let contenido = "";

    if (errores.length === 0) {

        contenido = `
            <div class="resultado-exito">
                <div class="resultado-exito-icono">✓</div>
                <h4>¡Código correcto!</h4>
                <p>No encontramos ninguno de los errores que estamos buscando.</p>

                <div class="mensaje-ayuda">
                    ¡Muy bien! Llevas ${datos.progreso.porcentajeCurso}% del curso.
                </div>
            </div>
        `;

    } else {

        contenido = `
            <div class="resultado-error">
                <h4>Encontramos ${errores.length} error(es)</h4>
                <p>Revisa las siguientes recomendaciones:</p>
        `;

        errores.forEach(function (error) {

            contenido += `
                <div class="error-item">

                    <strong>${escaparHtml(error.titulo)}</strong>

                    <p><strong>Línea:</strong> ${error.linea}</p>

                    <p>${escaparHtml(error.explicacionIA)}</p>

                    <div class="error-solucion">
                        <strong>¿Cómo solucionarlo?</strong><br>
                        ${escaparHtml(error.solucion)}
                    </div>

                    <br>

                    <div class="error-solucion">
                        <strong>Ejemplo incorrecto:</strong><br>
                        <code>${escaparHtml(error.ejemploIncorrecto)}</code>
                    </div>

                    <br>

                    <div class="error-solucion">
                        <strong>Ejemplo correcto:</strong><br>
                        <code>${escaparHtml(error.ejemploCorrecto)}</code>
                    </div>

                </div>
            `;
        });

        contenido += "</div>";
    }

    // Extensión: recomendación de estudio cuando el servidor detecta errores que se repiten
    if (datos.recomendacion) {
        contenido += htmlRecomendacion(datos.recomendacion, "Te recomendamos repasar");
    }

    resultado.innerHTML = contenido;
}

function htmlRecomendacion(recomendacion, titulo) {

    let causas = recomendacion.basadoEnErrores.map(function (tipo) {
        return NOMBRES_ERROR[tipo] || tipo;
    }).join(", ");

    let modulos = recomendacion.modulosSugeridos.map(function (m) {
        return "<li>" + escaparHtml(m.curso) + " · " + escaparHtml(m.modulo) + "</li>";
    }).join("");

    return '<div class="mensaje-ayuda">' +
        "<strong>" + escaparHtml(titulo) + "</strong>" +
        '<p class="mb-1 mt-1">Por tus errores repetidos (' + escaparHtml(causas) + "):</p>" +
        '<ul class="mb-0">' + modulos + "</ul>" +
        "</div>";
}


// ============================================
// PERFIL DEL ESTUDIANTE
// ============================================

async function mostrarPerfil() {

    let sesion = obtenerSesion();

    if (sesion) {

        document.getElementById("nombrePerfilEstudiante").textContent = sesion.nombre;
        document.getElementById("correoPerfilEstudiante").textContent = sesion.email;
        document.getElementById("avatarPerfilEstudiante").textContent = sesion.nombre.charAt(0).toUpperCase();

        document.getElementById("perfilNombre").textContent = sesion.nombre;
        document.getElementById("perfilCorreo").textContent = sesion.email;

        let diagnostico = progresoActual ? progresoActual.diagnostico : null;
        document.getElementById("perfilPuntaje").textContent = diagnostico
            ? diagnostico.aciertos + " de " + diagnostico.total + " (" + capitalizar(diagnostico.nivel) + ")"
            : "Sin hacer";

        document.getElementById("perfilErrores").textContent = progresoActual ? progresoActual.erroresCorregidos : 0;

        cargarRecomendaciones(sesion.id);
        cargarActividad(sesion.id);
    }

    mostrarPantalla("pantallaPerfil");
}

const NOMBRES_ACTIVIDAD = {
    registro: "Creaste tu cuenta", login: "Iniciaste sesión", curso_consultado: "Consultaste un curso",
    tema_visto: "Viste un tema", diagnostico_iniciado: "Iniciaste el diagnóstico",
    diagnostico_respuesta: "Respondiste una pregunta", diagnostico_finalizado: "Terminaste el diagnóstico",
    codigo_analizado: "Analizaste código HTML", comentario_creado: "Comentaste un módulo"
};

// Perfil completo: datos de SQLite + últimas 10 actividades guardadas en MongoDB
async function cargarActividad(idUsuario) {

    let caja = document.getElementById("perfilActividad");
    caja.textContent = "Cargando...";

    try {
        let datos = await api("/api/usuarios/" + idUsuario + "/perfil-completo");

        if (!datos.actividad.disponible) {
            caja.textContent = "El historial de actividad no está disponible en este momento.";
            return;
        }
        if (datos.actividad.ultimas.length === 0) {
            caja.textContent = "Todavía no tienes actividad registrada.";
            return;
        }

        caja.innerHTML = "";
        datos.actividad.ultimas.forEach(function (a) {
            let fila = document.createElement("div");
            fila.style.fontSize = "14px";
            let cuando = new Date(a.fecha).toLocaleString("es-CO");
            fila.textContent = (NOMBRES_ACTIVIDAD[a.tipo] || a.tipo) + " · " + cuando;
            caja.appendChild(fila);
        });

    } catch (error) {
        caja.textContent = error.message;
    }
}

async function cargarRecomendaciones(idUsuario) {

    let caja = document.getElementById("perfilRecomendaciones");
    caja.textContent = "Cargando...";

    try {
        let datos = await api("/api/recomendaciones/" + idUsuario);

        if (datos.modulosSugeridos.length === 0) {
            caja.textContent = "Todavía no tenemos recomendaciones. Aparecen cuando repites el mismo tipo de error.";
        } else {
            caja.innerHTML = htmlRecomendacion(datos, "Repasa estos módulos");
        }

    } catch (error) {
        caja.textContent = error.message;
    }
}

function volverAlEditor() {
    mostrarPantalla("pantallaEditor");
}


// ============================================
// PROFESOR - PANEL DE PROGRESO
// ============================================

async function mostrarPanelProfesor() {

    aplicarRolEnMenus();

    try {
        let cursos = (await api("/api/cursos")).cursos;

        if (cursos.length === 0) {
            dibujarPanelProfesor(null);
        } else {
            dibujarPanelProfesor(await api("/api/profesor/progreso/" + cursos[0].id));
        }

    } catch (error) {
        alert(error.message);
    }

    mostrarPantalla("pantallaPanelProfesor");
}

function dibujarPanelProfesor(datos) {

    let listaEstudiantes = document.getElementById("listaEstudiantesProfesor");
    let listaErrores = document.getElementById("listaTopErroresProfesor");
    listaEstudiantes.innerHTML = "";
    listaErrores.innerHTML = "";

    if (!datos) {
        document.getElementById("panelSubtitulo").textContent = "Todavía no hay cursos. Crea uno en la pestaña Cursos.";
        document.getElementById("statActivos").textContent = "0";
        document.getElementById("statPromedio").textContent = "0%";
        document.getElementById("statErrores").textContent = "0";
        return;
    }

    document.getElementById("panelSubtitulo").textContent = "Así va tu grupo en " + datos.curso + ".";
    document.getElementById("statActivos").textContent = datos.estudiantesActivos;
    document.getElementById("statPromedio").textContent = datos.promedioProgreso + "%";
    document.getElementById("statErrores").textContent = datos.erroresDetectados;

    if (datos.estudiantes.length === 0) {
        listaEstudiantes.innerHTML = '<p class="text-muted mb-0">Aún no hay estudiantes con actividad.</p>';
    }

    datos.estudiantes.forEach(function (estudiante) {

        let fila = document.createElement("div");
        fila.className = "fila-estudiante";
        fila.innerHTML =
            "<span>" + escaparHtml(estudiante.nombre) + "</span>" +
            '<div class="barra-mini"><div class="barra-mini-relleno" style="width:' + estudiante.progreso + '%"></div></div>' +
            "<span>" + estudiante.progreso + "%</span>";
        listaEstudiantes.appendChild(fila);
    });

    if (datos.topErrores.length === 0) {
        listaErrores.innerHTML = '<p class="text-muted mb-0">Aún no hay errores registrados.</p>';
    }

    datos.topErrores.forEach(function (error, indice) {

        let fila = document.createElement("div");
        fila.className = "fila-error-top";
        fila.innerHTML =
            '<div class="fila-error-top-encabezado">' +
                "<strong>" + (indice + 1) + ". " + escaparHtml(error.nombre) + "</strong>" +
                "<span>" + error.porcentaje + "% (" + error.cantidad + ")</span>" +
            "</div>" +
            '<div class="barra-mini"><div class="barra-mini-relleno barra-mini-roja" style="width:' + error.porcentaje + '%"></div></div>';
        listaErrores.appendChild(fila);
    });
}


// ============================================
// PROFESOR - GESTION DE CURSOS
// ============================================

let cursosCache = [];

async function dibujarListaCursos() {

    cursosCache = (await api("/api/cursos")).cursos;

    let lista = document.getElementById("listaCursos");
    lista.innerHTML = "";

    if (cursosCache.length === 0) {
        lista.innerHTML = '<p class="text-muted">Todavía no hay cursos. Crea el primero con el botón de arriba.</p>';
    }

    cursosCache.forEach(function (curso) {

        let claseEstado = curso.estado === "Activo" ? "curso-estado-activo" : "curso-estado-inactivo";
        let modulos = curso.totalModulos + (curso.totalModulos === 1 ? " módulo" : " módulos");

        let item = document.createElement("div");
        item.className = "curso-item";
        item.innerHTML =
            "<div>" +
                "<h4>" + escaparHtml(curso.nombre) + "</h4>" +
                "<p>" + escaparHtml(curso.descripcion) + "</p>" +
                '<span class="curso-estado ' + claseEstado + '">' + escaparHtml(curso.estado) + "</span> " +
                '<span class="text-muted" style="font-size:12px;">' + escaparHtml(curso.nivel) + " · " + modulos + "</span>" +
            "</div>" +
            '<div class="curso-acciones">' +
                '<button onclick="verCurso(' + curso.id + ')">Ver</button>' +
                '<button onclick="editarCurso(' + curso.id + ')">Editar</button>' +
                '<button class="btn-eliminar-curso" onclick="eliminarCurso(' + curso.id + ')">Eliminar</button>' +
            "</div>";
        lista.appendChild(item);
    });
}

async function mostrarGestionCursos() {

    aplicarRolEnMenus();

    try {
        await dibujarListaCursos();
        mostrarPantalla("pantallaGestionCursos");
    } catch (error) {
        alert(error.message);
    }
}

async function verCurso(idCurso) {

    try {
        let curso = await api("/api/cursos/" + idCurso);

        let modulos = curso.modulos.length === 0
            ? "Todavía no tiene módulos."
            : curso.modulos.map(function (m) { return m.orden + ". " + m.titulo; }).join("\n");

        alert(curso.nombre + "\n\nNivel: " + curso.nivel + "\nEstado: " + curso.estado +
            "\n\n" + curso.descripcion + "\n\nMódulos:\n" + modulos);

    } catch (error) {
        alert(error.message);
    }
}

function abrirFormularioCurso() {
    document.getElementById("formCurso").reset();
    document.getElementById("cursoId").value = "";
    document.getElementById("tituloFormularioCurso").textContent = "Crear curso";
    mostrarPantalla("pantallaCrearCurso");
}

function editarCurso(idCurso) {

    let curso = cursosCache.find(function (c) { return c.id === idCurso; });
    if (!curso) return;

    document.getElementById("cursoId").value = curso.id;
    document.getElementById("cursoNombre").value = curso.nombre;
    document.getElementById("cursoDescripcion").value = curso.descripcion;
    document.getElementById("cursoNivel").value = curso.nivel;
    document.getElementById("cursoEstado").value = curso.estado;
    document.getElementById("tituloFormularioCurso").textContent = "Editar curso";

    mostrarPantalla("pantallaCrearCurso");
}

async function eliminarCurso(idCurso) {

    let confirmacion = confirm("¿Seguro que quieres eliminar este curso? También se eliminarán sus módulos.");
    if (!confirmacion) return;

    try {
        await api("/api/cursos/" + idCurso, { method: "DELETE" });
        await dibujarListaCursos();
    } catch (error) {
        alert(error.message);
    }
}

document.getElementById("formCurso").addEventListener("submit", async function (event) {

    event.preventDefault();

    let idCurso = document.getElementById("cursoId").value;
    let cuerpo = {
        nombre: document.getElementById("cursoNombre").value.trim(),
        descripcion: document.getElementById("cursoDescripcion").value.trim(),
        nivel: document.getElementById("cursoNivel").value,
        estado: document.getElementById("cursoEstado").value
    };

    if (cuerpo.nombre === "" || cuerpo.descripcion === "") {
        alert("Completa el nombre y la descripción del curso.");
        return;
    }

    let boton = event.submitter;
    if (boton) boton.disabled = true;

    try {
        if (idCurso) {
            await api("/api/cursos/" + idCurso, { method: "PUT", body: cuerpo });   // editar
        } else {
            await api("/api/cursos", { method: "POST", body: cuerpo });             // crear
        }
        await mostrarGestionCursos();
    } catch (error) {
        alert(error.message);
    } finally {
        if (boton) boton.disabled = false;
    }
});


// ============================================
// ADMINISTRADOR - USUARIOS Y ROLES
// ============================================

const NOMBRES_ROL = { estudiante: "Estudiante", profesor: "Profesor", admin: "Administrador" };

async function mostrarAdminUsuarios() {

    aplicarRolEnMenus();

    try {
        await dibujarListaUsuarios();
        mostrarPantalla("pantallaAdminUsuarios");
    } catch (error) {
        alert(error.message);
    }
}

async function dibujarListaUsuarios() {

    let datos = await api("/api/admin/usuarios");
    let miId = obtenerSesion().id;
    let lista = document.getElementById("listaUsuarios");
    lista.innerHTML = "";

    datos.usuarios.forEach(function (u) {

        let item = document.createElement("div");
        item.className = "curso-item";

        let info = document.createElement("div");
        let nombre = document.createElement("h4");
        nombre.textContent = u.nombre + (u.id === miId ? " (tú)" : "");
        let correo = document.createElement("p");
        correo.textContent = u.email;
        info.appendChild(nombre);
        info.appendChild(correo);

        let acciones = document.createElement("div");
        acciones.className = "curso-acciones";

        let selector = document.createElement("select");
        selector.className = "form-select";
        selector.disabled = u.id === miId; // nadie puede cambiarse su propio rol
        Object.keys(NOMBRES_ROL).forEach(function (rol) {
            let opcion = document.createElement("option");
            opcion.value = rol;
            opcion.textContent = NOMBRES_ROL[rol];
            opcion.selected = rol === u.rol;
            selector.appendChild(opcion);
        });

        let guardar = document.createElement("button");
        guardar.textContent = "Guardar rol";
        guardar.disabled = u.id === miId;
        guardar.onclick = function () { cambiarRolUsuario(u.id, selector.value); };

        acciones.appendChild(selector);
        acciones.appendChild(guardar);
        item.appendChild(info);
        item.appendChild(acciones);
        lista.appendChild(item);
    });
}

async function cambiarRolUsuario(idUsuario, rol) {

    try {
        await api("/api/admin/usuarios/" + idUsuario + "/rol", { method: "PUT", body: { rol: rol } });
        await dibujarListaUsuarios();
    } catch (error) {
        alert(error.message);
    }
}

document.getElementById("formAdminUsuario").addEventListener("submit", async function (event) {

    event.preventDefault();

    let cuerpo = {
        nombre: document.getElementById("adminNombre").value.trim(),
        email: document.getElementById("adminEmail").value.trim().toLowerCase(),
        password: document.getElementById("adminPassword").value,
        rol: document.getElementById("adminRol").value
    };

    if (!contrasenaValida(cuerpo.password)) {
        alert("La contraseña debe tener mínimo 8 caracteres, con letras y números.");
        return;
    }

    try {
        await api("/api/admin/usuarios", { method: "POST", body: cuerpo });
        document.getElementById("formAdminUsuario").reset();
        await dibujarListaUsuarios();
    } catch (error) {
        alert(error.message);
    }
});


// ============================================
// PROFESOR - PERFIL
// ============================================

function mostrarPerfilProfesor() {

    aplicarRolEnMenus();

    let sesion = obtenerSesion();

    if (sesion) {
        document.getElementById("nombrePerfilProfesor").textContent = sesion.nombre;
        document.getElementById("correoPerfilProfesor").textContent = sesion.email;
        document.getElementById("avatarPerfilProfesor").textContent = sesion.nombre.charAt(0).toUpperCase();
        document.getElementById("perfilNombreProfesor").textContent = sesion.nombre;
        document.getElementById("perfilCorreoProfesor").textContent = sesion.email;
    }

    mostrarPantalla("pantallaPerfilProfesor");
}


// ============================================
// INICIALIZACION DE LA APLICACION
// ============================================

// Si ya había una sesión abierta (por ejemplo, se recargó la página), le preguntamos
// al servidor si sigue siendo válida y llevamos al usuario directo a su pantalla.
(async function () {

    let sesion = obtenerSesion();
    if (!sesion || !sesion.token) return;

    try {
        let datos = await api("/api/auth/yo", { silencioso: true });
        progresoActual = datos.progreso;
        irA(datos.siguiente);
    } catch (error) {
        if (error.estado === 401) {
            borrarSesion(); // sesión vencida: se queda en la pantalla inicial
        }
    }

})();
