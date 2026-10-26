// O app desktop abre esta página com o token no fragmento da URL (#token=...)
const TOKEN = new URLSearchParams(location.hash.slice(1)).get("token") || "";

const $ = (id) => document.getElementById(id);
let objetoAtual = null;

async function api(caminho, opcoes = {}) {
  const resposta = await fetch(caminho, {
    ...opcoes,
    headers: { "Content-Type": "application/json", "X-Token": TOKEN, ...(opcoes.headers || {}) },
  });
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    const detalhe = Array.isArray(corpo.detail) ? corpo.detail.map((d) => d.msg).join("; ") : corpo.detail;
    throw new Error(detalhe || `Erro ${resposta.status}`);
  }
  return resposta.status === 204 ? null : resposta.json();
}

function mostrarMensagem(texto, tipo = "") {
  $("mensagem").textContent = texto;
  $("mensagem").className = `mensagem ${tipo}`;
}

async function atualizarStatus() {
  try {
    const saude = await api("/saude");
    $("status-provedor").textContent = `IA: ${saude.provedor}`;
    $("status-provedor").className = "selo ok";
    $("status-sketchup").textContent = saude.sketchup_conectado ? "SketchUp conectado" : "SketchUp desconectado";
    $("status-sketchup").className = `selo ${saude.sketchup_conectado ? "ok" : ""}`;
  } catch {
    $("status-provedor").textContent = "servidor fora do ar";
    $("status-provedor").className = "selo erro";
  }
}

function lerImagem(arquivo) {
  return new Promise((resolver, rejeitar) => {
    const leitor = new FileReader();
    leitor.onload = () => resolver({ mime_type: arquivo.type, dados_base64: leitor.result.split(",")[1] });
    leitor.onerror = rejeitar;
    leitor.readAsDataURL(arquivo);
  });
}

$("imagens").addEventListener("change", () => {
  $("miniaturas").replaceChildren(
    ...[...$("imagens").files].slice(0, 4).map((arquivo) => {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(arquivo);
      img.alt = arquivo.name;
      return img;
    })
  );
});

// Desenha as peças como retângulos numa vista ortogonal; eixoH/eixoV escolhem o plano
function desenharVista(svg, objeto, eixoH, eixoV, invertido) {
  const dims = { x: "comprimento_x", y: "largura_y", z: "altura_z" };
  const totalH = objeto.dimensoes_totais[dims[eixoH]];
  const totalV = objeto.dimensoes_totais[dims[eixoV]];
  const margem = 12;
  const escala = Math.min((300 - 2 * margem) / totalH, (200 - 2 * margem) / totalV);
  const offH = (300 - totalH * escala) / 2;
  const offV = (200 - totalV * escala) / 2;

  svg.replaceChildren(
    ...objeto.pecas.map((peca) => {
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      const w = peca.dimensoes[dims[eixoH]] * escala;
      const h = peca.dimensoes[dims[eixoV]] * escala;
      const pH = peca.posicao_relativa[eixoH] * escala;
      const pV = peca.posicao_relativa[eixoV] * escala;
      rect.setAttribute("x", offH + pH);
      // Na vista frontal o Z cresce para cima, ao contrário do SVG
      rect.setAttribute("y", invertido ? 200 - offV - pV - h : offV + pV);
      rect.setAttribute("width", w);
      rect.setAttribute("height", h);
      const titulo = document.createElementNS("http://www.w3.org/2000/svg", "title");
      titulo.textContent = peca.nome_peca;
      rect.appendChild(titulo);
      return rect;
    })
  );
}

function mostrarPrevia(objeto) {
  objetoAtual = objeto;
  $("vazio").hidden = true;
  $("previa").hidden = false;
  $("nome-objeto").textContent = objeto.nome_objeto;
  desenharVista($("vista-frontal"), objeto, "x", "z", true);
  desenharVista($("vista-superior"), objeto, "x", "y", false);

  const fmt = (n) => Number(n.toFixed(1)).toLocaleString("pt-BR");
  $("tabela-pecas").replaceChildren(
    ...objeto.pecas.map((p) => {
      const linha = document.createElement("tr");
      const d = p.dimensoes, o = p.posicao_relativa;
      [p.nome_peca, `${fmt(d.comprimento_x)} × ${fmt(d.largura_y)} × ${fmt(d.altura_z)}`, `${fmt(o.x)}, ${fmt(o.y)}, ${fmt(o.z)}`]
        .forEach((texto) => {
          const celula = document.createElement("td");
          celula.textContent = texto;
          linha.appendChild(celula);
        });
      return linha;
    })
  );
}

$("formulario").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  $("botao-gerar").disabled = true;
  mostrarMensagem("Gerando…");
  try {
    const imagens = await Promise.all([...$("imagens").files].slice(0, 4).map(lerImagem));
    const objeto = await api("/v1/gerar", {
      method: "POST",
      body: JSON.stringify({
        prompt_usuario: $("prompt").value.trim(),
        imagens,
        dimensoes_limite: {
          comprimento_x: Number($("dim-x").value),
          largura_y: Number($("dim-y").value),
          altura_z: Number($("dim-z").value),
        },
      }),
    });
    mostrarPrevia(objeto);
    mostrarMensagem(`${objeto.pecas.length} peças geradas.`, "ok");
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  } finally {
    $("botao-gerar").disabled = false;
  }
});

$("botao-enviar").addEventListener("click", async () => {
  if (!objetoAtual) return;
  try {
    await api("/v1/fila", { method: "POST", body: JSON.stringify(objetoAtual) });
    const saude = await api("/saude");
    mostrarMensagem(
      saude.sketchup_conectado
        ? "Enviado. O SketchUp vai desenhar em instantes."
        : "Na fila. Abra o SketchUp e use Extensões › SketchUp AI Assistant › Conectar ao app.",
      "ok"
    );
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  }
});

atualizarStatus();
setInterval(atualizarStatus, 3000);
