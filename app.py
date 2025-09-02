# Importamos todas as bibliotecas necessárias
import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq as motor # Seu motor de cálculo!

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(layout="wide", page_title="Diagnóstico COPSOQ III")

# --- FUNÇÕES GLOBAIS E DE BANCO DE DADOS ---
NOME_DA_SUA_PLANILHA = 'Resultados_COPSOQ'

@st.cache_resource(ttl=600) # Cache do recurso para evitar reconexões constantes
def conectar_gsheet():
    """Conecta-se à Planilha Google usando as credenciais do Streamlit Secrets."""
    creds = dict(st.secrets["gcp_service_account"])
    # CORREÇÃO CRÍTICA: Garante que as quebras de linha na chave privada sejam formatadas corretamente.
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds)
    return gc

@st.cache_data(ttl=60) # Cache dos dados por 60 segundos
def carregar_dados_completos(_gc):
    """
    Carrega todos os dados da planilha de forma robusta, ignorando o cabeçalho da planilha
    e aplicando um cabeçalho correto internamente.
    """
    try:
        spreadsheet = _gc.open(NOME_DA_SUA_PLANILHA)
        worksheet = spreadsheet.sheet1
        
        todos_os_valores = worksheet.get_all_values()
        
        # Se houver menos de 2 linhas (só cabeçalho ou vazio), não há dados.
        if len(todos_os_valores) < 2:
            return pd.DataFrame()

        # Pega apenas as linhas de dados, ignorando o cabeçalho da planilha.
        dados = todos_os_valores[1:]

        # Define o cabeçalho completo e correto aqui no código.
        cabecalhos_respostas = [f"Resp_Q{i}" for i in range(1, 85)]
        cabecalhos_escalas = list(motor.definicao_escalas.keys())
        cabecalho_correto = ["Timestamp"] + cabecalhos_respostas + cabecalhos_escalas
        
        # Cria o DataFrame, garantindo que o número de colunas corresponda.
        # Pega o número de colunas da primeira linha de dados para evitar erros.
        num_cols_data = len(dados[0])
        cabecalho_para_usar = cabecalho_correto[:num_cols_data]
        
        df = pd.DataFrame(dados, columns=cabecalho_para_usar)
        
        return df
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro: A planilha '{NOME_DA_SUA_PLANILHA}' não foi encontrada. Verifique o nome e as permissões de compartilhamento.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()

