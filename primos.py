import time
import multiprocessing

# =====================================================================
# FUNÇÃO OBRIGATÓRIA (NÃO ALTERAR)
# =====================================================================
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    divisor = 5
    while divisor * divisor <= n:
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
    start_time = time.perf_counter()
    max_prime = -1
    current = 2

    while True:
        # Testar em blocos de 1000 para não sobrecarregar o CPU com 
        # chamadas à função do relógio em todas as iterações
        for _ in range(1000):
            if is_prime(current):
                max_prime = current
            current += 1
            
        # Terminação por tempo
        if time.perf_counter() - start_time >= timeout:
            break

    return max_prime


# =====================================================================
# COMPONENTE PARALELA
# =====================================================================
def _parallel_worker(stop_event, global_counter, global_max, lock, chunk_size):
    """
    Função executada por cada worker. Pede um intervalo de pesquisa, 
    pesquisa do FIM para o INÍCIO desse intervalo, atualiza o maior
    primo e salta para o próximo intervalo.
    """
    while not stop_event.is_set():
        # 1. Obter o próximo bloco de pesquisa de forma segura (Secção Crítica)
        with lock:
            chunk_start = global_counter.value
            global_counter.value += chunk_size
            
        chunk_end = chunk_start + chunk_size
        
        # 2. Pesquisar de TRÁS para a FRENTE (do maior para o menor)
        # O primeiro primo que encontrarmos é obrigatoriamente o maior deste bloco
        for n in range(chunk_end - 1, chunk_start - 1, -1):
            
            # Se o tempo acabar enquanto pesquisa, sai imediatamente
            if stop_event.is_set():
                break
                
            if is_prime(n):
                # 3. Atualizar o valor máximo global (Secção Crítica)
                with lock:
                    if n > global_max.value:
                        global_max.value = n
                # Como encontramos o maior deste bloco, não precisamos de testar mais
                # Quebramos o loop e vamos buscar o próximo bloco gigante
                break


def find_max_prime_parallel(timeout: int, workers: int) -> int:
    """
    Procura o maior número primo em tempo limitado usando múltiplos processos.
    Divide o espaço de procura em grandes fatias e procura em ordem decrescente
    dentro de cada fatia para acelerar a descoberta de números gigantes.
    """
    # 'q' cria um inteiro de 64-bits com sinal, suporta números com ~18 algarismos
    global_counter = multiprocessing.Value('q', 0)
    global_max = multiprocessing.Value('q', -1)
    
    lock = multiprocessing.Lock()
    stop_event = multiprocessing.Event()
    
    # Bloco de 200 milhões como falado no áudio
    chunk_size = 200_000_000 
    
    processes = []
    
    # 1. Criar e iniciar os Workers
    for _ in range(workers):
        p = multiprocessing.Process(
            target=_parallel_worker,
            args=(stop_event, global_counter, global_max, lock, chunk_size)
        )
        processes.append(p)
        p.start()

    # 2. Coordenação e Terminação (bloqueia o programa principal durante 'timeout')
    stop_event.wait(timeout)
    
    # 3. Sinalizar aos workers que o tempo acabou
    stop_event.set()

    # 4. Aguardar que todos terminem de forma limpa (Join)
    for p in processes:
        p.join()

    return global_max.value


# =====================================================================
# BLOCO PARA TESTE DIRETO NO TERMINAL
# =====================================================================
if __name__ == '__main__':
    # Valores de teste (Exemplo: 5 segundos)
    TEMPO_TESTE = 2
    NUM_WORKERS = multiprocessing.cpu_count()
    
    print("-" * 50)
    print(f"A iniciar pesquisa SEQUENCIAL (Contínua) por {TEMPO_TESTE}s...")
    resultado_seq = find_max_prime_sequential(TEMPO_TESTE)
    print(f"Resultado Sequencial: {resultado_seq}")
    print(f"Algarismos: {len(str(resultado_seq))}")
    print("-" * 50)
    
    print(f"A iniciar pesquisa PARALELA ({NUM_WORKERS} workers) por {TEMPO_TESTE}s...")
    print("Usando fatias de 200M com pesquisa invertida...")
    resultado_par = find_max_prime_parallel(TEMPO_TESTE, NUM_WORKERS)
    print(f"Resultado Paralelo: {resultado_par}")
    print(f"Algarismos: {len(str(resultado_par))}")
    print("-" * 50)