<template>
  <div>
    <nav-docente />
    <main class="pagina pagina-angosta">
      <nav class="migas" aria-label="Ruta"><router-link to="/cursos">Cursos</router-link><span>/</span><span>{{ curso ? curso.nombre : "..." }}</span></nav>
      <p v-if="cargando" class="cargando">Cargando módulos...</p>
      <template v-else-if="curso">
        <div class="encabezado-pagina">
          <div><h1 style="font-size:1.9rem">Módulos de {{ curso.nombre }}</h1><p>Agrega, edita o elimina el contenido que ven los estudiantes.</p></div>
          <router-link :to="'/cursos/' + curso.id + '/modulos/nuevo'" class="btn btn-primario">Agregar módulo</router-link>
        </div>
        <estado-vacio v-if="curso.modulos.length === 0" titulo="Este curso todavía no tiene módulos">Agrega el primero para que los estudiantes puedan empezar.
          <template #acciones><router-link :to="'/cursos/' + curso.id + '/modulos/nuevo'" class="btn btn-primario">Agregar módulo</router-link></template></estado-vacio>
        <div v-for="m in curso.modulos" :key="m.id" class="tabla-fila">
          <div><h4>{{ m.orden }}. {{ m.titulo }}</h4><p class="mb-0">{{ resumen(m) }}</p></div>
          <div class="acciones">
            <router-link :to="'/cursos/' + curso.id + '/modulos/' + m.id + '/editar'" class="btn btn-borde btn-chico">Editar</router-link>
            <button class="btn btn-peligro btn-chico" @click="eliminar(m)">Eliminar</button>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
// VISTA · Módulos de un curso, para el profesor (ruta /cursos/:id/modulos)
// GET /api/cursos/<id> y DELETE /api/modulos/<id>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

export default {
  name: "ModulosCursoView",
  components: { NavDocente, EstadoVacio },
  setup() {
    const route = useRoute(), router = useRouter();
    const curso = ref(null), cargando = ref(true);
    const resumen = (m) => { const t = (m.contenido || "").replace(/```[\s\S]*?```/g, " ").replace(/[#>\-]/g, "").replace(/\s+/g, " ").trim(); return t.length > 110 ? t.slice(0, 110) + "…" : (t || "Sin contenido todavía."); };
    async function cargar() {
      try { curso.value = await api("/api/cursos/" + route.params.id); }
      catch (e) { avisar(e.message, "error"); router.replace("/cursos"); return; }
      cargando.value = false;
    }
    async function eliminar(m) {
      if (!confirm("¿Eliminar el módulo «" + m.titulo + "»? No se puede deshacer.")) return;
      try { await api("/api/modulos/" + m.id, { method: "DELETE" }); avisar("Módulo eliminado"); await cargar(); }
      catch (e) { avisar(e.message, "error"); }
    }
    onMounted(cargar);
    return { curso, cargando, resumen, eliminar };
  }
};
</script>
