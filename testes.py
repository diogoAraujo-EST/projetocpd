import multiprocessing
import time
import random
from primos import is_prime, find_max_prime_sequential, find_max_prime_parallel
from game_of_life import game_of_life_sequential, game_of_life_parallel


def print_grelha(grelha):
    """Imprime a matriz linha a linha para ser fácil de visualizar."""
    for linha in grelha:
        print(linha)

def correr_todos_os_testes():
    print("="*50)
    print(" A INICIAR TESTES AUTOMÁTICOS DO PROJETO ")
    print("="*50)

    # ---------------------------------------------------------
    print("\n[TESTE 1] - Função is_prime()")
    print("O número 13 é primo? ->", is_prime(13))
    print("O número 15 é primo? ->", is_prime(15))

    # ---------------------------------------------------------
    print("\n[TESTE 2] - Primos (Versão Sequencial)")
    print("A procurar o maior primo durante 2 segundos...")
    primo_seq = find_max_prime_sequential(2)
    print("Resultado:", primo_seq)

    # ---------------------------------------------------------
    print("\n[TESTE 3] - Primos (Versão Paralela)")
    workers = multiprocessing.cpu_count()
    print(f"A procurar o maior primo durante 2 segundos com {workers} workers...")
    primo_par = find_max_prime_parallel(2, workers)
    print("Resultado:", primo_par)

    # ---------------------------------------------------------
    TAMANHO_GRELHA=500
    grelha_teste = [[random.choice([0,1]) for _ in range(TAMANHO_GRELHA)] for _ in range(TAMANHO_GRELHA)]
    GENERATION = 20
    
    print("\n[TESTE 4] - Game of Life (Versão Sequencial)")
    start_time = time.perf_counter()
    gol_seq, tempo_exec_seq = game_of_life_sequential(grelha_teste, GENERATION, return_time=True)
    print(f"Tempo de execução: {tempo_exec_seq:.6f}s")
    print("Grelha final:")
    print_grelha(gol_seq)

    # ---------------------------------------------------------
    print("\n[TESTE 5] - Game of Life (Versão Paralela)")
    start_time = time.perf_counter()
    gol_par, tempo_exec_par = game_of_life_parallel(grelha_teste, GENERATION, workers, return_time=True)
    print(f"Tempo de execução: {tempo_exec_par:.6f}s")
    print("Grelha final:")
    print_grelha(gol_par)

    print(f"[TESTE4] - Tempo de execução Sequencial: {tempo_exec_seq:.6f}s")
    print(f"[TESTE5] - Tempo de execução Paralela: {tempo_exec_par:.6f}s")

    print("\n" + "="*50)
    print(" TODOS OS TESTES FORAM EXECUTADOS COM SUCESSO! ")
    print("="*50 + "\n")


if __name__ == '__main__':
    # Necessário no Windows para o multiprocessing não dar erro
    multiprocessing.freeze_support()
    correr_todos_os_testes()