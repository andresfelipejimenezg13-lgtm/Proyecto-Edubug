<template>
  <auth-layout>
    <h1>Iniciar sesión</h1>
    <p class="texto-suave">Entra para seguir donde lo dejaste.</p>
    <form @submit.prevent="enviar">
      <div class="campo"><label for="correoLogin">Correo electrónico</label>
        <input type="email" id="correoLogin" v-model="email" class="entrada" placeholder="correo@ejemplo.com" autocomplete="email" required></div>
      <div class="campo"><label for="passwordLogin">Contraseña</label>
        <input type="password" id="passwordLogin" v-model="password" class="entrada" autocomplete="current-password" required></div>
      <button type="submit" class="btn btn-primario btn-bloque" :disabled="enviando">{{ enviando ? "Entrando..." : "Entrar" }}</button>
    </form>
    <p class="mt-2 texto-suave">¿No tienes cuenta? <router-link to="/registro">Crea una</router-link></p>
    <div class="acceso-demo">Cuentas de prueba (contraseña 123456):
      <div><button type="button" class="btn btn-borde btn-chico" @click="usar('estudiante@edudebug.com')">Estudiante</button>
        <button type="button" class="btn btn-borde btn-chico" @click="usar('profesor@edudebug.com')">Profesor</button></div></div>
    <button class="enlace-volver" @click="$router.push('/')">← Volver al inicio</button>
  </auth-layout>
</template>

<script>
// VISTA · Iniciar sesión (ruta /login) → POST /api/auth/login
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api.js";
import { sesion, rutaSegun } from "../store/sesion.js";
import { avisar } from "../store/toast.js";
import AuthLayout from "../components/AuthLayout.vue";

export default {
  name: "LoginView",
  components: { AuthLayout },
  setup() {
    const router = useRouter();
    const email = ref(""), password = ref(""), enviando = ref(false);
    function usar(correo) { email.value = correo; password.value = "123456"; }
    async function enviar() {
      enviando.value = true;
      try {
        const datos = await api("/api/auth/login", { method: "POST", body: { email: email.value.trim().toLowerCase(), password: password.value } });
        sesion.iniciar(datos);
        password.value = "";
        router.push(rutaSegun(datos.siguiente));   // el backend decide: panel / catálogo / diagnóstico
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    return { email, password, enviando, enviar, usar };
  }
};
</script>
