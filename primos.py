"""
Módulo primos.py
Implementação das funções de procura de números primos (sequencial e paralela).
Ponto 3.1 do guião do trabalho prático.
"""

import time
import multiprocessing as mp


# 3.1.1. "Função para verificação de primalidade"
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


# 3.1.3. Funções a implementar - Versão Sequencial
def find_max_prime_sequential(timeout: int) -> int:
    """
    Procura o maior número primo possível durante 'timeout' segundos,
    usando ubordagem sequencial contínua
    :param timeout: Limite temporal em segundos.
    :return: O maior número primo encontrado.
    """
    start_time = time.time()
    max_prime = -1
    current_number = 2

    # Executa até que a diferença entre o tempo atual e o tempo inicial atinja o timeout
    while (time.time() - start_time) < timeout:
        if is_prime(current_number):
            max_prime = current_number
        current_number += 1

    return max_prime


# Lógica Auxiliar para a Versão Paralela (O Worker)
def _prime_worker(start_num: int, step: int, timeout: int, start_time: float, global_max: mp.Value, lock: mp.Lock):
    """
    Lógica executada por cada processo worker.
    Utiliza uma estratégia de "Interleaving" (divisão intercalada) para garantir
    que os processos não verificam os mesmos números.
    """
    current_number = start_num
    local_max = -1

    # O worker verifica os números atribuídos a ele até o tempo acabar
    while (time.time() - start_time) < timeout:
        if is_prime(current_number):
            local_max = current_number
        current_number += step  # Salta o número de workers para o próximo candidato

    # Sincronização: Terminada a procura temporal, atualiza o resultado global partilhado.
    # O uso do lock previne condições de corrida (race conditions) entre workers.
    if local_max > -1:
        with lock:
            if local_max > global_max.value:
                global_max.value = local_max



# 3.1.3. Funções a implementar - Versão Paralela
def find_max_prime_parallel(timeout: int, workers: int) -> int:
    """
    Procura o maior número primo possível durante 'timeout' segundos,
    recorrendo à execução paralela de múltiplos workers.

    :param timeout: Limite temporal em segundos.
    :param workers: Número de processos paralelos a criar.
    :return: O maior número primo encontrado de entre todos os workers.
    """
    start_time = time.time()

    # Estruturas de dados partilhadas com sincronização
    # mp.Value('q', -1) cria um inteiro partilhado (long long) iniciado a -1
    global_max = mp.Value('q', -1)
    lock = mp.Lock()

    processes = []

    # Criação e arranque dos workers
    for i in range(workers):
        """
        Estratégia de divisão do espaço de procura:
        Se workers = 4:
        Worker 0: testa 2, 6, 10, 14...
        Worker 1: testa 3, 7, 11, 15...
        Worker 2: testa 4, 8, 12, 16...
        """
        start_num = 2 + i
        step = workers

        p = mp.Process(target=_prime_worker, args=(start_num, step, timeout, start_time, global_max, lock))
        processes.append(p)
        p.start()

    # Termina coordenada: o processo principal aguarda que todos os workers terminem
    for p in processes:
        p.join()

    return global_max.value


# =====================================================================
# Testes
# =====================================================================
if __name__ == "__main__":
    TEMPO_LIMITE = 3  # Testar 3 segundos
    NUM_WORKERS = 5  # Quantidade de processos paralelos

    print(f"A iniciar teste SEQUENCIAL ({TEMPO_LIMITE} segundos)...")
    resultado_seq = find_max_prime_sequential(TEMPO_LIMITE)
    print(f"Maior primo encontrado (Sequencial): {resultado_seq}")

    print("-" * 40)

    print(f"A iniciar teste PARALELO ({TEMPO_LIMITE} segundos com {NUM_WORKERS} workers)...")
    resultado_par = find_max_prime_parallel(TEMPO_LIMITE, NUM_WORKERS)
    print(f"Maior primo encontrado (Paralelo): {resultado_par}")

    print("-" * 40)
    print("Conclusão:")
    if resultado_par > resultado_seq:
        print("O método paralelo encontrou um número maior no mesmo tempo! (Sucesso)")
    else:
        print(
            "O método sequencial foi igual ou melhor.") # pode acontecer em CPUs mais fracos ou com tempos muito curtos, isto faz diferença