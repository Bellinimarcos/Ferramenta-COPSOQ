# Importamos todas as bibliotecas necessárias
import streamlit as st
import gspread
from datetime import datetime
import calculadora_copsoq as motor # Seu motor de cálculo!

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(layout="wide", page_title="Diagnóstico COPSOQ III")

# Inicializa o session_state para armazenar as respostas
if 'respostas' not in st.session_state:
    st.session_state.respostas = {}

# --- FUNÇÕES ---
NOME_DA_SUA_PLANILHA = 'Resultados_COPSOQ'

def salvar_dados(lista_de_dados):
    try:
        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(NOME_DA_SUA_PLANILHA)
        worksheet = spreadsheet.sheet1
        if len(worksheet.get_all_values()) == 0:
            cabecalhos_respostas = [f"Resp_Q{i}" for i in range(1, 85)]
            cabecalhos_escalas = list(motor.definicao_escalas.keys())
            cabecalho_completo = ["Timestamp"] + cabecalhos_respostas + cabecalhos_escalas
            worksheet.update('A1', [cabecalho_completo])
        worksheet.append_row(lista_de_dados)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
        st.error("Verifique as configurações de 'Secrets' no Streamlit Cloud e as permissões da planilha.")
        return False

def obter_cor_e_significado(nome_escala, valor):
    if valor is None:
        return "#6c757d", "N/A"
    escalas_de_risco = [
        "Exigências Quantitativas", "Ritmo de Trabalho", "Exigências Cognitivas",
        "Exigências Emocionais", "Conflitos de Papéis Laborais", "Insegurança Laboral",
        "Insegurança nas Condições de Trabalho", "Conflito Trabalho-Família",
        "Problemas de Sono", "Burnout", "Stress", "Sintomas Depressivos"
    ]
    verde = "#28a745"; amarelo = "#ffc107"; vermelho = "#dc3545"
    if valor <= 33.3: cor_padrao = verde
    elif 33.4 <= valor <= 66.6: cor_padrao = amarelo
    else: cor_padrao = vermelho
    if nome_escala not in escalas_de_risco:
        if cor_padrao == verde: return vermelho, f"{valor} (Crítico)"
        if cor_padrao == vermelho: return verde, f"{valor} (Favorável)"
        return amarelo, f"{valor} (Atenção)"
    significado = f"{valor}"
    if cor_padrao == verde: significado += " (Baixo Risco)"
    if cor_padrao == amarelo: significado += " (Atenção)"
    if cor_padrao == vermelho: significado += " (Alto Risco)"
    return cor_padrao, significado

# --- ESTRUTURA DE DADOS DO QUESTIONÁRIO (AGRUPADO POR TEMAS) ---
opcoes_frequencia = ("Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre")

