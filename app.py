# Importamos todas as bibliotecas necessárias
import streamlit as st
import gspread
import base64
import json
from datetime import datetime
import calculadora_copsoq as motor # Nosso motor de cálculo!

# --- CONFIGURAÇÃO INICIAL ---
# Configura a página para usar o layout "largo", aproveitando melhor a tela
st.set_page_config(layout="wide")
st.title("Ferramenta de Diagnóstico de Riscos Psicossociais (COPSOQ III)")

# O nome exato da sua planilha no Google Drive. Verifique se está correto!
NOME_DA_SUA_PLANILHA = 'Resultados_COPSOQ'

# --- FUNÇÕES AUXILIARES (LÓGICA DO APP) ---

# Função para salvar os dados na Planilha Google
def salvar_dados(lista_de_dados):
    try:
        # AQUI ESTÁ A MUDANÇA: convertemos o segredo para um dicionário normal
        creds = dict(st.secrets["gcp_service_account"])
        
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(NOME_DA_SUA_PLANILHA)
        worksheet = spreadsheet.sheet1
        worksheet.append_row(lista_de_dados)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
        st.error("Verifique as configurações de 'Secrets' no Streamlit Cloud e as permissões da planilha.")
        return False

# Função que define a cor correta para cada resultado (Semáforo)
def obter_cor_e_significado(nome_escala, valor):
    if valor is None:
        return "#6c757d", "N/A" # Cinza para valores não calculados

    escalas_de_risco = [
        "Exigências Quantitativas", "Ritmo de Trabalho", "Exigências Cognitivas",
        "Exigências Emocionais", "Conflitos de Papéis Laborais", "Insegurança Laboral",
        "Insegurança nas Condições de Trabalho", "Conflito Trabalho-Família",
        "Problemas de Sono"
    ]
    verde = "#28a745"; amarelo = "#ffc107"; vermelho = "#dc3545"

    if valor <= 33.3: cor_padrao = verde
    elif 33.4 <= valor <= 66.6: cor_padrao = amarelo
    else: cor_padrao = vermelho
        
    if nome_escala not in escalas_de_risco: # Se for uma escala de RECURSO
        if cor_padrao == verde: # Baixo recurso é crítico
            return vermelho, f"{valor} (Crítico)"
        if cor_padrao == vermelho: # Alto recurso é favorável
            return verde, f"{valor} (Favorável)"
        # Amarelo continua sendo atenção
        return amarelo, f"{valor} (Atenção)"
    
    # Para escalas de RISCO, a lógica é direta
    significado = f"{valor}"
    if cor_padrao == verde: significado += " (Baixo Risco)"
    if cor_padrao == amarelo: significado += " (Atenção)"
    if cor_padrao == vermelho: significado += " (Alto Risco)"
    return cor_padrao, significado


# --- CONTEÚDO DO APLICATIVO ---

# Bloco de Introdução e Instruções
st.markdown("""
    **Prezado(a) Colaborador(a),**

    Este questionário tem como objetivo avaliar os riscos psicossociais no ambiente de trabalho da nossa organização. 
    Sua participação é voluntária e as suas respostas são **confidenciais e anônimas**. 
    Não existem respostas certas ou erradas. Por favor, responda com a maior sinceridade possível, baseando-se nas suas experiências nas **últimas 4 semanas**.

    **Instruções:**
    * Leia atentamente cada pergunta.
    * Para cada pergunta, selecione na caixa a opção que melhor descreve a sua situação.
    * É necessário responder a todas as perguntas para que o botão de cálculo dos resultados seja habilitado no final.

    Agradecemos a sua valiosa contribuição!
""")
st.divider()

