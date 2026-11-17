<template>
  <div class="estado-vacio">
    <div class="icono" aria-hidden="true">{{ icono }}</div>
    <h4>{{ titulo }}</h4>
    <p><slot /></p>
    <slot name="acciones" />
  </div>
</template>

<script>
// COMPONENTE · Pantalla vacía con una acción sugerida (en vez de dejar un hueco).
export default { name: "EstadoVacio", props: { titulo: { type: String, required: true }, icono: { type: String, default: "{ }" } } };
</script>
