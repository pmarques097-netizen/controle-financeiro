
import streamlit as st
import sqlite3
import hashlib
import os
import pandas as pd
from datetime import date, datetime

APP_TITLE = "Controle Financeiro Profissional"
DB_PATH = os.path.join(os.path.dirname(__file__), "financeiro_v8.db")

CATEGORIAS_RECEITA = ["Salário", "Venda", "Serviço", "Transferência", "Investimento", "Reembolso", "Outros"]
CATEGORIAS_DESPESA = ["Alimentação", "Moradia", "Transporte", "Saúde", "Educação", "Cartão", "Empréstimo", "Lazer", "Impostos", "Fornecedor", "Mercado", "Outros"]
FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito", "Boleto", "Transferência", "Outro"]
STATUS_OPCOES = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
:root {
    --bg: #0B1020;
    --panel: #111827;
    --panel2: #0F172A;
    --border: #263244;
    --text: #F8FAFC;
    --muted: #94A3B8;
    --blue: #38BDF8;
    --green: #22C55E;
    --red: #EF4444;
    --yellow: #F59E0B;
}
.main .block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
    max-width: 1180px;
}
[data-testid="stSidebar"] {
    background: #050816;
}
.hero {
    padding: 18px 22px;
    border-radius: 22px;
    background: linear-gradient(135deg, #0f172a 0%, #111827 58%, #082f49 100%);
    border: 1px solid #243247;
    margin-bottom: 18px;
}
.hero-title {
    font-size: 28px;
    font-weight: 850;
    margin: 0;
    letter-spacing: -0.03em;
}
.hero-sub {
    color: #CBD5E1;
    margin-top: 4px;
    font-size: 14px;
}
.metric-card {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 18px;
    padding: 16px;
    min-height: 108px;
    box-shadow: 0 12px 28px rgba(0,0,0,.18);
}
.metric-label {
    color: #94A3B8;
    font-size: 13px;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 26px;
    font-weight: 850;
    letter-spacing: -0.02em;
}
.positive {color:#22C55E;}
.negative {color:#EF4444;}
.warning {color:#F59E0B;}
.info {color:#38BDF8;}
.card {
    padding: 14px;
    border-radius: 16px;
    background: #0F172A;
    border: 1px solid #243247;
    margin-bottom: 10px;
}
.badge {
    display:inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    border:1px solid #334155;
    background:#0f172a;
    color:#cbd5e1;
    font-size:12px;
    margin-right: 6px;
    margin-bottom: 6px;
}
.small {font-size: 0.86rem; color: #94A3B8;}
.section-title {
    font-size: 20px;
    font-weight: 850;
    margin: 8px 0 12px 0;
}
.stButton>button {
    width: 100%;
    border-radius: 12px;
    min-height: 44px;
    font-weight: 750;
}
.stTextInput input, .stNumberInput input, .stDateInput input {
    border-radius: 12px !important;
    font-size: 16px !important;
}
div[data-baseweb="select"] > div {
    border-radius: 12px !important;
}
.login-box {
    padding: 20px;
    border-radius: 20px;
    border: 1px solid #243247;
    background: #111827;
}
@media (max-width: 768px) {
    .main .block-container {padding-left: .8rem; padding-right: .8rem;}
    .hero-title {font-size: 23px;}
    .metric-value {font-size: 22px;}
}
</style>
""", unsafe_allow_html=True)


def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def senha_hash(senha: str, salt: str = "eirox_financeiro_v8") -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        str(senha).encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()


def coluna_existe(conn, tabela, coluna):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabela})")
    return coluna in [r[1] for r in cur.fetchall()]


def garantir_coluna(conn, tabela, coluna, tipo):
    if not coluna_existe(conn, tabela, coluna):
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def init_db():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'Ativa',
        criado_em TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        usuario TEXT NOT NULL,
        senha_hash TEXT NOT NULL,
        perfil TEXT NOT NULL DEFAULT 'Usuario',
        status TEXT NOT NULL DEFAULT 'Ativo',
        criado_em TEXT NOT NULL,
        UNIQUE(empresa_id, usuario)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS lancamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        valor REAL NOT NULL,
        forma_pagamento TEXT,
        status TEXT NOT NULL,
        data_lancamento TEXT NOT NULL,
        data_vencimento TEXT,
        data_pagamento TEXT,
        observacao TEXT,
        criado_por TEXT,
        criado_em TEXT NOT NULL
    )""")

    garantir_coluna(conn, "usuarios", "nome", "TEXT")
    garantir_coluna(conn, "usuarios", "pergunta", "TEXT")
    garantir_coluna(conn, "usuarios", "resposta_hash", "TEXT")
    garantir_coluna(conn, "lancamentos", "atualizado_em", "TEXT")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM empresas")
    if cur.fetchone()[0] == 0:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", ("Pessoal", agora))
        empresa_id = cur.lastrowid
        cur.execute("""INSERT INTO usuarios
            (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, 'Admin', 'Ativo', ?, ?, ?)""",
            (empresa_id, "admin", "Administrador", senha_hash("admin123"), "Código de recuperação", senha_hash("admin123"), agora))
        conn.commit()

    cur.execute("UPDATE usuarios SET nome=usuario WHERE nome IS NULL OR trim(nome)=''")
    cur.execute("UPDATE usuarios SET pergunta='Código de recuperação' WHERE pergunta IS NULL OR trim(pergunta)=''")
    cur.execute("UPDATE usuarios SET resposta_hash=? WHERE resposta_hash IS NULL OR trim(resposta_hash)=''", (senha_hash("admin123"),))
    conn.commit()
    conn.close()


def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def empresas_ativas():
    conn = conectar()
    df = pd.read_sql_query("SELECT id, nome FROM empresas WHERE status='Ativa' ORDER BY nome", conn)
    conn.close()
    return df


def autenticar(empresa_nome, usuario, senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.id, u.usuario, COALESCE(u.nome,u.usuario), u.perfil, e.id, e.nome
                   FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)
                   AND u.senha_hash=? AND u.status='Ativo' AND e.status='Ativa'""",
                (empresa_nome.strip(), usuario.strip(), senha_hash(senha)))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "usuario": row[1], "nome": row[2], "perfil": row[3], "empresa_id": row[4], "empresa": row[5]}
    return None


def criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta):
    empresa = empresa.strip()
    usuario = usuario.strip().lower()
    if not empresa or not usuario or not senha:
        return False, "Preencha empresa, usuário e senha."
    if len(senha) < 4:
        return False, "A senha precisa ter pelo menos 4 caracteres."

    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (empresa,))
        row = cur.fetchone()
        if row:
            empresa_id = row[0]
            perfil = "Usuario"
        else:
            cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", (empresa, agora))
            empresa_id = cur.lastrowid
            perfil = "Admin"

        cur.execute("""INSERT INTO usuarios
            (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?)""",
            (empresa_id, usuario, nome.strip() or usuario, senha_hash(senha), perfil,
             pergunta.strip() or "Código de recuperação", senha_hash(resposta.strip().lower()), agora))
        conn.commit()
        return True, f"Conta criada com sucesso. Perfil: {perfil}."
    except sqlite3.IntegrityError:
        return False, "Esse usuário já existe nessa empresa."
    finally:
        conn.close()


def pergunta_recuperacao(empresa, usuario):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.pergunta
                   FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""",
                (empresa.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def resetar_senha(empresa, usuario, resposta, nova_senha):
    if len(nova_senha) < 4:
        return False, "A nova senha precisa ter pelo menos 4 caracteres."

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.id, u.resposta_hash
                   FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""",
                (empresa.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Empresa ou usuário não encontrado."
    user_id, resposta_hash = row
    if senha_hash(resposta.strip().lower()) != resposta_hash:
        conn.close()
        return False, "Resposta de recuperação incorreta."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova_senha), user_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso."


def carregar_lancamentos(empresa_id):
    conn = conectar()
    df = pd.read_sql_query(
        "SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC",
        conn,
        params=(empresa_id,)
    )
    conn.close()
    if not df.empty:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        for c in ["data_lancamento", "data_vencimento", "data_pagamento"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def filtrar_mes(df, mes, ano):
    if df.empty:
        return df
    return df[(df["data_lancamento"].dt.month == mes) & (df["data_lancamento"].dt.year == ano)].copy()


def salvar_lancamento(auth, dados, lancamento_id=None):
    conn = conectar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if lancamento_id:
        conn.execute("""UPDATE lancamentos
            SET tipo=?, descricao=?, categoria=?, valor=?, forma_pagamento=?, status=?,
                data_lancamento=?, data_vencimento=?, data_pagamento=?, observacao=?, atualizado_em=?
            WHERE id=? AND empresa_id=?""",
            (dados["tipo"], dados["descricao"], dados["categoria"], float(dados["valor"]), dados["forma_pagamento"],
             dados["status"], dados["data_lancamento"], dados["data_vencimento"], dados["data_pagamento"],
             dados["observacao"], agora, lancamento_id, auth["empresa_id"]))
    else:
        conn.execute("""INSERT INTO lancamentos
            (empresa_id, tipo, descricao, categoria, valor, forma_pagamento, status,
             data_lancamento, data_vencimento, data_pagamento, observacao, criado_por, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (auth["empresa_id"], dados["tipo"], dados["descricao"], dados["categoria"], float(dados["valor"]),
             dados["forma_pagamento"], dados["status"], dados["data_lancamento"], dados["data_vencimento"],
             dados["data_pagamento"], dados["observacao"], auth["usuario"], agora, agora))
    conn.commit()
    conn.close()


def excluir_lancamento(auth, lancamento_id):
    conn = conectar()
    conn.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?", (lancamento_id, auth["empresa_id"]))
    conn.commit()
    conn.close()


def tela_login():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">💼 Controle Financeiro Profissional</div>
        <div class="hero-sub">Organize receitas, despesas, vencimentos e usuários por empresa.</div>
    </div>
    """, unsafe_allow_html=True)

    col_info, col_login = st.columns([1.05, 1])

    with col_info:
        st.markdown("### Gestão simples para uso diário")
        st.markdown("""
        <div class="card">
            <span class="badge">Multiempresa</span>
            <span class="badge">Login seguro</span>
            <span class="badge">Mobile</span>
            <span class="badge">Administração</span>
            <br><br>
            <span class="small">
            Cada empresa possui sua própria base de lançamentos. Quem cria uma nova empresa vira Admin dessa empresa.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Acesso inicial: empresa **Pessoal**, usuário **admin**, senha **admin123**.")

    with col_login:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        abas = st.tabs(["Entrar", "Criar conta", "Esqueci senha"])

        with abas[0]:
            empresas = empresas_ativas()
            if empresas.empty:
                st.error("Nenhuma empresa ativa cadastrada.")
            else:
                with st.form("login"):
                    empresa = st.selectbox("Empresa", empresas["nome"].tolist())
                    usuario = st.text_input("Usuário")
                    senha = st.text_input("Senha", type="password")
                    entrar = st.form_submit_button("Entrar")
                if entrar:
                    sess = autenticar(empresa, usuario, senha)
                    if sess:
                        st.session_state["auth"] = sess
                        st.rerun()
                    else:
                        st.error("Empresa, usuário ou senha inválidos.")

        with abas[1]:
            st.caption("Se a empresa não existir, ela será criada e você será Admin.")
            with st.form("cadastro_publico"):
                empresa = st.text_input("Empresa")
                nome = st.text_input("Seu nome")
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                pergunta = st.text_input("Pergunta de recuperação", value="Qual seu código de recuperação?")
                resposta = st.text_input("Resposta de recuperação", type="password")
                criar = st.form_submit_button("Criar acesso")
            if criar:
                ok, msg = criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta)
                st.success(msg) if ok else st.error(msg)

        with abas[2]:
            with st.form("buscar_pergunta"):
                empresa = st.text_input("Empresa", key="rec_empresa")
                usuario = st.text_input("Usuário", key="rec_usuario")
                buscar = st.form_submit_button("Buscar pergunta")
            if buscar:
                pergunta = pergunta_recuperacao(empresa, usuario)
                if pergunta:
                    st.session_state["recuperacao"] = {"empresa": empresa, "usuario": usuario, "pergunta": pergunta}
                else:
                    st.error("Empresa ou usuário não encontrado.")

            if "recuperacao" in st.session_state:
                st.info(st.session_state["recuperacao"]["pergunta"])
                with st.form("resetar_senha"):
                    resposta = st.text_input("Resposta", type="password")
                    nova_senha = st.text_input("Nova senha", type="password")
                    alterar = st.form_submit_button("Alterar senha")
                if alterar:
                    rec = st.session_state["recuperacao"]
                    ok, msg = resetar_senha(rec["empresa"], rec["usuario"], resposta, nova_senha)
                    st.success(msg) if ok else st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)


def filtro_mes_ano():
    hoje = date.today()
    c1, c2 = st.columns([1, 1])
    with c1:
        mes = st.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1, format_func=lambda x: f"{x:02d}")
    with c2:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=hoje.year, step=1)
    return int(mes), int(ano)


def form_lancamento(default=None, form_key="form_lancamento"):
    default = default or {}
    tipo_default = default.get("tipo", "Despesa")
    with st.form(form_key):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, index=0 if tipo_default == "Despesa" else 1)
        categorias = CATEGORIAS_DESPESA if tipo == "Despesa" else CATEGORIAS_RECEITA

        c1, c2 = st.columns(2)
        with c1:
            descricao = st.text_input("Descrição", value=default.get("descricao", ""))
            categoria_default = default.get("categoria", categorias[0])
            categoria = st.selectbox("Categoria", categorias, index=categorias.index(categoria_default) if categoria_default in categorias else 0)
            valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f", value=float(default.get("valor", 0) or 0))

        with c2:
            dl = default.get("data_lancamento")
            dv = default.get("data_vencimento")
            data_lanc = st.date_input("Data lançamento", value=pd.to_datetime(dl).date() if pd.notna(dl) and dl is not None else date.today())
            venc = st.date_input("Vencimento", value=pd.to_datetime(dv).date() if pd.notna(dv) and dv is not None else date.today())
            status_default = default.get("status", "Em aberto")
            status = st.selectbox("Status", STATUS_OPCOES, index=STATUS_OPCOES.index(status_default) if status_default in STATUS_OPCOES else 0)

        c3, c4 = st.columns(2)
        with c3:
            forma_default = default.get("forma_pagamento", FORMAS_PAGAMENTO[0])
            forma = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO, index=FORMAS_PAGAMENTO.index(forma_default) if forma_default in FORMAS_PAGAMENTO else 0)
        with c4:
            data_pag = None
            if status == "Pago":
                dp = default.get("data_pagamento")
                data_pag = st.date_input("Data de pagamento", value=pd.to_datetime(dp).date() if pd.notna(dp) and dp is not None else date.today())

        obs = st.text_area("Observação", value=default.get("observacao", "") or "", height=80)
        salvar = st.form_submit_button("Salvar", type="primary")

    dados = {
        "tipo": tipo,
        "descricao": descricao.strip(),
        "categoria": categoria,
        "valor": valor,
        "forma_pagamento": forma,
        "status": status,
        "data_lancamento": str(data_lanc),
        "data_vencimento": str(venc),
        "data_pagamento": str(data_pag) if data_pag else None,
        "observacao": obs,
    }
    return salvar, dados


