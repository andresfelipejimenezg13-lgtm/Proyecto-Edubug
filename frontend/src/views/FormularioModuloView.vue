<template>
  <div>
    <nav-docente />
    <main class="pagina">
      <nav class="migas" aria-label="Ruta"><router-link to="/cursos">Cursos</router-link><span>/</span>
        <router-link :to="'/cursos/' + $route.params.id + '/modulos'">Módulos</router-link><span>/</span><span>{{ idModulo ? "Editar" : "Nuevo" }}</span></nav>
      <h1 style="font-size:1.9rem">{{ idModulo ? "Editar módulo" : "Agregar módulo" }}</h1>
      <form class="editor-modulo" @submit.prevent="guardar">
        <section class="tarjeta">
          <div class="fila-campos">
            <div class="campo" style="grid-column: span 2"><label for="modTitulo">Título</label><input id="modTitulo" v-model="modulo.titulo" class="entrada" maxlength="150" required></div>
            <div class="campo"><label for="modOrden">Posición</label><input id="modOrden" type="number" min="1" v-model="modulo.orden" class="entrada" placeholder="Al final">
              <p class="ayuda">Déjalo vacío para agregarlo al final.</p></div>
          </div>
          <div class="campo"><label for="modContenido">Contenido</label>
            <div class="herramientas" role="toolbar" aria-label="Insertar formato">
              <button v-for="h in HERRAMIENTAS" :key="h.nombre" type="button" class="btn btn-borde btn-chico" @click="insertar(h.texto)">{{ h.nombre }}</button>
            </div>
            <textarea id="modContenido" ref="area" v-model="modulo.contenido" rows="18" class="area-contenido" spellcheck="true" placeholder="Escribe aquí. Separa los párrafos con una línea en blanco."></textarea>
            <p class="ayuda">Los botones agregan un ejemplo del formato en el lugar del cursor. Mira la vista previa para ver cómo queda.</p></div>
          <div style="display:flex;gap:.7rem;flex-wrap:wrap">
            <button type="submit" class="btn btn-primario" :disabled="enviando">Guardar módulo</button>
            <router-link :to="'/cursos/' + $route.params.id + '/modulos'" class="btn btn-borde">Cancelar</router-link>
          </div>
        </section>
        <section class="tarjeta" aria-label="Vista previa">
          <h3>Vista previa</h3>
          <div class="articulo"><h1 style="font-size:1.6rem">{{ modulo.titulo || "Título del módulo" }}</h1>
            <contenido-modulo v-if="modulo.contenido.trim()" :contenido="modulo.contenido" />
            <p v-else class="texto-suave">Aquí verás el contenido a medida que lo escribas.</p></div>
        </section>
      </form>
    </main>
  </div>
</template>

<script>
// VISTA · Crear / editar un módulo (rutas /cursos/:id/modulos/nuevo y /cursos/:id/modulos/:idModulo/editar)
// POST /api/cursos/<id>/modulos (crear) o PUT /api/modulos/<id> (editar).
import { reactive, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";
import ContenidoModulo from "../components/ContenidoModulo.vue";

const HERRAMIENTAS = [
  { nombre: "Subtítulo", texto: "\n\n## Subtítulo\n" },
  { nombre: "Lista", texto: "\n\n- Primer punto\n- Segundo punto\n" },
  { nombre: "Consejo", texto: "\n\n> Un consejo útil para quien lee.\n" },
  { nombre: "Código", texto: "\n\n```html\n<p>Escribe tu ejemplo aquí</p>\n```\n" },
  { nombre: "Imagen", texto: "\n\n![Descripción de la imagen](https://dirección-de-la-imagen.png)\n" },
  { nombre: "Video", texto: "\n\n@video https://www.youtube.com/watch?v=CÓDIGO\n" }
];

export default {
  name: "FormularioModuloView",
  components: { NavDocente, ContenidoModulo },
  setup() {
    const route = useRoute(), router = useRouter();
    const idCurso = route.params.id, idModulo = route.params.idModulo || null;
    const modulo = reactive({ titulo: "", contenido: "", orden: "" });
    const enviando = ref(false), area = ref(null);

    onMounted(async () => {
      if (!idModulo) return;
      try {
        const curso = await api("/api/cursos/" + idCurso);
        const m = curso.modulos.find((x) => String(x.id) === String(idModulo));
        if (!m) throw new Error("No encontramos ese módulo.");
        Object.assign(modulo, { titulo: m.titulo, contenido: m.contenido || "", orden: m.orden });
      } catch (e) { avisar(e.message, "error"); router.replace("/cursos/" + idCurso + "/modulos"); }
    });

    function insertar(texto) {
      const t = area.value, ini = t ? t.selectionStart : modulo.contenido.length, fin = t ? t.selectionEnd : ini;
      modulo.contenido = modulo.contenido.slice(0, ini) + texto + modulo.contenido.slice(fin);
      if (t) { t.focus(); requestAnimationFrame(() => { t.selectionStart = t.selectionEnd = ini + texto.length; }); }
    }
    async function guardar() {
      const cuerpo = { titulo: modulo.titulo.trim(), contenido: modulo.contenido };
      if (modulo.orden !== "" && modulo.orden !== null) cuerpo.orden = Number(modulo.orden);
      if (cuerpo.titulo === "") { avisar("Escribe el título del módulo.", "error"); return; }
      enviando.value = true;
      try {
        if (idModulo) await api("/api/modulos/" + idModulo, { method: "PUT", body: cuerpo });
        else await api("/api/cursos/" + idCurso + "/modulos", { method: "POST", body: cuerpo });
        avisar("Módulo guardado");
        router.push("/cursos/" + idCurso + "/modulos");
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    return { idModulo, modulo, enviando, area, HERRAMIENTAS, insertar, guardar };
  }
};
</script>
