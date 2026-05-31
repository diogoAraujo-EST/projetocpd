import socket
import json

HOST = '127.0.0.1'
PORTA = 8000

def enviar_pedido_rpc(metodo, parametros={}):
    """Cria a estrutura JSON, envia para o socket e devolve a resposta."""
    pedido = {
        "method": metodo,
        "params": parametros
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORTA))
            
            # Converter para JSON e enviar bytes
            dados_enviar = json.dumps(pedido).encode('utf-8')
            s.sendall(dados_enviar)
            
            # Aguardar resposta (buffer grande)
            dados_recebidos = s.recv(1024 * 1024)
            resposta = json.loads(dados_recebidos.decode('utf-8'))
            return resposta
            
    except ConnectionRefusedError:
        return {"error": "Não foi possível ligar ao servidor. Verifica se o servidor.py está a correr."}
    except Exception as e:
        return {"error": f"Erro de comunicação: {e}"}


def mostrar_menu():
    while True:
        print("\n=== CLIENTE RPC ===")
        print("1. list_methods()")
        print("2. is_prime(n)")
        print("3. find_max_prime(timeout)")
        print("4. game_of_life(grid, generations)")
        print("0. Sair")
        
        opcao = input("Escolhe uma operação: ")
        
        if opcao == '0':
            break
            
        elif opcao == '1':
            print("\nA pedir lista de métodos...")
            resposta = enviar_pedido_rpc("list_methods")
            
            if "error" in resposta:
                print(f"Erro: {resposta['error']}")
            else:
                for func in resposta["result"]:
                    print(f"\n-> Função: {func['nome']}")
                    print(f"   Parâmetros: {func['parametros']}")
                    print(f"   Descrição: {func['descricao']}")
                    
        elif opcao == '2':
            try:
                n = int(input("Qual o número a testar? "))
                print(f"\nA verificar se {n} é primo...")
                resposta = enviar_pedido_rpc("is_prime", {"n": n})
                print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um número inteiro válido.")
                
        elif opcao == '3':
            try:
                tempo = int(input("Tempo limite de pesquisa (segundos)? "))
                print(f"\nA pesquisar o maior primo em {tempo}s. Aguarda...")
                resposta = enviar_pedido_rpc("find_max_prime", {"timeout": tempo})
                print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um tempo válido.")
                
        elif opcao == '4':
            try:
                gens = int(input("Quantas gerações queres simular? "))
                # Grelha de teste: Um "Blinker" 5x5 para não teres de escrever uma matriz à mão
                grid_teste = [
                    [0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0]
                ]
                print(f"\nA simular Game of Life ({gens} gerações) numa grelha 5x5...")
                resposta = enviar_pedido_rpc("game_of_life", {"grid": grid_teste, "generations": gens})
                
                if "result" in resposta:
                    print("\nMatriz Resultante:")
                    for row in resposta["result"]:
                        print(row)
                else:
                    print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um número válido de gerações.")
        else:
            print("Opção inválida.")


if __name__ == '__main__':
    mostrar_menu()