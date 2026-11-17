// ARRANQUE · Crea la app Vue, restaura la sesión (si hay token válido) y monta el router.
import { createApp } from "vue";
import "./assets/estilos.css";
import App from "./App.vue";
import { router } from "./router/index.js";
import { api } from "./services/api.js";
import { sesion, rutaSegun } from "./store/sesion.js";

async function restaurarSesion() {
  if (!sesion.activa) return null;
  try {
    const datos = await api("/api/auth/yo", { silencioso: true });
    sesion.progreso = datos.progreso;
    return datos.siguiente;
  } catch (error) {
    if (error.estado === 401) sesion.cerrar();   // sesión vencida: vuelve a las pantallas públicas
    return null;
  }
}

async function arrancar() {
  const siguiente = await restaurarSesion();
  const app = createApp(App);
  app.use(router);
  app.mount("#app");
  await router.isReady();
  // Con sesión abierta, las pantallas públicas llevan a la que le toca según el rol
  if (siguiente && ["/", "/login", "/registro"].includes(router.currentRoute.value.path)) {
    router.replace(rutaSegun(siguiente));
  }
}
arrancar();
