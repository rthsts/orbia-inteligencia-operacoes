import os
import re
import time
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import pandas as pd

from google import genai

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================

st.set_page_config(
    page_title="ORBIA | Inteligência de Operações",
    page_icon="🌌",
    layout="wide"
)


# ==========================================
# IDENTIDADE VISUAL
# ==========================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #071426, #102B45);
    color: #FFFFFF;
}

h1, h2, h3 {
    color: #36C5F0 !important;
}

p, label {
    color: #DCEAF5;
}

.stButton > button {
    background-color: #087EA4;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #36C5F0;
    color: #071426;
}

[data-testid="stMetricValue"] {
    color: #36C5F0;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# CABEÇALHO
# ==========================================

st.title("🌌 ORBIA")

st.subheader(
    "Inteligência de Operações Comerciais"
)

st.markdown("""
Transforme dados operacionais em informações estratégicas
com análise inteligente e relatórios automatizados.
""")

st.divider()


# ==========================================
# FUNÇÃO: INDICADORES
# ==========================================

def atualizar_indicadores(pedidos):

    total = len(pedidos)

    atrasados = (
        pedidos["Situacao_Prazo"] == "Atrasado"
    ).sum()

    criticos = (
        pedidos["Prioridade_Operacional"] == "Crítica"
    ).sum()

    valor_pendente = pedidos["Valor_Pendente"].sum()

    percentual_atrasados = (
        atrasados / total * 100 if total else 0
    )

    percentual_pendente = (
        valor_pendente / pedidos["Valor_Pedido"].sum() * 100
        if pedidos["Valor_Pedido"].sum() else 0
    )

    return {
        "total_pedidos": int(total),
        "pedidos_atrasados": int(atrasados),
        "pedidos_criticos": int(criticos),
        "valor_pendente": float(valor_pendente),
        "percentual_atrasados": float(percentual_atrasados),
        "percentual_pendente": float(percentual_pendente)
    }


# ==========================================
# FUNÇÃO: ANÁLISE COM GEMINI
# ==========================================

def gerar_analise(indicadores):

    chave_api = os.getenv("GEMINI_API_KEY")

    if not chave_api:
        raise ValueError(
            "A chave da API do Gemini não foi encontrada. "
            "Verifique se a variável GEMINI_API_KEY está configurada."
        )

    cliente_ia = genai.Client(api_key=chave_api)

    prompt = f"""
Você é a inteligência analítica da ORBIA,
um projeto de inteligência de operações comerciais.

Analise exclusivamente os indicadores desta base fictícia:

- Total de pedidos: {indicadores["total_pedidos"]}
- Pedidos atrasados: {indicadores["pedidos_atrasados"]}
- Pedidos críticos: {indicadores["pedidos_criticos"]}
- Valor pendente: R$ {indicadores["valor_pendente"]:,.2f}
- Percentual de pedidos atrasados: {indicadores["percentual_atrasados"]:.2f}%
- Percentual do valor pendente: {indicadores["percentual_pendente"]:.2f}%

Organize a resposta nas seguintes seções:

1. DIAGNÓSTICO OPERACIONAL
Interprete os indicadores e apresente os percentuais relevantes.
Explique o que os números revelam sobre a situação atual.

2. RISCOS E LIMITAÇÕES
Diferencie fatos confirmados de riscos hipotéticos.
Não invente causas para os atrasos nem presuma inadimplência,
cancelamentos ou bloqueios de faturamento.

3. AÇÕES PRIORITÁRIAS
Recomende três ações operacionais práticas.
Priorize a investigação dos pedidos críticos e das causas dos atrasos.
Explique brevemente a finalidade de cada ação.

REGRAS:
- Utilize somente os indicadores fornecidos.
- Não mencione erros de programação ou conexão.
- Não afirme ter analisado pedidos individualmente.
- Não invente dados nem afirme que ações foram realizadas.
- Escreva em português brasileiro, com clareza e objetividade.
"""

    # Faz até três tentativas quando o serviço está temporariamente indisponível.
    # Os intervalos evitam repetir a chamada imediatamente.
    intervalos_espera = [3, 8]
    ultimo_erro = None

    for tentativa in range(3):

        try:
            resposta = cliente_ia.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if not resposta.text:
                raise ValueError(
                    "O Gemini não retornou uma análise."
                )

            return resposta.text

        except Exception as erro:

            ultimo_erro = erro
            mensagem_erro = str(erro).upper()

            erro_temporario = any(
                codigo in mensagem_erro
                for codigo in (
                    "429",
                    "500",
                    "502",
                    "503",
                    "504",
                    "UNAVAILABLE",
                    "RESOURCE_EXHAUSTED",
                    "INTERNAL"
                )
            )

            # Erros que não parecem temporários não são repetidos.
            if not erro_temporario:
                raise

            # Se ainda houver tentativas, aguarda antes de tentar novamente.
            if tentativa < 2:
                time.sleep(intervalos_espera[tentativa])

    raise RuntimeError(
        "O serviço do Gemini permaneceu indisponível após três tentativas. "
        "A planilha foi recebida, mas a análise por IA não pôde ser concluída. "
        "Tente novamente mais tarde. "
        f"Detalhe técnico: {ultimo_erro}"
    )


# ==========================================
# FUNÇÃO: GERAR PDF
# ==========================================

def gerar_pdf(indicadores, analise):

    memoria = BytesIO()

    azul_marinho = colors.HexColor("#101B2D")
    ciano = colors.HexColor("#45D9F5")
    cinza_claro = colors.HexColor("#F1F5F9")
    cinza_texto = colors.HexColor("#475569")

    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloOrbia",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=31,
        textColor=azul_marinho,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    estilos.add(ParagraphStyle(
        name="SubtituloOrbia",
        parent=estilos["Normal"],
        fontSize=10,
        leading=15,
        textColor=cinza_texto,
        alignment=TA_CENTER,
        spaceAfter=18
    ))

    estilos.add(ParagraphStyle(
        name="SecaoOrbia",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=azul_marinho,
        spaceBefore=14,
        spaceAfter=8
    ))

    estilos.add(ParagraphStyle(
        name="TextoOrbia",
        parent=estilos["BodyText"],
        fontSize=9,
        leading=14,
        textColor=cinza_texto,
        spaceAfter=6
    ))

    conteudo = []

    conteudo.append(
        Paragraph("ORBIA", estilos["TituloOrbia"])
    )

    conteudo.append(
        Paragraph(
            "INTELIGÊNCIA DE OPERAÇÕES COMERCIAIS",
            estilos["SubtituloOrbia"]
        )
    )

    conteudo.append(
        Paragraph(
            "RELATÓRIO DE ANÁLISE OPERACIONAL",
            estilos["SecaoOrbia"]
        )
    )

    conteudo.append(
        Paragraph(
            f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            estilos["TextoOrbia"]
        )
    )

    conteudo.append(Spacer(1, 10))

    conteudo.append(
        Paragraph(
            "1. INDICADORES OPERACIONAIS",
            estilos["SecaoOrbia"]
        )
    )

    dados_tabela = [
        ["Indicador", "Resultado"],
        ["Total de pedidos", str(indicadores["total_pedidos"])],
        ["Pedidos atrasados", str(indicadores["pedidos_atrasados"])],
        ["Pedidos críticos", str(indicadores["pedidos_criticos"])],
        ["Valor pendente", f'R$ {indicadores["valor_pendente"]:,.2f}'],
        ["Pedidos atrasados (%)", f'{indicadores["percentual_atrasados"]:.2f}%'],
        ["Valor pendente (%)", f'{indicadores["percentual_pendente"]:.2f}%']
    ]

    tabela = Table(
        dados_tabela,
        colWidths=[9 * cm, 7 * cm],
        repeatRows=1
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), azul_marinho),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), cinza_claro),
        ("TEXTCOLOR", (0, 1), (-1, -1), azul_marinho),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("PADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    conteudo.append(tabela)

    conteudo.append(
        Paragraph(
            "2. ANÁLISE INTELIGENTE",
            estilos["SecaoOrbia"]
        )
    )

    for linha in analise.splitlines():

        linha = linha.strip()

        if not linha:
            conteudo.append(Spacer(1, 4))
            continue

        linha = re.sub(r"^\s*#+\s*", "", linha)
        linha = linha.replace("**", "").replace("*", "")

        conteudo.append(
            Paragraph(
                escape(linha),
                estilos["TextoOrbia"]
            )
        )

    conteudo.append(Spacer(1, 16))

    conteudo.append(
        Paragraph(
            "Documento demonstrativo elaborado com dados fictícios. "
            "As recomendações geradas por IA devem ser validadas "
            "antes de qualquer aplicação em contexto real.",
            estilos["TextoOrbia"]
        )
    )

    documento.build(conteudo)

    memoria.seek(0)

    return memoria.getvalue()


# ==========================================
# ENVIO DA PLANILHA
# ==========================================

st.header("📊 Análise operacional")

arquivo = st.file_uploader(
    "Selecione sua planilha de pedidos",
    type=["xlsx"]
)


# ==========================================
# PROCESSAMENTO
# ==========================================

if arquivo:

    st.success(f"Arquivo recebido: {arquivo.name}")

    if st.button("✨ Iniciar análise"):

        with st.spinner(
            "A ORBIA está analisando os dados. "
            "Se o serviço estiver ocupado, novas tentativas serão realizadas..."
        ):

            try:

                pedidos = pd.read_excel(
                    arquivo,
                    sheet_name="Pedidos"
                )

                colunas_obrigatorias = [
                    "Pedido_ID",
                    "Cliente_ID",
                    "Valor_Pedido",
                    "Situacao_Prazo",
                    "Alerta_Documental",
                    "Alerta_Cadastral",
                    "Valor_Pendente",
                    "Prioridade_Operacional"
                ]

                faltantes = [
                    coluna for coluna in colunas_obrigatorias
                    if coluna not in pedidos.columns
                ]

                if faltantes:
                    raise ValueError(
                        "Colunas não encontradas na planilha: "
                        + ", ".join(faltantes)
                    )

                indicadores = atualizar_indicadores(pedidos)

                analise = gerar_analise(indicadores)

                pdf = gerar_pdf(indicadores, analise)

                st.session_state["indicadores"] = indicadores
                st.session_state["analise"] = analise
                st.session_state["pdf"] = pdf

                st.success("Análise concluída com sucesso!")

            except Exception as erro:

                st.error("Não foi possível concluir a análise.")

                st.write(
                    f"Tipo de erro: {type(erro).__name__}"
                )

                st.write(f"Detalhes: {erro}")


# ==========================================
# RESULTADOS
# ==========================================

if "indicadores" in st.session_state:

    indicadores = st.session_state["indicadores"]

    st.divider()

    st.header("📈 Indicadores operacionais")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total de pedidos",
        indicadores["total_pedidos"]
    )

    col2.metric(
        "Pedidos atrasados",
        indicadores["pedidos_atrasados"],
        f'{indicadores["percentual_atrasados"]:.2f}%'
    )

    col3.metric(
        "Pedidos críticos",
        indicadores["pedidos_criticos"]
    )

    col4.metric(
        "Valor pendente",
        f'R$ {indicadores["valor_pendente"]:,.2f}'
    )

    st.divider()

    st.header("🤖 Análise inteligente da ORBIA")

    st.markdown(st.session_state["analise"])

    st.divider()

    st.header("📄 Relatório operacional")

    st.download_button(
        label="⬇️ Baixar relatório em PDF",
        data=st.session_state["pdf"],
        file_name="Relatorio_ORBIA.pdf",
        mime="application/pdf"
    )


# ==========================================
# RODAPÉ
# ==========================================

st.divider()

st.caption(
    "ORBIA | Inteligência de Operações Comerciais"
)