# ==============================================================================
# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO (O QUE O COLABORADOR VÊ) ---
# ==============================================================================
def pagina_do_questionario():
    if 'respostas' not in st.session_state:
        st.session_state.respostas = {str(i): None for i in range(1, 85)}

    def salvar_dados(lista_de_dados):
        try:
            gc = conectar_gsheet()
            spreadsheet = gc.open(NOME_DA_SUA_PLANILHA)
            worksheet = spreadsheet.sheet1
            # Verifica se a planilha está completamente vazia para adicionar o cabeçalho
            if not worksheet.get_all_values():
                cabecalhos_respostas = [f"Resp_Q{i}" for i in range(1, 85)]
                cabecalhos_escalas = list(motor.definicao_escalas.keys())
                cabecalho_completo = ["Timestamp"] + cabecalhos_respostas + cabecalhos_escalas
                worksheet.update('A1', [cabecalho_completo])
            worksheet.append_row(lista_de_dados)
            return True
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
            return False

    def obter_cor_e_significado(nome_escala, valor):
        if valor is None: return "#6c757d", "N/A"
        try:
            valor = float(valor)
        except (ValueError, TypeError):
            return "#6c757d", "N/A"
        escalas_de_risco = ["Exigências Quantitativas", "Ritmo de Trabalho", "Exigências Cognitivas", "Exigências Emocionais", "Conflitos de Papéis Laborais", "Insegurança Laboral", "Insegurança nas Condições de Trabalho", "Conflito Trabalho-Família", "Problemas de Sono", "Burnout", "Stress", "Sintomas Depressivos"]
        verde = "#28a745"; amarelo = "#ffc107"; vermelho = "#dc3545"
        if valor <= 33.3: cor_padrao = verde
        elif 33.4 <= valor <= 66.6: cor_padrao = amarelo
        else: cor_padrao = vermelho
        if nome_escala not in escalas_de_risco:
            if cor_padrao == verde: return vermelho, f"{valor:.1f} (Crítico)"
            if cor_padrao == vermelho: return verde, f"{valor:.1f} (Favorável)"
            return amarelo, f"{valor:.1f} (Atenção)"
        significado = f"{valor:.1f}"
        if cor_padrao == verde: significado += " (Baixo Risco)"
        if cor_padrao == amarelo: significado += " (Atenção)"
        if cor_padrao == vermelho: significado += " (Alto Risco)"
        return cor_padrao, significado

    opcoes_frequencia = ("Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre")
    perguntas_agrupadas = {
        "💼 Ambiente e Carga de Trabalho": {"1": "A sua carga de trabalho acumula-se por ser mal distribuída?", "2": "Com que frequência fica com trabalho atrasado?", "3": "Com que frequência não tem tempo para completar todas as suas tarefas do seu trabalho?", "4": "Precisa de trabalhar muito rapidamente?", "5": "Trabalha a um ritmo elevado ao longo de toda a jornada de trabalho?", "6": "O seu trabalho exige a sua atenção constante?", "7": "O seu trabalho requer que memorize muitas informações?", "8": "O seu trabalho requer que seja bom a propor novas ideias?", "9": "O seu trabalho exige que tome decisões difíceis?"},
        "🧘 Exigências Emocionais e Autonomia": {"10": "O seu trabalho coloca-o/a em situações emocionalmente perturbadoras?", "11": "No seu trabalho tem de lidar com os problemas pessoais de outras pessoas?", "12": "O seu trabalho exige emocionalmente de si?", "13": "Tem um elevado grau de influência nas decisões sobre o seu trabalho?", "14": "Pode influenciar a quantidade de trabalho que lhe compete a si?", "15": "Tem influência sobre o que faz no seu trabalho?", "16": "Tem influência sobre como faz o seu trabalho?", "20": "Pode decidir quando fazer uma pausa?", "21": "Geralmente, pode tirar férias quando quer?", "22": "Pode deixar o seu local de trabalho por breves instantes para falar com um colega?"},
        "🌱 Desenvolvimento e Significado": {"17": "O seu trabalho dá-lhe a possibilidade de aprender coisas novas?", "18": "No seu trabalho, consegue usar as suas competências e conhecimentos?", "19": "O seu trabalho dá-lhe oportunidade para desenvolver as suas competências?", "23": "O seu trabalho é significativo para si?", "24": "Sente que o trabalho que faz é importante?", "25": "Sente-se motivado e envolvido no seu trabalho?"},
        "👥 Liderança, Gestão e Relações": {"26": "Gosta de falar sobre o seu local de trabalho com pessoas que não trabalham lá?", "27": "Sente orgulho em pertencer à sua organização?", "28": "É informado com a devida antecedência sobre decisões, mudanças ou planos importantes para o futuro?", "29": "Recebe todas as informações necessárias para fazer bem o seu trabalho?", "30": "O seu trabalho é reconhecido e apreciado pela gerência?", "31": "A gerência respeita os trabalhadores?", "32": "A gerência trata todos os trabalhadores de maneira justa?", "39": "A sua chefia imediata garante que os trabalhadores tenham boas oportunidades de desenvolvimento?", "40": "A sua chefia imediata é adequada no planejamento do trabalho?", "41": "A sua chefia imediata é adequada na resolução de conflitos?", "42": "A sua chefia imediata prioriza a satisfação no trabalho?"},
        "🤝 Apoio Social e Papel no Trabalho": {"33": "O seu trabalho tem objetivos claros?", "34": "Sabe exatamente quais são as suas áreas de responsabilidade?", "35": "Sabe exatamente o que se espera de si no trabalho?", "36": "No seu trabalho são-lhe solicitadas exigências contraditórias?", "37": "Tem que fazer coisas que parecem ser de modo diferente de como teriam sido planejadas?", "38": "Tem que fazer coisas que lhe parecem desnecessárias?", "43": "Se necessário, consegue apoio e ajuda dos seus colegas para o trabalho?", "44": "Se necessário, os seus colegas ouvem os seus problemas relacionados com o trabalho?", "45": "Os seus colegas falam consigo sobre o seu desempenho no trabalho?", "46": "Se necessário, a sua chefia imediata ouve os seus problemas relacionados com o trabalho?", "47": "Se necessário, consegue apoio e ajuda da sua chefia imediata para o trabalho?", "48": "A sua chefia imediata fala consigo sobre o seu desempenho no trabalho?"},
        "🛡️ Comunidade, Segurança e Justiça": {"49": "Existe um bom clima de trabalho entre os colegas?", "50": "Sente-se parte de uma equipe no seu local de trabalho?", "51": "Existe uma boa cooperação entre os colegas de trabalho?", "52": "Está preocupado em vir a ficar desempregado?", "53": "Está preocupado com a dificuldade em encontrar outro emprego, caso seja despedido?", "54": "Está preocupado em ser transferido para outro departamento ou função contra a sua vontade?", "55": "Está preocupado com a possibilidade de o seu cronograma de trabalho ser alterado contra a sua vontade?", "56": "Está preocupado com a possibilidade de o seu rendimento diminuir?", "64": "Os conflitos no seu local de trabalho são resolvidos de modo justo?", "65": "O trabalho é distribuído de forma justa?", "66": "As sugestões dos trabalhadores são tratadas de forma séria pela gestão de topo?", "67": "Quando os trabalhadores fazem um bom trabalho são reconhecidos?"},
        "⚖️ Confiança e Equilíbrio Pessoal": {"57": "Está satisfeito com a qualidade do trabalho que executa?", "58": "No geral, os empregados confiam uns nos outros?", "59": "Os empregados escondem informações uns dos outros?", "60": "Os empregados escondem informações da gerência?", "61": "A gerência confia nos empregados para fazerem bem o seu trabalho?", "62": "Os empregados confiam na informação que recebem da gerência?", "63": "Os empregados podem expressar os seus sentimentos e pontos de vista à gerência?", "68": "Sente que o seu trabalho lhe exige tanta energia, que acaba por afetar a sua vida privada / familiar negativamente?", "69": "Sente que o seu trabalho lhe exige tanto tempo, que acaba por afetar a sua vida privada / familiar negativamente?", "70": "As exigências do seu trabalho interferem com a sua vida privada e familiar?"},
        "❤️ Saúde e Satisfação Pessoal": {"71": "As suas perspetivas de trabalho?", "72": "O seu trabalho de uma forma global?", "73": "A forma como as suas capacidades e competências são usadas?", "74": "Em geral, sente que a sua saúde é:", "75": "Sou sempre capaz de resolver problemas se tentar o suficiente.", "76": "É fácil seguir os meus planos e atingir os meus objectivos.", "77": "Sentiu dificuldade em adormecer?", "78": "Acordou várias vezes durante a noite e depois não conseguia adormecer novamente?", "79": "Tem-se sentido fisicamente exausto/a?", "80": "Tem-se sentido emocionalmente exausto/a?", "81": "Tem-se sentido tenso/a?", "82": "Tem-se sentido triste ou deprimido/a?", "83": "Tem tido falta de interesse pelas suas atividades diárias?", "84": "Tem tido falta de interesse pelas pessoas que o/a rodeiam?"}
    }
    total_perguntas = sum(len(p) for p in perguntas_agrupadas.values())

    st.title("Diagnóstico de Riscos Psicossociais (COPSOQ III)")
    with st.expander("Clique aqui para ver as instruções completas", expanded=True):
        st.markdown("""
        **Prezado(a) Colaborador(a),**

        Bem-vindo(a)! Sua participação é um passo fundamental para construirmos, juntos, um ambiente de trabalho mais saudável.

        - **Confidencialidade:** Suas respostas são **100% confidenciais e anônimas**. Os resultados são sempre analisados de forma agrupada.
        - **Sinceridade:** Por favor, responda com base nas suas experiências das **últimas 4 semanas**. Não há respostas "certas" ou "erradas".
        - **Como Navegar:** A pesquisa está dividida em **8 seções (abas)**, como pode ver abaixo.
            1. Responda a todas as perguntas de uma seção.
            2. Clique na próxima aba para continuar.
            3. Repita o processo até que a barra de progresso atinja 100%.
        - **Finalização:** O botão para finalizar e ver seu diagnóstico só aparecerá quando **todas as 84 perguntas** forem respondidas.

        A sua contribuição é extremamente valiosa. Muito obrigado!
        """)
    st.divider()

    perguntas_respondidas = len([r for r in st.session_state.respostas.values() if r is not None])
    progresso = perguntas_respondidas / total_perguntas
    st.progress(progresso, text=f"Progresso Geral: {perguntas_respondidas} de {total_perguntas} perguntas respondidas ({progresso:.0%})")
    st.markdown("---")


    lista_de_abas = list(perguntas_agrupadas.keys())
    tabs = st.tabs(lista_de_abas)

    for i, (nome_tema, perguntas) in enumerate(perguntas_agrupadas.items()):
        with tabs[i]:
            perguntas_na_aba = len(perguntas)
            respostas_na_aba = len([key for key in st.session_state.respostas if key in perguntas.keys() and st.session_state.respostas[key] is not None])
            if respostas_na_aba == perguntas_na_aba:
                st.info(f"✅ **Ótimo!** Você completou todas as {perguntas_na_aba} perguntas desta seção.")
            else:
                st.warning(f"**Faltam {perguntas_na_aba - respostas_na_aba} perguntas nesta seção.**")

            for num_pergunta, texto_pergunta in perguntas.items():
                with st.container(border=True):
                    st.markdown(f"**Pergunta {num_pergunta}:** {texto_pergunta}")
                    resposta_atual = st.session_state.respostas[num_pergunta]
                    indice_selecionado = opcoes_frequencia.index(resposta_atual) if resposta_atual is not None else None
                    
                    st.radio(
                        "Sua resposta:",
                        options=opcoes_frequencia,
                        key=f"q_{num_pergunta}",
                        index=indice_selecionado,
                        horizontal=True,
                        label_visibility="collapsed",
                        on_change=lambda n=num_pergunta: st.session_state.respostas.update({n: st.session_state[f'q_{n}']})
                    )
    st.divider()

    if progresso == 1.0:
        st.success("🎉 **Parabéns! Você respondeu a todas as perguntas.**")
        st.markdown("Clique no botão abaixo para finalizar e receber seu diagnóstico psicossocial individual e anônimo.")
        if st.button("Finalizar e Ver Meu Diagnóstico", type="primary", use_container_width=True):
            with st.spinner('Analisando suas respostas... Por favor, aguarde.'):
                respostas_ordenadas = [st.session_state.respostas[str(i)] for i in range(1, total_perguntas + 1)]
                
                pontuacoes = motor.calcular_pontuacoes(respostas_ordenadas)
                resultados = motor.calcular_escalas_finais(pontuacoes)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nomes_escalas_ordenadas = list(motor.definicao_escalas.keys())
                resultados_ordenados = [resultados.get(nome, "") for nome in nomes_escalas_ordenadas]
                linha_para_salvar = [timestamp] + respostas_ordenadas + resultados_ordenados
                
                if salvar_dados(linha_para_salvar):
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
                                <h3 style="color:white; font-size: 16px; font-weight: bold; margin-bottom: 10px;">{nome}</h3>
                                <p style="color:white; font-size: 22px; font-weight: bold; margin-top: 5px;">{texto_valor}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        col_index = (col_index + 1) % 3
    else:
        st.info("Por favor, navegue por todas as abas e responda às perguntas restantes para habilitar o botão de finalização.")

