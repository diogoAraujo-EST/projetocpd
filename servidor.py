import socket
import threading
import json
import inspect
import multiprocessing

# --- Reutilização da Componente 1 ---
# Importamos explicitamente as duas versões de cada função para as podermos
# expor individualmente através do nosso sistema de RPC.
from primos import is_prime, find_max_prime_sequential, find_max_prime_parallel
from game_of_life import game_of_life_sequential, game_of_life_parallel

# =====================================================================
# WRAPPERS DAS FUNÇÕES PARA RPC
# =====================================================================
# Um "wrapper" é uma função que "embrulha" outra para simplificar ou adaptar
# a sua chamada. Aqui, usamos wrappers para que o cliente não precise de saber
# quantos 'workers' (núcleos de CPU) existem na máquina do servidor.

def find_max_prime_p(timeout: int):
    """(PARALELO) Procura o maior primo usando todos os cores do CPU."""
    # O servidor descobre automaticamente quantos núcleos tem e passa-os à função paralela.
    workers = multiprocessing.cpu_count()
    return find_max_prime_parallel(timeout, workers)

def game_of_life_p(grid: list, generations: int):
    """(PARALELO) Executa o Game of Life usando todos os cores do CPU."""
    workers = multiprocessing.cpu_count()
    # Chamamos a função paralela pedindo explicitamente que devolva o tempo de execução.
    final_grid, exec_time = game_of_life_parallel(grid, generations, workers, return_time=True)
    # Devolvemos um dicionário bem formatado para o cliente, com a grelha e o tempo.
    return {
        "grid": final_grid,
        "execution_time": f"{exec_time:.6f}s"
    }

def game_of_life_s(grid: list, generations: int):
    """(SEQUENCIAL) Executa o Game of Life numa única thread."""
    # A mesma lógica do wrapper paralelo, mas para a versão sequencial.
    final_grid, exec_time = game_of_life_sequential(grid, generations, return_time=True)
    return {
        "grid": final_grid,
        "execution_time": f"{exec_time:.6f}s"
    }

def list_methods():
    """Devolve a lista das operacoes disponiveis no servidor com introspecao."""
    metodos_disponiveis = []
    # A introspeção permite que o código "leia" a si mesmo em tempo de execução.
    # Aqui, usamos para construir uma lista de ajuda automática para o cliente.
    for nome, funcao in FUNCOES_RPC.items():
        # `inspect.signature` descobre quais os parâmetros que a função aceita.
        assinatura = inspect.signature(funcao)
        lista_params = list(assinatura.parameters.keys())
        # `__doc__` acede à 'docstring' (o comentário com aspas triplas) da função.
        descricao = funcao.__doc__ if funcao.__doc__ else "Sem descrição disponível."
        
        metodos_disponiveis.append({
            "nome": nome, "parametros": lista_params, "descricao": descricao.strip()
        })
    return metodos_disponiveis

# --- O Coração do Servidor RPC: O Dispatcher Dinâmico ---
# Este dicionário é a "tabela de encaminhamento" do nosso servidor.
# Quando um cliente pede para executar "find_max_prime_parallel", o servidor vem aqui,
# encontra a chave correspondente e executa a função associada (o nosso wrapper `find_max_prime_p`).
FUNCOES_RPC = {
    "is_prime": is_prime,
    "find_max_prime_sequential": find_max_prime_sequential,
    "find_max_prime_parallel": find_max_prime_p,
    "game_of_life_sequential": game_of_life_s,
    "game_of_life_parallel": game_of_life_p,
    "list_methods": list_methods
}


# =====================================================================
# LÓGICA DO SERVIDOR TCP / SOCKETS (Esta parte não precisou de alterações)
# =====================================================================
# Esta função é executada por uma thread dedicada para cada cliente.
def processar_cliente(conn, addr):
    """Função executada por uma Thread para tratar um cliente."""
    print(f"[+] Novo cliente ligado: {addr}")
    try:
        while True:
            # O servidor fica à espera de receber dados. Buffer de 1MB para grelhas grandes.
            dados = conn.recv(1024 * 1024)
            if not dados: break # Ligação fechada pelo cliente.
            
            # Desserializa a mensagem: bytes -> string -> dicionário Python.
            pedido = json.loads(dados.decode('utf-8'))
            
            # Extrai o nome do método e os parâmetros do pedido.
            metodo_nome = pedido.get("method")
            parametros = pedido.get("params", {})
            
            resposta = {}
            # Verifica se o método pedido existe na nossa tabela de encaminhamento.
            if metodo_nome in FUNCOES_RPC:
                try:
                    # Executa a função correspondente, desempacotando os parâmetros com `**`.
                    resultado = FUNCOES_RPC[metodo_nome](**parametros)
                    resposta = {"result": resultado} # Resposta de sucesso.
                except Exception as e:
                    # Se ocorrer um erro durante a execução da função (ex: parâmetros inválidos).
                    resposta = {"error": f"Erro ao executar '{metodo_nome}': {str(e)}"}
            else:
                # Se o método nem sequer está registado no dicionário.
                resposta = {"error": f"Metodo '{metodo_nome}' não suportado."}
                
            # Serializa a resposta: dicionário -> string JSON -> bytes e envia.
            conn.sendall(json.dumps(resposta).encode('utf-8'))
            
    except ConnectionResetError:
        print(f"[-] Cliente {addr} desconectou-se abruptamente.")
    except Exception as e:
        print(f"[-] Erro com o cliente {addr}: {e}")
    finally:
        # Garante que a ligação é sempre fechada no fim.
        conn.close()
        print(f"[-] Ligação terminada com {addr}")


def iniciar_servidor(host='127.0.0.1', porta=8000):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, porta))
    servidor.listen(5)
    print(f"=== Servidor RPC a escutar em {host}:{porta} ===")
    try:
        # Loop principal do servidor, sempre a aceitar novas ligações.
        while True:
            conn, addr = servidor.accept()
            # Para cada novo cliente, criamos e lançamos uma nova thread para o atender.
            # Isto permite que o servidor atenda múltiplos clientes em simultâneo (concorrência).
            thread_cliente = threading.Thread(target=processar_cliente, args=(conn, addr))
            thread_cliente.daemon = True # Garante que a thread fecha se o programa principal fechar.
            thread_cliente.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo utilizador.")
    finally:
        servidor.close()

# Proteção para `multiprocessing` em sistemas como Windows e macOS.
if __name__ == '__main__':
    multiprocessing.freeze_support()
    iniciar_servidor()