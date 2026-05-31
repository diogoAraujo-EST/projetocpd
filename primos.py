import time
import multiprocessing

# =====================================================================
# FUNÇÃO OBRIGATÓRIA (NÃO ALTERAR)
# =====================================================================

# Esta função foi fornecida no guião e, por regra, não pode ser alterada.
# É uma função otimizada para verificar se um número é primo.
def is_prime(n: int) -> bool:
    # Primos são números maiores que 1.
    if n < 2:
        return False
    # Casos especiais: 2 e 3 são primos.
    if n in (2, 3):
        return True
    # Otimização: Se for divisível por 2 ou 3, não é primo.
    # Isto permite-nos saltar muitos números na verificação.
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Começamos a testar a partir do 5.
    divisor = 5
    # Otimização: Só precisamos de testar divisores até à raiz quadrada de 'n'.
    while divisor * divisor <= n:
        # Outra otimização: Todos os primos (exceto 2 e 3) são da forma 6k ± 1.
        # Por isso, só testamos os divisores que estão perto de múltiplos de 6.
        if n % divisor == 0 or n % (divisor + 2) == 0:
            return False
        divisor += 6
        
    return True


# =====================================================================
# COMPONENTE SEQUENCIAL
# =====================================================================

def find_max_prime_sequential(timeout: int) -> int:
    """
    Procura o maior número primo possível durante, no máximo, `timeout` segundos,
    utilizando uma abordagem sequencial.
    A pesquisa é contínua a partir do número 2 até o tempo acabar.
    """
    # Guarda o momento exato em que a função começou, para podermos controlar o tempo.
    start_time = time.perf_counter()
    
    # Variáveis para guardar o maior primo encontrado e o número que estamos a testar.
    max_prime = -1
    current = 2

    # Loop "infinito" que só vai ser interrompido quando o tempo esgotar.
    while True:
        # Otimização de performance: Em vez de verificar o relógio a cada número
        # (o que seria muito lento), testamos os números em "blocos" de 1000.
        for _ in range(1000):
            if is_prime(current):
                max_prime = current # Se for primo, atualizamos o nosso recorde.
            current += 1 # Passamos para o próximo número.
            
        # A cada 1000 números testados, verificamos se o tempo limite já passou.
        if time.perf_counter() - start_time >= timeout:
            break # Se o tempo acabou, saímos do loop.

    return max_prime


# =====================================================================
# COMPONENTE PARALELA
# =====================================================================

# Esta é a função que cada processo (worker) vai executar em paralelo.
def _parallel_worker(stop_event, global_counter, global_max, lock, chunk_size):
    """
    Função executada por cada worker. Pede um intervalo de pesquisa, 
    pesquisa do FIM para o INÍCIO desse intervalo, atualiza o maior
    primo e salta para o próximo intervalo.
    """
    # Cada processo continua a trabalhar enquanto a "bandeira" de paragem não for levantada.
    while not stop_event.is_set():
        # --- SECÇÃO CRÍTICA: Obter trabalho ---
        # Usamos o 'lock' (cadeado) para garantir que apenas UM processo de cada vez
        # mexe no contador global. Isto evita que dois processos peguem no mesmo bloco.
        with lock:
            # Pega no valor atual do contador global e guarda-o localmente.
            chunk_start = global_counter.value
            # Avança o contador global para o próximo bloco.
            global_counter.value += chunk_size
            
        chunk_end = chunk_start + chunk_size
        
        # --- Pesquisa Otimizada ---
        # Aqui está a grande otimização: em vez de procurar do início para o fim,
        # procuramos de TRÁS PARA A FRENTE (do número maior para o menor).
        # Assim, o primeiro primo que encontrarmos é garantidamente o maior deste bloco.
        for n in range(chunk_end - 1, chunk_start - 1, -1):
            
            # Verificação extra: se o tempo acabar enquanto estamos a meio do loop, paramos logo.
            if stop_event.is_set():
                break
                
            if is_prime(n):
                # --- SECÇÃO CRÍTICA: Atualizar resultado ---
                # Usamos o lock outra vez para garantir que a atualização do máximo é segura.
                # Evita que um processo escreva por cima do resultado de outro (race condition).
                with lock:
                    if n > global_max.value:
                        global_max.value = n
                
                # Como já encontrámos o maior primo deste bloco, não vale a pena continuar.
                # Quebramos o loop e vamos buscar um novo bloco de trabalho.
                break


