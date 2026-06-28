
import os
import sqlite3
import hashlib
import hmac
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_PATH = os.path.join("dados", "controle_financeiro.db")

CATEGORIAS = {
    "Receita": ["Salário", "Venda", "Serviço", "Investimento", "Reembolso", "Outras Receitas"],
    "Despesa": ["Alimentação", "Mercado", "Moradia", "Transporte", "Saúde", "Educação", "Lazer", "Cartão", "Empréstimo", "Impostos", "Outras Despesas"],
}
FORMAS = ["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito", "Boleto", "Transferência", "Cheque", "Outro"]
STATUS = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    :root {
        --bg: #0b1020;
        --panel: #111827;
        --panel2: #0f172a;
        --border: #243247;
        --text: #f8fafc;
        --muted: #94a3b8;
        --accent: #38bdf8;
        --ok: #22c55e;
        --bad: #ef4444;
        --warn: #f59e0b;
    }
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1180px;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .hero {
        padding: 18px 22px;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a 0%, #111827 55%, #082f49 100%);
        border: 1px solid #243247;
        margin-bottom: 16px;
    }
    .hero-title {font-size: 28px; font-weight: 800; margin: 0;}
    .hero-sub {color: #cbd5e1; margin-top: 4px; font-size: 14px;}
    .metric-card {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 18px;
        padding: 16px 16px;
        min-height: 108px;
        box-shadow: 0 10px 24px rgba(0,0,0,.16);
    }
    .metric-label {color:#94a3b8; font-size: 13px; margin-bottom: 8px;}
    .metric-value {font-size: 26px; font-weight: 800;}
    .metric-positive {color:#22c55e;}
    .metric-negative {color:#ef4444;}
    .metric-warning {color:#f59e0b;}
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 18px;
        padding: 14px;
    }
    .stButton>button {
        width: 100%;
        min-height: 44px;
        border-radius: 12px;
        font-weight: 700;
    }
    .stTextInput input, .stNumberInput input, .stDateInput input, textarea {
        border-radius: 12px !important;
        font-size: 16px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 12px !important;
    }
    .badge {
        display:inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        border:1px solid #334155;
        background:#0f172a;
        color:#cbd5e1;
        font-size:12px;
    }
    .login-box {
        padding: 22px;
        border-radius: 20px;
        border: 1px solid #243247;
        background: #111827;
    }
    .section-title {
        font-size: 20px;
        font-weight: 800;
        margin: 8px 0 12px 0;
    }
    .caption-muted {color:#94a3b8; font-size:13px;}
    [data-testid="stSidebar"] {
        background: #050816;
    }
    @media (max-width: 768px) {
        .main .block-container {padding-left: .8rem; padding-right: .8rem;}
        .hero-title {font-size: 23px;}
        .metric-value {font-size: 22px;}
    }
</style>
""", unsafe_allow_html=True)

def conn():
    os.makedirs("dados", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hsenha(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

def senha_ok(senha, senha_hash):
    return hmac.compare_digest(hsenha(senha), senha_hash or "")

def init_db():
    con = conn()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Ativa',
        criado_em TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        usuario TEXT NOT NULL,
        nome TEXT,
        senha_hash TEXT NOT NULL,
        perfil TEXT DEFAULT 'usuario',
        status TEXT DEFAULT 'Ativo',
        pergunta TEXT,
        resposta_hash TEXT,
        criado_em TEXT,
        UNIQUE(empresa_id, usuario)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS lancamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        usuario_id INTEGER,
        tipo TEXT,
        descricao TEXT,
        categoria TEXT,
        valor REAL,
        data_lancamento TEXT,
        vencimento TEXT,
        data_pagamento TEXT,
        forma_pagamento TEXT,
        status TEXT,
        observacao TEXT,
        criado_em TEXT,
        atualizado_em TEXT
    )""")
    cur.execute("SELECT COUNT(*) FROM empresas")
    if cur.fetchone()[0] == 0:
        agora = datetime.now().isoformat(timespec="seconds")
        cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES ('Pessoal', 'Ativa', ?)", (agora,))
        eid = cur.lastrowid
        cur.execute("""INSERT INTO usuarios
            (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, 'admin', 'Administrador', ?, 'admin', 'Ativo', 'Código de recuperação', ?, ?)""",
            (eid, hsenha("admin123"), hsenha("admin123"), agora))
    con.commit()
    con.close()

def empresas_df():
    con = conn()
    df = pd.read_sql_query("SELECT * FROM empresas WHERE status='Ativa' ORDER BY nome", con)
    con.close()
    return df

def autenticar(empresa, usuario, senha):
    con = conn()
    cur = con.cursor()
    cur.execute("""
        SELECT u.id,u.usuario,u.nome,u.senha_hash,u.perfil,u.status,e.id,e.nome,e.status
        FROM usuarios u
        JOIN empresas e ON e.id=u.empresa_id
        WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)
    """, (empresa.strip(), usuario.strip()))
    r = cur.fetchone()
    con.close()
    if not r:
        return None, "Empresa ou usuário não encontrado."
    uid, user, nome, sh, perfil, st_user, eid, emp, st_emp = r
    if st_emp != "Ativa":
        return None, "Empresa inativa."
    if st_user != "Ativo":
        return None, "Usuário inativo."
    if not senha_ok(senha, sh):
        return None, "Senha inválida."
    return {"id": uid, "usuario": user, "nome": nome or user, "perfil": perfil, "empresa_id": eid, "empresa": emp}, None

def criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta):
    empresa, usuario = empresa.strip(), usuario.strip().lower()
    if not empresa or not usuario or not senha:
        return False, "Preencha empresa, usuário e senha."
    if len(senha) < 4:
        return False, "A senha precisa ter pelo menos 4 caracteres."
    con = conn()
    cur = con.cursor()
    agora = datetime.now().isoformat(timespec="seconds")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (empresa,))
        r = cur.fetchone()
        if r:
            eid, perfil = r[0], "usuario"
        else:
            cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?, 'Ativa', ?)", (empresa, agora))
            eid, perfil = cur.lastrowid, "admin"
        cur.execute("""INSERT INTO usuarios
            (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?)""",
            (eid, usuario, nome.strip() or usuario, hsenha(senha), perfil, pergunta.strip(), hsenha(resposta.strip().lower()), agora))
        con.commit()
        return True, f"Conta criada com sucesso. Perfil: {perfil}."
    except sqlite3.IntegrityError:
        return False, "Esse usuário já existe nessa empresa."
    finally:
        con.close()

def pergunta_recuperacao(empresa, usuario):
    con = conn()
    cur = con.cursor()
    cur.execute("""SELECT u.pergunta FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""", (empresa.strip(), usuario.strip().lower()))
    r = cur.fetchone()
    con.close()
    return r[0] if r else None

def resetar_senha(empresa, usuario, resposta, nova):
    if len(nova) < 4:
        return False, "A nova senha precisa ter pelo menos 4 caracteres."
    con = conn()
    cur = con.cursor()
    cur.execute("""SELECT u.id,u.resposta_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""", (empresa.strip(), usuario.strip().lower()))
    r = cur.fetchone()
    if not r:
        con.close()
        return False, "Empresa ou usuário não encontrado."
    uid, rh = r
    if not senha_ok(resposta.strip().lower(), rh):
        con.close()
        return False, "Resposta de recuperação incorreta."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (hsenha(nova), uid))
    con.commit()
    con.close()
    return True, "Senha alterada com sucesso."

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def carregar_lancamentos(eid):
    con = conn()
    df = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC", con, params=(eid,))
    con.close()
    if not df.empty:
        for c in ["data_lancamento","vencimento","data_pagamento"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def salvar_lancamento(eid, uid, dados, lid=None):
    con = conn()
    cur = con.cursor()
    agora = datetime.now().isoformat(timespec="seconds")
    params = (
        dados["tipo"], dados["descricao"], dados["categoria"], float(dados["valor"]),
        dados["data_lancamento"], dados["vencimento"], dados["data_pagamento"],
        dados["forma_pagamento"], dados["status"], dados["observacao"]
    )
    if lid:
        cur.execute("""UPDATE lancamentos SET tipo=?,descricao=?,categoria=?,valor=?,data_lancamento=?,vencimento=?,
            data_pagamento=?,forma_pagamento=?,status=?,observacao=?,atualizado_em=? WHERE id=? AND empresa_id=?""",
            params + (agora, lid, eid))
    else:
        cur.execute("""INSERT INTO lancamentos
            (empresa_id,usuario_id,tipo,descricao,categoria,valor,data_lancamento,vencimento,data_pagamento,
             forma_pagamento,status,observacao,criado_em,atualizado_em)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (eid, uid) + params + (agora, agora))
    con.commit()
    con.close()

def excluir_lancamento(eid, lid):
    con = conn()
    con.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?", (lid, eid))
    con.commit()
    con.close()

def usuarios_df(eid):
    con = conn()
    df = pd.read_sql_query("SELECT id,usuario,nome,perfil,status,pergunta,criado_em FROM usuarios WHERE empresa_id=? ORDER BY perfil, usuario", con, params=(eid,))
    con.close()
    return df

def criar_usuario_admin(eid, nome, usuario, senha, perfil, pergunta, resposta):
    if not usuario or not senha:
        return False, "Preencha usuário e senha."
    con = conn()
    try:
        con.execute("""INSERT INTO usuarios
            (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em)
            VALUES (?,?,?,?,?,'Ativo',?,?,?)""",
            (eid, usuario.strip().lower(), nome.strip(), hsenha(senha), perfil, pergunta.strip(), hsenha(resposta.strip().lower()), datetime.now().isoformat(timespec="seconds")))
        con.commit()
        return True, "Usuário criado."
    except sqlite3.IntegrityError:
        return False, "Usuário já existe nessa empresa."
    finally:
        con.close()

def alterar_senha_admin(uid, nova):
    con = conn()
    con.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (hsenha(nova), uid))
    con.commit()
    con.close()

def status_usuario_admin(uid, status):
    con = conn()
    con.execute("UPDATE usuarios SET status=? WHERE id=?", (status, uid))
    con.commit()
    con.close()

def excluir_usuario_admin(uid, eid, current_id):
    if uid == current_id:
        return False, "Você não pode excluir seu próprio usuário."
    con = conn()
    con.execute("DELETE FROM usuarios WHERE id=? AND empresa_id=?", (uid, eid))
    con.commit()
    con.close()
    return True, "Usuário excluído."

def login_page():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">💼 Controle Financeiro Profissional</div>
        <div class="hero-sub">Gestão simples, segura e organizada por empresa.</div>
    </div>
    """, unsafe_allow_html=True)

    col_info, col_login = st.columns([1.05, 1])
    with col_info:
        st.markdown("### Organize receitas, despesas e contas em aberto")
        st.markdown("""
        <div class="small-card">
            <span class="badge">Multiempresa</span>
            <span class="badge">Usuários e senhas</span>
            <span class="badge">Mobile</span>
            <span class="badge">Filtro mensal</span>
            <br><br>
            <span class="caption-muted">Cada empresa possui seus próprios lançamentos. O primeiro usuário criado em uma nova empresa vira administrador.</span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Acesso inicial: Empresa **Pessoal**, usuário **admin**, senha **admin123**.")

    with col_login:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        tabs = st.tabs(["Entrar", "Criar conta", "Esqueci senha"])
        with tabs[0]:
            emp = empresas_df()
            opcoes = emp["nome"].tolist() if not emp.empty else ["Pessoal"]
            empresa = st.selectbox("Empresa", opcoes)
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary"):
                user, erro = autenticar(empresa, usuario, senha)
                if erro:
                    st.error(erro)
                else:
                    st.session_state.user = user
                    st.rerun()
        with tabs[1]:
            empresa = st.text_input("Empresa", key="cad_emp")
            nome = st.text_input("Nome", key="cad_nome")
            usuario = st.text_input("Usuário", key="cad_user")
            senha = st.text_input("Senha", type="password", key="cad_senha")
            pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?", key="cad_perg")
            resposta = st.text_input("Resposta recuperação", type="password", key="cad_resp")
            if st.button("Criar acesso"):
                ok, msg = criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta)
                st.success(msg) if ok else st.error(msg)
        with tabs[2]:
            empresa = st.text_input("Empresa", key="rec_emp")
            usuario = st.text_input("Usuário", key="rec_user")
            if st.button("Buscar pergunta"):
                p = pergunta_recuperacao(empresa, usuario)
                if p:
                    st.session_state.rec = {"empresa": empresa, "usuario": usuario, "pergunta": p}
                else:
                    st.error("Usuário não encontrado.")
            if "rec" in st.session_state:
                st.info(st.session_state.rec["pergunta"])
                resp = st.text_input("Resposta", type="password", key="rec_resp")
                nova = st.text_input("Nova senha", type="password", key="rec_nova")
                if st.button("Alterar senha"):
                    ok, msg = resetar_senha(st.session_state.rec["empresa"], st.session_state.rec["usuario"], resp, nova)
                    st.success(msg) if ok else st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

def filtro_mes_ano():
    hoje = date.today()
    c1, c2 = st.columns([1,1])
    with c1:
        mes = st.selectbox("Mês", list(range(1,13)), index=hoje.month-1, format_func=lambda x: f"{x:02d}")
    with c2:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=hoje.year, step=1)
    return int(mes), int(ano)

def filtrar(df, mes, ano):
    if df.empty:
        return df
    return df[(df["data_lancamento"].dt.month == mes) & (df["data_lancamento"].dt.year == ano)].copy()

def lancamento_form(default=None):
    default = default or {}
    tipo_padrao = default.get("tipo", "Despesa")
    tipo = st.radio("Tipo", ["Despesa", "Receita"], index=0 if tipo_padrao == "Despesa" else 1, horizontal=True)
    categorias = CATEGORIAS[tipo]
    c1, c2 = st.columns(2)
    with c1:
        descricao = st.text_input("Descrição", value=default.get("descricao", ""))
        cat_default = default.get("categoria", categorias[0])
        categoria = st.selectbox("Categoria", categorias, index=categorias.index(cat_default) if cat_default in categorias else 0)
        valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f", value=float(default.get("valor", 0) or 0))
    with c2:
        data_lanc = st.date_input("Data lançamento", value=pd.to_datetime(default.get("data_lancamento")).date() if default.get("data_lancamento") else date.today())
        venc = st.date_input("Vencimento", value=pd.to_datetime(default.get("vencimento")).date() if default.get("vencimento") else date.today())
        st_default = default.get("status", "Em aberto")
        status = st.selectbox("Status", STATUS, index=STATUS.index(st_default) if st_default in STATUS else 0)
    c3, c4 = st.columns(2)
    with c3:
        fp_default = default.get("forma_pagamento", FORMAS[0])
        forma = st.selectbox("Forma de pagamento", FORMAS, index=FORMAS.index(fp_default) if fp_default in FORMAS else 0)
    with c4:
        data_pag = None
        if status == "Pago":
            data_pag = st.date_input("Data pagamento", value=pd.to_datetime(default.get("data_pagamento")).date() if default.get("data_pagamento") else date.today())
    obs = st.text_area("Observação", value=default.get("observacao", ""))
    return {
        "tipo": tipo, "descricao": descricao, "categoria": categoria, "valor": valor,
        "data_lancamento": str(data_lanc), "vencimento": str(venc),
        "data_pagamento": str(data_pag) if data_pag else None, "forma_pagamento": forma,
        "status": status, "observacao": obs
    }

def dashboard_cards(df):
    receitas = df[(df["tipo"]=="Receita") & (df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    despesas = df[(df["tipo"]=="Despesa") & (df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    saldo = receitas - despesas
    aberto = df[df["status"]=="Em aberto"]["valor"].sum() if not df.empty else 0
    pagos = df[df["status"]=="Pago"]["valor"].sum() if not df.empty else 0
    cols = st.columns(4)
    vals = [("Receitas", receitas, "metric-positive"), ("Despesas", despesas, "metric-negative"), ("Saldo", saldo, "metric-positive" if saldo >= 0 else "metric-negative"), ("Em aberto", aberto, "metric-warning")]
    for col, (label, value, css) in zip(cols, vals):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {css}">{moeda(value)}</div>
        </div>
        """, unsafe_allow_html=True)

def app_page():
    u = st.session_state.user
    with st.sidebar:
        st.markdown("## 💼 Financeiro")
        st.caption(f"Empresa: **{u['empresa']}**")
        st.caption(f"Usuário: **{u['usuario']}**")
        st.caption(f"Perfil: **{u['perfil']}**")
        st.divider()
        menu_items = ["Painel", "Novo lançamento", "Alterar lançamento", "Alterar status", "Excluir lançamento", "Lançamentos"]
        if u["perfil"] == "admin":
            menu_items.append("Admin usuários")
        menu = st.radio("Menu", menu_items)
        st.divider()
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">Controle Financeiro</div>
        <div class="hero-sub">Empresa: {u['empresa']} · Usuário: {u['usuario']}</div>
    </div>
    """, unsafe_allow_html=True)

    mes, ano = filtro_mes_ano()
    df = carregar_lancamentos(u["empresa_id"])
    df_mes = filtrar(df, mes, ano)

    if menu == "Painel":
        dashboard_cards(df_mes)
        st.markdown('<div class="section-title">Resumo do mês</div>', unsafe_allow_html=True)
        if df_mes.empty:
            st.info("Nenhum lançamento no período selecionado.")
        else:
            resumo_cat = df_mes.groupby(["tipo", "categoria"], as_index=False)["valor"].sum()
            resumo_status = df_mes.groupby(["status"], as_index=False)["valor"].sum()
            c1, c2 = st.columns(2)
            with c1:
                st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
            with c2:
                st.dataframe(resumo_status, use_container_width=True, hide_index=True)

            vencidos = df_mes[(df_mes["status"]=="Em aberto") & (df_mes["vencimento"].dt.date < date.today())]
            if not vencidos.empty:
                st.warning(f"Você tem {len(vencidos)} lançamento(s) em aberto vencido(s).")

    elif menu == "Novo lançamento":
        st.markdown('<div class="section-title">Novo lançamento</div>', unsafe_allow_html=True)
        dados = lancamento_form()
        if st.button("Salvar lançamento", type="primary"):
            if not dados["descricao"] or dados["valor"] <= 0:
                st.error("Preencha descrição e valor.")
            else:
                salvar_lancamento(u["empresa_id"], u["id"], dados)
                st.success("Lançamento salvo.")
                st.rerun()

    elif menu == "Alterar lançamento":
        st.markdown('<div class="section-title">Alterar lançamento</div>', unsafe_allow_html=True)
        if df_mes.empty:
            st.info("Nenhum lançamento no mês.")
        else:
            op = {f"#{int(r.id)} | {r.tipo} | {r.descricao} | {moeda(r.valor)} | {r.status}": int(r.id) for r in df_mes.itertuples()}
            esc = st.selectbox("Selecione", list(op.keys()))
            lid = op[esc]
            row = df[df["id"] == lid].iloc[0].to_dict()
            dados = lancamento_form(row)
            if st.button("Salvar alteração", type="primary"):
                salvar_lancamento(u["empresa_id"], u["id"], dados, lid)
                st.success("Alterado com sucesso.")
                st.rerun()

    elif menu == "Alterar status":
        st.markdown('<div class="section-title">Alterar status</div>', unsafe_allow_html=True)
        if df_mes.empty:
            st.info("Nenhum lançamento no mês.")
        else:
            op = {f"#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {moeda(r.valor)}": int(r.id) for r in df_mes.itertuples()}
            esc = st.selectbox("Lançamento", list(op.keys()))
            novo = st.selectbox("Novo status", STATUS)
            pag = None
            if novo == "Pago":
                pag = st.date_input("Data pagamento", value=date.today())
            if st.button("Atualizar status", type="primary"):
                lid = op[esc]
                row = df[df["id"] == lid].iloc[0].to_dict()
                row["status"] = novo
                row["data_pagamento"] = str(pag) if pag else None
                salvar_lancamento(u["empresa_id"], u["id"], row, lid)
                st.success("Status atualizado.")
                st.rerun()

    elif menu == "Excluir lançamento":
        st.markdown('<div class="section-title">Excluir lançamento</div>', unsafe_allow_html=True)
        if df_mes.empty:
            st.info("Nenhum lançamento no mês.")
        else:
            op = {f"#{int(r.id)} | {r.tipo} | {r.descricao} | {moeda(r.valor)} | {r.status}": int(r.id) for r in df_mes.itertuples()}
            esc = st.selectbox("Selecione", list(op.keys()))
            confirmar = st.checkbox("Confirmo que desejo excluir definitivamente.")
            if st.button("Excluir", type="primary"):
                if confirmar:
                    excluir_lancamento(u["empresa_id"], op[esc])
                    st.success("Lançamento excluído.")
                    st.rerun()
                else:
                    st.warning("Confirme antes de excluir.")

    elif menu == "Lançamentos":
        st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
        if df_mes.empty:
            st.info("Nenhum lançamento no mês.")
        else:
            show = df_mes.copy()
            show["valor"] = show["valor"].apply(moeda)
            for c in ["data_lancamento","vencimento","data_pagamento"]:
                show[c] = show[c].dt.strftime("%d/%m/%Y").fillna("")
            st.dataframe(show[["id","tipo","descricao","categoria","valor","data_lancamento","vencimento","data_pagamento","forma_pagamento","status","observacao"]], use_container_width=True, hide_index=True)
            csv = df_mes.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Exportar CSV", csv, file_name=f"financeiro_{ano}_{mes:02d}.csv", mime="text/csv")

    elif menu == "Admin usuários":
        st.markdown('<div class="section-title">Administração de usuários</div>', unsafe_allow_html=True)
        users = usuarios_df(u["empresa_id"])
        st.dataframe(users, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Criar usuário")
            nome = st.text_input("Nome")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["usuario", "admin"])
            pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?")
            resposta = st.text_input("Resposta recuperação", type="password")
            if st.button("Criar usuário"):
                ok, msg = criar_usuario_admin(u["empresa_id"], nome, usuario, senha, perfil, pergunta, resposta)
                st.success(msg) if ok else st.error(msg)
                if ok: st.rerun()
        with c2:
            st.subheader("Gerenciar usuário")
            if not users.empty:
                op = {f"{r.usuario} | {r.nome} | {r.perfil} | {r.status}": int(r.id) for r in users.itertuples()}
                esc = st.selectbox("Usuário", list(op.keys()))
                uid = op[esc]
                nova = st.text_input("Nova senha", type="password")
                if st.button("Trocar senha"):
                    if len(nova) < 4:
                        st.error("Senha precisa ter pelo menos 4 caracteres.")
                    else:
                        alterar_senha_admin(uid, nova)
                        st.success("Senha alterada.")
                status = st.selectbox("Status do usuário", ["Ativo", "Inativo"])
                if st.button("Atualizar status usuário"):
                    status_usuario_admin(uid, status)
                    st.success("Status atualizado.")
                    st.rerun()
                conf = st.checkbox("Confirmo excluir usuário")
                if st.button("Excluir usuário"):
                    if conf:
                        ok, msg = excluir_usuario_admin(uid, u["empresa_id"], u["id"])
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()
                    else:
                        st.warning("Confirme antes de excluir.")

init_db()
if "user" not in st.session_state:
    login_page()
else:
    app_page()
