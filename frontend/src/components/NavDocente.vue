<template>
  <header class="barra">
    <div class="barra-interior">
      <logo-edudebug a="/panel" />
      <nav class="barra-enlaces" aria-label="Principal">
        <router-link to="/panel">Panel</router-link>
        <router-link to="/cursos">Cursos</router-link>
        <router-link v-if="sesion.esAdmin" to="/usuarios">Usuarios</router-link>
        <router-link to="/perfil-docente">Perfil</router-link>
      </nav>
    </div>
  </header>
</template>

<script>
// COMPONENTE · Barra superior del profesor/admin (Panel, Cursos, Usuarios solo admin, Perfil).
import { sesion } from "../store/sesion.js";
import LogoEdudebug from "./LogoEdudebug.vue";

export default { name: "NavDocente", components: { LogoEdudebug }, setup() { return { sesion }; } };
</script>
