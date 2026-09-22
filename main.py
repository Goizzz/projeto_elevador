import time
import signal
import sys
import gpio_module as gpio

def tratar_sigint(signum, frame):
    print("\n[AVISO] Encerrando o programa com segurança...")
    gpio.parar_elevador()
    gpio.limpar_gpio()
    sys.exit(0)

def imprimir_estado():
    pos_pulsos = gpio.obter_posicao_encoder()
    pos_mm = pos_pulsos
    cortina = gpio.obter_estado_cortina()
    sensor = gpio.obter_estado_sensor_andar()
    duty_atual, dir_atual = gpio.obter_estado_motor()
    
    print("\n--- ESTADO ATUAL (CABINE 1) ---")
    print(f"Posição: {pos_pulsos} pulsos ({pos_mm} mm)")
    print(f"Motor: Direção '{dir_atual}' a {duty_atual}% de potência")
    print(f"Cortina de Luz: {'Obstruída' if cortina else 'Livre'}")
    print(f"Sensor de Andar: {'Ativo (Na bandeirola)' if sensor else 'Inativo'}")
    print("-------------------------------\n")

def menu_acionamento_direto():
    print("\n--- ACIONAMENTO DIRETO ---")
    direcao = input("Direção (livre|subir|descer|freio): ").strip().lower()
    if direcao not in ['livre', 'subir', 'descer', 'freio']:
        print("Direção inválida!")
        return
        
    try:
        duty = float(input("Duty cycle (0 a 100): "))
        if duty < 0 or duty > 100:
            print("O duty cycle deve estar entre 0 e 100!")
            return
    except ValueError:
        print("Valor numérico inválido!")
        return
    
    gpio.acionar_motor(direcao, duty)
    print(f"Comando enviado: Motor em modo '{direcao}' com {duty}%.")

def menu_chamar_elevador():
    try:
        andar = int(input("\nDigite o andar de destino (0, 1 ou 2): "))
        if andar not in [0, 1, 2]:
            print("Andar inválido! O modelo reduzido possui andares 0, 1 e 2.")
            return
    except ValueError:
        print("Entrada inválida!")
        return
    
    posicoes_nominais = {0: 0, 1: 3000, 2: 6000}
    alvo_pulsos = posicoes_nominais[andar]
    pos_inicial = gpio.obter_posicao_encoder()
    
    if abs(alvo_pulsos - pos_inicial) <= 10:
        print("A cabine já está nivelada neste andar.")
        return

    print(f"Iniciando movimento para o Andar {andar} (Alvo: {alvo_pulsos} pulsos)...")
    
    duty_min = 15.0
    duty_max = 100.0
    zona_aceleracao = 600
    zona_desaceleracao = 800
    tolerancia = 10

    while True:
        pos_atual = gpio.obter_posicao_encoder()
        erro = alvo_pulsos - pos_atual
        distancia_percorrida = abs(pos_atual - pos_inicial)
        
        if pos_atual < -50 or pos_atual > 6050:
            gpio.acionar_motor('freio', 0)
            print("\n[ERRO] Fim de curso atingido! Parada de emergência.")
            break
            
        if abs(erro) <= tolerancia:
            gpio.acionar_motor('freio', 0)
            print(f"\nDestino alcançado! Posição final: {pos_atual} pulsos.")
            break
            
        direcao = 'subir' if erro > 0 else 'descer'
        
        if distancia_percorrida < zona_aceleracao:
            fator = distancia_percorrida / zona_aceleracao
            duty = duty_min + (duty_max - duty_min) * fator
        elif abs(erro) < zona_desaceleracao:
            fator = abs(erro) / zona_desaceleracao
            duty = duty_min + (duty_max - duty_min) * fator
        else:
            duty = duty_max
            
        duty = max(duty_min, min(duty_max, duty))
        
        gpio.acionar_motor(direcao, duty)
        time.sleep(0.02)

def main():
    signal.signal(signal.SIGINT, tratar_sigint)
    
    print("Inicializando sistema GPIO...")
    gpio.inicializar_hardware()

    while True:
        print("\n=== CONTROLE DO ELEVADOR ===")
        print("1. Chamar elevador para um andar (Malha Fechada)")
        print("2. Acionamento direto do motor (Malha Aberta)")
        print("3. Ver estado atual dos sensores e posição")
        print("0. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == '1':
            menu_chamar_elevador()
        elif opcao == '2':
            menu_acionamento_direto()
        elif opcao == '3':
            imprimir_estado()
        elif opcao == '0':
            tratar_sigint(None, None)
        else:
            print("Opção inválida.")
        
        time.sleep(0.1)

if __name__ == '__main__':
    main()