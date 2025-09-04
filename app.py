# Importamos todas as bibliotecas necessárias
import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq as motor # O motor de cálculo da versão PT
from fpdf import FPDF
import io
import requests

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(layout="wide", page_title="Diagnóstico COPSOQ III - PT")

# --- URL DO LOGO ---
LOGO_URL = "https://i.imgur.com/4l7Drym.png"

# --- FUNÇÕES GLOBAIS E DE BANCO DE DADOS ---
NOME_DA_SUA_PLANILHA = 'Resultados_COPSOQ'

@st.cache_resource(ttl=600)
def conectar_gsheet():
    """Conecta-se à Planilha Google usando as credenciais do Streamlit Secrets."""
    creds = dict(st.secrets["gcp_service_account"])
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds)
    return gc

@st.cache_data(ttl=60)
def carregar_dados_completos(_gc):
    """
    Carrega todos os dados da planilha de forma robusta, ignorando o cabeçalho da planilha
    e aplicando um cabeçalho correto internamente.
    """
    try:
        spreadsheet = _gc.open(NOME_DA_SUA_PLANILHA)
        worksheet = spreadsheet.sheet1
        
        todos_os_valores = worksheet.get_all_values()
        
        if len(todos_os_valores) < 2:
            return pd.DataFrame()

        dados = todos_os_valores[1:]

        cabecalhos_respostas = [f"Resp_Q{i}" for i in range(1, 85)]
        cabecalhos_escalas = list(motor.definicao_escalas.keys())
        cabecalho_correto = ["Timestamp"] + cabecalhos_respostas + cabecalhos_escalas
        
        num_cols_data = len(dados[0])
        cabecalho_para_usar = cabecalho_correto[:num_cols_data]
        
        df = pd.DataFrame(dados, columns=cabecalho_para_usar)
        
        return df
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro: A planilha '{NOME_DA_SUA_PLANILHA}' não foi encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
class PDF(FPDF):
    def header(self):
        try:
            response = requests.get(LOGO_URL, timeout=5)
            response.raise_for_status()
            logo_bytes = io.BytesIO(response.content)
            self.image(logo_bytes, x=10, y=8, w=35)
            self.ln(20)
        except Exception as e:
            st.warning(f"Não foi possível carregar o logo para o PDF: {e}")
            self.ln(10)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Diagnóstico Psicossocial - COPSOQ III', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_relatorio_pdf(df_medias, total_respostas):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Sumário dos Resultados', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Este relatório apresenta a média consolidada dos resultados do questionário COPSOQ III, com base num total de {total_respostas} respostas recolhidas.")
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Tabela de Pontuações Médias por Escala', 0, 1, 'L')
    pdf.set_font('Arial', 'B', 10)
    col_width_escala = 130
    col_width_pontuacao = 40
    pdf.cell(col_width_escala, 10, 'Escala', 1, 0, 'C')
    pdf.cell(col_width_pontuacao, 10, 'Pontuação Média', 1, 1, 'C')
    pdf.set_font('Arial', '', 10)
    for index, row in df_medias.iterrows():
        pdf.cell(col_width_escala, 8, row['Escala'].encode('latin-1', 'replace').decode('latin-1'), 1, 0)
        pdf.cell(col_width_pontuacao, 8, f"{row['Pontuação Média']:.2f}", 1, 1, 'C')
    pdf.ln(10)
    
    return pdf.output()

# ==============================================================================
# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO ---
# ==============================================================================
def pagina_do_questionario():
    # O código do questionário que já funciona perfeitamente permanece aqui
    # ...
    pass # Omitido por brevidade para focar na correção do painel


