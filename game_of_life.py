import time
import multiprocessing

def count_live_neighbors(grid, r, c, rows, cols):
    """Conta o número de vizinhos vivos de uma célula (r, c)."""
    live_count = 0
    # Limites para não sair fora da grelha (grelha não cíclica)
    r_start = max(0, r - 1)
    r_end = min(rows, r + 2)
    c_start = max(0, c - 1)
    c_end = min(cols, c + 2)

    for i in range(r_start, r_end):
        for j in range(c_start, c_end):
            if (i, j) != (r, c): 
                live_count += grid[i][j]
    return live_count

# =====================================================================
# ABORDAGEM SEQUENCIAL
# =====================================================================
def game_of_life_sequential(grid, generations):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    current_grid = grid

    for _ in range(generations):
        next_grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                neighbors = count_live_neighbors(current_grid, r, c, rows, cols)
                cell = current_grid[r][c]
                
                if cell == 1 and neighbors in (2, 3):
                    next_grid[r][c] = 1
                elif cell == 0 and neighbors == 3:
                    next_grid[r][c] = 1
                else:
                    next_grid[r][c] = 0
                    
        current_grid = next_grid

    return current_grid

# =====================================================================
# ABORDAGEM PARALELA
# =====================================================================
def _compute_chunk_next_gen(args):
    """Função do worker para calcular a sua parte da grelha."""
    chunk, has_top_ghost, has_bottom_ghost = args
    rows = len(chunk)
    cols = len(chunk[0])
    
    start_idx = 1 if has_top_ghost else 0
    end_idx = rows - 1 if has_bottom_ghost else rows
    
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

def game_of_life_parallel(grid, generations, workers):
    rows = len(grid)
    if rows == 0: return grid
    current_grid = grid
    
    with multiprocessing.Pool(processes=workers) as pool:
        for _ in range(generations):
            chunk_size = max(1, rows // workers)
            tasks = []
            
            # Divide a grelha e adiciona as linhas vizinhas (ghost rows)
            for i in range(workers):
                start_row = i * chunk_size
                end_row = rows if i == workers - 1 else (i + 1) * chunk_size
                if start_row >= rows: continue
                
                has_top_ghost = start_row > 0
                has_bottom_ghost = end_row < rows
                
                chunk_start = start_row - 1 if has_top_ghost else start_row
                chunk_end = end_row + 1 if has_bottom_ghost else end_row
                
                chunk = current_grid[chunk_start:chunk_end]
                tasks.append((chunk, has_top_ghost, has_bottom_ghost))
            
            # Sincroniza e junta os pedaços
            results = pool.map(_compute_chunk_next_gen, tasks)
            current_grid = [row for res_chunk in results for row in res_chunk]
                
    return current_grid

# =====================================================================
# FUNÇÃO AUXILIAR DE PRINT
# =====================================================================
def print_grid_simples(grid, titulo):
    print(f"\n{titulo}")
    for row in grid:
        print(row)

# =====================================================================
# BLOCO DE TESTE
# =====================================================================
if __name__ == '__main__':
    # Pequena grelha 5x5 com um "Blinker" (padrão que roda a cada geração)
    grelha_inicial = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    
    WORKERS = 2
    
    # ---------------------------------------------------------
    # TESTE SEQUENCIAL
    # ---------------------------------------------------------
    print("=== TESTE SEQUENCIAL (Imprimindo geração a geração) ===")
    estado_seq = grelha_inicial
    print_grid_simples(estado_seq, "Geração 0 (Inicial):")
    
    # Fazemos um ciclo de fora para podermos imprimir o estado intermédio
    for gen in range(1, 4):
        # Avança 1 geração de cada vez
        estado_seq = game_of_life_sequential(estado_seq, 1)
        print_grid_simples(estado_seq, f"Geração {gen}:")
    
    
    # ---------------------------------------------------------
    # TESTE PARALELO
    # ---------------------------------------------------------
    print("\n\n=== TESTE PARALELO (Imprimindo geração a geração) ===")
    estado_par = grelha_inicial
    print_grid_simples(estado_par, "Geração 0 (Inicial):")
    
    # Fazemos o mesmo para o paralelo
    for gen in range(1, 4):
        # Avança 1 geração de cada vez
        estado_par = game_of_life_parallel(estado_par, 1, WORKERS)
        print_grid_simples(estado_par, f"Geração {gen}:")
        
    
    # ---------------------------------------------------------
    # VALIDAÇÃO FINAL
    # ---------------------------------------------------------
    print("\nAs matrizes finais são iguais?")
    print(estado_seq == estado_par)