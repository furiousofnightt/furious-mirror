# 📶 Engenharia Wireless e Modo Híbrido

O Furious Mirror possui um sistema exclusivo de transição entre USB e Wi-Fi, permitindo mobilidade sem a necessidade de reconfigurar o dispositivo manualmente.

## 1. O Protocolo ADB sobre TCP/IP
O Android suporta a depuração via rede, mas por segurança, ela vem desativada por padrão. O Furious Mirror automatiza este processo:
1.  **Ativação**: O app envia `adb tcpip 5555` via cabo USB. Isso instrui o daemon do ADB no celular a abrir uma porta de escuta na rede Wi-Fi.
2.  **Persistência**: Uma vez ativado, o modo TCP/IP permanece ligado até que o celular seja reiniciado.

## 2. Descoberta Inteligente de IP (Smart Discovery)
A maior dificuldade de conexões sem fio é saber o IP do celular. O módulo `wireless.py` resolve isso através de uma busca em multinível:
- **Nível 1 (IP Route)**: O app executa `ip route` no Android e busca o endereço de origem (`src`) da rota principal. Isso evita erros com nomes de interface (como `wlan0` vs `wlan1`).
- **Nível 2 (IP Addr Scan)**: Se a rota falhar, o app escaneia todas as interfaces ativas buscando por IPs de redes privadas (`192.168.x.x`, `10.x.x.x` ou `172.x.x.x`).

## 3. Fluxo do Modo Híbrido
O Modo Híbrido é uma transição em "quente":
1.  O usuário inicia o espelhamento via **USB**.
2.  Ao ativar o modo híbrido no menu, o app descobre o IP via cabo.
3.  O app executa o comando `adb connect [IP]:5555`.
4.  O `FuriousMirror` recebe o sinal de sucesso e sinaliza para o motor principal que o novo "serial" do dispositivo agora é o endereço IP.
5.  O stream é reiniciado automaticamente usando o novo caminho de rede.

## 4. Otimizações de Rede
Para compensar a instabilidade inerente do Wi-Fi:
- **Bitrate Adaptado**: O sistema trava em **6 Mbps** no Wi-Fi (contra 8 Mbps no cabo) para garantir que a banda do roteador não sature, reduzindo os *Dropped Frames*.
- **Keep-Alive**: O motor envia pacotes de "dummy bytes" periodicamente para garantir que a conexão TCP não entre em modo de espera (idle) pelo roteador.
