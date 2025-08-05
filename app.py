from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import date, timedelta
from config import Config
from models import db, Veiculo, Programacao, User  # Certifique-se de importar User aqui
from sqlalchemy import extract
import plotly.graph_objs as go
from markupsafe import Markup
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm 
from flask_migrate import Migrate
from babel.dates import format_date
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timedelta
from fpdf import FPDF  # ✅ Correto para fpdf2
import os
import locale

# ✅ Inicialização da app e configuração
app = Flask(__name__)
app.permanent_session_lifetime = timedelta(minutes=30)
app.config.from_object(Config)

# ✅ Banco de dados e migrações
db.init_app(app)
migrate = Migrate(app, db)

# ✅ Bcrypt para senhas
bcrypt = Bcrypt(app)

# ✅ Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None  # Evita mensagens padrão do Flask-Login

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def job_gerar_programacao():
    with app.app_context():
        gerar_programacao_diaria()

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=job_gerar_programacao,
    trigger=CronTrigger(hour=7, minute=0),  # Executa todos os dias às 07:00
    id='gerar_programacao_diaria',
    replace_existing=True
)
scheduler.start()


def gerar_programacao_diaria():
    hoje = date.today()
    tipo = "PAR" if hoje.day % 2 == 0 else "IMPAR"

    if Programacao.query.filter_by(data=hoje).first():
        return

    veiculos_do_dia = Veiculo.query.filter_by(tipo_frota=tipo, status='ativo').all()
    remarcados_ids = db.session.query(Programacao.veiculo_id).filter_by(remarcado_para=hoje).all()
    remarcados = Veiculo.query.filter(Veiculo.id.in_([r[0] for r in remarcados_ids])).all()

    veiculos = veiculos_do_dia + remarcados

    for v in veiculos:
        prog = Programacao(data=hoje, veiculo_id=v.id)
        db.session.add(prog)

    db.session.commit()

    
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if "expired" in request.args:
        erro = "Sessão expirada. Faça login novamente."

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session.permanent = True  # 🔒 garante validade com timedelta
            return redirect(url_for("index"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/reset_programacoes", methods=["POST"])
@login_required
def reset_programacoes():
    db.session.query(Programacao).delete()
    db.session.commit()
    return redirect(url_for("programacao"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")
@app.route("/programacao")
def programacao():
    gerar_programacao_diaria()
    hoje = date.today()
    tipo = "PAR" if hoje.day % 2 == 0 else "IMPAR"

    # Apenas veículos habilitados para vistoria (pré-selecionados)
    programacoes = Programacao.query.filter_by(data=hoje, habilitado_para_vistoria=True).all()
    veiculos = [p.veiculo for p in programacoes]

    remarcados_ids = [p.veiculo_id for p in programacoes if p.remarcado_para == hoje]

    gerar_pdf_programacao_assinatura(hoje, tipo, veiculos)

    return render_template("programacao.html",
                           data=hoje.strftime("%d/%m/%Y"),
                           tipo=tipo,
                           veiculos=veiculos,
                           remarcados_ids=remarcados_ids)


@app.route("/gerar_pdf")
def gerar_pdf():
    hoje = date.today()
    tipo = "PAR" if hoje.day % 2 == 0 else "IMPAR"

    programacoes = Programacao.query.filter_by(data=hoje, habilitado_para_vistoria=True).all()
    veiculos = [p.veiculo for p in programacoes]

    nome_arquivo = gerar_pdf_programacao_assinatura(hoje, tipo, veiculos)
    return send_file(nome_arquivo, as_attachment=True)


def proximo_dia_util():
    dia = date.today() + timedelta(days=1)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia
def classificar_apontamento(texto):
    texto = texto.lower()
    if "motor" in texto or "quebrou" in texto or "falha" in texto or "pane" in texto:
        return "Quebra"
    if "pneu" in texto or "roda" in texto:
        return "Pneu"
    if "limpeza" in texto or "sujo" in texto:
        return "Higiene"
    if "luz" in texto or "elétrico" in texto:
        return "Elétrica"
    return "Outro"

def ultima_data_programada():
    ultima = db.session.query(Programacao.data) \
        .filter(Programacao.habilitado_para_vistoria == True) \
        .order_by(Programacao.data.desc()) \
        .first()
    return ultima[0] if ultima else None

@app.route("/vistoria", methods=["GET", "POST"])
def vistoria():
    gerar_programacao_diaria()

    data_vistoria = ultima_data_programada()

    if not data_vistoria:
        hoje = date.today().strftime("%d/%m/%Y")
        return render_template("vistorias.html",
                               data="hoje",
                               programacoes=[])

    if request.method == "POST":
        for key in request.form:
            if key.startswith("veiculo_"):
                prog_id = int(key.split("_")[1])
                compareceu = request.form.get(key) == "on"
                observacao = request.form.get(f"obs_{prog_id}", "")

                prog = Programacao.query.get(prog_id)
                prog.compareceu = compareceu
                prog.observacao = observacao.strip() if observacao else None

                if observacao:
                    prog.motivo_classificado = classificar_apontamento(observacao)

                if not compareceu:
                    prog.remarcado_para = proximo_dia_util()

        db.session.commit()
        return redirect(url_for("index"))

    programacoes = Programacao.query.filter_by(data=data_vistoria, habilitado_para_vistoria=True).all()

    return render_template("vistorias.html",
                           data=data_vistoria.strftime("%d/%m/%Y"),
                           programacoes=programacoes)

def gerar_pdf_programacao_assinatura(data, tipo, veiculos):
    try:
      locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')


    tmp_dir = "/tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    nome_arquivo = os.path.join(tmp_dir, f"programacao_{data.strftime('%Y-%m-%d')}.pdf")

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleCustom', parent=styles['Title'], fontSize=18,
                                 alignment=1, textColor=colors.HexColor("#003366"))

    story = []
    titulo = Paragraph(f"PROGRAMAÇÃO DE VISTORIA<br/>{data.strftime('%d/%m/%Y')} — FROTA {tipo}", title_style)
    story.append(titulo)
    story.append(Spacer(1, 24))

    tabela_data = [["DATA", "VEI"]]
    remarcados_ids = db.session.query(Programacao.veiculo_id).filter_by(remarcado_para=data).all()
    remarcados_set = set([r[0] for r in remarcados_ids])

    veiculos_ordenados = sorted(veiculos, key=lambda v: v.numero_frota)
    for v in veiculos_ordenados:
        numero = str(v.numero_frota)
        if v.id in remarcados_set:
            numero += " (REMARCADO)"
        data_formatada = format_date(data, format='full', locale='pt_BR')
        tabela_data.append([data_formatada, numero])

    tabela = Table(tabela_data, colWidths=[350, 100])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(tabela)
    story.append(Spacer(1, 48))
    assinatura = Paragraph("<para alignment='center'><br/><br/>__________________________<br/>Assinatura do Vistoriador</para>", styles["Normal"])
    story.append(assinatura)

    doc.build(story)
    return nome_arquivo
from datetime import datetime

@app.route("/dashboard")
def dashboard():
    from datetime import datetime
    mes = int(request.args.get("mes", date.today().month))
    ano = int(request.args.get("ano", date.today().year))
    frota_filtro = request.args.get("frota")

    data_filtro_str = request.args.get("data_filtro")
    if data_filtro_str:
        try:
            data_filtro = datetime.strptime(data_filtro_str, "%Y-%m-%d").date()
        except ValueError:
            data_filtro = date.today()
    else:
        data_filtro = date.today()

    mes = data_filtro.month
    ano = data_filtro.year
    frota_filtro = request.args.get("frota")

    # 🔢 Gráfico mensal
    query = db.session.query(
        Veiculo.numero_frota,
        db.func.count(Programacao.id).label("total"),
        db.func.sum(db.func.cast(Programacao.compareceu, db.Integer)).label("vistoriados"),
        db.func.count(Programacao.observacao).label("apontamentos")
    ).join(Programacao).filter(
        extract('month', Programacao.data) == mes,
        extract('year', Programacao.data) == ano,
        Programacao.data < date.today()
    )

    if frota_filtro:
        query = query.filter(Veiculo.numero_frota == int(frota_filtro))

    query = query.group_by(Veiculo.numero_frota).order_by(Veiculo.numero_frota)
    registros = query.all()

    frotas = [str(r[0]) for r in registros]
    realizados = [r[2] or 0 for r in registros]
    total_dias = [r[1] or 0 for r in registros]
    faltas = [total - vis for total, vis in zip(total_dias, realizados)]
    apontamentos = [r[3] or 0 for r in registros]

    cores_falta = ['crimson' if faltas[i] > (total_dias[i] // 2) else 'gray' for i in range(len(faltas))]
    cores_apont = ['darkorange' if apontamentos[i] >= 3 else 'orange' for i in range(len(apontamentos))]

    trace1 = go.Bar(name='Vistoriado', x=frotas, y=realizados, marker_color='green')
    trace2 = go.Bar(name='Faltou', x=frotas, y=faltas, marker_color=cores_falta)
    trace3 = go.Bar(name='Apontamentos', x=frotas, y=apontamentos, marker_color=cores_apont)

    layout = go.Layout(
        title=f"Resumo de {mes:02d}/{ano}",
        barmode='group',
        xaxis_title='Veículo (Nº Frota)',
        yaxis_title='Ocorrências',
        height=600,
        template='plotly_dark',              # 🌙 Tema escuro
        paper_bgcolor='#121212',             # Cor de fundo (escura)
        plot_bgcolor='#121212',
        font=dict(color='white')             # Texto branco
    )

    fig = go.Figure(data=[trace1, trace2, trace3], layout=layout)
    grafico_html = fig.to_html(full_html=False)

    # Salva PNG para download/exportação
    fig.write_image("static/grafico_dashboard.png", width=1000, height=600)

    # 🔍 Pendentes do dia anterior
    pendentes = Programacao.query.filter(
        Programacao.data < date.today(),
        Programacao.compareceu == False,
        Programacao.habilitado_para_vistoria == True
    ).join(Veiculo).order_by(Veiculo.numero_frota).all()

    return render_template(
        "dashboard.html",
        grafico=Markup(grafico_html),
        mes=mes,
        ano=ano,
        frota=frota_filtro or "",
        data_filtro=data_filtro,
        pendentes=pendentes,
        relatorio_url=url_for('relatorio_mensal', mes=mes, ano=ano)
    )

@app.route("/risco")
def risco():
    mes = int(request.args.get("mes", date.today().month))
    ano = int(request.args.get("ano", date.today().year))

    query = db.session.query(
        Veiculo.numero_frota,
        db.func.count(Programacao.id).label("total"),
        db.func.sum(db.func.cast(Programacao.compareceu, db.Integer)).label("vistoriados"),
        db.func.count(Programacao.observacao).label("apontamentos")
    ).join(Programacao).filter(
        extract('month', Programacao.data) == mes,
        extract('year', Programacao.data) == ano
    ).group_by(Veiculo.numero_frota)

    risco_lista = []

    for numero, total, vis, apont in query.all():
        vis = vis or 0
        apont = apont or 0
        faltas = (total or 0) - vis

        # Classificação de risco
        if faltas > (total / 2) and apont >= 3:
            nivel = "ALTO"
        elif faltas > (total / 2) or apont >= 3:
            nivel = "MÉDIO"
        else:
            nivel = "BAIXO"

        # Histórico de motivos (sempre executado, independente do nível)
        motivos = db.session.query(Programacao.motivo_classificado, Programacao.data).filter(
            Veiculo.numero_frota == numero,
            Programacao.veiculo_id == Veiculo.id,
            Programacao.motivo_classificado != None
        ).order_by(Programacao.data.desc()).all()

        motivos_formatados = [f"{d.strftime('%d/%m/%Y')}: {m}" for m, d in motivos]
        ultimo_motivo = motivos_formatados[0] if motivos_formatados else "—"

        risco_lista.append({
            "numero": numero,
            "faltas": faltas,
            "vistoriados": vis,
            "apontamentos": apont,
            "nivel": nivel,
            "ultimo_motivo": ultimo_motivo,
            "motivos_historico": motivos_formatados
        })

    risco_lista.sort(
        key=lambda x: (x['nivel'] == 'ALTO', x['nivel'] == 'MÉDIO', -x['faltas'], -x['apontamentos']),
        reverse=True
    )

    return render_template("risco.html", riscos=risco_lista, mes=mes, ano=ano)


@app.route("/relatorio_mensal")
def relatorio_mensal():
    mes = int(request.args.get("mes", date.today().month))
    ano = int(request.args.get("ano", date.today().year))

    registros = db.session.query(
        Veiculo.numero_frota,
        db.func.count(Programacao.id),
        db.func.sum(db.func.cast(Programacao.compareceu, db.Integer)),
        db.func.count(Programacao.observacao)
    ).join(Programacao).filter(
        extract("month", Programacao.data) == mes,
        extract("year", Programacao.data) == ano
    ).group_by(Veiculo.numero_frota).all()

    dados = []
    for frota, total, feitos, apont in registros:
        feitos = feitos or 0
        apont = apont or 0
        faltas = total - feitos
        if faltas > total / 2 and apont >= 3:
            risco = "ALTO"
        elif faltas > total / 2 or apont >= 3:
            risco = "MÉDIO"
        else:
            risco = "BAIXO"

        dados.append([str(frota), str(total), str(feitos), str(faltas), str(apont), risco])

    # Gerar PDF
    try:
       locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')

    os.makedirs("relatorios", exist_ok=True)
    nome_arquivo = f"relatorios/relatorio_{mes:02d}_{ano}.pdf"

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(name='Title', parent=styles['Title'], alignment=1, fontSize=18, textColor=colors.darkblue)
    story = [Paragraph(f"RELATÓRIO MENSAL DE VISTORIAS - {mes:02d}/{ano}", title), Spacer(1, 24)]

    # Cabeçalho da tabela
    tabela_dados = [["Frota", "Programado", "Vistoriado", "Faltas", "Apontamentos", "Risco"]] + dados

    tabela = Table(tabela_dados, colWidths=[60, 80, 80, 60, 90, 80])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (-1, 1), (-1, -1), colors.whitesmoke),
    ]))

    story.append(tabela)
    story.append(Spacer(1, 36))
    story.append(Paragraph("<para alignment='center'>__________________________<br/>Assinatura do Responsável</para>", styles['Normal']))

    doc.build(story)
    return send_file(nome_arquivo, as_attachment=True)

@app.route("/relatorio_botao")
def relatorio_botao():
    hoje = date.today()
    return render_template("relatorio_botao.html", mes=hoje.month, ano=hoje.year, link=url_for('relatorio_mensal', mes=hoje.month, ano=hoje.year))

@app.route("/regenerar_hoje")
def regenerar_hoje():
    hoje = date.today()

    # Remove programação existente
    Programacao.query.filter_by(data=hoje).delete()
    db.session.commit()

    # Gera novamente
    gerar_programacao_diaria()

    return redirect(url_for("programacao"))

@app.route("/pre_vistoria", methods=["GET", "POST"])
def pre_vistoria():
    hoje = date.today()
    programacoes = Programacao.query.filter_by(data=hoje).all()

    if request.method == "POST":
        for prog in programacoes:
            checkbox = f"liberar_{prog.id}"
            motivo = request.form.get(f"motivo_{prog.id}")
            descricao = request.form.get(f"descricao_{prog.id}", "").strip()

            prog.habilitado_para_vistoria = checkbox in request.form

            if not prog.habilitado_para_vistoria:
                if motivo == "Outro":
                    if descricao:
                        prog.observacao = f"Outro: {descricao}"
                    else:
                        prog.observacao = "Outro (sem detalhes)"
                else:
                    prog.observacao = motivo or "Sem motivo informado"

        db.session.commit()
        return redirect(url_for("programacao"))

    return render_template("pre_vistoria.html", programacoes=programacoes, data=hoje.strftime("%d/%m/%Y"))


   
@app.route("/veiculo/<int:numero>")
def historico_veiculo(numero):
    veiculo = Veiculo.query.filter_by(numero_frota=numero).first_or_404()
    vistorias = Programacao.query.filter_by(veiculo_id=veiculo.id).order_by(Programacao.data.desc()).all()

    return render_template("historico_veiculo.html", veiculo=veiculo, vistorias=vistorias)
@app.route("/ranking")
def ranking():
    mes = int(request.args.get("mes", date.today().month))
    ano = int(request.args.get("ano", date.today().year))
    frota_filtro = request.args.get("frota", "").strip()

    query = db.session.query(
        Veiculo.numero_frota,
        db.func.count(Programacao.id).label("total"),
        db.func.sum(db.func.cast(Programacao.compareceu, db.Integer)).label("vistoriados"),
        db.func.count(Programacao.observacao).label("apontamentos")
    ).join(Programacao).filter(
        extract('month', Programacao.data) == mes,
        extract('year', Programacao.data) == ano
    )

    if frota_filtro.isdigit():
        query = query.filter(Veiculo.numero_frota == int(frota_filtro))

    query = query.group_by(Veiculo.numero_frota)

    risco_lista = []

    for numero, total, vis, apont in query.all():
        vis = vis or 0
        apont = apont or 0
        faltas = total - vis

        if faltas > (total / 2) and apont >= 3:
            nivel = "ALTO"
        elif faltas > (total / 2) or apont >= 3:
            nivel = "MÉDIO"
        else:
            nivel = "BAIXO"

        motivos = db.session.query(Programacao.motivo_classificado, Programacao.data).filter(
            Veiculo.numero_frota == numero,
            Programacao.veiculo_id == Veiculo.id,
            Programacao.motivo_classificado != None
        ).order_by(Programacao.data.desc()).all()

        motivos_formatados = [f"{d.strftime('%d/%m/%Y')}: {m}" for m, d in motivos]
        ultimo_motivo = motivos_formatados[0] if motivos_formatados else "—"

        risco_lista.append({
            "numero": numero,
            "faltas": faltas,
            "vistoriados": vis,
            "apontamentos": apont,
            "nivel": nivel,
            "ultimo_motivo": ultimo_motivo,
            "motivos_historico": motivos_formatados
        })

    risco_lista.sort(
        key=lambda x: (x['nivel'] == 'ALTO', x['nivel'] == 'MÉDIO', -x['faltas'], -x['apontamentos']),
        reverse=True
    )

    return render_template("ranking.html", riscos=risco_lista, mes=mes, ano=ano, frota=frota_filtro)


@app.route("/reset_dados", methods=["POST"])
@login_required
def reset_dados():
    hoje = date.today()
    Programacao.query.filter(Programacao.data < hoje).delete()
    db.session.commit()

    return redirect(url_for("programacao"))


@app.route("/exportar_dashboard/png")
def exportar_dashboard_png():
    return send_file("static/grafico_dashboard.png", mimetype="image/png", as_attachment=True)

from fpdf import FPDF
import os

@app.route("/exportar_dashboard/pdf")
def exportar_dashboard_pdf():
    img_path = "static/grafico_dashboard.png"

    if not os.path.exists(img_path):
        return "Imagem do gráfico não encontrada", 404

    # Criar PDF e inserir a imagem
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Resumo de Vistorias - Dashboard", ln=True, align="C")
    pdf.ln(10)
    pdf.image(img_path, x=10, y=30, w=270)  # Ajuste conforme necessário

    output_path = "static/grafico_dashboard.pdf"
    pdf.output(output_path)

    return send_file(output_path, mimetype="application/pdf", as_attachment=True)


if __name__ == "__main__":
    from flask_migrate import upgrade
    with app.app_context():
        db.create_all()
        upgrade()
        
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
