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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --orbia-bg: #071426;
    --orbia-panel: #10243A;
    --orbia-panel-2: #142F49;
    --orbia-cyan: #36C5F0;
    --orbia-cyan-light: #A7EDFF;
    --orbia-text: #F4F9FD;
    --orbia-muted: #B9CAD8;
}

.stApp {
    background:
        radial-gradient(ellipse at 8% 3%, rgba(54,197,240,.16), transparent 30%),
        radial-gradient(ellipse at 94% 17%, rgba(54,120,190,.17), transparent 28%),
        linear-gradient(145deg, #061222 0%, #0A1B30 48%, #102B45 100%);
    color: var(--orbia-text);
    font-family: 'DM Sans', sans-serif;
}
.block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}
h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--orbia-text) !important;
    letter-spacing: -.025em;
}
p, label, li, .stMarkdown { color: #DCEAF5; }
[data-testid="stCaptionContainer"] { color: var(--orbia-muted) !important; }

/* Cabeçalho principal */
.orbia-hero {
    position: relative;
    overflow: hidden;
    padding: 2.35rem 2.5rem;
    margin: .2rem 0 1.8rem 0;
    border: 1px solid rgba(117,213,242,.30);
    border-radius: 26px;
    background:
        radial-gradient(circle at 83% 24%, rgba(54,197,240,.23), transparent 23%),
        linear-gradient(115deg, rgba(16,42,68,.98), rgba(7,24,43,.96));
    box-shadow: 0 20px 55px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.06);
}
.orbia-hero:after {
    content: "";
    position: absolute;
    width: 255px; height: 255px;
    right: -68px; top: -118px;
    border: 1px solid rgba(91,214,246,.25);
    border-radius: 50%;
    box-shadow: 0 0 0 22px rgba(91,214,246,.045), 0 0 0 48px rgba(91,214,246,.025);
    pointer-events: none;
}
.orbia-kicker {
    color: var(--orbia-cyan-light);
    font-size: .74rem; font-weight: 700;
    letter-spacing: .19em; text-transform: uppercase;
    margin-bottom: .75rem;
}
.orbia-brand {
    color: #fff; font-family: 'Manrope', sans-serif;
    font-size: clamp(2.7rem, 7vw, 4.5rem);
    font-weight: 800; line-height: 1;
    letter-spacing: .045em; margin: 0;
}
.orbia-brand span { color: var(--orbia-cyan); }
.orbia-subtitle {
    color: #E2F0F8; font-size: 1.12rem;
    margin-top: .75rem; margin-bottom: .7rem; font-weight: 600;
}
.orbia-description {
    color: #B9CAD8; font-size: .96rem;
    max-width: 720px; line-height: 1.7;
}
.orbia-chip-row { display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.25rem; }
.orbia-chip {
    border: 1px solid rgba(95,211,243,.30);
    background: rgba(54,197,240,.09);
    color: #C7F2FC; padding: .38rem .75rem;
    border-radius: 999px; font-size: .76rem; font-weight: 600;
}

