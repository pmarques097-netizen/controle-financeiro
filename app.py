import streamlit as st
import sqlite3
import hashlib
import os
import pandas as pd
from datetime import date, datetime

APP_TITLE = "Controle Financeiro V8"
DB_PATH = os.path.join(os.path.dirname(__file__), "financeiro_v8.db")
CATEGORIAS_RECEITA = ["Salário", "Venda", "Serviço", "Transferência", "Outros"]
CATEGORIAS_DESPESA = ["Alimentação", "Moradia", "Transporte", "Saúde", "Educação", "Cartão", "Empréstimo", "Lazer", "Impostos", "Fornecedor", "Outros"]
FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito", "Boleto", "Transferência", "Outro"]
STATUS_OPCOES = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 900px;}
[data-testid="stMetricValue"] {font-size: 1.45rem;}
.stButton>button {width: 100%; border-radius: 12px; height: 3rem; font-weight: 700;}
.stTextInput input, .stNumberInput input, .stDateInput input {border-radius: 10px;}
div[data-baseweb="select"] > div {border-radius: 10px;}
.card {padding: 14px; border-radius: 16px; background: rgba(128,128,128,0.08); margin-bottom: 10px;}
.small {font-size: 0.86rem; opacity: 0.78;}
</style>
""", unsafe_allow_html=True)


def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def senha_hash(senha: str, salt: str = "eirox_financeiro_v8") -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 120000).hex()


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
    conn.commit()
    # cria empresa/admin padrão se banco vazio
    cur.execute("SELECT COUNT(*) FROM empresas")
    if cur.fetchone()[0] == 0:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", ("Pessoal", agora))
        empresa_id = cur.lastrowid
        cur.execute("""INSERT INTO usuarios (empresa_id, usuario, senha_hash, perfil, status, criado_em)
                    VALUES (?, ?, ?, 'Admin', 'Ativo', ?)""", (empresa_id, "admin", senha_hash("admin123"), agora))
        conn.commit()
    conn.close()


def empresas_ativas():
    conn = conectar()
    df = pd.read_sql_query("SELECT id, nome FROM empresas WHERE status='Ativa' ORDER BY nome", conn)
    conn.close()
    return df


def autenticar(empresa_nome, usuario, senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.id, u.usuario, u.perfil, e.id, e.nome
                   FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE e.nome=? AND u.usuario=? AND u.senha_hash=? AND u.status='Ativo' AND e.status='Ativa'""",
                (empresa_nome, usuario.strip(), senha_hash(senha)))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "usuario": row[1], "perfil": row[2], "empresa_id": row[3], "empresa": row[4]}
    return None


def carregar_lancamentos(empresa_id):
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_vencimento) DESC, id DESC", conn, params=(empresa_id,))
    conn.close()
    return df


def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def tela_login():
    st.title("💰 Controle Financeiro")
    st.caption("Login por empresa")
    empresas = empresas_ativas()
    if empresas.empty:
        st.error("Nenhuma empresa ativa cadastrada.")
        return
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
    st.info("Acesso inicial: empresa **Pessoal**, usuário **admin**, senha **admin123**. Altere depois em Administração.")


def menu_topo():
    auth = st.session_state["auth"]
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"### 💰 {auth['empresa']}  \n<span class='small'>Usuário: {auth['usuario']} | Perfil: {auth['perfil']}</span>", unsafe_allow_html=True)
    with c2:
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()


