import statistics

# Parte 1: O Dicionário de Pontuação
# Mapeia cada resposta em texto para o seu valor numérico.
pontuacao_map = {
    "Nunca": 0, "Raramente": 25, "Às vezes": 50, "Frequentemente": 75, "Sempre": 100,
    "Nada": 0, "Um pouco": 25, "Moderadamente": 50, "Muito": 75, "Extremamente": 100,
    "Fraca": 0, "Razoável": 25, "Boa": 50, "Muito boa": 75, "Excelente": 100
}

# Parte 2: A Função que Calcula as Pontuações Individuais
# Recebe as respostas de um funcionário e retorna as 78 pontuações calculadas.
# Versão corrigida COM a inversão da Q58, conforme o documento oficial
def calcular_pontuacoes(respostas):
    pontuacoes_calculadas = []
    # O número de perguntas é 84, conforme o questionário
    total_de_perguntas = 84 
    respostas_completas = respostas + [""] * (total_de_perguntas - len(respostas))

    for i, resposta_texto in enumerate(respostas_completas):
        # i começa em 0, então o número da pergunta é i + 1
        numero_da_pergunta = i + 1
        pontuacao = pontuacao_map.get(resposta_texto, None)

        # AQUI ESTÁ A REGRA DE INVERSÃO CORRIGIDA PARA A PERGUNTA 58
        if numero_da_pergunta == 58 and pontuacao is not None:
            # A pontuação de 0-100 é invertida (0->100, 25->75, etc.)
            pontuacao_final = 100 - pontuacao
        else:
            # Para todas as outras perguntas, a pontuação é normal
            pontuacao_final = pontuacao

        pontuacoes_calculadas.append(pontuacao_final)

    return pontuacoes_calculadas

# Parte 4: A Função Final que Calcula as Médias das Escalas
# Recebe as 78 pontuações e retorna os resultados finais das 32 escalas.
def calcular_escalas_finais(pontuacoes):
    resultados_finais = {}
    for nome_escala, indices in definicao_escalas.items():
        # Pega apenas as pontuações relevantes para esta escala, ignorando valores nulos
        pontuacoes_da_escala = [pontuacoes[i] for i in indices if pontuacoes[i] is not None]
        
        if pontuacoes_da_escala:
            media = statistics.mean(pontuacoes_da_escala)
            resultados_finais[nome_escala] = round(media, 2)
        else:
            resultados_finais[nome_escala] = None # Não há dados para calcular a média
            
    return resultados_finais

# Parte 5: Teste Completo para vermos o código em ação
# O código dentro deste 'if' só executa quando você roda o arquivo diretamente.
if __name__ == '__main__':
    # Criamos uma lista de respostas de um funcionário de teste
    respostas_de_teste = [
        'Sempre', 'Nunca', 'Às vezes',  # Para a Escala EQ
        'Frequentemente', 'Às vezes',   # Para a Escala Ritmo
    ]
    
    print("--- EXECUTANDO O TESTE DO MOTOR DE CÁLCULO ---")
    
    # 1. Usamos a primeira função para obter as pontuações individuais
    pontuacoes_individuais = calcular_pontuacoes(respostas_de_teste)
    
    # 2. Usamos a segunda função para obter os resultados finais das escalas
    resultados_das_escalas = calcular_escalas_finais(pontuacoes_individuais)

    print("\n--- RESULTADOS FINAIS CALCULADOS ---")
    for nome, valor in resultados_das_escalas.items():
        if valor is not None:
            print(f"-> {nome}: {valor}")