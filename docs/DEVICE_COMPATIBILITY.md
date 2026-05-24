# Compatibilidade de Dispositivos (Device Compatibility)

Este documento registra os testes de compatibilidade do Furious Mirror em diferentes dispositivos e versões do Android.

## Testes Bem-Sucedidos (Conexão Completa)

Os seguintes dispositivos conectaram perfeitamente, transmitindo tanto **Áudio** quanto **Vídeo** sem problemas:

*   **Poco X5 Pro 5G**
    *   **Status:** Conexão Perfeita (Áudio e Vídeo)
    *   **Observações:** Testado com as últimas atualizações do Android (até maio de 2026).
*   **Infinix Hot 50 Pro Plus**
    *   **Status:** Conexão Perfeita (Áudio e Vídeo)
    *   **Observações:** Testado com as últimas atualizações do Android (até maio de 2026).

## Testes Parciais (Apenas Vídeo)

Os seguintes dispositivos conectaram, mas apresentaram limitações na transmissão de áudio (geralmente devido a restrições do sistema operacional Android inferior ao 11, que não suporta redirecionamento de áudio nativo de forma padrão):

*   **Xiaomi Note 7**
    *   **Sistema:** Android 10 (MIUI 12.5.1)
    *   **Status:** Conexão Parcial (Apenas Vídeo)
    *   **Observações (Áudio):** O vídeo é transmitido corretamente para o PC, mas o áudio continua sendo reproduzido no próprio celular. Este é um comportamento esperado em versões mais antigas do Android sem suporte a forward de áudio nativo via scrcpy.
    *   **Observações (Controles/Mouse):** Os cliques do mouse e o teclado do PC podem não funcionar inicialmente (a tela é espelhada, mas você não consegue controlar o celular). Isso não é um bug do Furious Mirror, mas sim uma exigência de segurança da MIUI.
    *   **Solução para os Controles:** Para o mouse e teclado funcionarem, você deve ir em **Configurações > Configurações Adicionais > Opções do Desenvolvedor** e ativar a opção **"Depuração USB (Configurações de Segurança)"** (ou "USB debugging (Security settings)"). O celular pedirá vários alertas de segurança; aceite todos. Pode ser necessário **reiniciar o celular** após ativar a opção para que ela faça efeito.

## Testes Mal-Sucedidos (Problemas de Conexão)

Os seguintes dispositivos apresentaram problemas severos de conexão com o ADB/scrcpy, impedindo o funcionamento do Furious Mirror:

*   **Samsung Galaxy A12**
    *   **Sistema:** Android 12
    *   **Status:** Conexão Falhou (Loop de Reconexão)
    *   **Sintomas:** O aplicativo entra em um loop infinito de tentativas de conexão. Em cada tentativa, o celular exibe o prompt de permissão de depuração USB, mas mesmo após o usuário aprovar (aceitar) a permissão, a conexão de vídeo e áudio nunca é estabelecida.
    *   **Diagnóstico / Causa Raiz:** Foram realizados testes de controle com a versão original do Scrcpy puro via linha de comando, e o mesmo problema ocorreu (o Scrcpy original também falhou ao conectar ao A12). Isso indica que é um problema de compatibilidade profundo com o dispositivo (possivelmente limitação de hardware de encoding, firmware customizado da Samsung neste modelo específico, ou drivers ADB), e não um bug na lógica de conexão do Furious Mirror.