def tela_lancamento(auth):
    st.subheader("➕ Novo lançamento")
    tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
    categorias = CATEGORIAS_DESPESA if tipo == "Despesa" else CATEGORIAS_RECEITA
    with st.form("novo_lancamento", clear_on_submit=True):
        descricao = st.text_input("Descrição", placeholder="Ex.: Mercado, aluguel, salário")
        valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f")
        categoria = st.selectbox("Categoria", categorias)
        forma = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO)
        status = st.selectbox("Status", STATUS_OPCOES, index=0)
        col1, col2 = st.columns(2)
        with col1:
            data_lanc = st.date_input("Data do lançamento", value=date.today())
        with col2:
            venc = st.date_input("Data de vencimento", value=date.today())
        data_pag = None
        if status == "Pago":
            data_pag = st.date_input("Data de pagamento", value=date.today())
        obs = st.text_area("Observação", height=80)
        salvar = st.form_submit_button("Salvar lançamento")
    if salvar:
        if not descricao.strip() or valor <= 0:
            st.warning("Preencha descrição e valor maior que zero.")
        else:
            conn = conectar()
            conn.execute("""INSERT INTO lancamentos
                (empresa_id, tipo, descricao, categoria, valor, forma_pagamento, status, data_lancamento, data_vencimento, data_pagamento, observacao, criado_por, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (auth["empresa_id"], tipo, descricao.strip(), categoria, float(valor), forma, status,
                 str(data_lanc), str(venc), str(data_pag) if data_pag else None, obs, auth["usuario"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit(); conn.close()
            st.success("Lançamento salvo.")
            st.rerun()


def painel(auth):
    df = carregar_lancamentos(auth["empresa_id"])
    if df.empty:
        st.info("Nenhum lançamento cadastrado ainda.")
        return
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    receitas = df[df["tipo"] == "Receita"]["valor"].sum()
    despesas = df[df["tipo"] == "Despesa"]["valor"].sum()
    saldo = receitas - despesas
    aberto = df[df["status"] == "Em aberto"]["valor"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receitas", brl(receitas))
    c2.metric("Despesas", brl(despesas))
    c3.metric("Saldo", brl(saldo))
    c4.metric("Em aberto", brl(aberto))

    st.subheader("📌 Próximos vencimentos")
    abertos = df[df["status"] == "Em aberto"].copy()
    if not abertos.empty:
        abertos["data_vencimento_dt"] = pd.to_datetime(abertos["data_vencimento"], errors="coerce")
        abertos = abertos.sort_values("data_vencimento_dt").head(10)
        for _, r in abertos.iterrows():
            st.markdown(f"<div class='card'><b>{r['descricao']}</b><br>{r['categoria']} | {brl(r['valor'])}<br><span class='small'>Vencimento: {r['data_vencimento']} | {r['forma_pagamento']}</span></div>", unsafe_allow_html=True)
    else:
        st.success("Nenhuma conta em aberto.")

    st.subheader("📊 Resumo por categoria")
    resumo = df.groupby(["tipo", "categoria"], as_index=False)["valor"].sum()
    resumo["Valor"] = resumo["valor"].apply(brl)
    st.dataframe(resumo[["tipo", "categoria", "Valor"]], use_container_width=True, hide_index=True)


def alterar_status(auth):
    st.subheader("✅ Alterar status")
    df = carregar_lancamentos(auth["empresa_id"])
    if df.empty:
        st.info("Nenhum lançamento para alterar.")
        return
    df["label"] = df.apply(lambda r: f"#{int(r['id'])} | {r['status']} | {r['tipo']} | {r['descricao']} | {brl(r['valor'])} | Venc.: {r['data_vencimento']}", axis=1)
    escolha = st.selectbox("Escolha o lançamento", df["label"].tolist())
    id_sel = int(escolha.split("|")[0].replace("#", "").strip())
    novo_status = st.selectbox("Novo status", STATUS_OPCOES)
    data_pag = None
    if novo_status == "Pago":
        data_pag = st.date_input("Data de pagamento", value=date.today())
    if st.button("Atualizar status"):
        conn = conectar()
        conn.execute("UPDATE lancamentos SET status=?, data_pagamento=? WHERE id=? AND empresa_id=?", (novo_status, str(data_pag) if data_pag else None, id_sel, auth["empresa_id"]))
        conn.commit(); conn.close()
        st.success("Status atualizado.")
        st.rerun()


def listar(auth):
    st.subheader("📄 Lançamentos")
    df = carregar_lancamentos(auth["empresa_id"])
    if df.empty:
        st.info("Sem dados.")
        return
    col1, col2 = st.columns(2)
    with col1:
        filtro_status = st.selectbox("Filtrar status", ["Todos"] + STATUS_OPCOES)
    with col2:
        filtro_tipo = st.selectbox("Filtrar tipo", ["Todos", "Receita", "Despesa"])
    if filtro_status != "Todos":
        df = df[df["status"] == filtro_status]
    if filtro_tipo != "Todos":
        df = df[df["tipo"] == filtro_tipo]
    df_show = df[["id", "tipo", "descricao", "categoria", "valor", "forma_pagamento", "status", "data_vencimento", "data_pagamento"]].copy()
    df_show["valor"] = df_show["valor"].apply(brl)
    st.dataframe(df_show, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar CSV", data=csv, file_name=f"financeiro_{auth['empresa']}.csv", mime="text/csv")


def administracao(auth):
    if auth["perfil"] != "Admin":
        st.warning("Apenas Admin pode acessar Administração.")
        return
    st.subheader("⚙️ Administração")
    tab1, tab2, tab3 = st.tabs(["Empresas", "Usuários", "Trocar senha"])
    with tab1:
        with st.form("nova_empresa"):
            nome = st.text_input("Nova empresa")
            criar = st.form_submit_button("Criar empresa")
        if criar and nome.strip():
            try:
                conn = conectar(); conn.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", (nome.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close()
                st.success("Empresa criada.")
            except sqlite3.IntegrityError:
                st.error("Empresa já existe.")
        st.dataframe(empresas_ativas(), use_container_width=True, hide_index=True)
    with tab2:
        empresas = empresas_ativas()
        with st.form("novo_usuario"):
            emp_nome = st.selectbox("Empresa do usuário", empresas["nome"].tolist())
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["Usuario", "Admin"])
            criar_user = st.form_submit_button("Criar usuário")
        if criar_user:
            emp_id = int(empresas.loc[empresas["nome"] == emp_nome, "id"].iloc[0])
            try:
                conn = conectar(); conn.execute("""INSERT INTO usuarios (empresa_id, usuario, senha_hash, perfil, status, criado_em)
                    VALUES (?, ?, ?, ?, 'Ativo', ?)""", (emp_id, usuario.strip(), senha_hash(senha), perfil, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close()
                st.success("Usuário criado.")
            except sqlite3.IntegrityError:
                st.error("Usuário já existe nessa empresa.")
        conn = conectar()
        users = pd.read_sql_query("""SELECT e.nome AS empresa, u.usuario, u.perfil, u.status FROM usuarios u JOIN empresas e ON e.id=u.empresa_id ORDER BY e.nome, u.usuario""", conn)
        conn.close()
        st.dataframe(users, use_container_width=True, hide_index=True)
    with tab3:
        with st.form("troca_senha"):
            nova = st.text_input("Nova senha do meu usuário", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")
            trocar = st.form_submit_button("Alterar minha senha")
        if trocar:
            if not nova or nova != confirmar:
                st.error("As senhas não conferem.")
            else:
                conn = conectar(); conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova), auth["user_id"])); conn.commit(); conn.close()
                st.success("Senha alterada. Faça login novamente.")


def main():
    init_db()
    if "auth" not in st.session_state:
        tela_login()
        return
    auth = st.session_state["auth"]
    menu_topo()
    abas = ["Painel", "Novo", "Alterar Status", "Lançamentos"]
    if auth["perfil"] == "Admin":
        abas.append("Administração")
    escolha = st.radio("Menu", abas, horizontal=True, label_visibility="collapsed")
    if escolha == "Painel": painel(auth)
    elif escolha == "Novo": tela_lancamento(auth)
    elif escolha == "Alterar Status": alterar_status(auth)
    elif escolha == "Lançamentos": listar(auth)
    elif escolha == "Administração": administracao(auth)

if __name__ == "__main__":
    main()
