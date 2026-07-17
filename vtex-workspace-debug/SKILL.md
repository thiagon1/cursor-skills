# VTEX Workspace — abrir, esperar login e debugar no navegador

Skill para abrir **workspaces VTEX IO** (que são **privados** e exigem login) no navegador via MCP `user-chrome-devtools`, **esperar o usuário logar** e então **debugar/validar/ajustar** com console, network, screenshots e viewport. Use quando o usuário mandar uma URL de workspace VTEX e pedir para "abrir no navegador", "testar", "debugar", "validar o ajuste" ou "ver o console/erro".

## Pré-requisito

- Server MCP `user-chrome-devtools` com status **ready**. Se estiver "needsAuth", chamar `mcp_auth` desse server.
- O Chrome controlado é o **navegador real do usuário** (compartilha cookies/sessão). Por isso o **usuário loga manualmente** e a navegação seguinte já fica autenticada — o agente **NUNCA** deve tentar digitar credenciais.

## Como reconhecer um workspace VTEX

Padrão de URL:

```
https://{workspace}--{conta}.myvtex.com/{rota}
```

Exemplos:
- `https://task14783--lojamm.myvtex.com/` → workspace `task14783`, conta `lojamm`
- `https://mytest--leeloo.myvtex.com/lancamentos` → workspace `mytest`, conta `leeloo`

O `--` separa **workspace** de **conta**. Workspaces (diferentes de `master`) são **privados**: sem sessão VTEX válida, a página redireciona/bloqueia (login VTEX ID, tela de acesso, 401/403).

---

# Fluxo

## Passo 1 — Abrir o workspace

Abrir em uma aba nova:

```
server: user-chrome-devtools
toolName: new_page
arguments: { "url": "https://{workspace}--{conta}.myvtex.com/{rota}" }
```

- Se já houver uma aba do projeto, usar `list_pages` + `select_page` em vez de abrir outra.
- Guardar o `pageId` retornado para as próximas chamadas.

## Passo 2 — Detectar se precisa de login

Tirar um snapshot de acessibilidade (mais barato que screenshot) para ver o estado:

```
server: user-chrome-devtools
toolName: take_snapshot
```

Sinais de **parede de login / workspace privado** (precisa o usuário logar):
- URL redirecionou para `.../login`, `vtexid`, `/_v/segment/admin-login/...` ou domínio de login.
- Snapshot mostra tela de "Entrar", "Login", "Acesse sua conta", campos de e-mail/senha, botão Google/VTEX ID.
- Console/network com **401/403** nas requisições principais (`list_network_requests`, `list_console_messages`).

Se **não** houver parede de login (a loja renderizou normal), pular para o Passo 4.

## Passo 3 — PAUSAR e esperar o usuário logar (regra central)

Se detectou parede de login:

1. **NÃO** tentar preencher login, senha ou clicar em "Entrar". Não usar `fill`/`type_text`/`click` na tela de login.
2. Avisar o usuário e **parar**, pedindo que ele logue manualmente na aba já aberta:

   ```
   O workspace {workspace}--{conta} é privado e está pedindo login.
   Abri a página no seu Chrome. Faça o login manualmente nessa aba
   (VTEX ID / Google) e me avise quando estiver logado e na página
   {rota} que eu continuo o debug/ajuste.
   ```

3. **Esperar a confirmação do usuário.** Não prosseguir sozinho. Duas formas de retomar:
   - **Preferida:** aguardar o usuário responder "logado"/"pode seguir" no chat.
   - **Opcional (se o usuário pedir para você detectar):** usar `wait_for` por um texto que só aparece **depois** do login (um elemento da loja, ex.: nome de um produto, menu, footer):

     ```
     server: user-chrome-devtools
     toolName: wait_for
     arguments: { "text": ["<texto que aparece só na loja logada>"], "timeout": 120000 }
     ```

4. Depois do "ok", recarregar/navegar para a rota alvo e confirmar que está autenticado:

   ```
   server: user-chrome-devtools
   toolName: navigate_page
   arguments: { "type": "url", "url": "https://{workspace}--{conta}.myvtex.com/{rota}" }
   ```

   Tirar novo `take_snapshot` para confirmar que a loja renderizou (sem login).

## Passo 4 — Debugar / validar / ajustar

Com a página autenticada, usar as ferramentas conforme a necessidade:

