<!-- RAÍZ · El <router-view> muestra la pantalla que decide el router; ToastHost muestra los avisos. -->
<template>
  <router-view />
  <toast-host />
</template>

<script>
import ToastHost from "./components/ToastHost.vue";
export default { name: "App", components: { ToastHost } };
</script>
