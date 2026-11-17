// UTILIDAD · Convierte el texto de un módulo (el que guarda la base de datos) en bloques para mostrar.
// Formato: párrafos separados por línea en blanco · "## " subtítulo · "- " lista · "> " consejo · ```html ... ``` código
// · ![descripción](https://...) imagen · @video https://... video (YouTube o .mp4).
// Enlaces de YouTube se convierten a su versión "embed"; un enlace directo a .mp4 se reproduce tal cual.
function videoEmbed(url) {
  const y = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/);
  return y ? { embed: "https://www.youtube.com/embed/" + y[1] } : { directo: url };
}

export function bloquesDe(contenido) {
  const bloques = [];
  const lineas = (contenido || "").replace(/\r/g, "").split("\n");
  let i = 0;
  while (i < lineas.length) {
    const l = lineas[i];
    if (l.trim() === "") { i++; continue; }
    if (l.startsWith("```")) {
      const codigo = [];
      const lenguaje = l.slice(3).trim().toLowerCase() || "html";
      i++;
      while (i < lineas.length && !lineas[i].startsWith("```")) codigo.push(lineas[i++]);
      i++;
      bloques.push({ tipo: "codigo", lenguaje, lineas: codigo });
    } else if (/^!\[[^\]]*\]\((?:https?:\/\/|\/)[^)\s]+\)\s*$/.test(l)) {
      const m = l.match(/^!\[([^\]]*)\]\(([^)\s]+)\)/);
      bloques.push({ tipo: "imagen", alt: m[1], url: m[2] }); i++;
    } else if (/^@video https?:\/\/\S+\s*$/.test(l)) {
      bloques.push({ tipo: "video", url: videoEmbed(l.slice(7).trim()) }); i++;
    } else if (l.startsWith("## ")) {
      bloques.push({ tipo: "subtitulo", texto: l.slice(3) }); i++;
    } else if (l.startsWith("- ")) {
      const items = [];
      while (i < lineas.length && lineas[i].startsWith("- ")) items.push(lineas[i++].slice(2));
      bloques.push({ tipo: "lista", items });
    } else if (l.startsWith("> ")) {
      const partes = [];
      while (i < lineas.length && lineas[i].startsWith("> ")) partes.push(lineas[i++].slice(2));
      bloques.push({ tipo: "consejo", texto: partes.join(" ") });
    } else {
      const partes = [];
      while (i < lineas.length && lineas[i].trim() !== "" && !/^(```|## |- |> )/.test(lineas[i])) partes.push(lineas[i++]);
      bloques.push({ tipo: "parrafo", texto: partes.join(" ") });
    }
  }
  return bloques;
}

// Etiquetas como <p> dentro del texto se muestran como código en línea (sin interpretarlas como HTML).
export function partesDeTexto(texto) {
  return texto.split(/(<\/?[a-zA-Z!][^>]*>)/g).filter((t) => t !== "").map((t) => ({ codigo: /^<\/?[a-zA-Z!]/.test(t), texto: t }));
}
