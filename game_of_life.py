import time
import multiprocessing

# Esta função é um bloco de construção fundamental para o Game of Life.
# Dada uma grelha e as coordenadas de uma célula, ela "olha" para os 8
# vizinhos e conta quantos estão vivos (valor 1).
def count_live_neighbors(grid, r, c, rows, cols):
    """Conta o número de vizinhos vivos de uma célula (r, c)."""
    live_count = 0
    # Otimização: Em vez de usar 'try/except' para as bordas, calculamos
    # os limites seguros para o loop. Garante que nunca tentamos aceder a uma
    # posição que não existe na matriz (ex: índice -1).
    r_start = max(0, r - 1)
    r_end = min(rows, r + 2)
    c_start = max(0, c - 1)
    c_end = min(cols, c + 2)

    for i in range(r_start, r_end):
        for j in range(c_start, c_end):
            # A condição `(i, j) != (r, c)` é crucial para não contarmos a própria célula.
            if (i, j) != (r, c): 
                live_count += grid[i][j]
    return live_count

# =====================================================================
# ABORDAGEM SEQUENCIAL
# =====================================================================
def game_of_life_sequential(grid, generations, return_time=False):
    # Guardamos o tempo inicial para medir a performance.
    start_time = time.perf_counter()
    
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    current_grid = grid

    # O loop principal que avança as gerações.
    for _ in range(generations):
        # Criamos uma grelha nova, vazia, para guardar o estado da próxima geração.
        # É fundamental não alterar a grelha atual enquanto a estamos a ler!
        next_grid = [[0 for _ in range(cols)] for _ in range(rows)]
        # Percorremos cada célula da grelha atual.
        for r in range(rows):
            for c in range(cols):
                neighbors = count_live_neighbors(current_grid, r, c, rows, cols)
                cell = current_grid[r][c]
                
                # --- Aplicação das 4 Regras do Game of Life ---
                if cell == 1 and neighbors in (2, 3):
                    next_grid[r][c] = 1 # Sobrevivência
                elif cell == 0 and neighbors == 3:
                    next_grid[r][c] = 1 # Nascimento
                else:
                    next_grid[r][c] = 0 # Morte (Solidão ou Superpopulação)
                    
        # A nova grelha passa a ser a grelha atual para a próxima iteração.
        current_grid = next_grid
    
    # Calculamos o tempo total que a função demorou a executar.
    elapsed_time = time.perf_counter() - start_time
    
    # Se quem chamou a função pediu o tempo, devolvemos a grelha E o tempo.
    if return_time:
        return current_grid, elapsed_time
    
    # Caso contrário, devolvemos só a grelha (comportamento padrão).
    return current_grid

# =====================================================================
# ABORDAGEM PARALELA
# =====================================================================
# Esta é a função que cada processo (worker) vai executar.
def _compute_chunk_next_gen(args):
    """Função do worker para calcular a sua parte da grelha."""
    # Desempacotamos os argumentos que recebemos.
    chunk, has_top_ghost, has_bottom_ghost = args
    rows = len(chunk)
    cols = len(chunk[0])
    
    # Lógica para descobrir quais são as linhas "reais" deste worker,
    # ignorando as linhas "fantasma" que são só para leitura.
    start_idx = 1 if has_top_ghost else 0
    end_idx = rows - 1 if has_bottom_ghost else rows
    
    # A lógica de cálculo aqui dentro é idêntica à da versão sequencial,
    # mas aplicada apenas ao seu pequeno pedaço da grelha.
    new_chunk = []
    for r in range(start_idx, end_idx):
        new_row = []
        for c in range(cols):
            neighbors = count_live_neighbors(chunk, r, c, rows, cols)
            cell = chunk[r][c]
            
            if cell == 1 and neighbors in (2, 3):
                new_row.append(1)
            elif cell == 0 and neighbors == 3:
                new_row.append(1)
            else:
                new_row.append(0)
        new_chunk.append(new_row)
    return new_chunk

