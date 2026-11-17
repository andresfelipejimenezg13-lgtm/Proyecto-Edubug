<template>
  <div>
    <app-barra />
    <main class="pagina">
      <nav class="migas" aria-label="Ruta">
        <router-link to="/catalogo">Cursos</router-link><span>/</span>
        <router-link :to="'/curso/' + $route.params.id">{{ curso ? curso.nombre : "Curso" }}</router-link>
      </nav>
      <p v-if="cargando" class="cargando">Cargando módulo...</p>
      <div v-else-if="modulo" class="lectura">
        <aside class="lectura-indice" aria-label="Módulos del curso">
          <h4>Módulos</h4>
          <router-link v-for="m in curso.modulos" :key="m.id" :to="'/curso/' + curso.id + '/modulo/' + m.orden"><span>{{ m.orden }}</span>{{ m.titulo }}</router-link>
        </aside>
        <article class="articulo">
          <p class="texto-suave mb-0" style="font-weight:700">Módulo {{ modulo.orden }} de {{ curso.modulos.length }}</p>
          <h1>{{ modulo.titulo }}</h1>
          <contenido-modulo :contenido="modulo.contenido" probar @probar="probar" />
          <div class="articulo-pie">
            <router-link v-if="anterior" :to="'/curso/' + curso.id + '/modulo/' + anterior.orden" class="btn btn-borde">‹ {{ anterior.titulo }}</router-link><span v-else></span>
            <router-link v-if="siguiente" :to="'/curso/' + curso.id + '/modulo/' + siguiente.orden" class="btn btn-primario">Siguiente: {{ siguiente.titulo }} ›</router-link>
            <router-link v-else to="/editor" class="btn btn-menta">Terminar y practicar en el editor</router-link>
          </div>
          <comentarios-modulo :id-modulo="modulo.id" />
        </article>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Lectura de un módulo (ruta /curso/:id/modulo/:orden) → GET /api/cursos/<id> + comentarios de MongoDB.
import { ref, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import { borrador } from "../store/editor.js";
import AppBarra from "../components/AppBarra.vue";
import ContenidoModulo from "../components/ContenidoModulo.vue";
import ComentariosModulo from "../components/ComentariosModulo.vue";

export default {
  name: "ModuloView",
  components: { AppBarra, ContenidoModulo, ComentariosModulo },
  setup() {
    const route = useRoute(), router = useRouter();
    const curso = ref(null), cargando = ref(true);
    const modulo = computed(() => curso.value && curso.value.modulos.find((m) => m.orden === Number(route.params.orden)));
    const posicion = computed(() => curso.value && modulo.value ? curso.value.modulos.indexOf(modulo.value) : -1);
    const anterior = computed(() => posicion.value > 0 ? curso.value.modulos[posicion.value - 1] : null);
    const siguiente = computed(() => posicion.value >= 0 ? curso.value.modulos[posicion.value + 1] || null : null);

    async function cargar() {
      if (curso.value && String(curso.value.id) === String(route.params.id)) { cargando.value = false; return; }
      cargando.value = true;
      try { curso.value = await api("/api/cursos/" + route.params.id); }
      catch (e) { avisar(e.message, "error"); router.replace("/catalogo"); return; }
      cargando.value = false;
    }
    watch(() => route.params.id, cargar, { immediate: true });
    watch(modulo, (m) => {
      if (curso.value && !m && !cargando.value) router.replace("/curso/" + curso.value.id);
      else window.scrollTo({ top: 0 });
    });
    function probar(codigo) { borrador.codigo = codigo; router.push("/editor"); }
    return { curso, cargando, modulo, anterior, siguiente, probar };
  }
};
</script>
