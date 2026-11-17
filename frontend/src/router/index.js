// RUTAS · Cada pantalla tiene su dirección (ej. /#/login). Aquí se ve todo el flujo de la Vista.
// Los "guards" protegen las pantallas por rol; el backend vuelve a validar el rol en cada /api.
import { createRouter, createWebHashHistory } from "vue-router";
import { sesion } from "../store/sesion.js";

import InicioView from "../views/InicioView.vue";
import LoginView from "../views/LoginView.vue";
import RegistroView from "../views/RegistroView.vue";
import DiagnosticoView from "../views/DiagnosticoView.vue";
import ResultadoView from "../views/ResultadoView.vue";
import CatalogoView from "../views/CatalogoView.vue";
import CursoView from "../views/CursoView.vue";
import ModuloView from "../views/ModuloView.vue";
import EditorView from "../views/EditorView.vue";
import PerfilEstudianteView from "../views/PerfilEstudianteView.vue";
import PanelProfesorView from "../views/PanelProfesorView.vue";
import GestionCursosView from "../views/GestionCursosView.vue";
import FormularioCursoView from "../views/FormularioCursoView.vue";
import ModulosCursoView from "../views/ModulosCursoView.vue";
import FormularioModuloView from "../views/FormularioModuloView.vue";
import AdminUsuariosView from "../views/AdminUsuariosView.vue";
import PerfilProfesorView from "../views/PerfilProfesorView.vue";

// acceso: "publica" | "estudiante" (cualquier sesión) | "docente" (profesor o admin) | "admin"
const rutas = [
  { path: "/",             name: "inicio",       component: InicioView,           meta: { acceso: "publica" } },
  { path: "/bienvenida",   redirect: "/" },
  { path: "/login",        name: "login",        component: LoginView,            meta: { acceso: "publica" } },
  { path: "/registro",     name: "registro",     component: RegistroView,         meta: { acceso: "publica" } },

  { path: "/diagnostico",  name: "diagnostico",  component: DiagnosticoView,      meta: { acceso: "estudiante" } },
  { path: "/resultado",    name: "resultado",    component: ResultadoView,        meta: { acceso: "estudiante" } },
  { path: "/teoria",       redirect: "/catalogo" },
  { path: "/curso/:id",    name: "curso",        component: CursoView,            meta: { acceso: "estudiante" } },
  { path: "/curso/:id/modulo/:orden", name: "modulo", component: ModuloView,       meta: { acceso: "estudiante" } },
  { path: "/catalogo",     name: "catalogo",     component: CatalogoView,         meta: { acceso: "estudiante" } },
  { path: "/editor",       name: "editor",       component: EditorView,           meta: { acceso: "estudiante" } },
  { path: "/perfil",       name: "perfil",       component: PerfilEstudianteView, meta: { acceso: "estudiante" } },

  { path: "/panel",        name: "panel",        component: PanelProfesorView,    meta: { acceso: "docente" } },
  { path: "/cursos",       name: "cursos",       component: GestionCursosView,    meta: { acceso: "docente" } },
  { path: "/cursos/nuevo", name: "curso-nuevo",  component: FormularioCursoView,  meta: { acceso: "docente" } },
  { path: "/cursos/:id/editar", name: "curso-editar", component: FormularioCursoView, meta: { acceso: "docente" } },
  { path: "/cursos/:id/modulos", name: "modulos-curso", component: ModulosCursoView, meta: { acceso: "docente" } },
  { path: "/cursos/:id/modulos/nuevo", name: "modulo-nuevo", component: FormularioModuloView, meta: { acceso: "docente" } },
  { path: "/cursos/:id/modulos/:idModulo/editar", name: "modulo-editar", component: FormularioModuloView, meta: { acceso: "docente" } },
  { path: "/perfil-docente", name: "perfil-docente", component: PerfilProfesorView, meta: { acceso: "docente" } },

  { path: "/usuarios",     name: "usuarios",     component: AdminUsuariosView,    meta: { acceso: "admin" } },

  { path: "/:resto(.*)*",  redirect: "/" }
];

export const router = createRouter({ history: createWebHashHistory(), routes: rutas });

router.beforeEach((destino) => {
  const acceso = destino.meta.acceso;
  if (acceso === "publica") return true;
  if (!sesion.activa) return "/login";
  if (acceso === "admin" && !sesion.esAdmin) return "/panel";
  if (acceso === "docente" && !sesion.esDocente) return "/catalogo";
  if (acceso === "estudiante" && sesion.esDocente) return "/panel";
  return true;
});
