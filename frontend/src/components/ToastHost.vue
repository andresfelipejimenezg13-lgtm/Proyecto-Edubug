<template>
  <div class="avisos" role="status" aria-live="polite">
    <div v-for="a in avisos" :key="a.id" class="aviso" :class="{ 'aviso-error': a.tipo === 'error' }">{{ a.mensaje }}</div>
  </div>
</template>

<script>
// COMPONENTE · Muestra los avisos de store/toast.js (una sola vez, en App.vue).
import { avisos } from "../store/toast.js";
export default { name: "ToastHost", setup() { return { avisos }; } };
</script>