# Lista completa das 78 perguntas
todas_as_perguntas = [
    "1. Com que frequência a sua carga de trabalho se acumula?", "2. Com que frequência você fica com trabalho por fazer quando termina o seu dia de trabalho?", "3. Com que frequência você não tem tempo para completar todas as suas tarefas de trabalho?", "4. Com que frequência tem que trabalhar muito depressa?", "5. Com que frequência o seu trabalho exige que trabalhe a um ritmo muito elevado durante todo o dia?", "6. O seu trabalho exige atenção constante?", "7. O seu trabalho exige que se lembre de muitas coisas?", "8. O seu trabalho exige que tenha novas ideias?", "9. O seu trabalho exige que tome decisões difíceis?", "10. O seu trabalho coloca-o em situações emocionalmente perturbadoras?", "11. O seu trabalho exige que lide com os problemas pessoais dos outros (clientes, utentes, etc.)?", "12. O seu trabalho é exigente do ponto de vista emocional?", "13. Tem grande influência nas decisões acerca do seu trabalho?", "14. Tem influência sobre a quantidade de trabalho que lhe é atribuída?", "15. Tem influência sobre o que faz no seu trabalho?", "16. Tem influência sobre como faz o seu trabalho?", "17. O seu trabalho dá-lhe a possibilidade de aprender coisas novas?", "18. No seu trabalho, consegue usar as suas competências e conhecimentos?", "19. O seu trabalho dá-lhe oportunidade para desenvolver as suas competências?", "20. Pode decidir quando fazer uma pausa?", "21. Geralmente, pode tirar férias quando quer?", "22. Pode deixar o seu local de trabalho por breves instantes para falar com um colega?", "23. O seu trabalho é significativo para si?", "24. Sente que o trabalho que faz é importante?", "25. Sente-se motivado e envolvido no seu trabalho?", "26. Gosta de falar sobre o seu local de trabalho com pessoas que não trabalham lá?", "27. Sente orgulho em pertencer à sua organização?", "28. É informado com a devida antecedência sobre decisões, mudanças ou planos importantes para o futuro?", "29. Recebe todas as informações necessárias para fazer bem o seu trabalho?", "30. O seu trabalho é reconhecido e apreciado pela gerência?", "31. A gerência respeita os trabalhadores?", "32. A gerência trata todos os trabalhadores de maneira justa?", "33. O seu trabalho tem objetivos claros?", "34. Sabe exatamente quais são as suas áreas de responsabilidade?", "35. Sabe exatamente o que se espera de si no trabalho?", "36. No seu trabalho são-lhe solicitadas exigências contraditórias?", "37. Tem que fazer coisas que parecem ser de modo diferente de como teriam sido planejadas?", "38. Tem que fazer coisas que lhe parecem desnecessárias?", "39. A sua chefia imediata garante que os trabalhadores tenham boas oportunidades de desenvolvimento?", "40. A sua chefia imediata é adequada no planejamento do trabalho?", "41. A sua chefia imediata é adequada na resolução de conflitos?", "42. A sua chefia imediata prioriza a satisfação no trabalho?", "43. Se necessário, consegue apoio e ajuda dos seus colegas para o trabalho?", "44. Se necessário, os seus colegas ouvem os seus problemas relacionados com o trabalho?", "45. Os seus colegas falam consigo sobre o seu desempenho no trabalho?", "46. Se necessário, a sua chefia imediata ouve os seus problemas relacionados com o trabalho?", "47. Se necessário, consegue apoio e ajuda da sua chefia imediata para o trabalho?", "48. A sua chefia imediata fala consigo sobre o seu desempenho no trabalho?", "49. Existe um bom clima de trabalho entre os colegas?", "50. Sente-se parte de uma equipe no seu local de trabalho?", "51. Existe uma boa cooperação entre os colegas de trabalho?", "52. Está preocupado em vir a ficar desempregado?", "53. Está preocupado com a dificuldade em encontrar outro emprego, caso seja despedido?", "54. Está preocupado em ser transferido para outro departamento ou função contra a sua vontade?", "55. Está preocupado com a possibilidade de o seu cronograma de trabalho ser alterado contra a sua vontade?", "56. Está preocupado com a possibilidade de o seu rendimento diminuir?", "57. Está satisfeito com a qualidade do trabalho que executa?", "58. No geral, os empregados confiam uns nos outros?", "59. Os empregados escondem informações uns dos outros?", "60. Os empregados escondem informações da gerência?", "61. A gerência confia nos empregados para fazerem bem o seu trabalho?", "62. Os empregados confiam na informação que recebem da gerência?", "63. Os empregados podem expressar os seus sentimentos e pontos de vista à gerência?", "64. Os conflitos no seu local de trabalho são resolvidos de modo justo?", "65. O trabalho é distribuído de maneira justa?", "66. As sugestões dos trabalhadores são tratadas com seriedade pela gerência?", "67. Os empregados são reconhecidos quando fazem um bom trabalho?", "68. O seu trabalho tira-lhe energias para a sua vida privada?", "69. O seu trabalho toma-lhe tempo que gostaria de dedicar à sua vida privada?", "70. As exigências do seu trabalho interferem com a sua vida privada?", "71. Está satisfeito com as suas perspectivas de trabalho?", "72. Considerando todos os aspectos, está satisfeito com o seu emprego?", "73. Está satisfeito com o modo como as suas competências são usadas no seu trabalho?", "74. De um modo geral, como diria que é a sua saúde?", "75. Consigo sempre encontrar diferentes maneiras de resolver um problema?", "76. Para mim, é fácil manter os meus planos e alcançar os meus objetivos.", "77. Nas últimas 4 semanas, com que frequência teve dificuldade em adormecer?", "78. Nas últimas 4 semanas, com que frequência acordou muito cedo e não conseguiu voltar a adormecer?"
]

