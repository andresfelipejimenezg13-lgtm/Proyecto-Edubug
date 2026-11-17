<template>
  <div class="acceso">
    <aside class="acceso-lateral">
      <logo-edudebug />
      <div>
        <h2>Cada error que corriges, lo aprendes.</h2>
        <p>Escribe HTML, encuentra tus fallos y entiende cómo arreglarlos, sin esperar a nadie.</p>
      </div>
      <div class="maqueta" aria-hidden="true">
        <div class="maqueta-barra"><i></i><i></i><i></i><span>pagina.html</span></div>
        <div class="maqueta-codigo">
          <div><b>1</b><span>&lt;h1&gt;Hola</span></div>
          <div><b>2</b><span>&lt;p&gt;Mi página&lt;/p&gt;</span></div>
        </div>
        <div class="maqueta-aviso"><span><strong>Línea 1:</strong> falta cerrar &lt;h1&gt; con &lt;/h1&gt;</span></div>
      </div>
    </aside>
    <main class="acceso-principal"><div class="acceso-formulario"><slot /></div></main>
  </div>
</template>

<script>
// COMPONENTE · Estructura de las pantallas de acceso (login y registro): panel de marca + formulario.
import LogoEdudebug from "./LogoEdudebug.vue";
export default { name: "AuthLayout", components: { LogoEdudebug } };
</script>
