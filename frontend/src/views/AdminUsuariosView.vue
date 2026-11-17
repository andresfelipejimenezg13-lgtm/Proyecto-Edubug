<template>
  <div>
    <nav-docente />
    <main class="pagina pagina-angosta">
      <h1 style="font-size:1.9rem">Usuarios y roles</h1>
      <p class="texto-suave">Crea cuentas de profesor o administrador y cambia el rol de las existentes.</p>
      <form class="tarjeta mb-3" @submit.prevent="crear">
        <h3>Crear cuenta</h3>
        <div class="fila-campos">
          <div class="campo"><label for="uNombre">Nombre</label><input id="uNombre" type="text" v-model="nuevo.nombre" class="entrada" required></div>
          <div class="campo"><label for="uCorreo">Correo</label><input id="uCorreo" type="email" v-model="nuevo.email" class="entrada" required></div>
          <div class="campo"><label for="uPass">Contraseña</label><input id="uPass" type="password" v-model="nuevo.password" class="entrada" minlength="8" required></div>
          <div class="campo"><label for="uRol">Rol</label><select id="uRol" v-model="nuevo.rol"><option value="profesor">Profesor</option><option value="admin">Administrador</option><option value="estudiante">Estudiante</option></select></div>
        </div>
        <p class="ayuda texto-suave">Contraseña: mínimo 8 caracteres, con letras y números.</p>
        <button type="submit" class="btn btn-primario">Crear cuenta</button>
      </form>
      <div v-for="u in usuarios" :key="u.id" class="tabla-fila">
        <div><h4>{{ u.nombre }}{{ u.id === sesion.id ? " (tú)" : "" }}</h4><p class="mb-0">{{ u.email }}</p></div>
        <div class="acciones">
          <select v-model="roles[u.id]" :disabled="u.id === sesion.id" :aria-label="'Rol de ' + u.nombre" class="entrada" style="width:auto">
            <option v-for="(texto, rol) in NOMBRES_ROL" :key="rol" :value="rol">{{ texto }}</option></select>
          <button class="btn btn-borde btn-chico" :disabled="u.id === sesion.id" @click="cambiarRol(u)">Guardar rol</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
// VISTA · Usuarios y roles, solo admin (ruta /usuarios) → GET/POST /api/admin/usuarios, PUT /api/admin/usuarios/<id>/rol
import { reactive, ref, onMounted } from "vue";
import { api } from "../services/api.js";
import { sesion, contrasenaValida } from "../store/sesion.js";
import { avisar } from "../store/toast.js";
import NavDocente from "../components/NavDocente.vue";

const NOMBRES_ROL = { estudiante: "Estudiante", profesor: "Profesor", admin: "Administrador" };

export default {
  name: "AdminUsuariosView",
  components: { NavDocente },
  setup() {
    const usuarios = ref([]), roles = reactive({});
    const nuevo = reactive({ nombre: "", email: "", password: "", rol: "profesor" });
    async function cargar() {
      try { usuarios.value = (await api("/api/admin/usuarios")).usuarios; usuarios.value.forEach((u) => { roles[u.id] = u.rol; }); }
      catch (e) { avisar(e.message, "error"); }
    }
    async function cambiarRol(u) {
      try { await api("/api/admin/usuarios/" + u.id + "/rol", { method: "PUT", body: { rol: roles[u.id] } }); avisar("Rol actualizado"); await cargar(); }
      catch (e) { avisar(e.message, "error"); }
    }
    async function crear() {
      const cuerpo = { nombre: nuevo.nombre.trim(), email: nuevo.email.trim().toLowerCase(), password: nuevo.password, rol: nuevo.rol };
      if (!contrasenaValida(cuerpo.password)) { avisar("La contraseña debe tener mínimo 8 caracteres, con letras y números.", "error"); return; }
      try {
        await api("/api/admin/usuarios", { method: "POST", body: cuerpo });
        Object.assign(nuevo, { nombre: "", email: "", password: "", rol: "profesor" });
        avisar("Cuenta creada"); await cargar();
      } catch (e) { avisar(e.message, "error"); }
    }
    onMounted(cargar);
    return { sesion, usuarios, roles, nuevo, NOMBRES_ROL, cambiarRol, crear };
  }
};
</script>