| Objetivo | Ferramenta(s) |
|---|---|
| Ver estrutura/elementos (com `uid`) | `take_snapshot` (preferir a screenshot) |
| Evidência visual / comparar layout | `take_screenshot` (`fullPage: true` p/ página inteira) |
| Erros de JS / logs | `list_console_messages` (+ `get_console_message` p/ detalhe) |
| Falhas de requisição, 4xx/5xx, payloads | `list_network_requests` (+ `get_network_request`) |
| Inspecionar/checar valores no DOM/JS | `evaluate_script` (função JSON-serializável) |
| Testar responsivo (mobile/tablet/desktop) | `emulate` (`viewport`) ou `resize_page` |
| Interagir (clicar, preencher form, hover) | `click`, `fill`, `fill_form`, `hover`, `press_key` |
| Throttle rede/CPU, dark mode, geoloc | `emulate` |
| Performance (LCP, INP, CLS) | `performance_start_trace` / `performance_stop_trace` |
| Acessibilidade/SEO/best practices | `lighthouse_audit` |

### Viewports comuns para validar responsivo

```
server: user-chrome-devtools
toolName: emulate
arguments: { "viewport": "375x812x3,mobile,touch" }   // mobile
```

```
arguments: { "viewport": "1440x900x1" }   // desktop
```

## Passo 5 — Loop de ajuste (código ↔ workspace)

Em VTEX IO, com `vtex link` rodando, as mudanças aparecem no workspace após alguns segundos. Ciclo típico:

1. Fazer o ajuste no código (CSS/componente) — usar `vtex-css` / `vtex-io-component` conforme o caso.
2. Aguardar o `vtex link` propagar (o terminal do link mostra o rebuild).
3. `navigate_page` (`type: "reload"`, `ignoreCache: true`) para recarregar o workspace.
4. Reconferir com `take_snapshot` / `take_screenshot` / `list_console_messages`.
5. Repetir até validar. A sessão continua logada — **não** precisa refazer o login a cada reload (só se a sessão expirar).

```
server: user-chrome-devtools
toolName: navigate_page
arguments: { "type": "reload", "ignoreCache": true }
```

---

## Regras

- **Nunca** tentar logar por conta própria em workspace privado: o usuário loga manualmente; o agente só **espera** e retoma.
- **Sempre** detectar a parede de login (snapshot + URL + 401/403) antes de assumir que a página carregou.
- Ao pausar para login, **deixar claro** qual aba/rota e **aguardar confirmação** antes de seguir.
- Preferir `take_snapshot` a `take_screenshot` para inspeção (mais barato); usar screenshot para evidência visual.
- Reutilizar a aba existente (`list_pages` + `select_page`) em vez de abrir várias.
- Se a sessão cair no meio do trabalho (voltou o login), repetir o Passo 3 (pausar e esperar).
- Prints de evidência: seguir `upload-image-cloudinary` / `runrunit-pr-commit` para hospedar e anexar na task/PR.

## Integração com outras skills

- **`runrunit-pr-commit`**: no Flow A (executar/validar) e Flow B (evidências), use esta skill para abrir o workspace da task, esperar o login e capturar prints antes/depois.
- **`vtex-css` / `vtex-io-component`**: fazer o ajuste no código; esta skill valida no navegador.
- **`registrar-evidencias`**: capturar screenshots em múltiplos viewports para o comentário/PR.

## Ferramentas MCP (server `user-chrome-devtools`)

| Ferramenta | Uso |
|---|---|
| `new_page` / `list_pages` / `select_page` / `close_page` | Gerenciar abas |
| `navigate_page` | Ir para URL, voltar/avançar, **reload** |
| `take_snapshot` | Árvore a11y com `uid` dos elementos (inspeção principal) |
| `take_screenshot` | Imagem da página/elemento (evidência) |
| `wait_for` | Esperar um texto aparecer (ex.: confirmar login) |
| `list_console_messages` / `get_console_message` | Logs e erros de JS |
| `list_network_requests` / `get_network_request` | Requisições, status, payloads |
| `evaluate_script` | Rodar JS na página (checar valores/estado) |
| `emulate` / `resize_page` | Viewport, rede/CPU, dark mode, geoloc |
| `click` / `fill` / `fill_form` / `hover` / `press_key` / `type_text` | Interações |
| `performance_start_trace` / `performance_stop_trace` | Performance (Core Web Vitals) |
| `lighthouse_audit` | Acessibilidade / SEO / best practices |
| `mcp_auth` | Autenticar o server quando `needsAuth` |
