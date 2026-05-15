# 🎬 Pipeline de Vídeo

O fluxo de vídeo do Furious Mirror é otimizado para latência sub-100ms.

## Do Android para a Tela (Passo a Passo)

1.  **Captura (Android)**: O `furious-core.jar` utiliza a API `MediaCodec` do Android para capturar a tela via `SurfaceControl`.
2.  **Encodificação**: Os frames são codificados em H.264 (AVC) diretamente no hardware do celular.
3.  **Streaming**: O fluxo é enviado sem encapsulamento (Raw AnnexB) via socket TCP.
4.  **Demuxing (PC)**: O módulo `demuxer.py` lê o fluxo, identifica os cabeçalhos de frame e separa os pacotes.
5.  **Decoding**: O `decoder.py` utiliza o FFmpeg (via bibliotecas dinâmicas) para transformar o H.264 em frames YUV (Planar YUV420p).
6.  **Rendering**: 
    - O frame YUV é enviado para a memória da GPU.
    - O SDL2 realiza a conversão de cores e o upscale/downscale necessário com filtragem linear.

---

# 🖱️ Mapeamento de Entrada (Input Mapping)

O mapeamento de entrada garante que um clique na janela do Windows atinja exatamente o botão desejado no Android.

## Desafios do Mapeamento
A janela do Windows pode ser redimensionada pelo usuário para qualquer formato, enquanto o celular tem uma resolução fixa (ex: 1080x2400). Isso gera bordas pretas (Letterboxing) na janela do PC.

## Lógica de Cálculo (`furious.py`)
Para converter um clique `(mx, my)` do Windows em um toque `(ax, ay)` no Android:

1.  **Identificação do Vídeo Rect**: O `screen.py` calcula continuamente a `_video_rect` (a área exata onde a imagem do celular está aparecendo dentro da janela).
2.  **Subtração de Offset**: Removemos a posição `x` e `y` da borda preta.
    - `local_x = mx - video_rect.x`
3.  **Normalização e Escala**: 
    - Dividimos o clique pela largura da área de vídeo exibida.
    - Multiplicamos pela largura real do frame vindo do Android.
    - `final_x = (local_x / video_rect.w) * android_w`

Esta fórmula permite que o controle remoto funcione perfeitamente, mesmo com a janela em modo janela, maximizada ou em monitores UltraWide.
