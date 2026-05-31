import socket
import json

# --- Configurações da Ligação ---
# O endereço IP do servidor. '127.0.0.1' (ou 'localhost') significa que o servidor está na nossa própria máquina.
HOST = '127.0.0.1'
# A porta que o servidor está a usar. Tem de ser a mesma para ambos conseguirem "falar".
PORTA = 8000

def enviar_pedido_rpc(metodo, parametros={}):
    """
    Função central que trata de toda a comunicação com o servidor.
    Ela faz tudo: monta o pedido, liga-se, envia, recebe a resposta e devolve-a.
    """
    # 1. Montamos o pedido num dicionário Python, seguindo o formato JSON-RPC do guião.
    #    'method' é o nome da função que queremos chamar, 'params' são os seus argumentos.
    pedido = {"method": metodo, "params": parametros}
    
    try:
        # `with socket.socket...` é uma forma segura de garantir que a ligação é sempre fechada no fim.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 2. Conecta-se ao servidor usando o HOST e a PORTA definidos.
            s.connect((HOST, PORTA))
            
            # 3. Prepara e envia os dados.
            #    - `json.dumps()`: Converte o nosso dicionário para uma string em formato JSON.
            #    - `.encode('utf-8')`: Converte a string para bytes, que é o que viaja na rede.
            s.sendall(json.dumps(pedido).encode('utf-8'))
            
            # 4. Fica à espera da resposta do servidor.
            #    O buffer de 1MB (1024*1024) é para garantir que recebemos a resposta completa.
            dados_recebidos = s.recv(1024 * 1024)
            
            # 5. Faz o processo inverso: converte os bytes de volta para um dicionário Python.
            return json.loads(dados_recebidos.decode('utf-8'))
            
    except ConnectionRefusedError:
        # Se o servidor não estiver a correr, este erro é apanhado e mostramos uma mensagem amigável.
        return {"error": "Não foi possível ligar ao servidor. Verifica se o servidor.py está a correr."}
    except Exception as e:
        # Apanha qualquer outro erro de rede para o programa não "crashar".
        return {"error": f"Erro de comunicação: {e}"}

def escolher_estrategia():
    """Função auxiliar, simples, só para perguntar ao utilizador se quer 's' ou 'p'."""
    # `.lower()` converte a resposta para minúsculas para aceitar 'S' ou 'P'.
    escolha = input("-> Quer usar a estratégia [s]equencial ou [p]aralela? ").lower()
    if escolha not in ['s', 'p']:
        # Se o utilizador escrever outra coisa, assumimos a opção mais segura (sequencial).
        print("Opção inválida. A usar 'sequencial' por defeito.")
        return 's'
    return escolha

def mostrar_menu():
    """Função principal que gere a interface com o utilizador."""
    # Loop infinito para mostrar o menu repetidamente até o utilizador sair.
    while True:
        print("\n=== CLIENTE RPC ===")
        print("1. list_methods()")
        print("2. is_prime(n)")
        print("3. find_max_prime(timeout)")
        print("4. game_of_life(grid, generations)")
        print("0. Sair")
        
        opcao = input("Escolhe uma operação: ")
        
        if opcao == '0':
            break # Quebra o loop e termina o programa.
            
        elif opcao == '1':
            print("\nA pedir lista de métodos...")
            resposta = enviar_pedido_rpc("list_methods") # Chama o método sem parâmetros.
            
            # Verifica se a resposta do servidor foi um erro ou um sucesso.
            if "error" in resposta:
                print(f"Erro: {resposta['error']}")
            else:
                # Se foi sucesso, formata a lista de métodos de forma legível.
                for func in resposta["result"]:
                    print(f"\n-> Função: {func['nome']}")
                    print(f"   Parâmetros: {func['parametros']}")
                    print(f"   Descrição: {func['descricao']}")
                    
        elif opcao == '2':
            try:
                n = int(input("Qual o número a testar? "))
                print(f"\nA verificar se {n} é primo...")
                # Envia o pedido com o parâmetro 'n' dentro de um dicionário.
                resposta = enviar_pedido_rpc("is_prime", {"n": n})
                print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um número inteiro válido.")
                
        elif opcao == '3':
            try:
                tempo = int(input("Tempo limite de pesquisa (segundos)? "))
                # Pede ao utilizador para escolher a estratégia.
                estrategia = escolher_estrategia()
                
                # --- Lógica Dinâmica ---
                # Construímos o nome do método que vamos chamar no servidor.
                # Se o utilizador escreveu 's', o nome será 'find_max_prime_sequential'.
                # Se escreveu 'p', será 'find_max_prime_parallel'.
                nome_metodo = f"find_max_prime_{'sequential' if estrategia == 's' else 'parallel'}"
                
                print(f"\nA pesquisar o maior primo em {tempo}s (Estratégia: {nome_metodo})...")
                # Enviamos o pedido com o nome do método dinâmico.
                resposta = enviar_pedido_rpc(nome_metodo, {"timeout": tempo})
                print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um tempo válido.")
                
        elif opcao == '4':
            try:
                gens = int(input("Quantas gerações queres simular? "))
                estrategia = escolher_estrategia()

                # A mesma lógica dinâmica para o Game of Life.
                nome_metodo = f"game_of_life_{'sequential' if estrategia == 's' else 'parallel'}"

                # Usamos uma grelha de teste fixa para ser mais fácil de usar.
                grid_teste = [
                    [0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0]
                ]
                print(f"\nA simular Game of Life ({gens} gerações) (Estratégia: {nome_metodo})...")
                
                resposta = enviar_pedido_rpc(nome_metodo, {"grid": grid_teste, "generations": gens})
                
                # Como o servidor devolve um dicionário com a grelha e o tempo,
                # temos de aceder a cada um deles para os mostrar.
                if "result" in resposta:
                    resultado = resposta["result"]
                    print(f"Tempo de execução no servidor: {resultado['execution_time']}")
                    print("Matriz Resultante:")
                    for row in resultado["grid"]:
                        print(row)
                else:
                    print("Resposta do Servidor:", resposta)
            except ValueError:
                print("Por favor insere um número válido de gerações.")
        else:
            print("Opção inválida.")

# Ponto de entrada do programa.
if __name__ == '__main__':
    mostrar_menu()