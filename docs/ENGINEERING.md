# 🏗️ Furious Mirror: Engenharia e Arquitetura

O **Furious Mirror** é uma solução de espelhamento de alto desempenho otimizada para baixa latência e resiliência em ambientes sem fio.

## 1. Pipeline de Dados
O sistema opera através de três sockets TCP paralelos com o servidor Android (`furious-core.jar`):

### A. Canal de Vídeo (Video Socket)
- **Protocolo**: H.264 bruto.
- **Processamento**: 
    1. `Demuxer.py`: Extração de NAL units.
    2. `Decoder.py`: Decodificação YUV420p via FFmpeg.
    3. `Screen.py`: Renderização acelerada por GPU via `SDL_UpdateYUVTexture`.

### B. Canal de Áudio (Audio Socket)
- **Protocolo**: Opus decodificado em tempo real para a API de áudio do SDL2.

### C. Canal de Controle (Control Socket)
- **Precisão de Toque**: Mapeamento matemático entre coordenadas da janela Windows e a tela do Android em `furious.py:process_mouse_event`, compensando bordas e escalas.

---

## 2. Mecânicas de Estabilidade

### 🌊 Jitter Buffer (Frame Pacing)
Implementado em `furious.py:run_event_loop` com um limiar de **4 frames**. 
- Absorve oscilações de rede Wi-Fi.
- Mantém latência fixa descartando frames obsoletos se a fila acumular.

### 🛡️ Gestão de Eventos Windows
- **Focus Guard**: O app detecta `FOCUS_LOST` e suspende a renderização pesada, mantendo o consumo do socket ativo em background para evitar atraso (lag) ao retomar.
- **Precision Timer**: Usa `winmm.dll` para forçar o Windows a usar timers de **1ms**, garantindo que o loop de 60 FPS seja exato.

---

## 3. Conectividade Híbrida
- **Discovery**: O módulo `wireless.py` busca o IP do dispositivo via rotas internas do Android (`ip route`), sendo compatível com diversas marcas (Infinix, Samsung, etc).
- **Handshake**: Transição transparente de USB para TCP/IP sem fechar o processo principal.
