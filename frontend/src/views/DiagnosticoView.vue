<template>
  <div>
    <header class="barra"><div class="barra-interior"><logo-edudebug /></div></header>
    <main class="pagina pagina-angosta">
      <div class="pregunta-caja">
        <h1 style="font-size:1.8rem">Diagnóstico de HTML</h1>
        <p class="texto-suave">Cinco preguntas para conocer tu nivel. Se adaptan a tus respuestas.</p>
        <div class="datos-fila mb-2"><span>Pregunta {{ estado ? estado.numero : 1 }} de {{ estado ? estado.total : 5 }}</span></div>
        <div class="progreso mb-3" role="progressbar" :aria-valuenow="porcentaje" aria-valuemin="0" aria-valuemax="100"><i :style="{ width: porcentaje + '%' }"></i></div>
        <form class="tarjeta" @submit.prevent="responder">
          <p v-if="cargando" class="cargando">Cargando pregunta...</p>
          <div v-else-if="error">
            <p>{{ error }}</p>
            <button type="button" class="btn btn-borde" @click="iniciar">Reintentar</button>
          </div>
          <fieldset v-else-if="estado" style="border:0;padding:0;margin:0">
            <legend style="font-weight:800;font-size:1.15rem;margin-bottom:1rem;padding:0">{{ estado.numero }}. {{ estado.pregunta.texto }}</legend>
            <label v-for="o in estado.pregunta.opciones" :key="o.idOpcion" class="opcion">
              <input type="radio" name="opcionDiagnostico" :value="o.idOpcion" v-model="opcion"><span>{{ o.texto }}</span>
            </label>
          </fieldset>
          <button type="submit" class="btn btn-primario btn-bloque mt-2" :disabled="opcion === null || enviando">{{ esUltima ? "Terminar diagnóstico" : "Responder" }}</button>
        </form>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Diagnóstico adaptativo (ruta /diagnostico)
// POST /api/diagnostico/iniciar → pregunta 1; POST /api/diagnostico/responder → siguiente o resultado.
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api.js";
import { sesion } from "../store/sesion.js";
import { diagnostico } from "../store/diagnostico.js";
import { avisar } from "../store/toast.js";
import LogoEdudebug from "../components/LogoEdudebug.vue";

export default {
  name: "DiagnosticoView",
  components: { LogoEdudebug },
  setup() {
    const router = useRouter();
    const estado = ref(null), error = ref(""), cargando = ref(true), opcion = ref(null), enviando = ref(false);
    const porcentaje = computed(() => estado.value ? Math.round((estado.value.numero - 1) * 100 / estado.value.total) : 0);
    const esUltima = computed(() => estado.value && estado.value.numero === estado.value.total);

    async function iniciar() {
      cargando.value = true; error.value = ""; opcion.value = null;
      try { estado.value = await api("/api/diagnostico/iniciar", { method: "POST" }); }
      catch (e) { error.value = e.message; }
      cargando.value = false;
    }
    async function responder() {
      if (opcion.value === null || !estado.value) return;
      enviando.value = true;
      try {
        const nuevo = await api("/api/diagnostico/responder", { method: "POST",
          body: { idTest: estado.value.idTest, idPregunta: estado.value.pregunta.idPregunta, idOpcion: parseInt(opcion.value, 10) } });
        if (nuevo.finalizado) {
          sesion.progreso = sesion.progreso || { porcentajeCurso: 0, erroresCorregidos: 0 };
          sesion.progreso.diagnostico = { idTest: nuevo.idTest, aciertos: nuevo.aciertos, total: nuevo.total, nivel: nuevo.nivel };
          diagnostico.resultado = nuevo;
          router.push("/resultado");
        } else { estado.value = nuevo; opcion.value = null; }
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    onMounted(iniciar);
    return { estado, error, cargando, opcion, enviando, porcentaje, esUltima, iniciar, responder };
  }
};
</script>
