# Tarefas de implementação e verificação

Siga a ordem abaixo. Os números de aceite apontam para [spec.md](spec.md) e os contratos das funções estão em [plan.md](plan.md).

## T01 · Preparar o pacote e validar caminhos em Python

**Aceite.** 3 e 4. **Arquivos.** Criar `scripts/validate_catalog.py` e `tests/test_validate_catalog.py`.

**Interfaces.** Implementar `prepare_site(source: Path, destination: Path) -> None`, `validate_links(site: Path, base_path: str) -> list[str]` e a interface de linha de comando definida no plano.

- [ ] Escreva `test_prepare_site_only_copies_public_files` com uma origem temporária que contenha todos os arquivos públicos e também `filmes/filme7.html`. Verifique `assert (site / "filmes/filme2.html").is_file()` e `assert not (site / "filmes/filme7.html").exists()`. Em `test_prepare_site_requires_listed_files`, remova `logo.html` da origem e verifique `with self.assertRaises(FileNotFoundError): prepare_site(source, site)`.
- [ ] Escreva `test_resolves_relative_and_encoded_asset_urls` com um HTML em `filmes/` que referencie `../img/mulheranha (1).png`, `../img/mulheranha%20%281%29.png` e `../index.html?origem=filme#catalogo`, além de `#titulo`, `https://example.invalid/` e `mailto:teste@example.invalid`. Com os arquivos locais presentes, verifique `assert validate_links(site, "/germinaFlix/") == []`.
- [ ] Escreva `test_reports_missing_wrong_case_and_outside_prefix` com `filmes/filme7.html` presente apenas na origem e as referências `filme7.html`, `../img/Logo.png` e `/img/logo.png` em `filmes/filme1.html`. Com `img/logo.png` presente no pacote, verifique que a lista contém três problemas, cada qual com `filmes/filme1.html` e a respectiva referência literal.
- [ ] Rode `python -m unittest discover -s tests -p test_validate_catalog.py -v` e confirme que a suíte acusa a ausência das funções antes da implementação.
- [ ] Implemente `prepare_site` copiando `index.html`, `autor.html`, `logo.html`, `style.css`, `logo.css`, `filmes/filme.css`, `filmes/filme1.html`, `filmes/filme2.html` e os recursos de imagem em `img/`. Preserve caminhos e grafia. O destino precisa ser novo para que arquivos de uma execução anterior não entrem no pacote.
- [ ] Implemente `validate_links` com `html.parser.HTMLParser` e `urllib.parse`. Percorra os HTML do pacote, resolva os caminhos relativos a cada página, remova query e fragmento da busca por arquivos e decodifique o caminho antes de conferir se ele permanece no prefixo. Compare com o conjunto de caminhos do pacote, respeitando a capitalização inclusive no Windows. Trate referências à própria página como locais e ignore URLs externas sem acessá-las.
- [ ] Implemente a interface de linha de comando. Imprima os caminhos relativos da pasta preparada e todos os erros encontrados, incluindo o caminho de origem. Conclua com código `1` se a preparação ou a validação falhar.
- [ ] Rode novamente a suíte e confirme `OK`. Rode também o comando abaixo no PowerShell. No HTML original, espere código `1` e um diagnóstico de `filmes/filme1.html` com a referência `index.html`. Confira que `filmes/filme7.html` não aparece na lista de arquivos preparados.

```powershell
$site = Join-Path ([System.IO.Path]::GetTempPath()) ('germinaflix-' + [guid]::NewGuid())
python -m scripts.validate_catalog --source . --output $site --base-path /germinaFlix/
$LASTEXITCODE
```

- [ ] Faça commit de `scripts/validate_catalog.py` e `tests/test_validate_catalog.py` com a mensagem `ci: prepare and validate the Pages site`.

## T02 · Configurar os dois jobs e registrar o push com falha

**Aceite.** 1, 2, 3 e 6. **Arquivos.** Criar `.github/workflows/ci-cd.yml`. Configurar também a fonte do Pages no GitHub.

**Interfaces.** O workflow executa a suíte e a interface de linha de comando de T01. O job `ci` fornece o artefato `github-pages` ao job `deploy` na mesma execução.

