<template>
  <div>
    <app-barra />
    <main class="pagina">
      <div class="encabezado-pagina">
        <div><h1 style="font-size:1.9rem">Hola, {{ primerNombre }}</h1><p>Elige un curso y sigue practicando.</p></div>
      </div>
      <p v-if="cargando" class="cargando">Cargando cursos...</p>
      <estado-vacio v-else-if="cursos.length === 0" titulo="Todavía no hay cursos">Cuando tu profesor publique un curso, lo verás aquí.</estado-vacio>
      <div v-else class="cuadricula">
        <article v-for="c in cursos" :key="c.id" class="curso-tarjeta" :class="{ 'curso-proximo': !c.disponible }">
          <div class="datos-fila">
            <span class="etiqueta" :class="c.disponible ? 'etiqueta-verde' : 'etiqueta-gris'">{{ c.disponible ? "Disponible" : "Próximamente" }}</span>
            <span>{{ c.nivel }}</span><span v-if="c.disponible">· {{ modulos(c) }}</span>
          </div>
          <h3>{{ c.nombre }}</h3>
          <p>{{ c.descripcion }}</p>
          <template v-if="c.disponible">
            <template v-if="c.id === cursos[0].id">
              <div class="progreso" aria-hidden="true"><i :style="{ width: porcentaje + '%' }"></i></div>
              <small class="texto-suave">{{ porcentaje }}% completado · tu nivel: {{ nivel }}</small>
            </template>
            <div class="acciones">
              <router-link :to="'/curso/' + c.id" class="btn btn-primario">Ver módulos</router-link>
              <router-link v-if="c.id === cursos[0].id" to="/editor" class="btn btn-borde">Practicar en el editor</router-link>
            </div>
          </template>
        </article>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Catálogo de cursos (ruta /catalogo) → GET /api/cursos
import { ref, computed, onMounted } from "vue";
import { api } from "../services/api.js";
import { sesion, capitalizar } from "../store/sesion.js";
import { avisar } from "../store/toast.js";
import AppBarra from "../components/AppBarra.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

export default {
  name: "CatalogoView",
  components: { AppBarra, EstadoVacio },
  setup() {
    const cursos = ref([]), cargando = ref(true);
    const porcentaje = computed(() => sesion.progreso ? sesion.progreso.porcentajeCurso : 0);
    const nivel = computed(() => sesion.progreso && sesion.progreso.diagnostico ? capitalizar(sesion.progreso.diagnostico.nivel) : "sin evaluar");
    const primerNombre = computed(() => sesion.nombre.split(" ")[0]);
    const modulos = (c) => c.totalModulos + (c.totalModulos === 1 ? " módulo" : " módulos");
    onMounted(async () => {
      try { cursos.value = (await api("/api/cursos")).cursos; } catch (e) { avisar(e.message, "error"); }
      cargando.value = false;
    });
    return { cursos, cargando, porcentaje, nivel, primerNombre, modulos };
  }
};
</script>
