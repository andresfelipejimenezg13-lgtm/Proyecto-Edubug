<template>
  <div class="perfil-cab">
    <div class="avatar" aria-hidden="true">{{ sesion.nombre.charAt(0).toUpperCase() }}</div>
    <div>
      <h1>{{ sesion.nombre }}</h1>
      <p>{{ sesion.email }}</p>
      <span class="etiqueta etiqueta-verde">{{ tipo }}</span>
    </div>
  </div>
</template>

<script>
// COMPONENTE · Avatar + nombre + correo + tipo de usuario (perfil de estudiante y de profesor).
import { sesion } from "../store/sesion.js";
export default { name: "PerfilCabecera", props: { tipo: { type: String, required: true } }, setup() { return { sesion }; } };
</script>
