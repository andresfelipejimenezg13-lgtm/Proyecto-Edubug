<template>
  <div class="sugerencia">
    <strong>{{ titulo }}</strong>
    <p class="mb-0 mt-1">Por tus errores repetidos ({{ causas }}):</p>
    <ul>
      <li v-for="(m, i) in recomendacion.modulosSugeridos" :key="i">
        <router-link v-if="m.idModulo && m.idCurso" :to="'/curso/' + m.idCurso + '/modulo/' + m.orden">{{ m.curso }} · {{ m.modulo }}</router-link>
        <template v-else>{{ m.curso }} · {{ m.modulo }}</template>
      </li>
    </ul>
  </div>
</template>

<script>
// COMPONENTE · "Te recomendamos repasar" (editor y perfil). Cada módulo es un enlace si la API da su id.
import { computed } from "vue";

const NOMBRES_ERROR = { etiqueta_sin_cerrar: "Etiqueta sin cerrar", atributo_sin_comillas: "Atributo sin comillas", etiqueta_en_mayusculas: "Etiqueta en mayúsculas",
  sin_html: "No hay etiquetas HTML", etiqueta_desconocida: "Etiqueta que no existe", atributo_faltante: "Atributo obligatorio ausente", etiqueta_incompleta: "Etiqueta sin terminar" };

export default {
  name: "RecomendacionCaja",
  props: { recomendacion: { type: Object, required: true }, titulo: { type: String, required: true } },
  setup(props) {
    return { causas: computed(() => props.recomendacion.basadoEnErrores.map((t) => NOMBRES_ERROR[t] || t).join(", ")) };
  }
};
</script>
