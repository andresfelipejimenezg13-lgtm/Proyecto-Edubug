<template>
  <div>
    <div class="heroe">
      <div class="heroe-interior">
        <div>
          <div class="barra-interior"><logo-edudebug /></div>
          <h1>Aprende HTML corrigiendo tus propios errores</h1>
          <p class="lead">Escribe código, descubre qué falló y entiende cómo arreglarlo. Sin esperar a que alguien lo revise.</p>
          <div class="heroe-botones">
            <router-link to="/registro" class="btn btn-menta">Crear cuenta gratis</router-link>
            <router-link to="/login" class="btn btn-borde">Ya tengo cuenta</router-link>
          </div>
          <p class="heroe-pie">¿Quieres verlo antes? <a href="#" @click.prevent="entrarComoDemo">Entra con una cuenta de prueba</a></p>
        </div>
        <div class="maqueta" aria-label="Ejemplo del editor con un error marcado">
          <div class="maqueta-barra"><i></i><i></i><i></i><span>mi-pagina.html</span></div>
          <div class="maqueta-codigo">
            <div><b>1</b><span>&lt;h1&gt;Mi primera página&lt;/h1&gt;</span></div>
            <div><b>2</b><span>&lt;img src=<span class="error-ondulado">gato.jpg</span> alt="Un gato"&gt;</span></div>
            <div><b>3</b><span>&lt;p&gt;Hola mundo&lt;/p&gt;</span></div>
          </div>
          <div class="maqueta-aviso"><span><strong>Línea 2:</strong> el valor de <code>src</code> va entre comillas. Escríbelo así: <code>src="gato.jpg"</code></span></div>
        </div>
      </div>
    </div>

    <section class="seccion">
      <h2>Cómo es aprender aquí</h2>
      <div class="pasos">
        <div class="paso"><h3>Haz un test corto</h3><p>Cinco preguntas que se adaptan a tus respuestas para saber desde dónde empezar.</p></div>
        <div class="paso"><h3>Lee un módulo</h3><p>Ocho módulos con ejemplos cortos. Cada ejemplo lo puedes copiar o probar en el editor.</p></div>
        <div class="paso"><h3>Practica y corrige</h3><p>El editor encuentra errores en tu código y te explica cómo solucionarlos.</p></div>
        <div class="paso"><h3>Repasa lo que falla</h3><p>Si repites un error, te recomendamos el módulo exacto para repasarlo.</p></div>
      </div>
    </section>

    <section class="seccion">
      <h2>Los errores que te ayudamos a encontrar</h2>
      <div class="errores-lista">
        <div class="error-ejemplo"><h4>Etiqueta sin cerrar</h4><p class="texto-suave mb-0">El navegador no sabe dónde termina el elemento.</p><pre>&lt;p&gt;Hola mundo</pre></div>
        <div class="error-ejemplo"><h4>Atributo sin comillas</h4><p class="texto-suave mb-0">Se rompe en cuanto el valor tiene un espacio.</p><pre>&lt;img src=gato.jpg&gt;</pre></div>
        <div class="error-ejemplo"><h4>Etiqueta en mayúsculas</h4><p class="texto-suave mb-0">Funciona, pero la buena práctica es usar minúsculas.</p><pre>&lt;P&gt;Hola&lt;/P&gt;</pre></div>
      </div>
    </section>

    <section class="cierre">
      <div>
        <h2>Empieza con el primer módulo hoy</h2>
        <router-link to="/registro" class="btn btn-primario">Crear cuenta gratis</router-link>
      </div>
    </section>
    <footer class="pie">EDUDEBUG · Plataforma para aprender HTML · Proyecto académico de Nuevas Tecnologías e Interfaces de Usuario</footer>
  </div>
</template>

<script>
// VISTA · Inicio (ruta /). Presenta la plataforma; "cuenta de prueba" entra con el estudiante demo.
import { useRouter } from "vue-router";
import { api } from "../services/api.js";
import { sesion, rutaSegun } from "../store/sesion.js";
import { avisar } from "../store/toast.js";
import LogoEdudebug from "../components/LogoEdudebug.vue";

export default {
  name: "InicioView",
  components: { LogoEdudebug },
  setup() {
    const router = useRouter();
    async function entrarComoDemo() {
      try {
        const datos = await api("/api/auth/login", { method: "POST", body: { email: "estudiante@edudebug.com", password: "123456" } });
        sesion.iniciar(datos);
        router.push(rutaSegun(datos.siguiente));
      } catch (e) { avisar("No se pudo abrir la demostración: " + e.message, "error"); }
    }
    return { entrarComoDemo };
  }
};
</script>
