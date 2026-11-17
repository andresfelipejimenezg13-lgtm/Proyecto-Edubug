<template><span><template v-for="(p, i) in partes" :key="i"><code v-if="p.codigo">{{ p.texto }}</code><template v-else>{{ p.texto }}</template></template></span></template>

<script>
// COMPONENTE · Texto en el que las etiquetas (<p>, </a>...) se muestran como código en línea.
import { computed } from "vue";
import { partesDeTexto } from "../utils/leccion.js";

export default {
  name: "TextoLinea",
  props: { texto: { type: String, required: true } },
  setup(props) { return { partes: computed(() => partesDeTexto(props.texto)) }; }
};
</script>
