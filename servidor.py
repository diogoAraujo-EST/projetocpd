import socket
import threading
import json
import inspect
import multiprocessing

# Importar as funções desenvolvidas na Componente 1
# Certifica-te de que os ficheiros primos.py e game_of_life.py estão na mesma pasta
from primos import is_prime, find_max_prime_parallel
from game_of_life import game_of_life_parallel

# =====================================================================
# WRAPPERS DAS FUNÇÕES PARA RPC
# =====================================================================
# O guião pede 'find_max_prime(timeout)', mas nós fizemos a versão paralela
# com 'workers'. Este wrapper ajusta os parâmetros para facilitar.
def find_max_prime(timeout: int):
    """Procura o maior numero primo num limite de tempo usando multiprocessamento."""
    workers = multiprocessing.cpu_count()
    return find_max_prime_parallel(timeout, workers)

def game_of_life(grid: list, generations: int):
    """Executa a simulacao do Game of Life em paralelo."""
    workers = multiprocessing.cpu_count()
    return game_of_life_parallel(grid, generations, workers)

def list_methods():
    """Devolve a lista das operacoes disponiveis no servidor com introspecao."""
    metodos_disponiveis = []
    
    for nome, funcao in FUNCOES_RPC.items():
        # Obter a assinatura da função (quais os parâmetros que recebe)
        assinatura = inspect.signature(funcao)
        lista_params = list(assinatura.parameters.keys())
        # Obter a docstring (comentário de documentação)
        descricao = funcao.__doc__ if funcao.__doc__ else "Sem descrição disponível."
        
        metodos_disponiveis.append({
            "nome": nome,
            "parametros": lista_params,
            "descricao": descricao.strip()
        })
        
    return metodos_disponiveis

# Dicionário que mapeia as strings recebidas pelo cliente para as funções reais
FUNCOES_RPC = {
    "is_prime": is_prime,
    "find_max_prime": find_max_prime,
    "game_of_life": game_of_life,
    "list_methods": list_methods
}


# =====================================================================
# LÓGICA DO SERVIDOR TCP / SOCKETS
# =====================================================================
def processar_cliente(conn, addr):
    """Função executada por uma Thread para tratar um cliente."""
    print(f"[+] Novo cliente ligado: {addr}")
    
    try:
        while True:
            # Receber dados do cliente (Usamos um buffer grande caso o Game of Life envie matrizes grandes)
            dados = conn.recv(1024 * 1024)
            if not dados:
                break # Cliente fechou a ligação
                
            # Converter de bytes para string JSON, e depois para Dicionário Python
            pedido = json.loads(dados.decode('utf-8'))
            
            metodo_nome = pedido.get("method")
            parametros = pedido.get("params", {})
            
            resposta = {}
            
            # Dispatch Dinâmico: Verifica se o método pedido existe no nosso dicionário
            if metodo_nome in FUNCOES_RPC:
                try:
                    funcao_alvo = FUNCOES_RPC[metodo_nome]
                    # Executa a função passando os parâmetros do dicionário JSON
                    resultado = funcao_alvo(**parametros)
                    resposta = {"result": resultado}
                except Exception as e:
                    # Se houver erro de execução ou parâmetros errados
                    resposta = {"error": f"Erro ao executar '{metodo_nome}': {str(e)}"}
            else:
                resposta = {"error": f"Metodo '{metodo_nome}' não suportado."}
                
            # Enviar a resposta de volta convertida em bytes
            conn.sendall(json.dumps(resposta).encode('utf-8'))
            
    except ConnectionResetError:
        print(f"[-] Cliente {addr} desconectou-se abruptamente.")
    except Exception as e:
        print(f"[-] Erro com o cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Ligação terminada com {addr}")


def iniciar_servidor(host='127.0.0.1', porta=8000):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, porta))
    servidor.listen(5)
    
    print(f"=== Servidor RPC a escutar em {host}:{porta} ===")
    
    try:
        while True:
            # Aceita clientes continuamente
            conn, addr = servidor.accept()
            # Cria uma Thread independente para não bloquear o servidor (Concorrência)
            thread_cliente = threading.Thread(target=processar_cliente, args=(conn, addr))
            thread_cliente.daemon = True
            thread_cliente.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo utilizador.")
    finally:
        servidor.close()

if __name__ == '__main__':
    # Necessário para o multiprocessing funcionar bem no Windows dentro do servidor
    multiprocessing.freeze_support()
    iniciar_servidor()