- [ ] Configure `push.branches` e `pull_request.branches` com `main`. Defina somente `ci` e `deploy`, ambos em `ubuntu-latest`.
- [ ] No job `ci`, use `actions/checkout@v6` e `actions/setup-python@v6` com `python-version: '3.11'`. Execute a suíte de T01 e depois `python -m scripts.validate_catalog --source . --output "$SITE_DIR" --base-path /germinaFlix/`. Defina `SITE_DIR` como `${{ runner.temp }}/germinaflix-site` no job. A biblioteca padrão dispensa instalação via pip.
- [ ] Após a validação, use `actions/upload-pages-artifact@v4` com `path` apontando para `SITE_DIR` e `name: github-pages`. Execute esse passo apenas com sucesso em `github.event_name == 'push' && github.ref == 'refs/heads/main'`.
- [ ] Configure `deploy` com `needs: ci` e `if: success() && github.event_name == 'push' && github.ref == 'refs/heads/main'`. Use `contents: read` como permissão padrão e conceda `pages: write` e `id-token: write` ao deploy. Configure o ambiente `github-pages` e use `actions/deploy-pages@v4` com `id: deployment`, `artifact_name: github-pages` e a URL do ambiente em `${{ steps.deployment.outputs.page_url }}`.
- [ ] Em **Settings → Pages**, selecione **GitHub Actions** como fonte e confira se o ambiente pode publicar a partir da `main`.
- [ ] Confira o diff, faça commit de `.github/workflows/ci-cd.yml` com a mensagem `ci: gate Pages deployment on validation` e leve o workflow e o validador para a `main` pela via permitida no repositório. Preserve os HTML originais nesse primeiro push.
- [ ] No GitHub Actions, capture o primeiro `push` na `main` com o workflow. O checkout, o setup do Python e a suíte devem passar. O validador deve registrar o erro em `filmes/filme1.html` com `index.html`, a CI deve falhar e o upload e o deploy devem ficar em `skipped`. Guarde link, evento, branch, SHA, captura e trecho do log antes de T03.

## T03 · Validar os cards e registrar a primeira falha do PR

**Aceite.** 1, 4, 5 e 6. **Arquivos.** Alterar `scripts/validate_catalog.py` e `tests/test_validate_catalog.py`.

**Interfaces.** Acrescentar `validate_catalog(site: Path, base_path: str) -> list[str]` à execução da linha de comando de T01. A marcação esperada mantém os IDs `filme1` a `filme10`. Os pendentes exibem um elemento de texto `.status-filme` com “Em breve”.

- [ ] Crie `codex/validacao-catalogo` a partir da `main` que já contém o workflow.
- [ ] Escreva `test_accepts_two_matching_cards_and_eight_pending_cards` com dez cards, os destinos `filmes/filme1.html` e `filmes/filme2.html` e oito marcadores “Em breve”. Inclua ano e espaços repetidos no título de um card e confira `assert validate_catalog(site, "/germinaFlix/") == []` quando os títulos correspondem. Use os títulos “Homem-Aranha: Através do Aranhaverso” e “Mufasa: O Rei Leão” nos arquivos de destino.
- [ ] Escreva `test_rejects_existing_destination_for_wrong_film` apontando Mufasa para `filmes/filme1.html` e verifique que o erro contém “Mufasa: O Rei Leão” e “Homem-Aranha: Através do Aranhaverso”. Em `test_rejects_pending_card_with_link`, dê a `filme3` um link para uma página existente e verifique que o erro identifica `filme3`.
- [ ] Rode `python -m unittest discover -s tests -p test_validate_catalog.py -v` e confira que os novos testes falham antes de implementar a função.
- [ ] Implemente `validate_catalog`. Exija os dez IDs de card, uma âncora para o destino previsto em cada card ativo e nenhuma âncora nos oito pendentes. Compare o texto do `h2` do card com o `title` da página de destino, normalizando espaços e removendo o ano terminal entre parênteses. Os selos devem estar fora do `h2` dos cards ativos. Reaproveite a resolução de caminhos de T01.
- [ ] Ligue a checagem de cards ao comando principal e preserve a lista de erros de caminhos no mesmo log, mesmo quando os cards também falharem.
- [ ] Rode a suíte novamente e confirme `OK`. Faça commit dos dois arquivos com a mensagem `ci: validate movie card destinations`. Envie a branch e abra o PR para a `main` com os links originais.
- [ ] **Antes de corrigir qualquer HTML, registre a primeira execução com falha do PR.** Guarde o link, o evento `pull_request`, a branch de origem e a base `main`, o SHA exibido e a captura do resultado. O log deve mostrar a falha da validação, incluindo `filmes/filme1.html` e `index.html`, e o deploy deve aparecer em `skipped`. Prossiga para T04 após salvar essa evidência.