perguntas_agrupadas = {
    "Ambiente e Carga de Trabalho": {
        "1": "A sua carga de trabalho acumula-se por ser mal distribuída?", "2": "Com que frequência fica com trabalho atrasado?", "3": "Com que frequência não tem tempo para completar todas as suas tarefas do seu trabalho?", "4": "Precisa de trabalhar muito rapidamente?", "5": "Trabalha a um ritmo elevado ao longo de toda a jornada de trabalho?", "6": "O seu trabalho exige a sua atenção constante?", "7": "O seu trabalho requer que memorize muitas informações?", "8": "O seu trabalho requer que seja bom a propor novas ideias?", "9": "O seu trabalho exige que tome decisões difíceis?"
    },
    "Exigências Emocionais e Autonomia": {
        "10": "O seu trabalho coloca-o/a em situações emocionalmente perturbadoras?", "11": "No seu trabalho tem de lidar com os problemas pessoais de outras pessoas?", "12": "O seu trabalho exige emocionalmente de si?", "13": "Tem um elevado grau de influência nas decisões sobre o seu trabalho?", "14": "Pode influenciar a quantidade de trabalho que lhe compete a si?", "15": "Tem influência sobre o que faz no seu trabalho?", "16": "Tem influência sobre como faz o seu trabalho?", "20": "Pode decidir quando fazer uma pausa?", "21": "Geralmente, pode tirar férias quando quer?", "22": "Pode deixar o seu local de trabalho por breves instantes para falar com um colega?"
    },
    "Desenvolvimento e Significado": {
        "17": "O seu trabalho dá-lhe a possibilidade de aprender coisas novas?", "18": "No seu trabalho, consegue usar as suas competências e conhecimentos?", "19": "O seu trabalho dá-lhe oportunidade para desenvolver as suas competências?", "23": "O seu trabalho é significativo para si?", "24": "Sente que o trabalho que faz é importante?", "25": "Sente-se motivado e envolvido no seu trabalho?"
    },
    "Liderança, Gestão e Relações": {
        "26": "Gosta de falar sobre o seu local de trabalho com pessoas que não trabalham lá?", "27": "Sente orgulho em pertencer à sua organização?", "28": "É informado com a devida antecedência sobre decisões, mudanças ou planos importantes para o futuro?", "29": "Recebe todas as informações necessárias para fazer bem o seu trabalho?", "30": "O seu trabalho é reconhecido e apreciado pela gerência?", "31": "A gerência respeita os trabalhadores?", "32": "A gerência trata todos os trabalhadores de maneira justa?", "39": "A sua chefia imediata garante que os trabalhadores tenham boas oportunidades de desenvolvimento?", "40": "A sua chefia imediata é adequada no planejamento do trabalho?", "41": "A sua chefia imediata é adequada na resolução de conflitos?", "42": "A sua chefia imediata prioriza a satisfação no trabalho?"
    },
    "Apoio Social e Papel no Trabalho": {
        "33": "O seu trabalho tem objetivos claros?", "34": "Sabe exatamente quais são as suas áreas de responsabilidade?", "35": "Sabe exatamente o que se espera de si no trabalho?", "36": "No seu trabalho são-lhe solicitadas exigências contraditórias?", "37": "Tem que fazer coisas que parecem ser de modo diferente de como teriam sido planejadas?", "38": "Tem que fazer coisas que lhe parecem desnecessárias?", "43": "Se necessário, consegue apoio e ajuda dos seus colegas para o trabalho?", "44": "Se necessário, os seus colegas ouvem os seus problemas relacionados com o trabalho?", "45": "Os seus colegas falam consigo sobre o seu desempenho no trabalho?", "46": "Se necessário, a sua chefia imediata ouve os seus problemas relacionados com o trabalho?", "47": "Se necessário, consegue apoio e ajuda da sua chefia imediata para o trabalho?", "48": "A sua chefia imediata fala consigo sobre o seu desempenho no trabalho?"
    },
    "Comunidade, Segurança e Justiça": {
        "49": "Existe um bom clima de trabalho entre os colegas?", "50": "Sente-se parte de uma equipe no seu local de trabalho?", "51": "Existe uma boa cooperação entre os colegas de trabalho?", "52": "Está preocupado em vir a ficar desempregado?", "53": "Está preocupado com a dificuldade em encontrar outro emprego, caso seja despedido?", "54": "Está preocupado em ser transferido para outro departamento ou função contra a sua vontade?", "55": "Está preocupado com a possibilidade de o seu cronograma de trabalho ser alterado contra a sua vontade?", "56": "Está preocupado com a possibilidade de o seu rendimento diminuir?", "64": "Os conflitos no seu local de trabalho são resolvidos de modo justo?", "65": "O trabalho é distribuído de forma justa?", "66": "As sugestões dos trabalhadores são tratadas de forma séria pela gestão de topo?", "67": "Quando os trabalhadores fazem um bom trabalho são reconhecidos?"
    },
    "Confiança e Equilíbrio Pessoal": {
        "57": "Está satisfeito com a qualidade do trabalho que executa?", "58": "No geral, os empregados confiam uns nos outros?", "59": "Os empregados escondem informações uns dos outros?", "60": "Os empregados escondem informações da gerência?", "61": "A gerência confia nos empregados para fazerem bem o seu trabalho?", "62": "Os empregados confiam na informação que recebem da gerência?", "63": "Os empregados podem expressar os seus sentimentos e pontos de vista à gerência?", "68": "Sente que o seu trabalho lhe exige tanta energia, que acaba por afetar a sua vida privada / familiar negativamente?", "69": "Sente que o seu trabalho lhe exige tanto tempo, que acaba por afetar a sua vida privada / familiar negativamente?", "70": "As exigências do seu trabalho interferem com a sua vida privada e familiar?"
    },
    "Satisfação e Saúde Geral": {
        "71": "As suas perspetivas de trabalho?", "72": "O seu trabalho de uma forma global?", "73": "A forma como as suas capacidades e competências são usadas?", "74": "Em geral, sente que a sua saúde é:", "75": "Sou sempre capaz de resolver problemas se tentar o suficiente.", "76": "É fácil seguir os meus planos e atingir os meus objectivos.", "77": "Sentiu dificuldade em adormecer?", "78": "Acordou várias vezes durante a noite e depois não conseguia adormecer novamente?", "79": "Tem-se sentido fisicamente exausto/a?", "80": "Tem-se sentido emocionalmente exausto/a?", "81": "Tem-se sentido tenso/a?", "82": "Tem-se sentido triste ou deprimido/a?", "83": "Tem tido falta de interesse pelas suas atividades diárias?", "84": "Tem tido falta de interesse pelas pessoas que o/a rodeiam?"
    }
}
total_perguntas = sum(len(p) for p in perguntas_agrupadas.values())

