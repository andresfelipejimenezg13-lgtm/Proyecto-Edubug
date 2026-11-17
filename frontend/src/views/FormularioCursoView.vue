<template>
  <div>
    <nav-docente />
    <main class="pagina pagina-angosta">
      <h1 style="font-size:1.9rem">{{ id ? "Editar curso" : "Crear curso" }}</h1>
      <p class="texto-suave">Completa la información del curso.</p>
      <form class="tarjeta" @submit.prevent="guardar">
        <div class="campo"><label for="cursoNombre">Nombre del curso</label><input type="text" id="cursoNombre" v-model="curso.nombre" class="entrada" placeholder="Ej: HTML Básico" required></div>
        <div class="campo"><label for="cursoDescripcion">Descripción</label><textarea id="cursoDescripcion" v-model="curso.descripcion" rows="3" placeholder="Qué se aprende en este curso" required></textarea></div>
        <div class="fila-campos">
          <div class="campo"><label for="cursoNivel">Nivel</label><select id="cursoNivel" v-model="curso.nivel"><option>Inicial</option><option>Intermedio</option><option>Avanzado</option></select></div>
          <div class="campo"><label for="cursoEstado">Estado</label><select id="cursoEstado" v-model="curso.estado"><option>Activo</option><option>Inactivo</option></select>
            <p class="ayuda">Un curso inactivo aparece como «Próximamente».</p></div>
        </div>
        <div style="display:flex;gap:.7rem">
          <button type="submit" class="btn btn-primario" :disabled="enviando">Guardar curso</button>
          <router-link to="/cursos" class="btn btn-borde">Cancelar</router-link>
        </div>
      </form>
    </main>
  </div>
</template>

<script>
// VISTA · Crear / editar curso (rutas /cursos/nuevo y /cursos/:id/editar)
// POST /api/cursos (crear) o PUT /api/cursos/<id> (editar).
import { reactive, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";

export default {
  name: "FormularioCursoView",
  components: { NavDocente },
  setup() {
    const route = useRoute(), router = useRouter();
    const id = route.params.id || null;
    const curso = reactive({ nombre: "", descripcion: "", nivel: "Inicial", estado: "Activo" });
    const enviando = ref(false);
    onMounted(async () => {
      if (!id) return;
      try { Object.assign(curso, await api("/api/cursos/" + id)); }
      catch (e) { avisar(e.message, "error"); router.replace("/cursos"); }
    });
    async function guardar() {
      const cuerpo = { nombre: curso.nombre.trim(), descripcion: curso.descripcion.trim(), nivel: curso.nivel, estado: curso.estado };
      if (cuerpo.nombre === "" || cuerpo.descripcion === "") { avisar("Completa el nombre y la descripción del curso.", "error"); return; }
      enviando.value = true;
      try {
        if (id) await api("/api/cursos/" + id, { method: "PUT", body: cuerpo });
        else await api("/api/cursos", { method: "POST", body: cuerpo });
        avisar("Curso guardado");
        router.push("/cursos");
      } catch (e) { avisar(e.message, "error"); }
      enviando.value = false;
    }
    return { id, curso, enviando, guardar };
  }
};
</script>