def find_max_prime_parallel(timeout: int, workers: int) -> int:
    """
    Procura o maior número primo em tempo limitado usando múltiplos processos.
    Divide o espaço de procura em grandes fatias e procura em ordem decrescente
    dentro de cada fatia para acelerar a descoberta de números gigantes.
    """
    # --- Variáveis Partilhadas ---
    # `Value` cria uma variável que pode ser partilhada entre todos os processos.
    # 'q' significa que é um número inteiro grande (signed long long de 64-bit).
    global_counter = multiprocessing.Value('q', 0) # Contador para distribuir o trabalho.
    global_max = multiprocessing.Value('q', -1)     # Para guardar o maior primo encontrado.
    
    # Cria um 'cadeado' para proteger o acesso às variáveis partilhadas.
    lock = multiprocessing.Lock()
    # Cria um 'sinalizador' ou 'bandeira' para avisar todos os processos quando devem parar.
    stop_event = multiprocessing.Event()
    
    # Define o tamanho de cada 'fatia' de trabalho que um processo vai buscar.
    chunk_size = 200_000_000 
    
    # Lista para guardar os processos que vamos criar.
    processes = []
    
    # --- Arranque dos Workers ---
    # Cria e lança um processo para cada 'worker' (normalmente, o número de cores do CPU).
    for _ in range(workers):
        p = multiprocessing.Process(
            target=_parallel_worker, # A função que o processo vai executar.
            # Os argumentos que passamos à função do worker.
            args=(stop_event, global_counter, global_max, lock, chunk_size) 
        )
        processes.append(p)
        p.start() # Lança o processo. A partir daqui, ele começa a trabalhar em paralelo.

    # --- Controlo de Tempo e Terminação ---
    # O programa principal vai ficar aqui 'bloqueado' à espera durante 'timeout' segundos.
    stop_event.wait(timeout)
    
    # Passado o tempo, 'levanta a bandeira', sinalizando a todos os processos que devem parar.
    stop_event.set()

    # Espera que cada processo termine o que estava a fazer de forma organizada.
    # Isto garante que a atualização final do `global_max` é feita.
    for p in processes:
        p.join()

    # Devolve o valor final guardado na variável partilhada.
    return global_max.value


# =====================================================================
# BLOCO PARA TESTE DIRETO NO TERMINAL
# =====================================================================

# Este bloco de código só é executado quando corremos o ficheiro diretamente (`python primos.py`).
# É uma proteção essencial, especialmente no Windows, para garantir que os novos processos
# (criados pelo multiprocessing) não tentam re-executar este código de arranque,
# o que causaria um loop infinito de criação de processos.
if __name__ == '__main__':
    # Tempo em segundos para os testes.
    TEMPO_TESTE = 2
    # Usa todos os 'cores' (núcleos) disponíveis no teu computador como workers.
    NUM_WORKERS = multiprocessing.cpu_count()
    
    # --- Teste Sequencial ---
    print("-" * 50)
    print(f"A iniciar pesquisa SEQUENCIAL (Contínua) por {TEMPO_TESTE}s...")
    resultado_seq = find_max_prime_sequential(TEMPO_TESTE)
    print(f"Resultado Sequencial: {resultado_seq}")
    print(f"Algarismos: {len(str(resultado_seq))}")
    print("-" * 50)
    
    # --- Teste Paralelo ---
    print(f"A iniciar pesquisa PARALELA ({NUM_WORKERS} workers) por {TEMPO_TESTE}s...")
    print("A usar blocos de 200M com pesquisa invertida...")
    resultado_par = find_max_prime_parallel(TEMPO_TESTE, NUM_WORKERS)
    print(f"Resultado Paralelo: {resultado_par}")
    print(f"Algarismos: {len(str(resultado_par))}")
    print("-" * 50)