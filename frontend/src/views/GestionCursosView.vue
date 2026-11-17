<template>
  <div>
    <nav-docente />
    <main class="pagina pagina-angosta">
      <div class="encabezado-pagina"><div><h1 style="font-size:1.9rem">Gestión de cursos</h1><p>Administra los cursos de la plataforma.</p></div>
        <router-link to="/cursos/nuevo" class="btn btn-primario">Crear curso</router-link></div>
      <estado-vacio v-if="cargado && cursos.length === 0" titulo="Todavía no hay cursos">Crea el primero con el botón «Crear curso».</estado-vacio>
      <div v-for="c in cursos" :key="c.id" class="tabla-fila">
        <div><h4>{{ c.nombre }}</h4><p>{{ c.descripcion }}</p>
          <span class="etiqueta" :class="c.estado === 'Activo' ? 'etiqueta-verde' : 'etiqueta-gris'">{{ c.estado }}</span>
          <small class="texto-suave"> {{ c.nivel }} · {{ modulos(c) }}</small></div>
        <div class="acciones">
          <router-link :to="'/cursos/' + c.id + '/modulos'" class="btn btn-borde btn-chico">Módulos</router-link>
          <router-link :to="'/cursos/' + c.id + '/editar'" class="btn btn-borde btn-chico">Editar</router-link>
          <button class="btn btn-peligro btn-chico" @click="eliminar(c)">Eliminar</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Gestión de cursos (ruta /cursos) → GET/DELETE /api/cursos
import { ref, onMounted } from "vue";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

export default {
  name: "GestionCursosView",
  components: { NavDocente, EstadoVacio },
  setup() {
    const cursos = ref([]), cargado = ref(false);
    const modulos = (c) => c.totalModulos + (c.totalModulos === 1 ? " módulo" : " módulos");
    async function cargar() {
      try { cursos.value = (await api("/api/cursos")).cursos; } catch (e) { avisar(e.message, "error"); }
      cargado.value = true;
    }
    async function eliminar(c) {
      if (!confirm("¿Seguro que quieres eliminar «" + c.nombre + "»? También se eliminarán sus módulos.")) return;
      try { await api("/api/cursos/" + c.id, { method: "DELETE" }); avisar("Curso eliminado"); await cargar(); }
      catch (e) { avisar(e.message, "error"); }
    }
    onMounted(cargar);
    return { cursos, cargado, modulos, eliminar };
  }
};
</script>