# --- INTERFACE PRINCIPAL ---
st.title("Diagnóstico de Riscos Psicossociais (COPSOQ III)")
st.markdown("Bem-vindo(a)! Sua participação é **100% confidencial e anônima** e essencial para construirmos um ambiente de trabalho melhor. Por favor, responda com base nas suas experiências das **últimas 4 semanas**.")
st.divider()

# --- BARRA DE PROGRESSO ---
perguntas_respondidas = len(st.session_state.respostas)
progresso = perguntas_respondidas / total_perguntas
st.progress(progresso, text=f"Progresso: {perguntas_respondidas} de {total_perguntas} perguntas respondidas ({progresso:.0%})")

# --- NAVEGAÇÃO POR ABAS ---
lista_de_abas = list(perguntas_agrupadas.keys())
tabs = st.tabs(lista_de_abas)

for i, (nome_tema, perguntas) in enumerate(perguntas_agrupadas.items()):
    with tabs[i]:
        st.subheader(nome_tema)
        
        # Validação para a aba
        perguntas_na_aba = len(perguntas)
        respostas_na_aba = len([key for key in st.session_state.respostas if key in perguntas.keys()])
        if respostas_na_aba == perguntas_na_aba:
            st.info(f"✅ Você completou todas as {perguntas_na_aba} perguntas desta seção!")
        else:
            st.warning(f"Faltam {perguntas_na_aba - respostas_na_aba} perguntas nesta seção.")

        for num_pergunta, texto_pergunta in perguntas.items():
            with st.container(border=True):
                st.markdown(f"**Pergunta {num_pergunta}:** {texto_pergunta}")
                # Usar o callback on_change é mais eficiente para atualizar o estado
                st.radio(
                    "Sua resposta:",
                    options=opcoes_frequencia,
                    key=f"q_{num_pergunta}",
                    index=None,
                    horizontal=True,
                    label_visibility="collapsed",
                    on_change=lambda: st.session_state.respostas.update({st.session_state[f'q_{num_pergunta}']: num_pergunta})
                )
st.divider()

# --- LÓGICA DE FINALIZAÇÃO E CÁLCULO ---
if progresso == 1.0:
    st.success("🎉 Excelente! Você respondeu a todas as perguntas.")
    if st.button("Finalizar e Ver Meu Diagnóstico", type="primary", use_container_width=True):
        with st.spinner('Analisando suas respostas...'):
            # Organiza as respostas na ordem correta de 1 a 84
            respostas_ordenadas = [st.session_state[f"q_{i}"] for i in range(1, total_perguntas + 1)]
            
            pontuacoes = motor.calcular_pontuacoes(respostas_ordenadas)
            resultados = motor.calcular_escalas_finais(pontuacoes)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nomes_escalas_ordenadas = list(motor.definicao_escalas.keys())
            resultados_ordenados = [resultados.get(nome, "") for nome in nomes_escalas_ordenadas]
            linha_para_salvar = [timestamp] + respostas_ordenadas + resultados_ordenados
            
            sucesso_ao_salvar = salvar_dados(linha_para_salvar)
            if sucesso_ao_salvar:
                st.balloons()
                st.success("Diagnóstico concluído e dados salvos anonimamente. Obrigado pela sua contribuição!")
                
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
    st.warning("Por favor, navegue por todas as abas e responda a todas as perguntas para habilitar o botão de finalização.")
