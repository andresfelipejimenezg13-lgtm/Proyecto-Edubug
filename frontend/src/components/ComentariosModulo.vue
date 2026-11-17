<template>
  <section class="comentarios" aria-labelledby="tituloComentarios">
    <h3 id="tituloComentarios">Dudas y comentarios ({{ total }})</h3>
    <form class="mb-3" @submit.prevent="publicar">
      <div class="campo">
        <label for="comentarioTexto">¿Qué dudas te quedaron o qué le sumarías a este módulo?</label>
        <textarea id="comentarioTexto" v-model="texto" rows="3" maxlength="1000" placeholder="Escribe tu comentario"></textarea>
      </div>
      <button type="submit" class="btn btn-primario" :disabled="enviando || texto.trim() === ''">Publicar comentario</button>
    </form>
    <p v-if="cargando" class="cargando">Cargando comentarios...</p>
    <p v-else-if="error" class="texto-suave">{{ error }}</p>
    <p v-else-if="lista.length === 0" class="texto-suave">Todavía no hay comentarios. Sé la primera persona en escribir.</p>
    <article v-for="c in lista" :key="c.id" class="comentario">
      <div class="comentario-cab">
        <span class="avatar" aria-hidden="true">{{ (c.autor || "?").charAt(0).toUpperCase() }}</span>
        <strong>{{ c.autor }}</strong>
        <small>{{ cuando(c.fecha) }}</small>
      </div>
      <p>{{ c.texto }}</p>
      <div class="reacciones">
        <button v-for="r in REACCIONES" :key="r.tipo" type="button" class="reaccion" @click="reaccionar(c, r.tipo)">
          {{ r.texto }} {{ c.reacciones[r.tipo] || 0 }}
        </button>
        <button v-if="puedeBorrar(c)" type="button" class="reaccion" @click="borrar(c)">Eliminar</button>
      </div>
    </article>
  </section>
</template>

<script>
// COMPONENTE · Comentarios de un módulo (se guardan en MongoDB).
// GET/POST /api/modulos/<id>/comentarios · POST /api/comentarios/<id>/reacciones · DELETE /api/comentarios/<id>
import { ref, watch } from "vue";
import { api } from "../services/api.js";
import { sesion } from "../store/sesion.js";
import { avisar } from "../store/toast.js";

const REACCIONES = [{ tipo: "util", texto: "Me sirvió" }, { tipo: "gracias", texto: "Gracias" }, { tipo: "confuso", texto: "Me confundió" }];

export default {
  name: "ComentariosModulo",
  props: { idModulo: { type: Number, required: true } },
  setup(props) {
    const lista = ref([]), total = ref(0), texto = ref(""), error = ref("");
    const cargando = ref(true), enviando = ref(false);

    async function cargar() {
      cargando.value = true; error.value = "";
      try {
        const d = await api("/api/modulos/" + props.idModulo + "/comentarios");
        lista.value = d.comentarios; total.value = d.total;
      } catch (e) { error.value = "Los comentarios no están disponibles ahora mismo."; }
      cargando.value = false;
    }
    async function publicar() {
      enviando.value = true;
      try {
        await api("/api/modulos/" + props.idModulo + "/comentarios", { method: "POST", body: { texto: texto.value.trim() } });
        texto.value = "";
        avisar("Comentario publicado");
        await cargar();
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    async function reaccionar(c, tipo) {
      try {
        const nuevo = await api("/api/comentarios/" + c.id + "/reacciones", { method: "POST", body: { tipo } });
        c.reacciones = nuevo.reacciones;
      } catch (e) { avisar(e.message, "error"); }
    }
    async function borrar(c) {
      if (!confirm("¿Eliminar este comentario?")) return;
      try { await api("/api/comentarios/" + c.id, { method: "DELETE" }); avisar("Comentario eliminado"); await cargar(); }
      catch (e) { avisar(e.message, "error"); }
    }
    const puedeBorrar = (c) => c.idUsuario === sesion.id || sesion.esDocente;
    const cuando = (f) => new Date(f).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });

    watch(() => props.idModulo, cargar, { immediate: true });
    return { lista, total, texto, error, cargando, enviando, REACCIONES, publicar, reaccionar, borrar, puedeBorrar, cuando };
  }
};
</script>