# ==============================================================================
# --- PÁGINA 2: PAINEL DO ADMINISTRADOR ---
# ==============================================================================
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor")
    
    try:
        SENHA_CORRETA = st.secrets["admin"]["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("A senha de administrador não foi configurada na secção [admin] dos 'Secrets'.")
        return

    st.header("Acesso à Área Restrita")
    senha_inserida = st.text_input("Por favor, insira a senha de acesso:", type="password")
    
    if not senha_inserida: return
    if senha_inserida != SENHA_CORRETA:
        st.error("Senha incorreta.")
        return

    st.success("Acesso garantido!")
    st.divider()
    
    gc = conectar_gsheet()
    df = carregar_dados_completos(gc)

    if df.empty:
        st.warning("Ainda não há dados para analisar.")
        return

    st.header("📊 Painel de Resultados Gerais")
    total_respostas = len(df)
    st.metric("Total de Respostas Recebidas", f"{total_respostas}")

    nomes_escalas = list(motor.definicao_escalas.keys())
    df_analise = df.copy()

    for escala in nomes_escalas:
        if escala in df_analise.columns:
            if df_analise[escala].dtype == 'object':
                 df_analise[escala] = df_analise[escala].str.replace(',', '.', regex=False)
            df_analise[escala] = pd.to_numeric(df_analise[escala], errors='coerce')
    
    escalas_presentes = [escala for escala in nomes_escalas if escala in df_analise.columns and pd.api.types.is_numeric_dtype(df_analise[escala])]
    
    if not escalas_presentes:
        st.error("Erro de Análise: Nenhuma coluna de escala com dados numéricos válidos foi encontrada.")
        return

    medias = df_analise[escalas_presentes].mean().sort_values(ascending=True)
    df_medias = medias.reset_index()
    df_medias.columns = ['Escala', 'Pontuação Média']
    
    # --- LÓGICA DO SEMÁFORO (REINTRODUZIDA) ---
    def estilo_semaforo(row):
        valor = row['Pontuação Média']
        # Esta lógica simplificada assume que valores mais altos são piores.
        # Pode ser aprimorada para diferenciar escalas de risco e recurso.
        if valor <= 33.3: return ['background-color: #28a745'] * 2 # Verde
        elif valor <= 66.6: return ['background-color: #ffc107'] * 2 # Amarelo
        else: return ['background-color: #dc3545'] * 2 # Vermelho

    st.subheader("Média Geral por Escala (0-100)")
    if not df_medias.empty:
        # APLICA O ESTILO DO SEMÁFORO À TABELA
        st.dataframe(df_medias.style.apply(estilo_semaforo, axis=1).format({'Pontuação Média': "{:.2f}"}), use_container_width=True)
        
        # ADICIONA AS CORES AO GRÁFICO
        fig = px.bar(
            df_medias,
            x='Pontuação Média',
            y='Escala',
            orientation='h',
            title='Pontuação Média para Cada Escala do COPSOQ III',
            text='Pontuação Média',
            color='Pontuação Média',
            color_continuous_scale='RdYlGn_r' # Escala de cores Vermelho-Amarelo-Verde
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=800, xaxis_title="Pontuação Média (0-100)", yaxis_title="")
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.header("📄 Gerar Relatório e Exportar Dados")
    col1, col2 = st.columns(2)
    with col1:
        if not df_medias.empty:
            pdf_bytes = gerar_relatorio_pdf(df_medias, total_respostas)
            st.download_button(label="Descarregar Relatório (.pdf)", data=pdf_bytes, file_name='relatorio_copsoq.pdf', mime='application/pdf')
    with col2:
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Descarregar Dados Brutos (.csv)", data=csv, file_name='dados_brutos_copsoq.csv', mime='text/csv')


# ==============================================================================
# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---
# ==============================================================================
def main():
    """Verifica a URL para decidir qual página mostrar."""
    params = st.query_params
    
    if params.get("page") == "admin":
        pagina_do_administrador()
    else:
        # Por simplicidade, o código do questionário foi omitido. 
        # ATENÇÃO: É necessário colar aqui o código completo da função pagina_do_questionario
        # que já temos no nosso histórico para a ferramenta funcionar.
        st.title("Página do Questionário")
        st.info("O código completo do questionário precisa de ser inserido aqui.")


if __name__ == "__main__":
    main()