def game_of_life_parallel(grid, generations, workers, return_time=False):
    start_time = time.perf_counter()

    rows = len(grid)
    # Proteção para o caso de uma grelha vazia.
    if rows == 0: 
        return (grid, 0.0) if return_time else grid
    current_grid = grid
    
    # Criamos o 'Pool' de processos fora do loop das gerações.
    # Isto é uma otimização crucial: criar processos é uma operação "cara",
    # por isso fazemo-lo apenas uma vez e reutilizamos os workers.
    with multiprocessing.Pool(processes=workers) as pool:
        for _ in range(generations):
            # --- Divisão da Grelha ---
            chunk_size = max(1, rows // workers) # Tamanho de cada fatia.
            tasks = []
            
            # Divide a grelha em fatias e prepara os argumentos para cada worker.
            for i in range(workers):
                start_row = i * chunk_size
                end_row = rows if i == workers - 1 else (i + 1) * chunk_size
                if start_row >= rows: continue
                
                # --- Gestão de Fronteiras com "Ghost Rows" ---
                # Verificamos se esta fatia precisa da linha do vizinho de cima ou de baixo.
                has_top_ghost = start_row > 0
                has_bottom_ghost = end_row < rows
                
                # Definimos o bloco real a enviar, incluindo as "linhas fantasma".
                chunk_start = start_row - 1 if has_top_ghost else start_row
                chunk_end = end_row + 1 if has_bottom_ghost else end_row
                
                chunk = current_grid[chunk_start:chunk_end]
                tasks.append((chunk, has_top_ghost, has_bottom_ghost))
            
            # --- Execução Paralela e Sincronização ---
            # `pool.map` envia cada tarefa para um worker e espera que TODOS acabem.
            # Isto funciona como uma "barreira de sincronização", garantindo que não
            # avançamos para a próxima geração antes de a atual estar completamente calculada.
            results = pool.map(_compute_chunk_next_gen, tasks)
            
            # Juntamos os pedaços (resultados) de volta numa única grelha.
            current_grid = [row for res_chunk in results for row in res_chunk]
                
    elapsed_time = time.perf_counter() - start_time
    if return_time:
        return current_grid, elapsed_time
    return current_grid

# =====================================================================
# FUNÇÃO AUXILIAR DE PRINT
# =====================================================================
def print_grid_simples(grid, titulo):
    """Função simples para imprimir a grelha no terminal de forma legível."""
    print(f"\n{titulo}")
    for row in grid:
        print(row)

# =====================================================================
# BLOCO DE TESTE
# =====================================================================
if __name__ == '__main__':
    # Grelha de teste pequena (5x5) com o padrão "Blinker" para ser fácil de verificar.
    grelha_inicial = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]

    GENERATION = 4
    WORKERS = multiprocessing.cpu_count()
    
    # --- Teste Sequencial ---
    print("=== TESTE SEQUENCIAL (Imprimindo geração a geração) ===")
    estado_seq = grelha_inicial
    print_grid_simples(grelha_inicial, "Geração 0 (Inicial):")
    
    # Ciclo exterior para podermos imprimir o estado a cada passo.
    for gen in range(1, GENERATION + 1):
        # Chamamos a função para avançar apenas UMA geração de cada vez.
        estado_seq, tempo_passo = game_of_life_sequential(estado_seq, 1, return_time=True)
        print_grid_simples(estado_seq, f"Geração {gen}: (demorou {tempo_passo:.6f}s)")
    
    # --- Teste Paralelo ---
    print("\n\n=== TESTE PARALELO (Imprimindo geração a geração) ===")
    estado_par = grelha_inicial
    print_grid_simples(estado_par, "Geração 0 (Inicial):")
    
    for gen in range(1, GENERATION + 1):
        estado_par, tempo_passo = game_of_life_parallel(estado_par, 1, WORKERS, return_time=True)
        print_grid_simples(estado_par, f"Geração {gen}: (demorou {tempo_passo:.6f}s)")
    
    # --- Validação Final ---
    print("\nAs matrizes finais são iguais?")
    print(estado_seq == estado_par)