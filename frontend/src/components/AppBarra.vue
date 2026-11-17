<template>
  <header class="barra">
    <div class="barra-interior">
      <logo-edudebug a="/catalogo" />
      <div v-if="sesion.progreso" class="barra-progreso" :title="'Avance del curso: ' + sesion.progreso.porcentajeCurso + '%'">
        <span>{{ sesion.progreso.porcentajeCurso }}%</span>
        <div class="pista"><i :style="{ width: sesion.progreso.porcentajeCurso + '%' }"></i></div>
      </div>
      <nav class="barra-enlaces" aria-label="Principal">
        <router-link to="/catalogo">Cursos</router-link>
        <router-link to="/editor">Editor</router-link>
        <router-link to="/perfil">Mi perfil</router-link>
      </nav>
    </div>
  </header>
</template>

<script>
// COMPONENTE · Barra superior del estudiante: cursos, editor y perfil, con su avance del curso.
import { sesion } from "../store/sesion.js";
import LogoEdudebug from "./LogoEdudebug.vue";

export default { name: "AppBarra", components: { LogoEdudebug }, setup() { return { sesion }; } };
</script>
