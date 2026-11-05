
import os
from io import BytesIO
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from google import genai

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

app = FastAPI(title="ORBIA - Inteligência de Operações Comerciais")


@app.get("/")
def inicio():
    return {"status": "ORBIA online"}


def calcular_indicadores(pedidos):
    total = len(pedidos)

    atrasados = (
        pedidos["Situacao_Prazo"] == "Atrasado"
    ).sum()

    criticos = (
        pedidos["Prioridade_Operacional"] == "Crítica"
    ).sum()

    valor_pendente = pd.to_numeric(
        pedidos["Valor_Pendente"], errors="coerce"
    ).fillna(0).sum()

    return {
        "total_pedidos": int(total),
        "pedidos_atrasados": int(atrasados),
        "pedidos_criticos": int(criticos),
        "valor_pendente": float(valor_pendente)
    }


def gerar_analise(indicadores):
    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ValueError("A chave GEMINI_API_KEY não foi configurada.")

    cliente_ia = genai.Client(api_key=chave)

    prompt = f"""
Você é a inteligência analítica da ORBIA,
um projeto de inteligência de operações comerciais.

Analise os indicadores desta base fictícia:

- Total de pedidos: {indicadores["total_pedidos"]}
- Pedidos atrasados: {indicadores["pedidos_atrasados"]}
- Pedidos críticos: {indicadores["pedidos_criticos"]}
- Valor pendente: R$ {indicadores["valor_pendente"]:,.2f}

Organize a resposta em três seções:

1. DIAGNÓSTICO OPERACIONAL
Interprete os números e apresente os percentuais relevantes.

2. RISCOS E LIMITAÇÕES
Separe fatos confirmados de hipóteses.
Não invente causas para os atrasos nem presuma inadimplência.

3. AÇÕES PRIORITÁRIAS
Recomende três ações práticas, priorizando os pedidos críticos.

Use português brasileiro profissional.
Não invente dados nem afirme que ações foram realizadas.
"""

    resposta = cliente_ia.interactions.create(
        model="gemini-3.5-flash-lite",
        input=prompt
    )

    return resposta.output_text


def gerar_pdf(indicadores, analise):
    arquivo = BytesIO()

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloORBIA",
        parent=estilos["Title"],
        textColor=colors.HexColor("#101B2D"),
        fontSize=22,
        alignment=1,
        spaceAfter=8
    )

    subtitulo = ParagraphStyle(
        "SubtituloORBIA",
        parent=estilos["Normal"],
        textColor=colors.HexColor("#168DA8"),
        fontSize=10,
        alignment=1,
        spaceAfter=20
    )

    corpo = ParagraphStyle(
        "CorpoORBIA",
        parent=estilos["BodyText"],
        fontSize=9,
        leading=14,
        spaceAfter=8
    )

    elementos = [
        Paragraph("ORBIA", titulo),
        Paragraph(
            "INTELIGÊNCIA DE OPERAÇÕES COMERCIAIS",
            subtitulo
        ),
        Paragraph("RELATÓRIO DE MONITORAMENTO OPERACIONAL", estilos["Heading2"]),
        Spacer(1, 12)
    ]

    dados = [
        ["INDICADOR", "RESULTADO"],
        ["Total de pedidos", str(indicadores["total_pedidos"])],
        ["Pedidos atrasados", str(indicadores["pedidos_atrasados"])],
        ["Pedidos críticos", str(indicadores["pedidos_criticos"])],
        [
            "Valor pendente",
            f'R$ {indicadores["valor_pendente"]:,.2f}'
        ]
    ]

    tabela = Table(dados, colWidths=[9 * cm, 7 * cm])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#101B2D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#EAF4F8")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#101B2D")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8D5E0")),
        ("PADDING", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))

    elementos.extend([
        tabela,
        Spacer(1, 24),
        Paragraph("ANÁLISE GERADA POR IA", estilos["Heading2"]),
        Spacer(1, 8)
    ])

    for paragrafo in analise.split("\n"):
        texto = paragrafo.strip()
        if texto:
            elementos.append(
                Paragraph(texto.replace("&", "&amp;"), corpo)
            )

    elementos.extend([
        Spacer(1, 24),
        Paragraph(
            "Relatório gerado automaticamente pela ORBIA. "
            "Base de dados fictícia, utilizada exclusivamente "
            "para demonstração do projeto.",
            estilos["Italic"]
        )
    ])

    documento.build(elementos)
    arquivo.seek(0)

    return arquivo


@app.post("/gerar-relatorio")
def gerar_relatorio(payload: dict):
    try:
        # Aceita os dados recebidos do Power Automate
        linhas = payload.get("value", payload.get("rows", payload))

        if not isinstance(linhas, list) or not linhas:
            raise ValueError("Nenhum pedido foi recebido.")

        pedidos = pd.DataFrame(linhas)

        colunas_necessarias = [
            "Situacao_Prazo",
            "Prioridade_Operacional",
            "Valor_Pendente"
        ]

        for coluna in colunas_necessarias:
            if coluna not in pedidos.columns:
                raise ValueError(
                    f"Coluna ausente na planilha: {coluna}"
                )

        indicadores = calcular_indicadores(pedidos)
        analise = gerar_analise(indicadores)
        pdf = gerar_pdf(indicadores, analise)

        nome = "Relatorio_ORBIA.pdf"

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nome}"'
            }
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )
