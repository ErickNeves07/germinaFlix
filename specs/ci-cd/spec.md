# Especificação de CI/CD do GerminaFlix

O GitHub Actions deve validar o catálogo estático do GerminaFlix antes de publicar uma versão no GitHub Pages. O Pages é adequado ao projeto porque o site é servido como arquivos estáticos de HTML, CSS e imagens.

## Critérios de aceite

### 1. Executar CI em pull requests para a `main`

O job `ci` deve executar no evento `pull_request` com destino à `main`. O job deve fazer checkout do código, preparar o ambiente do validador, instalar dependências se necessário e executar a validação. O deploy deve ser ignorado nesse evento.

**Como verificar.** Abra um PR de correção para a `main`. No GitHub Actions, confirme que a execução foi disparada por `pull_request`, confira no log as etapas de checkout, preparação e validação e registre o resultado `success` da CI e o estado `skipped` do deploy.

### 2. Executar CI a cada push na `main`

O mesmo job `ci` deve executar a cada evento `push` na `main`, inclusive após o merge de um PR.

**Como verificar.** No GitHub Actions, confira a execução do primeiro push com o workflow e a do push gerado pelo merge do PR de correção. Em ambas, confirme o evento `push`, a branch `main`, o SHA do commit e a execução do job `ci`.

### 3. Validar os arquivos que serão publicados

A CI deve preparar e validar uma pasta com `index.html`, `autor.html`, `logo.html`, os arquivos CSS e de imagem do site e as páginas `filmes/filme1.html` e `filmes/filme2.html`. As páginas `filmes/filme3.html` a `filmes/filme10.html` devem ficar fora dessa pasta. O deploy deve usar o artefato preparado e aprovado pela CI da mesma execução.

**Como verificar.** Compare o conteúdo da pasta entregue ao validador com o do artefato enviado ao Pages. Confirme a presença das páginas, dos estilos e das imagens previstos e a ausência das oito páginas provisórias. Confira no workflow que o envio do artefato usa a pasta validada.

### 4. Validar os caminhos locais do site

A CI deve verificar os destinos de `href` e `src` locais em todos os HTML da pasta de publicação. As referências devem ser resolvidas a partir da URL do HTML que as contém, dentro do prefixo `/germinaFlix/`. Cada destino deve existir na pasta de publicação com a mesma grafia, incluindo maiúsculas e minúsculas. URLs externas ficam fora da checagem obrigatória. Um caminho inválido deve fazer a CI falhar e aparecer no log com o arquivo de origem.

**Como verificar.** Rode o validador em uma cópia de teste da pasta de publicação. Confira que ele passa com os caminhos corrigidos. Em testes separados, aponte para um arquivo ausente, altere a capitalização de uma referência e troque um caminho relativo válido por `/img/logo.png`. Confirme que cada alteração causa falha e que o log identifica o HTML e o caminho que a provocaram.

### 5. Validar os destinos dos cards do catálogo

Os cards de Homem-Aranha e Mufasa devem abrir `filmes/filme1.html` e `filmes/filme2.html`, respectivamente. A CI deve comparar o nome de cada filme ativo com o título da página de destino, normalizando espaços e desconsiderando o ano e selos como “Mais vistos”. Os outros oito cards devem aparecer como “Em breve”, sem link.

**Como verificar.** Confira os dez cards no catálogo e rode a validação com os destinos corretos. Em uma cópia de teste, aponte o card de Mufasa para `filmes/filme1.html`. Confirme que a CI falha mesmo com o destino existente e que o log mostra o título esperado e o encontrado.

### 6. Publicar somente após CI bem-sucedida em push na `main`

O GitHub Pages deve ter GitHub Actions como fonte de publicação. No mesmo workflow, o job `deploy` deve depender de `ci` com `needs: ci` e só pode executar no evento `push` na `main`, após a conclusão bem-sucedida da CI.

**Como verificar.** No primeiro push com o workflow na `main`, use o erro já existente no link “Início” de `filmes/filme1.html`. O `href="index.html"` procura `filmes/index.html`. Registre a falha da CI no log e o deploy em estado `skipped`. No PR, corrija o link para `../index.html` junto com os demais erros encontrados e confirme que a CI passa com o deploy ainda em `skipped`. Após o merge, confirme que a execução do push na `main` mostra a CI concluída com sucesso antes do início do deploy e que ambos os jobs terminam com sucesso.

### 7. Confirmar a versão publicada

A execução bem-sucedida do deploy deve informar a URL do catálogo no GitHub Pages. A versão publicada deve corresponder ao commit da execução e permitir navegar pelo catálogo e pelas duas páginas de filme.

**Como verificar.** No histórico do ambiente `github-pages`, confira se o deploy ativo está associado ao mesmo SHA da execução bem-sucedida na `main`. Abra a URL exibida pelo job de deploy. Clique nos cards de Homem-Aranha e Mufasa, confira os títulos, verifique que as capas carregam e use “Início” em cada página para voltar ao catálogo. Confira os oito cards marcados como “Em breve”. Registre a URL e a captura do site junto ao link da execução de deploy e ao SHA do commit implantado.

### 8. Reunir as evidências em um único PDF

O PDF deve reunir o link do repositório, o YAML completo do workflow, a justificativa do GitHub Pages, as evidências de execução e o diário de uso da IA. Para cada interação relevante, o diário deve registrar o prompt, o resultado, o problema encontrado quando houver e o ajuste feito. A análise final deve informar a contagem de prompts, os principais problemas, as alterações necessárias, quais foram feitas manualmente e como o funcionamento da pipeline foi verificado.

**Como verificar.** Abra o PDF final e confira se ele contém os links e as capturas das três execuções, com evento, branch e SHA identificáveis. Confira se a captura do site está associada à execução bem-sucedida de deploy e se o diário e a análise permitem acompanhar as alterações até a versão final.
