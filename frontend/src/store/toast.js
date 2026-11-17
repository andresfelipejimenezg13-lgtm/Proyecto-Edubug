// ESTADO · Avisos breves en pantalla (reemplazan a alert). Uso: avisar("Guardado") o avisar(e.message, "error").
import { reactive } from "vue";

export const avisos = reactive([]);
let contador = 0;

export function avisar(mensaje, tipo = "ok") {
  const id = ++contador;
  avisos.push({ id, mensaje, tipo });
  setTimeout(() => {
    const i = avisos.findIndex((a) => a.id === id);
    if (i >= 0) avisos.splice(i, 1);
  }, 4500);
}
