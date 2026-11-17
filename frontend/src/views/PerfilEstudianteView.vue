<template>
  <div>
    <app-barra />
    <main class="pagina pagina-angosta">
      <perfil-cabecera tipo="Estudiante" />
      <div class="mini-tarjetas">
        <div class="mini-tarjeta"><span>Diagnóstico</span><strong>{{ puntaje }}</strong></div>
        <div class="mini-tarjeta"><span>Avance del curso</span><strong>{{ avance }}%</strong></div>
        <div class="mini-tarjeta"><span>Errores corregidos</span><strong>{{ errores }}</strong></div>
      </div>
      <div class="tarjeta mb-2"><h3>Recomendado para ti</h3>
        <recomendacion-caja v-if="recomendacion" :recomendacion="recomendacion" titulo="Repasa estos módulos" />
        <estado-vacio v-else titulo="Aún no hay recomendaciones" icono="✓">Aparecen cuando repites el mismo tipo de error en el editor.
          <template #acciones><router-link to="/editor" class="btn btn-borde btn-chico">Ir al editor</router-link></template></estado-vacio>
      </div>
      <div class="tarjeta mb-2"><h3>Actividad reciente</h3>
        <ul v-if="actividad.length" class="linea-tiempo"><li v-for="(a, i) in actividad" :key="i">{{ NOMBRES_ACTIVIDAD[a.tipo] || a.tipo }}<small>{{ cuando(a.fecha) }}</small></li></ul>
        <p v-else class="texto-suave mb-0">{{ textoActividad }}</p>
      </div>
      <div class="encabezado-pagina" style="margin-top:1.5rem"><span></span>
        <button class="btn btn-peligro" @click="cerrarSesion">Cerrar sesión</button></div>
    </main>
  </div>
</template>

<script>
// VISTA · Perfil del estudiante (ruta /perfil)
// GET /api/recomendaciones/<id> y GET /api/usuarios/<id>/perfil-completo (actividad desde MongoDB).
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api.js";
import { sesion, capitalizar } from "../store/sesion.js";
import AppBarra from "../components/AppBarra.vue";
import PerfilCabecera from "../components/PerfilCabecera.vue";
import RecomendacionCaja from "../components/RecomendacionCaja.vue";
import EstadoVacio from "../components/EstadoVacio.vue";

const NOMBRES_ACTIVIDAD = {
  registro: "Creaste tu cuenta", login: "Iniciaste sesión", curso_consultado: "Consultaste un curso",
  tema_visto: "Viste un tema", diagnostico_iniciado: "Iniciaste el diagnóstico",
  diagnostico_respuesta: "Respondiste una pregunta", diagnostico_finalizado: "Terminaste el diagnóstico",
  codigo_analizado: "Analizaste código HTML", comentario_creado: "Comentaste un módulo"
};

export default {
  name: "PerfilEstudianteView",
  components: { AppBarra, PerfilCabecera, RecomendacionCaja, EstadoVacio },
  setup() {
    const router = useRouter();
    const recomendacion = ref(null), actividad = ref([]), textoActividad = ref("Cargando...");
    const puntaje = computed(() => {
      const d = sesion.progreso && sesion.progreso.diagnostico;
      return d ? d.aciertos + "/" + d.total + " · " + capitalizar(d.nivel) : "Sin hacer";
    });
    const avance = computed(() => sesion.progreso ? sesion.progreso.porcentajeCurso : 0);
    const errores = computed(() => sesion.progreso ? sesion.progreso.erroresCorregidos : 0);
    const cuando = (f) => new Date(f).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
    onMounted(async () => {
      try { const d = await api("/api/recomendaciones/" + sesion.id); if (d.modulosSugeridos.length) recomendacion.value = d; } catch (e) { /* sin recomendación */ }
      try {
        const d = await api("/api/usuarios/" + sesion.id + "/perfil-completo");
        if (!d.actividad.disponible) textoActividad.value = "El historial no está disponible en este momento.";
        else if (!d.actividad.ultimas.length) textoActividad.value = "Todavía no tienes actividad registrada.";
        else actividad.value = d.actividad.ultimas;
      } catch (e) { textoActividad.value = e.message; }
    });
    return { recomendacion, actividad, textoActividad, puntaje, avance, errores, cuando, NOMBRES_ACTIVIDAD,
             cerrarSesion: () => { sesion.cerrar(); router.push("/"); } };
  }
};
</script>
