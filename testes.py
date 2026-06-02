import multiprocessing
import time
import random
import threading

# Importar as funções desenvolvidas nas Componentes 1 e 2
from primos import is_prime, find_max_prime_sequential, find_max_prime_parallel
from game_of_life import game_of_life_sequential, game_of_life_parallel
from servidor import iniciar_servidor
from cliente import enviar_pedido_rpc 

# =====================================================================
# FUNÇÃO AUXILIAR DE PRINT
# =====================================================================
def print_grelha_inteligente(grelha, titulo=""):
    """
    Imprime a matriz linha a linha para ser fácil de visualizar.
    No entanto, se a matriz for demasiado grande (ex: 500x500), omite o 
    output visual para não bloquear/inundar o terminal do utilizador.
    """
    if titulo:
        print(f"{titulo}")
        
    linhas = len(grelha)
    if linhas == 0:
        return
        
    colunas = len(grelha[0])
    
    # Se a matriz tiver mais de 15 linhas ou colunas, é considerada 'gigante'
    if linhas > 15 or colunas > 15:
        print(f"   [Grelha gigante de {linhas}x{colunas} omitida visualmente do ecrã para poupar recursos]")
    else:
        for linha in grelha:
            print("   ", linha)

# =====================================================================
# FUNÇÃO PRINCIPAL DE TESTES
# =====================================================================
def correr_todos_os_testes():
    print("="*60)
    print(" A INICIAR TESTES AUTOMÁTICOS DO PROJETO ")
    print("="*60)

    # ---------------------------------------------------------
    # TESTE 1: Validação básica da função de primalidade
    # ---------------------------------------------------------
    print("\n[TESTE 1] - Função is_prime()")
    print("O número 13 é primo? ->", is_prime(13))
    print("O número 15 é primo? ->", is_prime(15))

    # ---------------------------------------------------------
    # TESTE 2: Primos (Sequencial)
    # ---------------------------------------------------------
    print("\n[TESTE 2] - Primos (Versão Sequencial)")
    print("A procurar o maior primo durante 2 segundos...")
    primo_seq = find_max_prime_sequential(2)
    print("Resultado:", primo_seq)

    # ---------------------------------------------------------
    # TESTE 3: Primos (Paralelo)
    # ---------------------------------------------------------
    print("\n[TESTE 3] - Primos (Versão Paralela)")
    # Usa o número máximo de núcleos lógicos disponíveis no CPU
    workers = multiprocessing.cpu_count() 
    print(f"A procurar o maior primo durante 2 segundos com {workers} workers...")
    primo_par = find_max_prime_parallel(2, workers)
    print("Resultado:", primo_par)

    # ---------------------------------------------------------
    # PREPARAÇÃO PARA O GAME OF LIFE
    # ---------------------------------------------------------
    TAMANHO_GRELHA = 500
    GENERATION = 20
    # Gera uma matriz 500x500 com 0s e 1s aleatórios
    grelha_teste = [[random.choice([0,1]) for _ in range(TAMANHO_GRELHA)] for _ in range(TAMANHO_GRELHA)]
    
    # ---------------------------------------------------------
    # TESTE 4: Game of Life (Sequencial)
    # ---------------------------------------------------------
    print(f"\n[TESTE 4] - Game of Life (Versão Sequencial - {TAMANHO_GRELHA}x{TAMANHO_GRELHA})")
    print("A processar, aguarde...")
    gol_seq, tempo_exec_seq = game_of_life_sequential(grelha_teste, GENERATION, return_time=True)
    print_grelha_inteligente(gol_seq, "Grelha final:")

    # ---------------------------------------------------------
    # TESTE 5: Game of Life (Paralelo)
    # ---------------------------------------------------------
    print(f"\n[TESTE 5] - Game of Life (Versão Paralela - {TAMANHO_GRELHA}x{TAMANHO_GRELHA})")
    print(f"A processar com {workers} workers, aguarde...")
    gol_par, tempo_exec_par = game_of_life_parallel(grelha_teste, GENERATION, workers, return_time=True)
    print_grelha_inteligente(gol_par, "Grelha final:")

    # --- Resumo de Performance e Validação (GoL) ---
    print("\n--- RESUMO DE PERFORMANCE E VALIDAÇÃO (GAME OF LIFE) ---")
    print(f"[TESTE 4] - Tempo de execução Sequencial: {tempo_exec_seq:.6f}s")
    print(f"[TESTE 5] - Tempo de execução Paralela: {tempo_exec_par:.6f}s")
    
    if tempo_exec_par < tempo_exec_seq:
        speedup = tempo_exec_seq / tempo_exec_par
        print(f"Speedup: {speedup:.2f}x (Paralelo foi mais rápido!)")
    else:
        print("Aviso: Paralelo foi mais lento (para grelhas pequenas o overhead supera o ganho).")
        
    if gol_seq == gol_par:
        print("[SUCESSO] As matrizes finais coincidem! A lógica paralela está correta.")
    else:
        print("[ERRO] As matrizes finais são diferentes! Erro na gestão de fronteiras.")

    # ---------------------------------------------------------
    # TESTE 6: SISTEMA DISTRIBUÍDO (RPC)
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[TESTE 6] - SISTEMA DISTRIBUÍDO (RPC / Sockets)")
    print("="*60)
    
    # Inicia o servidor numa thread secundária. A tua porta 8000 será usada.
    print(">> A iniciar o Servidor em background na porta 8000...")
    thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    thread_servidor.start()
    
    # Dá 1 segundo para garantir que o socket fez o bind() antes do cliente atacar
    time.sleep(1) 
    
    # Teste 6.1: Lista de métodos
    print("\n>> CLIENTE: Pedir lista de métodos ao servidor (list_methods)")
    # ATUALIZADO: Chama a tua função enviar_pedido_rpc
    resposta_metodos = enviar_pedido_rpc("list_methods", {})
    if "result" in resposta_metodos:
        print(f"   [OK] O Servidor devolveu {len(resposta_metodos['result'])} métodos.")
    else:
        print(f"   [ERRO] Falha ao obter métodos: {resposta_metodos}")
        
    # Teste 6.2: Invocar um método real remotamente
    print("\n>> CLIENTE: Perguntar se 17 é primo (is_prime)")
    resposta_primo = enviar_pedido_rpc("is_prime", {"n": 17})
    print(f"   Resposta bruta do servidor: {resposta_primo}")
    if resposta_primo.get("result") is True:
        print("   [OK] Cálculo remoto correto.")
    
    # Teste 6.3: Validar a robustez do servidor (enviar lixo)
    print("\n>> CLIENTE: Tentar executar método que não existe")
    resposta_erro = enviar_pedido_rpc("método_inexistente", {})
    print(f"   Resposta do servidor a rejeitar o erro: {resposta_erro}")


    print("\n" + "="*60)
    print(" TODOS OS TESTES FORAM EXECUTADOS COM SUCESSO! ")
    print("="*60 + "\n")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    correr_todos_os_testes()