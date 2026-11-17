<template>
  <div>
    <header class="barra"><div class="barra-interior"><logo-edudebug /></div></header>
    <main class="pagina pagina-angosta" v-if="r">
      <h1 style="font-size:1.8rem">Diagnóstico terminado</h1>
      <div class="tarjeta mb-3">
        <div class="resultado-puntaje"><strong>{{ r.aciertos }}</strong><span class="texto-suave">de {{ r.total }} correctas</span>
          <span class="etiqueta" :class="clase" style="margin-left:auto">Nivel {{ r.nivel }}</span></div>
        <p class="mt-2 mb-0">{{ mensaje }}</p>
      </div>
      <div class="tarjeta">
        <h3>Revisa tus respuestas</h3>
        <div v-for="(item, i) in r.detalle" :key="i" class="revision">
          <span class="marca" :class="item.acerto ? 'marca-ok' : 'marca-mal'">{{ item.acerto ? "✓" : "✗" }}</span>
          <div>
            <strong>{{ item.texto }}</strong>
            <div class="texto-suave" style="font-size:.92rem">
              <template v-if="item.acerto">Tu respuesta: {{ item.respuestaCorrecta }}</template>
              <template v-else>Tu respuesta: {{ item.tuRespuesta }} · Correcta: {{ item.respuestaCorrecta }}</template>
            </div>
          </div>
        </div>
      </div>
      <button type="button" class="btn btn-primario btn-bloque mt-3" @click="continuar">Ir a los cursos</button>
    </main>
  </div>
</template>

<script>
// VISTA · Resultado del diagnóstico (ruta /resultado). Los datos vienen del store, no de otra llamada.
import { computed } from "vue";
import { useRouter } from "vue-router";
import { diagnostico } from "../store/diagnostico.js";
import LogoEdudebug from "../components/LogoEdudebug.vue";

const MENSAJES = {
  alto: "Tienes una buena base de HTML. Puedes pasar directo a los módulos y practicar en el editor.",
  medio: "Tienes conocimientos básicos. Repasa los módulos y sigue practicando.",
  bajo: "Conviene reforzar los conceptos básicos. Empieza por el primer módulo del curso."
};

export default {
  name: "ResultadoView",
  components: { LogoEdudebug },
  setup() {
    const router = useRouter();
    const r = computed(() => diagnostico.resultado);
    if (!r.value) router.replace("/diagnostico");
    const mensaje = computed(() => r.value ? MENSAJES[r.value.nivel] : "");
    const clase = computed(() => ({ alto: "etiqueta-verde", medio: "etiqueta-ambar", bajo: "etiqueta-coral" }[r.value && r.value.nivel]));
    return { r, mensaje, clase, continuar: () => router.push("/catalogo") };
  }
};
</script>