opcoes_frequencia = ["Selecione uma opção", "Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"]
respostas_do_usuario = []

st.info("Por favor, responda a todas as perguntas abaixo para habilitar o botão de cálculo.")

# Usamos colunas para deixar o layout do questionário mais compacto
col1, col2 = st.columns(2)
metade_das_perguntas = len(todas_as_perguntas) // 2

for i, pergunta_texto in enumerate(todas_as_perguntas):
    if i < metade_das_perguntas:
        with col1:
            resposta = st.selectbox(label=pergunta_texto, options=opcoes_frequencia, key=i)
            respostas_do_usuario.append(resposta)
    else:
        with col2:
            resposta = st.selectbox(label=pergunta_texto, options=opcoes_frequencia, key=i)
            respostas_do_usuario.append(resposta)

st.header("Finalizar e Ver Resultados")

if "Selecione uma opção" not in respostas_do_usuario:
    st.success("Tudo pronto! Você respondeu a todas as perguntas.")
    if st.button("Calcular e Salvar Meus Resultados"):
        with st.spinner('Calculando e salvando... Por favor, aguarde.'):
            pontuacoes = motor.calcular_pontuacoes(respostas_do_usuario)
            resultados = motor.calcular_escalas_finais(pontuacoes)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nomes_escalas_ordenadas = list(motor.definicao_escalas.keys())
            resultados_ordenados = [resultados.get(nome, "") for nome in nomes_escalas_ordenadas]
            linha_para_salvar = [timestamp] + respostas_do_usuario + resultados_ordenados
            
            sucesso_ao_salvar = salvar_dados(linha_para_salvar)
            
            if sucesso_ao_salvar:
                st.balloons()
                st.success("Resultados calculados e salvos com sucesso na Planilha Google!")

            st.subheader("Seu Diagnóstico Psicossocial:")
            col_res1, col_res2, col_res3 = st.columns(3)
            cols_resultado = [col_res1, col_res2, col_res3]
            col_index = 0
            for nome, valor in resultados.items():
                with cols_resultado[col_index]:
                    cor, texto_valor = obter_cor_e_significado(nome, valor)
                    st.markdown(f"""
                    <div style="background-color:{cor}; padding:15px; border-radius:10px; margin:5px; height: 160px; display: flex; flex-direction: column; justify-content: center; text-align: center;">
                        <h3 style="color:white; font-size: 16px; font-weight: bold;">{nome}</h3>
                        <p style="color:white; font-size: 24px; font-weight: bold;">{texto_valor}</p>
                    </div>
                    """, unsafe_allow_html=True)
                col_index = (col_index + 1) % 3
else:
    st.warning("Por favor, responda a todas as perguntas acima para que o botão de cálculo apareça.")
