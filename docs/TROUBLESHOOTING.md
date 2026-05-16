# 🛠️ Guia de Resolução de Problemas (Troubleshooting)

Este guia ajuda a resolver os problemas mais comuns encontrados ao tentar conectar e espelhar seu dispositivo Android.

## 1. O Computador não reconhece o Celular (No Device Found)

Mesmo que o Windows abra as pastas do seu celular, o motor do Furious Mirror pode não detectá-lo.

### Drivers ADB vs MTP
*   **MTP (Media Transfer Protocol)**: É o driver que o Windows instala automaticamente para você ver fotos e arquivos. **Não é suficiente para o espelhamento.**
*   **ADB Interface**: É o driver necessário para comandos de sistema e espelhamento.
*   **Como resolver**: 
    1. Abra o **Gerenciador de Dispositivos** do Windows.
    2. Procure por "Android Device" ou "Outros dispositivos".
    3. Se houver um ícone com uma exclamação amarela (⚠️), o driver ADB está faltando.
    4. Clique com o botão direito > Atualizar Driver > Procurar drivers no meu computador > Permitir que eu escolha em uma lista. 
    5. Escolha **"Google USB Driver"** ou **"ADB Composite Interface"**.

### Cabo e Portas
*   **Cabo de Dados**: Certifique-se de usar o cabo original ou um cabo de alta qualidade. Cabos de camelô muitas vezes servem apenas para carregar e não transmitem dados.
*   **Portas USB**: Evite usar hubs USB ou portas frontais de gabinetes de PC Desktop; conecte diretamente na porta traseira da placa-mãe.

---

## 2. Erro: "Dispositivo Não Autorizado" (Unauthorized)

Ao abrir o app, se aparecer uma mensagem de "Não Autorizado":
1. Olhe para a tela do seu celular.
2. Você verá uma mensagem perguntando: **"Permitir depuração USB?"**.
3. Marque a caixa **"Sempre permitir a partir deste computador"** e clique em OK.
4. Reinicie o Furious Mirror.

---

## 3. Falha na Conexão Wi-Fi (Modo Híbrido)

Se o USB funciona, mas o Wi-Fi falha ao tentar conectar:

*   **Mesma Rede**: O PC e o Celular **devem** estar na mesma rede Wi-Fi (ex: ambos no "Wi-Fi_da_Casa").
*   **Frequência (2.4GHz vs 5GHz)**: Se o seu roteador tiver as duas, tente colocar ambos na de **5GHz** para melhor performance.
*   **Isolamento de AP (AP Isolation)**: Alguns roteadores de condomínio ou empresas bloqueiam a comunicação entre aparelhos na mesma rede. Se isso estiver ativo, o modo Wi-Fi não funcionará.
*   **Firewall do Windows**: Na primeira vez que abrir o app, o Windows perguntará se deseja permitir o acesso à rede. Você **deve** marcar as duas caixas (Redes Privadas e Públicas) e permitir.

---

## 4. Problemas com Xiaomi / Redmi / POCO (MIUI)

Aparelhos Xiaomi possuem camadas extras de segurança que bloqueiam o controle remoto por padrão:
1. Vá em **Opções do Desenvolvedor**.
2. Ative **Depuração USB**.
3. Ative **Instalar via USB**.
4. Ative **Depuração USB (Configurações de Segurança)** — *Pode exigir que você faça login na Mi Account.*

---

## 5. Lag ou Engasgos na Imagem

*   **Rede Instável**: No modo Wi-Fi, o lag costuma ser causado por interferência. Mova-se para mais perto do roteador.
*   **Modo de Energia**: Se estiver em um notebook, certifique-se de que ele esteja conectado à tomada e em modo de "Melhor Performance".

---

### Ainda com problemas?
Envie o arquivo `furious_debug.log` (localizado na pasta do aplicativo) para nossa equipe técnica para análise detalhada.
