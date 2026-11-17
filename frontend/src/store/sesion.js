// ESTADO · Sesión del usuario (reactiva) guardada en localStorage.
// Es lo único que se comparte entre pantallas, junto con el progreso que devuelve la API.
import { reactive } from "vue";

const CLAVE = "edudebug_sesion";

function leer() {
  try { return JSON.parse(localStorage.getItem(CLAVE)) || {}; } catch (e) { return {}; }
}

export const sesion = reactive({
  id: null, nombre: "", email: "", rol: "", token: "",
  progreso: null,            // último resumen de progreso que devolvió el backend
  ...leer(),

  get activa() { return !!this.token; },
  get esDocente() { return this.rol === "profesor" || this.rol === "admin"; },
  get esAdmin() { return this.rol === "admin"; },

  // Recibe la respuesta de /api/auth/login o /api/auth/yo
  iniciar(datos) {
    this.id = datos.usuario.id;
    this.nombre = datos.usuario.nombre;
    this.email = datos.usuario.email;
    this.rol = datos.usuario.rol;
    this.token = datos.token;
    this.progreso = datos.progreso;
    try {
      localStorage.setItem(CLAVE, JSON.stringify({
        id: this.id, nombre: this.nombre, email: this.email, rol: this.rol, token: this.token
      }));
    } catch (e) { /* almacenamiento bloqueado */ }
  },

  cerrar() {
    this.id = null; this.nombre = ""; this.email = ""; this.rol = ""; this.token = ""; this.progreso = null;
    try { localStorage.removeItem(CLAVE); } catch (e) { /* nada */ }
  }
});

// Utilidades de presentación usadas por varias pantallas
export const capitalizar = (t) => t.charAt(0).toUpperCase() + t.slice(1);
export const contrasenaValida = (p) => p.length >= 8 && /[A-Za-z]/.test(p) && /\d/.test(p);

// A qué pantalla va cada usuario después de entrar (lo decide el backend: campo "siguiente")
export function rutaSegun(siguiente) {
  if (siguiente === "panel") return "/panel";
  if (siguiente === "catalogo") return "/catalogo";
  return "/diagnostico";
}