# ==============================================================================
# --- PÁGINA 2: PAINEL DO ADMINISTRADOR (O QUE O CONSULTOR VÊ) ---
# ==============================================================================
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor")
    
    # --- Lógica de Autenticação Robusta ---
    try:
        SENHA_CORRETA = st.secrets["admin"]["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("A senha de administrador não foi configurada corretamente na seção [admin] dos 'Secrets'.")
        st.info("Por favor, verifique a sua configuração de 'Secrets' no Streamlit Cloud.")
        st.code("""
# Exemplo de formato correto nos Secrets:
[gcp_service_account]
# ...suas chaves do google aqui...
[admin]
ADMIN_PASSWORD = "sua_senha_aqui"
        """)
        return

    st.header("Acesso à Área Restrita")
    senha_inserida = st.text_input("Por favor, insira a senha de acesso:", type="password", key="admin_password_input")
    
    if not senha_inserida:
        st.info("Esta é uma área restrita para análise dos resultados consolidados.")
        return

    if senha_inserida != SENHA_CORRETA:
        st.error("Senha incorreta. Tente novamente.")
        return

    st.success("Acesso garantido!")
    
    # --- Carregamento dos Dados ---
    gc = conectar_gsheet()
    df = carregar_dados_completos(gc)

    if df.empty:
        st.warning("Ainda não há dados para analisar ou ocorreu um erro ao carregar a planilha. Assim que houver respostas, os gráficos aparecerão aqui.")
        return

    # --- Funcionalidade de Exportação de Dados ---
    st.header("📥 Exportar Dados Brutos")
    st.write("Clique no botão abaixo para descarregar todos os dados recolhidos (respostas e pontuações) num ficheiro CSV, compatível com Excel e outras ferramentas de análise.")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
       label="Descarregar todos os dados (.csv)",
       data=csv,
       file_name='dados_completos_copsoq.csv',
       mime='text/csv',
    )
    st.divider()

    # --- Dashboard de Análise ---
    st.header("📊 Painel de Resultados Gerais")
    total_respostas = len(df)
    st.metric("Total de Respostas Recebidas", f"{total_respostas}")

    st.subheader("Média Geral por Escala (0-100)")
    
    nomes_escalas = list(motor.definicao_escalas.keys())
    df_analise = df.copy()

    for escala in nomes_escalas:
        if escala in df_analise.columns:
            # CORREÇÃO DE LOCALIDADE: Substitui vírgula por ponto.
            if df_analise[escala].dtype == 'object':
                 df_analise[escala] = df_analise[escala].str.replace(',', '.', regex=False)
            
            # Converte para numérico, forçando erros a virarem NaN (Not a Number)
            df_analise[escala] = pd.to_numeric(df_analise[escala], errors='coerce')
    
    with st.expander("Clique aqui para ver o Diagnóstico de Dados"):
        st.write("Amostra dos dados brutos (primeiras 5 linhas), como foram lidos da planilha:")
        st.dataframe(df.head())
        st.write("A tabela abaixo mostra os tipos de dados de cada coluna após a tentativa de conversão para número. As colunas das escalas devem ser do tipo `float64` ou `int64`.")
        st.dataframe(df_analise.dtypes.astype(str).reset_index().rename(columns={'index': 'Coluna', 0: 'Tipo de Dado'}))

    # Filtra apenas as colunas que são de fato numéricas para fazer os cálculos
    escalas_presentes = [escala for escala in nomes_escalas if escala in df_analise.columns and pd.api.types.is_numeric_dtype(df_analise[escala])]
    
    if not escalas_presentes:
        st.error("Erro de Análise: Nenhuma coluna de escala com dados numéricos válidos foi encontrada. Verifique se os dados em sua Planilha Google estão corretos.")
        return

    medias = df_analise[escalas_presentes].mean().sort_values(ascending=False)
    df_medias = medias.reset_index()
    df_medias.columns = ['Escala', 'Pontuação Média']

    if not df_medias.empty:
        st.dataframe(df_medias.style.format({'Pontuação Média': "{:.2f}"}))

        fig = px.bar(
            df_medias,
            x='Pontuação Média',
            y='Escala',
            orientation='h',
            title='Pontuação Média para Cada Escala do COPSOQ III',
            text='Pontuação Média'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=800, xaxis_title="Pontuação Média (0-100)", yaxis_title="")
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---
# ==============================================================================
def main():
    """Verifica a URL para decidir qual página mostrar."""
    params = st.query_params
    
    if params.get("page") == "admin":
        pagina_do_administrador()
    else:
        pagina_do_questionario()

if __name__ == "__main__":
    main()

