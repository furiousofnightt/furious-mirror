# 💻 Guia do Desenvolvedor

Este documento auxilia na manutenção e expansão do código fonte do Furious Mirror.

## Estrutura de Pastas e Módulos

### `/app/util/`
Contém utilitários transversais:
- `log.py`: Sistema de log unificado (saída para console e arquivo).
- `msgbox.py`: Abstração para caixas de diálogo nativas do Windows (Win32 API).

### `app/control_msg.py`
Define a serialização binária dos comandos de controle. Se quiser adicionar suporte a novos botões (ex: Home, Back, App Switch), é aqui que a mensagem deve ser definida seguindo o protocolo Scrcpy.

### `app/options.py`
Objeto de configuração que viaja por todo o sistema. Nele você define resoluções máximas, bitrates padrão e flags de inicialização.

## Sistema de Logs e Debug
O projeto possui dois níveis de log:
1.  **Logger Principal**: Registra eventos de alto nível no console (conectar, desconectar, erros).
2.  **Furious Debug Log**: Um arquivo chamado `furious_debug.log` é criado na raiz do executável. Ele contém logs de baixo nível, erros ADB e stack traces completos. Útil para debugar problemas em computadores de usuários onde o console não está visível.

## Boas Práticas ao Adicionar Código
1.  **Timer Precision**: Se adicionar loops de tempo, sempre considere o `timeBeginPeriod(1)` que foi ativado no `run.py`.
2.  **Thread Safety**: A renderização SDL2 deve ocorrer apenas na thread principal. Use filas (`queue.Queue`) para passar dados entre threads de rede e a thread de tela.
3.  **ADB StartupInfo**: Ao rodar comandos ADB via `subprocess`, sempre utilize a flag `CREATE_NO_WINDOW` (via `startupinfo`) para evitar que janelas pretas de terminal fiquem piscando na tela do usuário.
