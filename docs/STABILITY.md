# 🌊 Engenharia de Estabilidade e Fluidez

O Furious Mirror implementa técnicas avançadas de sincronização de frames para garantir uma experiência de 60 FPS estável, mesmo em redes sem fio 2.4GHz.

## 1. High-Precision Timing (Win32)
O Windows, por padrão, tem uma resolução de timer de aproximadamente 15.6ms. Para o Furious Mirror, isso é inaceitável, pois causaria micro-stutters em um stream de 60 FPS (onde cada frame precisa de ~16.6ms).
- **Solução**: Em `run.py`, utilizamos a API `winmm.dll` via `timeBeginPeriod(1)`.
- **Efeito**: Forçamos o escalonador do Windows a trabalhar com precisão de **1ms**, permitindo que o nosso loop principal seja cirúrgico na entrega dos frames.

## 2. Jitter Buffer (Amortecedor de Rede)
O Wi-Fi não entrega pacotes de forma constante. Muitas vezes os frames chegam em "rajadas".
- **O Problema**: Se tentarmos renderizar assim que chegam, a imagem parece acelerar e desacelerar (jitter).
- **A Solução**: Implementamos um buffer de **4 frames**. 
    - O sistema mantém sempre 4 frames "na reserva".
    - Isso cria um atraso imperceptível de ~60ms, mas garante que, se a rede oscilar por alguns milissegundos, o app tenha frames prontos para exibir.
- **Auto-Descarte**: Se a fila crescer além de 4 frames, o app descarta o excesso instantaneamente para manter a latência em tempo real.

## 3. Focus and Window Management
O sistema protege o stream contra comportamentos do Sistema Operacional:
- **Focus Lost**: Quando o usuário clica fora da janela, o app suspende a chamada `SDL_RenderPresent`. Isso economiza recursos da GPU do PC. No entanto, o `Demuxer` e o `Decoder` continuam rodando para limpar os sockets, evitando "Lag Acumulado" ao retomar o foco.
- **Grace Period**: O monitor de performance ignora os primeiros 2 segundos após um redimensionamento ou ganho de foco para evitar alarmes falsos de "Dropped Frames".

## 4. Hardware Acceleration
Toda a renderização YUV é feita diretamente na GPU. O processador (CPU) é usado apenas para a decodificação de software, enquanto o SDL2 utiliza shaders de hardware para converter as cores YUV em RGB e exibi-las na tela.
