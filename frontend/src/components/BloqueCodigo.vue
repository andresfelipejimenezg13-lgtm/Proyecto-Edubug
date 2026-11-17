<template>
  <div class="codigo">
    <div class="codigo-barra">
      <span>{{ lenguaje.toUpperCase() }}</span>
      <div>
        <button type="button" @click="copiar">{{ copiado ? "Copiado" : "Copiar" }}</button>
        <button v-if="probar && lenguaje === 'html'" type="button" @click="$emit('probar', lineas.join('\n'))">Probar en el editor</button>
      </div>
    </div>
    <pre><code><span v-for="(l, i) in lineas" :key="i" class="linea"><b>{{ i + 1 }}</b>{{ l }}
</span></code></pre>
  </div>
</template>

<script>
// COMPONENTE · Código con números de línea, botón de copiar y (opcional) "Probar en el editor".
import { ref } from "vue";
import { avisar } from "../store/toast.js";

export default {
  name: "BloqueCodigo",
  props: { lineas: { type: Array, required: true }, probar: { type: Boolean, default: false },
           lenguaje: { type: String, default: "html" } },
  emits: ["probar"],
  setup(props) {
    const copiado = ref(false);
    async function copiar() {
      try {
        await navigator.clipboard.writeText(props.lineas.join("\n"));
        copiado.value = true;
        setTimeout(() => { copiado.value = false; }, 1800);
      } catch (e) { avisar("No se pudo copiar. Selecciona el código y copia con Ctrl+C.", "error"); }
    }
    return { copiado, copiar };
  }
};
</script>
