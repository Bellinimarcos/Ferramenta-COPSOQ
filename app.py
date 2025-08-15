import streamlit as st
import gspread
import base64
import json
from datetime import datetime
import calculadora_copsoq as motor

# --- CONFIGURAÇÃO INICIAL E FUNÇÕES ---
st.set_page_config(layout="wide")
NOME_DA_SUA_PLANILHA = 'Resultados_COPSOQ'

# ... (Cole aqui as funções 'salvar_dados' e 'obter_cor_e_significado' da nossa versão anterior) ...
# Para economizar espaço, não vou repetir as funções aqui, mas elas devem estar no seu código.

# --- TÍTULO E INSTRUÇÕES ---
st.title("Ferramenta de Diagnóstico de Riscos Psicossociais (COPSOQ III)")
st.markdown("""
    **Prezado(a) Colaborador(a),**
    Este questionário tem como objetivo avaliar os riscos psicossociais no ambiente de trabalho... 
    *(Seu texto de introdução completo aqui)*
""")
st.divider()

# --- DADOS DO QUESTIONÁRIO ---
# Lista completa e correta das 84 perguntas
todas_as_perguntas = [
    "1. A sua carga de trabalho acumula-se por ser mal distribuída?", "2. Com que frequência fica com trabalho atrasado?", "3. Com que frequência não tem tempo para completar todas as tarefas do seu trabalho?", "4. Precisa de trabalhar muito rapidamente?", "5. Trabalha a um ritmo elevado ao longo de toda a jornada de trabalho?", "6. O seu trabalho exige a sua atenção constante?", "7. O seu trabalho requer que memorize muitas informações?", "8. O seu trabalho requer que seja bom a propor novas ideias?", "9. O seu trabalho exige que tome decisões difíceis?", "10. O seu trabalho coloca-o/a em situações emocionalmente perturbadoras?", "11. No seu trabalho tem de lidar com os problemas pessoais de outras pessoas?", "12. O seu trabalho exige emocionalmente de si?", "13. Tem um elevado grau de influência nas decisões sobre o seu trabalho?", "14. Pode influenciar a quantidade de trabalho que lhe compete a si?", "15. Tem influência sobre o que faz no seu trabalho?", "16. Tem influência sobre como faz o seu trabalho?", "17. O seu trabalho dá-lhe a possibilidade de aprender coisas novas?", "18. No seu trabalho, consegue usar as suas competências e conhecimentos?", "19. O seu trabalho dá-lhe oportunidade para desenvolver as suas competências?", "20. Pode decidir quando fazer uma pausa?", "21. Geralmente, pode tirar férias quando quer?", "22. Pode deixar o seu local de trabalho por breves instantes para falar com um colega?", "23. O seu trabalho é significativo para si?", "24. Sente que o trabalho que faz é importante?", "25. Sente-se motivado e envolvido no seu trabalho?", "26. Gosta de falar sobre o seu local de trabalho com pessoas que não trabalham lá?", "27. Sente orgulho em pertencer à sua organização?", "28. É informado com a devida antecedência sobre decisões, mudanças ou planos importantes para o futuro?", "29. Recebe todas as informações necessárias para fazer bem o seu trabalho?", "30. O seu trabalho é reconhecido e apreciado pela gerência?", "31. A gerência respeita os trabalhadores?", "32. A gerência trata todos os trabalhadores de maneira justa?", "33. O seu trabalho tem objetivos claros?", "34. Sabe exatamente quais são as suas áreas de responsabilidade?", "35. Sabe exatamente o que se espera de si no trabalho?", "36. No seu trabalho são-lhe solicitadas exigências contraditórias?", "37. Tem que fazer coisas que parecem ser de modo diferente de como teriam sido planejadas?", "38. Tem que fazer coisas que lhe parecem desnecessárias?", "39. A sua chefia imediata garante que os trabalhadores tenham boas oportunidades de desenvolvimento?", "40. A sua chefia imediata é adequada no planejamento do trabalho?", "41. A sua chefia imediata é adequada na resolução de conflitos?", "42. A sua chefia imediata prioriza a satisfação no trabalho?", "43. Se necessário, consegue apoio e ajuda dos seus colegas para o trabalho?", "44. Se necessário, os seus colegas ouvem os seus problemas relacionados com o trabalho?", "45. Os seus colegas falam consigo sobre o seu desempenho no trabalho?", "46. Se necessário, a sua chefia imediata ouve os seus problemas relacionados com o trabalho?", "47. Se necessário, consegue apoio e ajuda da sua chefia imediata para o trabalho?", "48. A sua chefia imediata fala consigo sobre o seu desempenho no trabalho?", "49. Existe um bom clima de trabalho entre os colegas?", "50. Sente-se parte de uma equipe no seu local de trabalho?", "51. Existe uma boa cooperação entre os colegas de trabalho?", "52. Está preocupado em vir a ficar desempregado?", "53. Está preocupado com a dificuldade em encontrar outro emprego, caso seja despedido?", "54. Está preocupado em ser transferido para outro departamento ou função contra a sua vontade?", "55. Está preocupado com a possibilidade de o seu cronograma de trabalho ser alterado contra a sua vontade?", "56. Está preocupado com a possibilidade de o seu rendimento diminuir?", "57. Está satisfeito com a qualidade do trabalho que executa?", "58. No geral, os empregados confiam uns nos outros?", "59. Os empregados escondem informações uns dos outros?", "60. Os empregados escondem informações da gerência?", "61. A gerência confia nos empregados para fazerem bem o seu trabalho?", "62. Os empregados confiam na informação que recebem da gerência?", "63. Os empregados podem expressar os seus sentimentos e pontos de vista à gerência?", "64. Os conflitos no seu local de trabalho são resolvidos de modo justo?", "65. O trabalho é distribuído de forma justa?", "66. As sugestões dos trabalhadores são tratadas de forma séria pela gestão de topo?", "67. Quando os trabalhadores fazem um bom trabalho são reconhecidos?", "68. Sente que o seu trabalho lhe exige tanta energia, que acaba por afetar a sua vida privada / familiar negativamente?", "69. Sente que o seu trabalho lhe exige tanto tempo, que acaba por afetar a sua vida privada / familiar negativamente?", "70. As exigências do seu trabalho interferem com a sua vida privada e familiar?", "71. As suas perspetivas de trabalho?", "72. O seu trabalho de uma forma global?", "73. A forma como as suas capacidades e competências são usadas?", "74. Em geral, sente que a sua saúde é:", "75. Sou sempre capaz de resolver problemas se tentar o suficiente.", "76. É fácil seguir os meus planos e atingir os meus objectivos.", "77. Sentiu dificuldade em adormecer?", "78. Acordou várias vezes durante a noite e depois não conseguia adormecer novamente?", "79. Tem-se sentido fisicamente exausto/a?", "80. Tem-se sentido emocionalmente exausto/a?", "81. Tem-se sentido tenso/a?", "82. Tem-se sentido triste ou deprimido/a?", "83. Tem tido falta de interesse pelas suas atividades diárias?", "84. Tem tido falta de interesse pelas pessoas que o/a rodeiam?"
]
opcoes_frequencia = ("Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre")
respostas_do_usuario = []

