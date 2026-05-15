# Planejamento: Criação do Executável Furious Mirror (OneFile)

O objetivo é gerar um único arquivo `.exe` que contenha todo o código Python, as bibliotecas (SDL2, PyAV) e as ferramentas externas (ADB, JAR).

## 🛠️ Ferramenta Escolhida: PyInstaller
O PyInstaller permite embutir arquivos binários e pastas inteiras dentro do executável.

## 📋 Passos Necessários

### 1. Adaptação do Código (Caminhos Dinâmicos)
Atualmente, o código procura a pasta `portables` usando caminhos relativos ao arquivo `.py`. No executável, precisamos usar o `sys._MEIPASS`, que é o caminho da pasta temporária onde o Windows extrai os arquivos ao rodar o `.exe`.

*   **Arquivo alvo**: `app/server.py`
*   **Mudança**: Detectar se o app está "congelado" (frozen) e ajustar o caminho base.

### 2. Inclusão de Binários e Dependências
Precisamos garantir que o PyInstaller inclua:
*   A pasta `portables/` inteira.
*   As DLLs do SDL2 e as bibliotecas do PyAV.

### 3. Configuração do Arquivo `.spec`
Em vez de um comando gigante no terminal, criaremos um arquivo `furious-mirror.spec`. Isso permite:
*   Definir o ícone do app.
*   Esconder o console do Windows (opcional).
*   Gerenciar as permissões de administrador (necessário para o ADB).

---

## 🚀 Estratégia de Build
Usaremos um comando que empacota a pasta `portables` e gera o binário final:
```powershell
pyinstaller --onefile --windowed --add-data "portables;portables" --name "FuriousMirror" run.py
```

## ⚠️ Pontos de Atenção
*   **Antivírus**: Executáveis OneFile não assinados às vezes são detectados como falsos positivos pelo Windows Defender.
*   **Extração**: Na primeira vez que abre, ele demora uns 2 segundos a mais porque está extraindo o ADB para a pasta temporária.

---

**Deseja prosseguir com a preparação do código?**
