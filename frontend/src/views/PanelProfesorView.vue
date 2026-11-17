<template>
  <div>
    <nav-docente />
    <main class="pagina">
      <div class="encabezado-pagina"><div><h1 style="font-size:1.9rem">Panel de progreso</h1>
        <p><template v-if="datos">Así va tu grupo en {{ datos.curso }}.</template><template v-else-if="cargado">Todavía no hay cursos.</template></p></div></div>
      <estado-vacio v-if="cargado && !datos" titulo="Crea tu primer curso para ver el progreso">Cuando haya un curso con estudiantes, aquí verás su avance y los errores más comunes.
        <template #acciones><router-link to="/cursos/nuevo" class="btn btn-primario">Crear curso</router-link></template></estado-vacio>
      <template v-if="datos">
        <div class="mini-tarjetas">
          <div class="mini-tarjeta"><span>Estudiantes activos</span><strong>{{ datos.estudiantesActivos }}</strong></div>
          <div class="mini-tarjeta"><span>Promedio de progreso</span><strong>{{ datos.promedioProgreso }}%</strong></div>
          <div class="mini-tarjeta"><span>Errores detectados</span><strong>{{ datos.erroresDetectados }}</strong></div>
        </div>
        <div class="dos-columnas">
          <div class="tarjeta"><h3>Progreso por estudiante</h3>
            <p v-if="datos.estudiantes.length === 0" class="texto-suave mb-0">Aún no hay estudiantes con actividad. Aparecen cuando hacen el diagnóstico o validan código.</p>
            <div v-for="e in datos.estudiantes" :key="e.nombre" class="fila-estudiante"><span>{{ e.nombre }}</span>
              <div class="progreso"><i :style="{ width: e.progreso + '%' }"></i></div><span>{{ e.progreso }}%</span></div></div>
          <div class="tarjeta"><h3>Errores más cometidos</h3>
            <p v-if="datos.topErrores.length === 0" class="texto-suave mb-0">Aún no hay errores registrados.</p>
            <div v-for="e in datos.topErrores" :key="e.nombre" class="error-top"><div><span>{{ e.nombre }}</span><span>{{ e.porcentaje }}% ({{ e.cantidad }})</span></div>
              <div class="progreso progreso-roja"><i :style="{ width: e.porcentaje + '%' }"></i></div></div></div>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
// VISTA · Panel de progreso del grupo (ruta /panel) → GET /api/cursos y GET /api/profesor/progreso/<id>
import { ref, onMounted } from "vue";
import { api } from "../services/api.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

export default {
  name: "PanelProfesorView",
  components: { NavDocente, EstadoVacio },
  setup() {
    const datos = ref(null), cargado = ref(false);
    onMounted(async () => {
      try {
        const cursos = (await api("/api/cursos")).cursos;
        if (cursos.length > 0) datos.value = await api("/api/profesor/progreso/" + cursos[0].id);
      } catch (e) { avisar(e.message, "error"); }
      cargado.value = true;
    });
    return { datos, cargado };
  }
};
</script>
