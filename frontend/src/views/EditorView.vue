<template>
  <div>
    <app-barra />
    <main class="pagina">
      <div class="encabezado-pagina">
        <div><h1 style="font-size:1.9rem">Editor de práctica</h1><p>Escribe HTML, pulsa Validar y mira qué errores encontramos.</p></div>
        <button type="button" class="btn btn-borde btn-chico" @click="usarEjemplo">Cargar un ejemplo con errores</button>
      </div>
      <div class="editor">
        <section class="editor-codigo" aria-label="Tu código">
          <div class="codigo-barra"><span>mi-pagina.html</span><span>{{ numeros.length }} líneas</span></div>
          <div class="editor-zona">
            <pre class="editor-numeros" aria-hidden="true">{{ numeros.join("\n") }}</pre>
            <textarea id="codigoHtml" v-model="codigo" class="editor-texto" spellcheck="false" aria-label="Código HTML" placeholder="Escribe tu código HTML aquí" @keydown.tab.prevent="tabular"></textarea>
          </div>
          <div class="editor-pie">
            <button type="button" class="btn btn-menta" :disabled="validando || codigo.trim() === ''" @click="validar">{{ validando ? "Validando..." : "Validar código" }}</button>
            <button type="button" class="btn btn-borde btn-chico" style="color:#DCE8F7;border-color:#27487C" @click="codigo = ''" :disabled="codigo === ''">Limpiar</button>
            <small>Tab inserta dos espacios</small>
          </div>
        </section>
        <section class="editor-resultado" aria-live="polite" aria-label="Resultado">
          <div v-if="!datos" class="vacio-editor"><div><div class="icono estado-vacio" style="border:0;padding:0" aria-hidden="true"><span class="icono">✓</span></div><h4>Listo para revisar</h4><p class="mb-0">Escribe tu código y pulsa <strong>Validar código</strong>.<br>Si no sabes por dónde empezar, abre un <router-link to="/catalogo">módulo</router-link>.</p></div></div>
          <template v-else>
            <div v-if="datos.erroresDetectados.length === 0" class="exito">
              <h4>Código correcto</h4>
              <p class="mb-0">No encontramos ninguno de los errores que buscamos. Llevas {{ datos.progreso.porcentajeCurso }}% del curso.</p>
            </div>
            <template v-else>
              <h3>{{ datos.erroresDetectados.length }} {{ datos.erroresDetectados.length === 1 ? "error encontrado" : "errores encontrados" }}</h3>
              <div v-for="(e, i) in datos.erroresDetectados" :key="i" class="hallazgo">
                <h4>{{ e.titulo }} <span class="etiqueta etiqueta-coral">línea {{ e.linea }}</span></h4>
                <p>{{ e.explicacionIA }}</p>
                <p><strong>Cómo solucionarlo:</strong> {{ e.solucion }}</p>
                <pre class="mal">{{ e.ejemploIncorrecto }}</pre>
                <pre class="bien">{{ e.ejemploCorrecto }}</pre>
              </div>
            </template>
            <recomendacion-caja v-if="datos.recomendacion" :recomendacion="datos.recomendacion" titulo="Te recomendamos repasar" />
          </template>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Editor de práctica (ruta /editor) → POST /api/depurador/analizar
// Si vienes de "Probar en el editor" en un módulo, el código ya aparece escrito.
import { ref, computed } from "vue";
import { api } from "../services/api.js";
import { sesion } from "../store/sesion.js";
import { borrador } from "../store/editor.js";
import { avisar } from "../store/toast.js";
import AppBarra from "../components/AppBarra.vue";
import RecomendacionCaja from "../components/RecomendacionCaja.vue";

const EJEMPLO = '<h1>Mi página\n<P>Hola mundo</P>\n<img src=gato.jpg alt="Un gato">';

export default {
  name: "EditorView",
  components: { AppBarra, RecomendacionCaja },
  setup() {
    const codigo = ref(borrador.codigo);
    borrador.codigo = "";
    const datos = ref(null), validando = ref(false);
    const numeros = computed(() => Array.from({ length: Math.max(codigo.value.split("\n").length, 12) }, (_, i) => i + 1));

    function tabular(e) {
      const t = e.target, ini = t.selectionStart;
      codigo.value = codigo.value.slice(0, ini) + "  " + codigo.value.slice(t.selectionEnd);
      requestAnimationFrame(() => { t.selectionStart = t.selectionEnd = ini + 2; });
    }
    function usarEjemplo() { codigo.value = EJEMPLO; datos.value = null; }
    async function validar() {
      validando.value = true;
      try {
        const r = await api("/api/depurador/analizar", { method: "POST", body: { codigoHtml: codigo.value } });
        sesion.progreso = r.progreso;
        datos.value = r;
      } catch (e) { avisar(e.message, "error"); }
      validando.value = false;
    }
    return { codigo, datos, validando, numeros, tabular, usarEjemplo, validar };
  }
};
</script>
