# GerminaFlix CI/CD Implementation Plan

> **Para agentes que executarem o plano:** use a subskill superpowers:subagent-driven-development (recomendada) ou superpowers:executing-plans e acompanhe as etapas com as caixas de seleção.

**Objetivo.** Validar o catálogo em PRs e pushes para a `main` e publicar no GitHub Pages os arquivos aprovados em um push na `main`.

**Arquitetura.** O job `ci` prepara uma pasta temporária, testa o validador e valida os arquivos dessa pasta. Em um push na `main`, após a validação, `ci` envia a pasta como artefato e `deploy` publica esse artefato da mesma execução.

**Tecnologias.** Python 3.11 com biblioteca padrão e `unittest`, GitHub Actions em `ubuntu-latest` e GitHub Pages com GitHub Actions como fonte.

**Especificação.** [spec.md](spec.md)

## Restrições

- Um workflow com dois jobs, `ci` e `deploy`. Os gatilhos são `pull_request` com destino à `main` e `push` na `main`. O deploy depende de `ci` e só é elegível no segundo evento.
- A pasta publicada inclui `index.html`, `autor.html`, `logo.html`, os CSS, as imagens e `filmes/filme1.html` e `filmes/filme2.html`. `filmes/filme3.html` a `filmes/filme10.html` ficam fora do artefato.
- Todo `href` e `src` local dos HTML publicados deve resolver, com a grafia exata, para um arquivo da pasta publicada sob `/germinaFlix/`. URLs externas ficam fora da checagem.
- Homem-Aranha e Mufasa são os cards ativos. A CI compara os nomes dos filmes aos títulos de destino, desconsiderando o ano e os selos. Os outros oito cards exibem “Em breve” sem link.
- Registre a falha em push na `main` e a primeira falha do PR antes de corrigir o HTML. Preserve as regras do repositório. Se elas impedirem o push inicial com o workflow e os links originais, registre o impedimento antes de prosseguir.

## Arquivos e interfaces

| Arquivo | Responsabilidade |
|---|---|
| `scripts/validate_catalog.py` | Preparar a pasta e emitir o diagnóstico das referências locais e dos cards. |
| `tests/test_validate_catalog.py` | Exercitar a preparação e as validações com pastas temporárias. |
| `.github/workflows/ci-cd.yml` | Disparar a CI, enviar o artefato aprovado e publicá-lo. |
| `index.html`, `style.css` | Corrigir os destinos e exibir o estado dos cards pendentes. |
| `autor.html`, `filmes/filme1.html`, `filmes/filme2.html` | Corrigir referências locais que falham sob o prefixo do Pages. |
| `entrega-ci-cd.pdf` | Reunir as evidências e o diário em um único PDF, na pasta de entrega fora do repositório. |

- `prepare_site(source: Path, destination: Path) -> None` recebe um destino novo, copia os arquivos públicos preservando os caminhos e falha se uma origem obrigatória estiver ausente.
- `validate_links(site: Path, base_path: str) -> list[str]` retorna os problemas encontrados nos HTML da pasta preparada, identificando o HTML e a referência original.
- `validate_catalog(site: Path, base_path: str) -> list[str]` verifica os dez cards pelos IDs `filme1` a `filme10` e retorna os problemas encontrados, incluindo o título esperado e o encontrado em caso de divergência.
- A interface de linha de comando é `python -m scripts.validate_catalog --source . --output <pasta-nova> --base-path /germinaFlix/`. Ela prepara a pasta, lista os arquivos preparados e executa as validações disponíveis. Retorna `0` se tudo passar e `1` se houver erro. O workflow usa o mesmo caminho em `--output` e no envio do artefato.

## Pontos de revisão

- Um arquivo presente no repositório e excluído do pacote deve ser tratado como ausente na validação. Teste em T01.
- Uma imagem cujo nome contém espaços e parênteses deve resolver com espaços literais e com codificação de URL. Teste em T01.
- Um caminho com query ou fragmento deve resolver para o mesmo arquivo. Links externos e `mailto:` não devem gerar requisições. Teste em T01.
- Um caminho absoluto como `/img/logo.png` deve falhar mesmo quando o arquivo existe no pacote. Teste em T01.
- Um card pendente com link ou um card ativo que abre o filme errado deve falhar mesmo quando o destino existe. Teste em T03.

## Ordem de implementação e evidências

Execute [tasks.md](tasks.md) em ordem. Guarde desde a primeira tarefa os prompts, as respostas e o que foi aceito, corrigido ou feito manualmente.

| Momento | O que a execução deve mostrar |
|---|---|
| T02 · primeiro push na `main` | CI falha no link “Início” de `filmes/filme1.html` e deploy fica `skipped`. |
| T03 · primeira execução do PR para a `main` | O mesmo link continua quebrado. Capture o log da falha e o deploy `skipped` antes de editar os HTML. |
| T04 · novo commit no mesmo PR | CI passa com os links e cards corrigidos. O deploy fica `skipped`. |
| T05 · push do merge na `main` | CI passa, envia o artefato e libera o deploy. O Pages mostra o SHA ativo e o catálogo correspondente está acessível. |

Registre para cada execução o link, o evento, a branch e o SHA. Mantenha separadas as duas execuções com falha. A falha do PR comprova que a validação também roda no PR. O push com falha na `main` comprova o bloqueio do deploy quando o evento permitiria publicar. Em T06, reúna essas evidências e o diário de uso da IA no PDF.

O workflow segue o mecanismo de artefatos do Pages e a dependência entre jobs do GitHub Actions. [Publicação via workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) · [Dependências entre jobs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idneeds) · [Configuração do Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
