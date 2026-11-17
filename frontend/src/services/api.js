// SERVICIO · Único punto donde la Vista habla con el Controlador (Flask, rutas /api/...).
// Ninguna pantalla usa fetch directamente: todas pasan por api().
import { sesion } from "../store/sesion.js";

// En producción el frontend lo sirve Flask (mismo origen). Si se abre como archivo o desde un
// servidor de desarrollo (puerto 55xx) apunta al backend local.
export const API_URL = window.EDUDEBUG_API ||
  ((location.protocol === "file:" || /^55\d\d$/.test(location.port)) ? "http://127.0.0.1:5000" : "");

export async function api(ruta, opciones = {}) {
  const cabeceras = { "Content-Type": "application/json" };
  if (sesion.token) cabeceras["Authorization"] = "Bearer " + sesion.token;

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
  try { datos = await respuesta.json(); } catch (e) { /* sin cuerpo JSON */ }

  if (!respuesta.ok) {
    const error = new Error(datos.error || "Ocurrió un error inesperado.");
    error.estado = respuesta.status;
    // Token vencido o inválido: se limpia la sesión y se vuelve al login.
    if (respuesta.status === 401 && sesion.token && !opciones.silencioso) {
      sesion.cerrar();
      location.hash = "#/login";
    }
    throw error;
  }
  return datos;
}
