from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# Caminho do PDF
pdf_path = "/mnt/data/Checklist_Vistoria_Veicular.pdf"

# Estilos
styles = getSampleStyleSheet()
styleN = styles["Normal"]
styleB = styles["Heading2"]

# Criar documento
doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
elements = []

# Cabeçalho
elements.append(Paragraph("CHECKLIST DE VISTORIA VEICULAR", styleB))
elements.append(Spacer(1, 12))
elements.append(Paragraph("Espaço reservado para logo da empresa", styleN))
elements.append(Spacer(1, 12))
elements.append(Paragraph("Funcionário: ____________________________________    Matrícula: _______________    Data: ____/____/______", styleN))
elements.append(Spacer(1, 12))

# Itens obrigatórios
obrigatorios = [
    ["✅ Itens de Segurança e Funcionamento Obrigatório", "Conforme", "Não Conforme", "Observações"],
    ["DIREÇÃO (folga, alinhamento, puxando, pesada)", "", "", ""],
    ["FREIOS (funcionamento, perda de pressão)", "", "", ""],
    ["ALAVANCA DE CÂMBIO (folga e engates)", "", "", ""],
    ["EMBREAGEM (pesada, regulagem, folga)", "", "", ""],
    ["MOTOR (desempenho, ruídos, aquecimento)", "", "", ""],
    ["CINTA SALVA VIDAS DA TRANSMISSÃO", "", "", ""],
    ["ARREFECIMENTO (vazamentos)", "", "", ""],
    ["ILUMINAÇÃO EXTERNA", "", "", ""],
    ["ILUMINAÇÃO INTERNA", "", "", ""],
    ["CINTO DE SEGURANÇA", "", "", ""],
    ["PAINEL DE INSTRUMENTOS", "", "", ""],
    ["RETENTOR DE RODA", "", "", ""],
    ["ALÇAPÃO DE EMERGÊNCIA", "", "", ""],
    ["ELEVADOR (acessibilidade)", "", "", ""],
    ["FEIXES DE MOLAS / BOLSA DE AR", "", "", ""],
    ["VAZAMENTOS SISTEMA PNEUMÁTICO", "", "", ""],
    ["LIMPADORES DE PARA-BRISA E ESGUINCHOS", "", "", ""],
    ["CRLV", "", "", ""],
    ["CERTIFICADO CRONOTACÓGRAFO", "", "", ""],
    ["GRCT", "", "", ""],
]

# Tabela 1
t1 = Table(obrigatorios, repeatRows=1, colWidths=[9*cm, 2.5*cm, 2.5*cm, 5*cm])
t1.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
elements.append(t1)
elements.append(Spacer(1, 24))

# Itens secundários
secundarios = [
    ["✅ Itens Operacionais Secundários", "Conforme", "Não Conforme", "Observações"],
    ["FUNCIONAMENTO DO AR-CONDICIONADO", "", "", ""],
    ["PORTAS (fechamento, vedação e vazamento)", "", "", ""],
    ["BUZINA", "", "", ""],
    ["PARA-BRISA EM BOM ESTADO", "", "", ""],
    ["BANCO DO MOTORISTA", "", "", ""],
    ["CARROCERIA ATRAVESSADA", "", "", ""],
    ["CAPÔ (vedação, pintura, corrente)", "", "", ""],
    ["DESTINO (estado geral)", "", "", ""],
]

# Tabela 2
t2 = Table(secundarios, repeatRows=1, colWidths=[9*cm, 2.5*cm, 2.5*cm, 5*cm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
elements.append(t2)
elements.append(Spacer(1, 24))

# Assinatura
elements.append(Paragraph("Assinatura do Vistoriador: _______________________________________", styleN))

# Gerar PDF
doc.build(elements)
pdf_path
