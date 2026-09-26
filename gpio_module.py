import RPi.GPIO as GPIO
import time

PIN_PWM = 12
PIN_DIR1 = 17
PIN_DIR2 = 27
PIN_ENC_A = 5
PIN_ENC_B = 6
PIN_CORTINA = 16
PIN_SENSOR = 11

posicao_encoder = 0
estado_motor_duty = 0.0
estado_motor_dir = 'livre'
pwm_motor = None
borda_entrada_sensor = None

def _callback_encoder_a(channel):
    global posicao_encoder
    estado_a = GPIO.input(PIN_ENC_A)
    estado_b = GPIO.input(PIN_ENC_B)
    if estado_a == estado_b:
        posicao_encoder += 1
    else:
        posicao_encoder -= 1
    if posicao_encoder % 10 == 0:
        print(f"\n[LOG ENCODER A] Pos: {posicao_encoder} | A:{estado_a} B:{estado_b}")

def _callback_encoder_b(channel):
    global posicao_encoder
    estado_a = GPIO.input(PIN_ENC_A)
    estado_b = GPIO.input(PIN_ENC_B)
    if estado_a != estado_b:
        posicao_encoder += 1
    else:
        posicao_encoder -= 1
    if posicao_encoder % 10 == 0:
        print(f"\n[LOG ENCODER B] Pos: {posicao_encoder} | A:{estado_a} B:{estado_b}")

def _callback_cortina(channel):
    estado = GPIO.input(PIN_CORTINA)
    if estado:
        print(f"\n[CORTINA] Obstrução detetada! (Pino {PIN_CORTINA} HIGH)")
    else:
        print(f"\n[CORTINA] Porta liberada! (Pino {PIN_CORTINA} LOW)")

def _callback_sensor(channel):
    global borda_entrada_sensor, posicao_encoder
    estado = GPIO.input(PIN_SENSOR)
    if estado:
        borda_entrada_sensor = posicao_encoder
        print(f"\n[SENSOR] Entrou na bandeirola (Pino {PIN_SENSOR} HIGH). Posição: {posicao_encoder}")
    else:
        borda_saida = posicao_encoder
        print(f"\n[SENSOR] Saiu da bandeirola (Pino {PIN_SENSOR} LOW). Posição: {borda_saida}")
        if borda_entrada_sensor is not None:
            centro = (borda_entrada_sensor + borda_saida) / 2
            andar_estimado = round(centro / 3000) * 3000
            erro = centro - andar_estimado
            print(f"[SENSOR] Centro estimado: {centro} | Erro: {erro}")
        borda_entrada_sensor = None

def inicializar_hardware():
    global pwm_motor
    print("[LOG HARDWARE] Configurando modo BCM...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    print(f"[LOG HARDWARE] Configurando pinos de saída: DIR1({PIN_DIR1}), DIR2({PIN_DIR2}), PWM({PIN_PWM})")
    GPIO.setup(PIN_DIR1, GPIO.OUT)
    GPIO.setup(PIN_DIR2, GPIO.OUT)
    GPIO.setup(PIN_PWM, GPIO.OUT)
    print(f"[LOG HARDWARE] Configurando pinos de entrada: ENC_A({PIN_ENC_A}), ENC_B({PIN_ENC_B}), CORTINA({PIN_CORTINA}), SENSOR({PIN_SENSOR})")
    GPIO.setup(PIN_ENC_A, GPIO.IN)
    GPIO.setup(PIN_ENC_B, GPIO.IN)
    GPIO.setup(PIN_CORTINA, GPIO.IN)
    GPIO.setup(PIN_SENSOR, GPIO.IN)
    print("[LOG HARDWARE] Inicializando PWM a 1000Hz...")
    pwm_motor = GPIO.PWM(PIN_PWM, 1000)
    pwm_motor.start(0)
    print("[LOG HARDWARE] Adicionando detecção de eventos (callbacks)...")
    GPIO.add_event_detect(PIN_ENC_A, GPIO.BOTH, callback=_callback_encoder_a)
    GPIO.add_event_detect(PIN_ENC_B, GPIO.BOTH, callback=_callback_encoder_b)
    GPIO.add_event_detect(PIN_CORTINA, GPIO.BOTH, callback=_callback_cortina, bouncetime=200)
    GPIO.add_event_detect(PIN_SENSOR, GPIO.BOTH, callback=_callback_sensor)
    acionar_motor('livre', 0)
    print("[LOG HARDWARE] Hardware inicializado com sucesso.")

def acionar_motor(direcao, duty):
    global estado_motor_duty, estado_motor_dir, pwm_motor
    if direcao != estado_motor_dir or duty != estado_motor_duty:
        print(f"[LOG MOTOR] Comando: Direção={direcao} | Duty={duty:.2f}%")
    if direcao == 'livre':
        GPIO.output(PIN_DIR1, GPIO.LOW)
        GPIO.output(PIN_DIR2, GPIO.LOW)
        print("[LOG PINOS] DIR1=LOW, DIR2=LOW")
    elif direcao == 'subir':
        GPIO.output(PIN_DIR1, GPIO.HIGH)
        GPIO.output(PIN_DIR2, GPIO.LOW)
        print("[LOG PINOS] DIR1=HIGH, DIR2=LOW")
    elif direcao == 'descer':
        GPIO.output(PIN_DIR1, GPIO.LOW)
        GPIO.output(PIN_DIR2, GPIO.HIGH)
        print("[LOG PINOS] DIR1=LOW, DIR2=HIGH")
    elif direcao == 'freio':
        GPIO.output(PIN_DIR1, GPIO.HIGH)
        GPIO.output(PIN_DIR2, GPIO.HIGH)
        print("[LOG PINOS] DIR1=HIGH, DIR2=HIGH")
    if pwm_motor is not None:
        pwm_motor.ChangeDutyCycle(duty)
        print(f"[LOG PWM] ChangeDutyCycle({duty}) executado.")
    estado_motor_duty = duty
    estado_motor_dir = direcao

def parar_elevador():
    print("[LOG SISTEMA] Função parar_elevador() chamada.")
    acionar_motor('freio', 0)

def limpar_gpio():
    print("[LOG SISTEMA] Função limpar_gpio() chamada.")
    if pwm_motor is not None:
        pwm_motor.stop()
        print("[LOG PWM] PWM parado.")
    GPIO.cleanup()
    print("[LOG GPIO] GPIO.cleanup() executado.")

def obter_posicao_encoder():
    global posicao_encoder
    return posicao_encoder

def obter_estado_cortina():
    return GPIO.input(PIN_CORTINA) == GPIO.HIGH

def obter_estado_sensor_andar():
    return GPIO.input(PIN_SENSOR) == GPIO.HIGH

def obter_estado_motor():
    global estado_motor_duty, estado_motor_dir
    return estado_motor_duty, estado_motor_dir