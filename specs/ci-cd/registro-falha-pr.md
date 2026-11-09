# Registro da primeira falha da CI no PR

Reproduzi localmente os 18 erros do log do PR a partir do commit `a5ac00d`. A preparação do pacote terminou e o validador retornou código `1` ao conferir as referências dos HTML preparados.

## Causa confirmada

Usei `new URL(referencia, urlDoHtml)` com a origem `https://erickneves07.github.io` e o prefixo `/germinaFlix/` para reproduzir a resolução de URL do navegador. Sem uma barra inicial, o endereço é relativo à pasta do HTML. Uma barra inicial leva à raiz do domínio. [Padrão WHATWG de URLs](https://url.spec.whatwg.org/#url-parsing) · [API URL usada no teste](https://nodejs.org/api/url.html#new-urlinput-base)

| HTML de origem | Referência original | Caminho resolvido | Correção |
|---|---|---|---|
| `autor.html` | `img\n    /logo.png` | `/germinaFlix/img%20%20%20%20/logo.png` | `img/logo.png` |
| `filmes/filme1.html` | `index.html` e `logo.html` | `/germinaFlix/filmes/index.html` e `/germinaFlix/filmes/logo.html` | `../index.html` e `../logo.html` |
| `filmes/filme2.html` | `/index.html` e `/img/mufasa-icon.png` | `/index.html` e `/img/mufasa-icon.png`, fora do prefixo | `../index.html` e `../img/mufasa-icon.png`. A mesma regra vale para as demais imagens. |
| `index.html` | `filmes/filme7.html` | `/germinaFlix/filmes/filme7.html`, página excluída do pacote | Removido o link do card de Warcraft. |

Numa cópia do pacote, corrigi só o link “Início” de `filmes/filme1.html`. A lista caiu de 18 para 17 erros e a única mensagem removida foi a de `filmes/index.html`.

## Arquivos alterados

- `autor.html`, `filmes/filme1.html` e `filmes/filme2.html` receberam as correções de caminhos da tabela.
- `index.html` agora liga Mufasa à sua própria página. Os oito cards de filmes sem página publicada, incluindo Warcraft, exibem “Em breve” sem link.
- `style.css` posiciona o marcador sobre as capas e mostra o cursor de link apenas nos cards ativos.

## Resultado da validação local

```powershell
$site = Join-Path $env:TEMP ("germinaflix-" + [guid]::NewGuid())
python scripts/validate_site.py --source . --output $site --base-path /germinaFlix/
$LASTEXITCODE
```

O mesmo comando retornou código `1` e 18 erros antes das correções. Depois, retornou código `0` e a mensagem `Home e referências locais validadas.` A suíte do validador passou com 5 testes. A inspeção do catálogo confirmou os dois destinos ativos e os oito cards “Em breve” sem link. A próxima execução no PR fica pendente do push das correções.