/* Títulos e cartões de seção */
.orbia-eyebrow {
    color: var(--orbia-cyan); font-size: .72rem;
    font-weight: 700; letter-spacing: .16em;
    text-transform: uppercase; margin-bottom: .25rem;
}
.orbia-section-title {
    font-family: 'Manrope', sans-serif; font-size: 1.45rem;
    font-weight: 800; color: #F4FAFF; margin: 0 0 .35rem 0;
}
.orbia-section-copy { color: #B9CAD8; font-size: .92rem; margin-bottom: 1rem; }
.orbia-info-card {
    min-height: 118px; padding: 1.05rem 1.15rem;
    border: 1px solid rgba(139,190,215,.18);
    border-radius: 17px;
    background: linear-gradient(145deg, rgba(20,48,74,.88), rgba(10,29,48,.92));
    box-shadow: 0 10px 28px rgba(0,0,0,.12);
}
.orbia-info-icon { font-size: 1.25rem; margin-bottom: .5rem; }
.orbia-info-title { color: #F1F8FC; font-weight: 700; margin-bottom: .25rem; }
.orbia-info-copy { color: #B9CAD8; font-size: .82rem; line-height: 1.5; }

/* Área de upload — fundo claro e texto azul-escuro */
[data-testid="stFileUploader"] section {
    background: #EAF7FC !important;
    border: 1px dashed #63BBD5 !important;
    border-radius: 17px !important;
}
[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    color: #08263D !important;
}
[data-testid="stFileUploader"] button {
    background: #DDF6FF !important;
    color: #08263D !important;
    border: 1px solid #63BBD5 !important;
    font-weight: 800 !important;
}
[data-testid="stFileUploader"] button * {
    color: #08263D !important;
    fill: #08263D !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: #DDF6FF !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] * {
    color: #08263D !important;
    fill: #08263D !important;
}

/* Cartões dos indicadores */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(20,48,74,.96), rgba(10,29,48,.96));
    border: 1px solid rgba(116,195,224,.22);
    border-radius: 17px;
    padding: 1rem 1.1rem;
    box-shadow: 0 10px 28px rgba(0,0,0,.14);
}
[data-testid="stMetricLabel"] p {
    color: #C4D7E5 !important; font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #55D5F5 !important; font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
}
[data-testid="stMetricDelta"] {
    background: #DDF6FF !important;
    color: #08263D !important;
    border: 1px solid #8ADCF2 !important;
    border-radius: 999px !important;
    padding: .22rem .55rem !important;
    display: inline-flex !important;
    align-items: center !important;
    width: fit-content !important;
    font-weight: 800 !important;
}
[data-testid="stMetricDelta"] p,
[data-testid="stMetricDelta"] span,
[data-testid="stMetricDelta"] svg {
    color: #08263D !important;
    fill: #08263D !important;
}

/* Botões */
.stButton > button {
    background: linear-gradient(100deg, #087EA4, #16A7CC) !important;
    color: #FFFFFF !important; border: 1px solid rgba(120,225,248,.38) !important;
    border-radius: 11px !important; padding: .68rem 1.25rem !important;
    font-weight: 800 !important; transition: all .18s ease-in-out;
}
.stButton > button:hover {
    background: linear-gradient(100deg, #36C5F0, #8BE7FF) !important;
    color: #071426 !important; transform: translateY(-1px);
}
.stButton > button p { color: inherit !important; }

/* Mensagens de sucesso e erro */
[data-testid="stAlert"][data-alert-type="success"] {
    background: #DDF6FF !important;
    border: 1px solid #36C5F0 !important;
    border-radius: 12px !important;
}
[data-testid="stAlert"][data-alert-type="error"] {
    background: #FDECEF !important;
    border: 1px solid #E6A3B0 !important;
    border-radius: 12px !important;
}
[data-testid="stAlert"][data-alert-type="success"] *,
[data-testid="stAlert"][data-alert-type="error"] * {
    color: #08263D !important;
    fill: #08263D !important;
    font-weight: 700 !important;
}

/* Download PDF */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(100deg, #36C5F0, #8BE7FF) !important;
    color: #071426 !important; border: 1px solid #A7EDFF !important;
    border-radius: 11px !important; font-weight: 800 !important;
    min-height: 2.8rem;
}
[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button span { color: #071426 !important; font-weight: 800 !important; }
[data-testid="stDownloadButton"] button:hover { background: #C7F4FF !important; }
[data-testid="stDownloadButton"] button:focus { outline: 2px solid #FFFFFF !important; outline-offset: 2px !important; }

/* Área de análise e divisórias */
[data-testid="stMarkdownContainer"] strong { color: #9BE8FA; }
hr { border-color: rgba(125,190,218,.22) !important; }
[data-testid="stSpinner"] p { color: #DDF6FF !important; font-weight: 600; }

@media (max-width: 700px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .orbia-hero { padding: 1.6rem 1.35rem; }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# CABEÇALHO
# ==========================================

st.markdown("""
<div class="orbia-hero">
  <div class="orbia-kicker">Inteligência • Operações • Decisão</div>
  <div class="orbia-brand">ORB<span>IA</span></div>
  <div class="orbia-subtitle">Inteligência de Operações Comerciais</div>
  <div class="orbia-description">
    Transforme dados operacionais em clareza para agir.
    A ORBIA organiza indicadores, identifica pontos de atenção
    e apoia decisões com análises inteligentes e relatórios automatizados.
  </div>
  <div class="orbia-chip-row">
    <span class="orbia-chip">✦ Indicadores operacionais</span>
    <span class="orbia-chip">↗ Análise inteligente</span>
    <span class="orbia-chip">▤ Relatórios em PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

feature1, feature2, feature3 = st.columns(3)
with feature1:
    st.markdown("""
    <div class="orbia-info-card">
      <div class="orbia-info-icon">◈</div>
      <div class="orbia-info-title">Visão operacional</div>
      <div class="orbia-info-copy">Acompanhe volumes, atrasos e prioridades em uma visão organizada.</div>
    </div>
    """, unsafe_allow_html=True)
with feature2:
    st.markdown("""
    <div class="orbia-info-card">
      <div class="orbia-info-icon">✧</div>
      <div class="orbia-info-title">Inteligência aplicada</div>
      <div class="orbia-info-copy">Transforme indicadores em diagnósticos e recomendações objetivas.</div>
    </div>
    """, unsafe_allow_html=True)
with feature3:
    st.markdown("""
    <div class="orbia-info-card">
      <div class="orbia-info-icon">▤</div>
      <div class="orbia-info-title">Relatório estruturado</div>
      <div class="orbia-info-copy">Gere um documento para consultar e compartilhar os resultados.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)


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

st.markdown("""
<div class="orbia-eyebrow">Comece por aqui</div>
<div class="orbia-section-title">Análise operacional</div>
<div class="orbia-section-copy">Envie sua planilha para transformar os registros em indicadores e insights.</div>
""", unsafe_allow_html=True)

arquivo = st.file_uploader(
    "Selecione sua planilha de pedidos",
    type=["xlsx"]
)


# ==========================================
# PROCESSAMENTO
# ==========================================

if arquivo:

    st.markdown(
        f"""
        <div style="
            background-color: #DDF6FF;
            color: #08263D;
            border: 1px solid #36C5F0;
            padding: 14px;
            border-radius: 12px;
            font-weight: 700;
        ">
            Arquivo recebido: {escape(arquivo.name)}
        </div>
        """,
        unsafe_allow_html=True
    )

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

                st.markdown(
                    """
                    <div style="
                        background-color: #DDF6FF;
                        color: #08263D;
                        border: 1px solid #36C5F0;
                        padding: 14px;
                        border-radius: 12px;
                        font-weight: 700;
                    ">
                        Análise concluída com sucesso!
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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

    st.markdown("""
<div class="orbia-eyebrow">Visão geral</div>
<div class="orbia-section-title">Indicadores operacionais</div>
<div class="orbia-section-copy">Principais medidas calculadas a partir da planilha enviada.</div>
""", unsafe_allow_html=True)

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

    st.markdown("""
<div class="orbia-eyebrow">Leitura inteligente</div>
<div class="orbia-section-title">Análise inteligente da ORBIA</div>
<div class="orbia-section-copy">Diagnóstico, riscos observáveis e ações prioritárias sugeridas.</div>
""", unsafe_allow_html=True)

    st.markdown(st.session_state["analise"])

    st.divider()

    st.markdown("""
<div class="orbia-eyebrow">Exportação</div>
<div class="orbia-section-title">Relatório operacional</div>
<div class="orbia-section-copy">Leve os principais resultados em um documento PDF.</div>
""", unsafe_allow_html=True)

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
