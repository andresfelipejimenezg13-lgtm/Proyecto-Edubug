<template>
  <div>
    <template v-for="(b, i) in bloques" :key="i">
      <h2 v-if="b.tipo === 'subtitulo'">{{ b.texto }}</h2>
      <p v-else-if="b.tipo === 'parrafo'"><texto-linea :texto="b.texto" /></p>
      <ul v-else-if="b.tipo === 'lista'"><li v-for="(it, j) in b.items" :key="j"><texto-linea :texto="it" /></li></ul>
      <div v-else-if="b.tipo === 'consejo'" class="consejo"><p><texto-linea :texto="b.texto" /></p></div>
      <figure v-else-if="b.tipo === 'imagen'" class="medio"><img :src="b.url" :alt="b.alt" loading="lazy"><figcaption v-if="b.alt">{{ b.alt }}</figcaption></figure>
      <div v-else-if="b.tipo === 'video'" class="medio medio-video">
        <iframe v-if="b.url.embed" :src="b.url.embed" title="Video del módulo" allowfullscreen loading="lazy"></iframe>
        <video v-else :src="b.url.directo" controls preload="metadata"></video>
      </div>
      <bloque-codigo v-else :lineas="b.lineas" :lenguaje="b.lenguaje" :probar="probar" @probar="(c) => $emit('probar', c)" />
    </template>
  </div>
</template>

<script>
// COMPONENTE · Muestra el contenido de un módulo (texto con formato) como párrafos, listas, código, imágenes y videos.
// Lo usan la lectura del módulo y la vista previa del profesor.
import { computed } from "vue";
import { bloquesDe } from "../utils/leccion.js";
import BloqueCodigo from "./BloqueCodigo.vue";
import TextoLinea from "./TextoLinea.vue";

export default {
  name: "ContenidoModulo",
  components: { BloqueCodigo, TextoLinea },
  props: { contenido: { type: String, default: "" }, probar: { type: Boolean, default: false } },
  emits: ["probar"],
  setup(props) { return { bloques: computed(() => bloquesDe(props.contenido)) }; }
};
</script>
