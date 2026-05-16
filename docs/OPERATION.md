# 📖 Furious Mirror: Guia de Operação e Build

Este guia detalha o uso diário e o processo de empacotamento do software.

## 1. Modos de Conexão

### Modo USB
- **Bitrate**: 8 Mbps.
- Automático: Plugue o cabo e inicie `run.py`.

### Modo Wi-Fi (Híbrido)
- **Bitrate**: 6 Mbps.
- **Passos**:
    1. Inicie via USB.
    2. Use o ícone de bandeja (Tray Icon) do sistema.
    3. Selecione "Ativar conexão Wi-Fi (modo híbrido)".
    4. Remova o cabo após a mensagem de confirmação.

---

## 2. Monitoramento de Rede
O log no terminal exibe informações cruciais a cada 10 segundos:
- `FPS`: Frames exibidos por segundo.
- `Drops`: Quantidade de frames descartados nos últimos 5 segundos devido a congestionamento de rede.
- `Bitrate`: Taxa de transferência ativa.

---

## 3. Logs e Diagnóstico
O Furious Mirror gera logs detalhados para ajudar na identificação de problemas:
- **Localização**: O arquivo `furious_debug.log` é criado automaticamente na mesma pasta do executável (ou na raiz do projeto em modo Dev).
- **Conteúdo**: Registra tentativas de conexão ADB, erros de socket, mudanças de bitrate e stack traces de falhas.
- **Dica**: Sempre anexe este arquivo ao solicitar suporte técnico.

---

## 4. Criando o Executável (.EXE)
O Furious Mirror é compilado como um executável de arquivo único para portabilidade.

### Preparação
Certifique-se de ter as pastas `portables` e `sdl2_bins` na raiz do projeto.

### Compilação
```powershell
pyinstaller FuriousMirror.spec --clean
```

O arquivo final será gerado na pasta `dist/`.
