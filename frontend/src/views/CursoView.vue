<template>
  <div>
    <app-barra />
    <main class="pagina pagina-angosta">
      <nav class="migas" aria-label="Ruta"><router-link to="/catalogo">Cursos</router-link><span>/</span><span>{{ curso ? curso.nombre : "..." }}</span></nav>
      <p v-if="cargando" class="cargando">Cargando curso...</p>
      <template v-else-if="curso">
        <div class="encabezado-pagina">
          <div><h1 style="font-size:1.9rem">{{ curso.nombre }}</h1><p>{{ curso.descripcion }}</p></div>
          <router-link v-if="curso.modulos.length" :to="'/curso/' + curso.id + '/modulo/' + curso.modulos[0].orden" class="btn btn-menta">Empezar el curso</router-link>
        </div>
        <estado-vacio v-if="curso.modulos.length === 0" titulo="Este curso todavía no tiene módulos">Vuelve pronto: tu profesor los está preparando.</estado-vacio>
        <ol v-else class="lista-modulos">
          <li v-for="m in curso.modulos" :key="m.id">
            <router-link :to="'/curso/' + curso.id + '/modulo/' + m.orden" class="modulo-fila">
              <span class="modulo-num">{{ m.orden }}</span>
              <span><strong>{{ m.titulo }}</strong><small>{{ minutos(m) }} min de lectura</small></span>
              <span class="flecha" aria-hidden="true">›</span>
            </router-link>
          </li>
        </ol>
      </template>
    </main>
  </div>
</template>

<script>
// VISTA · Un curso con la lista de sus módulos (ruta /curso/:id) → GET /api/cursos/<id>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import AppBarra from "../components/AppBarra.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

export default {
  name: "CursoView",
  components: { AppBarra, EstadoVacio },
  setup() {
    const route = useRoute(), router = useRouter();
    const curso = ref(null), cargando = ref(true);
    const minutos = (m) => Math.max(1, Math.round((m.contenido || "").split(/\s+/).length / 180));
    onMounted(async () => {
      try { curso.value = await api("/api/cursos/" + route.params.id); }
      catch (e) { avisar(e.message, "error"); router.replace("/catalogo"); }
      cargando.value = false;
    });
    return { curso, cargando, minutos };
  }
};
</script>
