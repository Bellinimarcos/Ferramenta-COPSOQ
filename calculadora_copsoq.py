import statistics

# Parte 1: O Dicionário de Pontuação
pontuacao_map = {
    "Nunca": 0, "Raramente": 25, "Às vezes": 50, "Frequentemente": 75, "Sempre": 100,
    "Nada": 0, "Um pouco": 25, "Moderadamente": 50, "Muito": 75, "Extremamente": 100,
    "Fraca": 0, "Razoável": 25, "Boa": 50, "Muito boa": 75, "Excelente": 100
}

# Parte 2: A Função que Calcula as Pontuações Individuais (COM a inversão da Q58)
def calcular_pontuacoes(respostas):
    pontuacoes_calculadas = []
    total_de_perguntas = 84
    respostas_completas = respostas + [""] * (total_de_perguntas - len(respostas))
    
    for i, resposta_texto in enumerate(respostas_completas):
        numero_da_pergunta = i + 1
        pontuacao = pontuacao_map.get(resposta_texto, None)
        
        if numero_da_pergunta == 58 and pontuacao is not None:
            pontuacao_final = 100 - pontuacao
        else:
            pontuacao_final = pontuacao
        pontuacoes_calculadas.append(pontuacao_final)
        
    return pontuacoes_calculadas

# Parte 3: A Definição das 32 Escalas (A parte que estava faltando)
definicao_escalas = {
    "Exigências Quantitativas": [0, 1, 2],
    "Ritmo de Trabalho": [3, 4],
    "Exigências Cognitivas": [5, 6, 7, 8],
    "Exigências Emocionais": [9, 10, 11],
    "Influência no Trabalho": [12, 13, 14, 15],
    "Possibilidades de Desenvolvimento": [16, 17, 18],
    "Controlo sobre o Tempo de Trabalho": [19, 20, 21],
    "Significado do Trabalho": [22, 23, 24],
    "Compromisso com o Local de Trabalho": [25, 26],
    "Previsibilidade": [27, 28],
    "Reconhecimento": [29, 30, 31],
    "Transparência do Papel Laboral": [32, 33, 34],
    "Conflitos de Papéis Laborais": [35, 36, 37],
    "Qualidade da Liderança": [38, 39, 40, 41],
    "Suporte Social de Colegas": [42, 43, 44],
    "Suporte Social de Superiores": [45, 46, 47],
    "Sentido de Pertença": [48, 49, 50],
    "Insegurança Laboral": [51, 52],
    "Insegurança nas Condições de Trabalho": [53, 54, 55],
    "Qualidade do Trabalho": [56],
    "Confiança Horizontal": [57, 58, 59],
    "Confiança Vertical": [60, 61, 62],
    "Justiça Organizacional": [63, 64, 65, 66],
    "Conflito Trabalho-Família": [67, 68, 69],
    "Satisfação com o Trabalho": [70, 71, 72],
    "Autoavaliação da Saúde": [73],
    "Autoeficácia": [74, 75],
    "Problemas de Sono": [76, 77],
    "Burnout": [78, 79],
    "Stress": [80, 81],
    "Sintomas Depressivos": [82, 83]
}

# Parte 4: A Função Final que Calcula as Médias das Escalas
def calcular_escalas_finais(pontuacoes):
    resultados_finais = {}
    for nome_escala, indices in definicao_escalas.items():
        pontuacoes_da_escala = [pontuacoes[i] for i in indices if pontuacoes[i] is not None]
        
        if pontuacoes_da_escala:
            media = statistics.mean(pontuacoes_da_escala)
            resultados_finais[nome_escala] = round(media, 2)
        else:
            resultados_finais[nome_escala] = None
            
    return resultados_finais