<template>
  <auth-layout>
    <h1>Crear cuenta</h1>
    <p class="texto-suave">Es gratis y toma un minuto.</p>
    <form @submit.prevent="enviar">
      <div class="campo"><label for="nombre">Nombre</label>
        <input type="text" id="nombre" v-model="nombre" class="entrada" autocomplete="name" required></div>
      <div class="campo"><label for="correo">Correo electrónico</label>
        <input type="email" id="correo" v-model="email" class="entrada" placeholder="correo@ejemplo.com" autocomplete="email" required></div>
      <div class="campo"><label for="password">Contraseña</label>
        <input type="password" id="password" v-model="password" class="entrada" minlength="8" autocomplete="new-password" required>
        <p class="ayuda">Mínimo 8 caracteres, con letras y números.</p></div>
      <div class="campo"><label for="confirmarPassword">Confirmar contraseña</label>
        <input type="password" id="confirmarPassword" v-model="confirmar" class="entrada" autocomplete="new-password" required></div>
      <div class="campo-check"><input type="checkbox" id="terminos" v-model="terminos" required>
        <label for="terminos">Acepto los términos y condiciones</label></div>
      <button type="submit" class="btn btn-primario btn-bloque" :disabled="enviando">{{ enviando ? "Creando..." : "Crear cuenta" }}</button>
    </form>
    <p class="mt-2 texto-suave">¿Ya tienes cuenta? <router-link to="/login">Inicia sesión</router-link></p>
    <button class="enlace-volver" @click="$router.push('/')">← Volver al inicio</button>
  </auth-layout>
</template>

<script>
// VISTA · Crear cuenta (ruta /registro) → POST /api/usuarios/registro (solo crea estudiantes)
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api.js";
import { contrasenaValida } from "../store/sesion.js";
import { avisar } from "../store/toast.js";
import AuthLayout from "../components/AuthLayout.vue";

export default {
  name: "RegistroView",
  components: { AuthLayout },
  setup() {
    const router = useRouter();
    const nombre = ref(""), email = ref(""), password = ref(""), confirmar = ref("");
    const terminos = ref(false), enviando = ref(false);
    async function enviar() {
      if (!contrasenaValida(password.value)) { avisar("La contraseña debe tener mínimo 8 caracteres, con letras y números.", "error"); return; }
      if (password.value !== confirmar.value) { avisar("Las contraseñas no coinciden.", "error"); return; }
      enviando.value = true;
      try {
        await api("/api/usuarios/registro", { method: "POST",
          body: { nombre: nombre.value.trim(), email: email.value.trim().toLowerCase(), password: password.value, rol: "estudiante" } });
        avisar("Cuenta creada. Ya puedes iniciar sesión.");
        router.push("/login");
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    return { nombre, email, password, confirmar, terminos, enviando, enviar };
  }
};
</script>