# --- RENDERIZAÇÃO DO QUESTIONÁRIO ---
st.info("Por favor, responda a todas as perguntas para habilitar o botão de cálculo.")
col1, col2 = st.columns(2)
metade = len(todas_as_perguntas) // 2

# Criamos um "espaço reservado" para o botão
placeholder_botao = st.empty()

# Loop para criar as perguntas
for i, pergunta in enumerate(todas_as_perguntas):
    coluna_atual = col1 if i < metade else col2
    with coluna_atual:
        # Usamos st.radio para a nova arquitetura
        resposta = st.radio(
            label=pergunta,
            options=opcoes_frequencia,
            index=None, # Começa sem nenhuma opção selecionada
            horizontal=True, # Deixa as opções na horizontal, economizando espaço
            key=f"q_{i}"
        )
        respostas_do_usuario.append(resposta)

# --- LÓGICA DO BOTÃO E CÁLCULO ---
# Verificamos se todas as perguntas foram respondidas (nenhuma resposta é 'None')
if None not in respostas_do_usuario:
    with placeholder_botao.container():
        st.success("Tudo pronto! Você respondeu a todas as perguntas.")
        if st.button("Calcular e Salvar Meus Resultados"):
            # ... (Cole aqui toda a lógica que vem depois do botão, da versão anterior) ...
else:
    with placeholder_botao.container():
        st.warning("Por favor, responda a todas as perguntas para que o botão de cálculo apareça.")