## T04 · Corrigir o catálogo no mesmo PR e confirmar a CI verde

**Aceite.** 1, 3, 4, 5 e 6. **Arquivos.** Alterar `index.html`, `style.css`, `autor.html`, `filmes/filme1.html` e `filmes/filme2.html`.

**Interfaces.** Atender à estrutura de cards de T03 e à resolução de caminhos de T01.

- [ ] Em `index.html`, corrija o atributo do card `filme1`, aponte Mufasa para `filmes/filme2.html` e separe o selo “Mais vistos” do `h2` do card ativo. Remova as âncoras de `filme3` a `filme10`, mantenha seus IDs e capas e adicione “Em breve” em um elemento `.status-filme`.
- [ ] Em `style.css`, posicione `.status-filme` sobre a capa fora da área que aparece só no hover. Limite o cursor de link aos cards ativos.
- [ ] Corrija o favicon de `autor.html` para `img/logo.png`. Em `filmes/filme1.html`, corrija “Início” para `../index.html` e o link do logo para `../logo.html`. Em `filmes/filme2.html`, troque `/img/…` por `../img/…` e `/index.html` por `../index.html`.
- [ ] Rode a suíte de T01 e repita o comando de validação de T01 com uma pasta nova. Espere `OK` na suíte e código `0` no validador. Confira que os cards pendentes não abrem páginas e que “Em breve” está visível sem passar o cursor.
- [ ] Faça commit dos cinco arquivos com a mensagem `fix: correct catalogue links for GitHub Pages`. Envie o commit ao mesmo PR e registre a nova execução com `ci: success`, upload e deploy em `skipped`. Guarde link, evento, branch, SHA e captura.

## T05 · Publicar no Pages e conferir o commit servido

**Aceite.** 2, 3, 6 e 7. **Arquivos.** Nenhuma edição adicional. A evidência vem do merge, do artefato e do site publicado.

- [ ] Faça o merge do PR verde na `main`. Na execução do `push` gerado pelo merge, confirme que a validação passou, que o upload de `github-pages` ocorreu depois dela e que `deploy` iniciou após a conclusão bem-sucedida de `ci`.
- [ ] Baixe o artefato `github-pages` da execução bem-sucedida e extraia o ZIP. Liste o conteúdo do `artifact.tar` com `tar -tf artifact.tar` e compare os caminhos de arquivos com a lista da pasta validada no log de CI. Confira que as duas páginas de filme ativas estão presentes e que as oito páginas provisórias ficaram de fora.
- [ ] No histórico do ambiente `github-pages`, compare o SHA do deploy ativo com o SHA da execução na `main`. Abra a URL indicada pelo job de deploy e confira as capas, os dois destinos corretos, o retorno por “Início” de ambas as páginas e os oito marcadores “Em breve”.
- [ ] Guarde o link da execução, o evento, a branch, o SHA, a URL do Pages e as capturas dos jobs e do catálogo publicado.

## T06 · Consolidar o PDF do laboratório

**Aceite.** 8. **Arquivos.** Criar `entrega-ci-cd.pdf` fora do repositório.

- [ ] Reúna o link do repositório, o YAML completo do workflow e a justificativa para usar GitHub Pages com HTML, CSS e imagens.
- [ ] Inclua as quatro execuções do plano com link, evento, branch, SHA e captura. Associe a imagem do site e a URL ao deploy bem-sucedido e destaque a diferença entre a falha do PR e a do push na `main`.
- [ ] Inclua os prompts relevantes com resultado, problema e ajuste. Registre na análise a contagem de prompts, os principais problemas, as alterações necessárias, as alterações manuais e as verificações feitas.
- [ ] Abra o PDF exportado, verifique se as capturas e o YAML são legíveis, abra os links e confira se todas as evidências estão no mesmo arquivo.
