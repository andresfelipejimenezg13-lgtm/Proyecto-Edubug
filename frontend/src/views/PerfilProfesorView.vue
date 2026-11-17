<template>
  <div>
    <nav-docente />
    <main class="pagina pagina-angosta">
      <perfil-cabecera :tipo="sesion.esAdmin ? 'Administrador' : 'Profesor'" />
      <div class="tarjeta"><h3>Tu cuenta</h3>
        <p class="texto-suave mb-0">Desde aquí gestionas los cursos y revisas el progreso del grupo.</p></div>
      <div class="encabezado-pagina" style="margin-top:1.5rem"><span></span><button class="btn btn-peligro" @click="cerrarSesion">Cerrar sesión</button></div>
    </main>
  </div>
</template>

<script>
// VISTA · Perfil del profesor/admin (ruta /perfil-docente). Solo lee la sesión; no llama a la API.
import { useRouter } from "vue-router";
import { sesion } from "../store/sesion.js";
import NavDocente from "../components/NavDocente.vue";
import PerfilCabecera from "../components/PerfilCabecera.vue";

export default {
  name: "PerfilProfesorView",
  components: { NavDocente, PerfilCabecera },
  setup() { const router = useRouter(); return { sesion, cerrarSesion: () => { sesion.cerrar(); router.push("/"); } }; }
};
</script>
