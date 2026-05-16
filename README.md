<p align="center">
  <img src="images/furious-mirror.png" width="200" alt="Furious Mirror Logo">
</p>

# <p align="center">Furious Mirror</p>

<p align="center">
  <strong>O Motor de Espelhamento Android de Elite para Windows</strong><br>
  <em>Alta Performance • Latência Zero • Conectividade Híbrida</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versão-1.0.0-00f0ff?style=for-the-badge" alt="Versão">
  <img src="https://img.shields.io/badge/Plataforma-Windows-blue?style=for-the-badge" alt="Plataforma">
  <img src="https://img.shields.io/badge/Status-Estável-green?style=for-the-badge" alt="Status">
</p>

---

## 🚀 O que é o Furious Mirror?

O **Furious Mirror** é uma evolução na engenharia de espelhamento de dispositivos Android. Construído para profissionais que exigem fluidez absoluta, ele combina a robustez do protocolo *scrcpy* com uma camada de inteligência exclusiva para estabilização de rede (Wi-Fi) e gerenciamento de frames em tempo real.

## ✨ Funcionalidades Premium

*   🏎️ **60 FPS Real-time**: Loop de renderização sincronizado com timer de alta precisão (1ms).
*   📶 **Modo Híbrido Inteligente**: Transição instantânea de USB para Wireless com um clique.
*   🌊 **Jitter Buffer**: Algoritmo amortecedor que elimina engasgos em redes 2.4GHz.
*   📊 **Active Performance Monitor**: Painel de diagnóstico de FPS e saúde de rede integrado.
*   🛡️ **Smart Focus**: Suspensão inteligente de processamento quando a janela está em background.
*   📦 **Zero Setup**: Totalmente portátil. ADB e dependências inclusas no binário.

---

## 📁 Estrutura do Ecossistema

| Pasta | Descrição |
| :--- | :--- |
| **`/app`** | Núcleo de engenharia em Python (Threads, Sockets, SDL2). |
| **`/docs`** | Wiki técnica detalhada com guias de arquitetura. |
| **`/portables`** | Binários essenciais e recursos de imagem. |

---

## 📖 Documentação Técnica

Para explorar as entranhas do projeto, consulte nossa base de conhecimento:


---

## 🛠️ Como Iniciar (Dev Mode)

1.  Certifique-se de ter o Python 3.10+ instalado.
2.  Instale as dependências: `pip install -r requirements.txt`.
3.  Execute o motor:
    ```powershell
    python run.py
    ```

---

## 🤝 Créditos e Licença

Este projeto utiliza componentes do [scrcpy](https://github.com/Genymobile/scrcpy), desenvolvido pela Genymobile e colaboradores. 

- O servidor `furious-core.jar` e o protocolo de comunicação são baseados no scrcpy e distribuídos sob a **Licença Apache 2.0**.
- O código fonte do Furious Mirror é uma implementação independente que estende essas funcionalidades.

A licença Apache 2.0 permite o uso, modificação e distribuição de softwares derivados, desde que os créditos originais sejam mantidos. Consulte o arquivo [LICENSE](./LICENSE) para mais detalhes.


---
<p align="center">
  <em>Propriedade de Furious Mirror.</em>
</p>