def cards(df):
    receitas = df[(df["tipo"] == "Receita") & (df["status"] != "Cancelado")]["valor"].sum() if not df.empty else 0
    despesas = df[(df["tipo"] == "Despesa") & (df["status"] != "Cancelado")]["valor"].sum() if not df.empty else 0
    saldo = receitas - despesas
    aberto = df[df["status"] == "Em aberto"]["valor"].sum() if not df.empty else 0

    dados = [
        ("Receitas", receitas, "positive"),
        ("Despesas", despesas, "negative"),
        ("Saldo", saldo, "positive" if saldo >= 0 else "negative"),
        ("Em aberto", aberto, "warning"),
    ]

    cols = st.columns(4)
    for col, (label, value, classe) in zip(cols, dados):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {classe}">{brl(value)}</div>
        </div>
        """, unsafe_allow_html=True)


def painel(auth, df_mes):
    cards(df_mes)

    st.markdown('<div class="section-title">Resumo do mês</div>', unsafe_allow_html=True)

    if df_mes.empty:
        st.info("Nenhum lançamento no período selecionado.")
        return

    c1, c2 = st.columns(2)
    with c1:
        resumo_cat = df_mes.groupby(["tipo", "categoria"], as_index=False)["valor"].sum()
        resumo_cat["valor"] = resumo_cat["valor"].apply(brl)
        st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
    with c2:
        resumo_status = df_mes.groupby(["status"], as_index=False)["valor"].sum()
        resumo_status["valor"] = resumo_status["valor"].apply(brl)
        st.dataframe(resumo_status, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Próximos vencimentos</div>', unsafe_allow_html=True)
    abertos = df_mes[df_mes["status"] == "Em aberto"].copy()
    if abertos.empty:
        st.success("Nenhuma conta em aberto neste mês.")
    else:
        abertos = abertos.sort_values("data_vencimento").head(10)
        for _, r in abertos.iterrows():
            venc = r["data_vencimento"].strftime("%d/%m/%Y") if pd.notna(r["data_vencimento"]) else "-"
            st.markdown(
                f"<div class='card'><b>{r['descricao']}</b><br>{r['categoria']} | {brl(r['valor'])}<br><span class='small'>Vencimento: {venc} | {r['forma_pagamento']}</span></div>",
                unsafe_allow_html=True
            )


def selecionar_lancamento(df_mes, label):
    if df_mes.empty:
        st.info("Nenhum lançamento no mês selecionado.")
        return None
    opcoes = {
        f"#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {brl(r.valor)}": int(r.id)
        for r in df_mes.itertuples()
    }
    escolha = st.selectbox(label, list(opcoes.keys()))
    return opcoes[escolha]


def listar(df_mes, auth):
    if df_mes.empty:
        st.info("Nenhum lançamento no mês selecionado.")
        return

    col1, col2 = st.columns(2)
    with col1:
        filtro_status = st.selectbox("Filtrar status", ["Todos"] + STATUS_OPCOES)
    with col2:
        filtro_tipo = st.selectbox("Filtrar tipo", ["Todos", "Receita", "Despesa"])

    df = df_mes.copy()
    if filtro_status != "Todos":
        df = df[df["status"] == filtro_status]
    if filtro_tipo != "Todos":
        df = df[df["tipo"] == filtro_tipo]

    show = df[["id", "tipo", "descricao", "categoria", "valor", "forma_pagamento", "status", "data_lancamento", "data_vencimento", "data_pagamento"]].copy()
    show["valor"] = show["valor"].apply(brl)
    for c in ["data_lancamento", "data_vencimento", "data_pagamento"]:
        show[c] = show[c].dt.strftime("%d/%m/%Y").fillna("")
    st.dataframe(show, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Exportar CSV", data=csv, file_name=f"financeiro_{auth['empresa']}.csv", mime="text/csv")


def administracao(auth):
    if auth["perfil"] != "Admin":
        st.warning("Apenas Admin pode acessar Administração.")
        return

    st.markdown('<div class="section-title">Administração</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Empresas", "Usuários", "Senhas / Status"])

    with tab1:
        with st.form("nova_empresa"):
            nome = st.text_input("Nova empresa")
            criar = st.form_submit_button("Criar empresa")
        if criar and nome.strip():
            try:
                conn = conectar()
                conn.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", (nome.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("Empresa criada.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Empresa já existe.")
        st.dataframe(empresas_ativas(), use_container_width=True, hide_index=True)

    with tab2:
        empresas = empresas_ativas()
        with st.form("novo_usuario"):
            emp_nome = st.selectbox("Empresa do usuário", empresas["nome"].tolist())
            nome = st.text_input("Nome")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["Usuario", "Admin"])
            pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?")
            resposta = st.text_input("Resposta recuperação", type="password")
            criar_user = st.form_submit_button("Criar usuário")
        if criar_user:
            if not usuario.strip() or not senha:
                st.error("Preencha usuário e senha.")
            else:
                emp_id = int(empresas.loc[empresas["nome"] == emp_nome, "id"].iloc[0])
                try:
                    conn = conectar()
                    conn.execute("""INSERT INTO usuarios
                        (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
                        VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?)""",
                        (emp_id, usuario.strip().lower(), nome.strip() or usuario.strip(), senha_hash(senha), perfil,
                         pergunta.strip(), senha_hash(resposta.strip().lower()), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                    st.success("Usuário criado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe nessa empresa.")

        conn = conectar()
        users = pd.read_sql_query("""SELECT u.id, e.nome AS empresa, u.usuario, COALESCE(u.nome,u.usuario) AS nome, u.perfil, u.status
                                    FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                                    ORDER BY e.nome, u.usuario""", conn)
        conn.close()
        st.dataframe(users, use_container_width=True, hide_index=True)

    with tab3:
        conn = conectar()
        users = pd.read_sql_query("""SELECT u.id, e.nome AS empresa, u.usuario, COALESCE(u.nome,u.usuario) AS nome, u.perfil, u.status
                                    FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                                    ORDER BY e.nome, u.usuario""", conn)
        conn.close()
        if users.empty:
            st.info("Nenhum usuário.")
            return

        opcoes = {
            f"{r.empresa} | {r.usuario} | {r.perfil} | {r.status}": int(r.id)
            for r in users.itertuples()
        }
        selecionado = st.selectbox("Usuário", list(opcoes.keys()))
        user_id = opcoes[selecionado]

        c1, c2 = st.columns(2)
        with c1:
            nova = st.text_input("Nova senha", type="password")
            if st.button("Trocar senha"):
                if len(nova) < 4:
                    st.error("Senha precisa ter pelo menos 4 caracteres.")
                else:
                    conn = conectar()
                    conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova), user_id))
                    conn.commit()
                    conn.close()
                    st.success("Senha alterada.")
        with c2:
            novo_status = st.selectbox("Status", ["Ativo", "Inativo"])
            if st.button("Atualizar status"):
                conn = conectar()
                conn.execute("UPDATE usuarios SET status=? WHERE id=?", (novo_status, user_id))
                conn.commit()
                conn.close()
                st.success("Status atualizado.")
                st.rerun()

        confirmar = st.checkbox("Confirmo excluir este usuário")
        if st.button("Excluir usuário"):
            if not confirmar:
                st.warning("Marque a confirmação.")
            elif user_id == auth["user_id"]:
                st.error("Você não pode excluir o usuário logado.")
            else:
                conn = conectar()
                conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
                conn.commit()
                conn.close()
                st.success("Usuário excluído.")
                st.rerun()


def app_logado():
    auth = st.session_state["auth"]

    with st.sidebar:
        st.markdown("## 💼 Financeiro")
        st.caption(f"Empresa: **{auth['empresa']}**")
        st.caption(f"Usuário: **{auth['usuario']}**")
        st.caption(f"Perfil: **{auth['perfil']}**")
        st.divider()

        menu = ["Painel", "Novo lançamento", "Alterar lançamento", "Alterar status", "Excluir lançamento", "Lançamentos"]
        if auth["perfil"] == "Admin":
            menu.append("Administração")
        escolha = st.radio("Menu", menu)

        st.divider()
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">Controle Financeiro</div>
        <div class="hero-sub">Empresa: {auth['empresa']} · Usuário: {auth['usuario']}</div>
    </div>
    """, unsafe_allow_html=True)

    mes, ano = filtro_mes_ano()
    df = carregar_lancamentos(auth["empresa_id"])
    df_mes = filtrar_mes(df, mes, ano)

    if escolha == "Painel":
        painel(auth, df_mes)

    elif escolha == "Novo lançamento":
        st.markdown('<div class="section-title">Novo lançamento</div>', unsafe_allow_html=True)
        salvar, dados = form_lancamento(form_key="novo_lancamento")
        if salvar:
            if not dados["descricao"] or dados["valor"] <= 0:
                st.warning("Preencha descrição e valor maior que zero.")
            else:
                salvar_lancamento(auth, dados)
                st.success("Lançamento salvo.")
                st.rerun()

    elif escolha == "Alterar lançamento":
        st.markdown('<div class="section-title">Alterar lançamento</div>', unsafe_allow_html=True)
        lancamento_id = selecionar_lancamento(df_mes, "Escolha o lançamento")
        if lancamento_id:
            row = df[df["id"] == lancamento_id].iloc[0].to_dict()
            salvar, dados = form_lancamento(row, form_key="editar_lancamento")
            if salvar:
                if not dados["descricao"] or dados["valor"] <= 0:
                    st.warning("Preencha descrição e valor maior que zero.")
                else:
                    salvar_lancamento(auth, dados, lancamento_id)
                    st.success("Lançamento alterado.")
                    st.rerun()

    elif escolha == "Alterar status":
        st.markdown('<div class="section-title">Alterar status</div>', unsafe_allow_html=True)
        lancamento_id = selecionar_lancamento(df_mes, "Escolha o lançamento")
        if lancamento_id:
            novo_status = st.selectbox("Novo status", STATUS_OPCOES)
            data_pag = None
            if novo_status == "Pago":
                data_pag = st.date_input("Data de pagamento", value=date.today())
            if st.button("Atualizar status", type="primary"):
                conn = conectar()
                conn.execute("UPDATE lancamentos SET status=?, data_pagamento=?, atualizado_em=? WHERE id=? AND empresa_id=?",
                             (novo_status, str(data_pag) if data_pag else None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lancamento_id, auth["empresa_id"]))
                conn.commit()
                conn.close()
                st.success("Status atualizado.")
                st.rerun()

    elif escolha == "Excluir lançamento":
        st.markdown('<div class="section-title">Excluir lançamento</div>', unsafe_allow_html=True)
        lancamento_id = selecionar_lancamento(df_mes, "Escolha o lançamento")
        if lancamento_id:
            confirmar = st.checkbox("Confirmo que desejo excluir definitivamente.")
            if st.button("Excluir lançamento", type="primary"):
                if confirmar:
                    excluir_lancamento(auth, lancamento_id)
                    st.success("Lançamento excluído.")
                    st.rerun()
                else:
                    st.warning("Confirme antes de excluir.")

    elif escolha == "Lançamentos":
        st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
        listar(df_mes, auth)

    elif escolha == "Administração":
        administracao(auth)


def main():
    init_db()
    if "auth" not in st.session_state:
        tela_login()
    else:
        app_logado()


if __name__ == "__main__":
    main()
