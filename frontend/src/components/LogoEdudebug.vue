<template>
  <router-link :to="a" class="logo" aria-label="EDUDEBUG, inicio">
    <span class="logo-marca" aria-hidden="true">&lt;/&gt;</span>
    <span>EDU<span class="logo-bug">DEBUG</span></span>
  </router-link>
</template>

<script>
// COMPONENTE · Logo con el subrayado ondulado de "error". Lleva al inicio de cada rol.
export default { name: "LogoEdudebug", props: { a: { type: String, default: "/" } } };
</script>
