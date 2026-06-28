
import os
import sqlite3
import hashlib
import hmac
from datetime import date, datetime
import pandas as pd
import streamlit as st

APP_TITLE = "Casa Marques Financeiro"
DB_PATH = os.path.join(os.path.dirname(__file__), "financeiro_casa_marques.db")
EMPRESA_PADRAO = "Casa Marques"

USUARIOS_PADRAO = [
    ("paulo", "Paulo Marques", "031730", "Admin"),
    ("mara", "Mara", "031730", "Usuario"),
]

CATEGORIAS = {
    "Receita": ["Salário", "Venda", "Serviço", "Transferência", "Investimento", "Reembolso", "Outros"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Saúde", "Educação", "Cartão", "Empréstimo", "Lazer", "Impostos", "Mercado", "Casa", "Outros"],
}
FORMAS = ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito", "Boleto", "Transferência", "Outro"]
STATUS = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(page_title=APP_TITLE, page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {background:#F7F8FC;}
.main .block-container {padding-top:.8rem; padding-bottom:5.5rem; max-width:760px;}
[data-testid="stSidebar"], #MainMenu, footer, header {visibility:hidden; display:none;}
.login-hero{min-height:92vh;border-radius:0 0 34px 34px;padding:28px 22px;background:radial-gradient(circle at 30% 10%,#4637ff 0%,#181043 42%,#030712 100%);color:white;}
.app-logo{width:84px;height:84px;border-radius:24px;background:linear-gradient(135deg,#7C3AED,#38BDF8);display:flex;align-items:center;justify-content:center;font-size:44px;margin:30px auto 18px auto;box-shadow:0 18px 40px rgba(99,91,255,.35);}
.login-title{text-align:center;font-size:29px;font-weight:850;margin:0;}
.login-sub{text-align:center;color:#CBD5E1;margin:8px 0 26px 0;}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:10px 2px 14px 2px;}
.top-title{font-size:23px;font-weight:850;color:#111827;letter-spacing:-.03em;}
.top-sub{font-size:13px;color:#6B7280;margin-top:2px;}
.avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#635BFF,#38BDF8);color:white;display:flex;align-items:center;justify-content:center;font-weight:850;}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0 14px 0;}
.kpi-card{background:#fff;border:1px solid #EEF0F5;border-radius:20px;padding:15px;box-shadow:0 8px 18px rgba(15,23,42,.05);}
.kpi-label{font-size:12px;color:#6B7280;font-weight:700;}
.kpi-value{font-size:22px;font-weight:850;margin-top:8px;}
.green{color:#22C55E}.red{color:#EF4444}.blue{color:#2563EB}.amber{color:#F59E0B}
.tx-card{display:flex;gap:12px;align-items:center;padding:14px;border-radius:18px;background:#fff;border:1px solid #EEF0F5;margin-bottom:10px;box-shadow:0 7px 18px rgba(15,23,42,.045);}
.tx-icon{width:42px;height:42px;border-radius:15px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}
.tx-main{flex:1}.tx-title{font-weight:820;color:#111827}.tx-sub{font-size:12px;color:#6B7280;margin-top:2px}.tx-value{font-weight:850;text-align:right;}
.section-title{font-size:18px;font-weight:850;margin:16px 0 10px;}
.stButton>button{
    width:100%;
    border-radius:18px;
    min-height:48px;
    font-weight:850;
    border:1px solid #E5E7EB;
    background:#FFFFFF;
    color:#334155;
    box-shadow:0 6px 14px rgba(15,23,42,.06);
}
.stButton>button:hover{
    border-color:#635BFF;
    color:#4F46E5;
    background:#EEF2FF;
}
.nav-wrap{
    position:fixed;
    left:50%;
    bottom:10px;
    transform:translateX(-50%);
    width:calc(100% - 18px);
    max-width:740px;
    z-index:9999;
    background:rgba(255,255,255,.96);
    border:1px solid #E5E7EB;
    box-shadow:0 16px 40px rgba(15,23,42,.18);
    border-radius:26px;
    padding:8px 8px 4px 8px;
}
.nav-label{
    text-align:center;
    font-size:11px;
    font-weight:800;
    color:#64748B;
    margin-top:-5px;
}
.nav-label-active{color:#4F46E5;}

.stTextInput input,.stNumberInput input,.stDateInput input,textarea{border-radius:16px!important;font-size:16px!important;}
div[data-baseweb="select"]>div{border-radius:16px!important;}
.bottom-spacer{height:40px;}
@media(max-width:600px){.main .block-container{padding-left:.7rem;padding-right:.7rem}.kpi-value{font-size:19px}.top-title{font-size:21px}}

div[role="radiogroup"]{
    background:#FFFFFF;
    border:1px solid #E5E7EB;
    border-radius:22px;
    padding:6px;
    box-shadow:0 8px 20px rgba(15,23,42,.06);
    margin-bottom:12px;
}
div[role="radiogroup"] label{
    border-radius:16px !important;
    padding:8px 10px !important;
}

</style>
""", unsafe_allow_html=True)


def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def senha_hash(senha: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", str(senha).encode(), b"casa_marques_final", 140000).hex()


def check_senha(senha, shash):
    return hmac.compare_digest(senha_hash(senha), shash or "")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, status TEXT DEFAULT 'Ativa', criado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, usuario TEXT, nome TEXT, senha_hash TEXT,
        perfil TEXT DEFAULT 'Usuario', status TEXT DEFAULT 'Ativo', pergunta TEXT, resposta_hash TEXT, criado_em TEXT,
        UNIQUE(empresa_id, usuario))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS lancamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, tipo TEXT, descricao TEXT, categoria TEXT,
        valor REAL, forma_pagamento TEXT, status TEXT, data_lancamento TEXT, data_vencimento TEXT,
        data_pagamento TEXT, observacao TEXT, criado_por TEXT, criado_em TEXT, atualizado_em TEXT)""")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (EMPRESA_PADRAO,))
    row = cur.fetchone()
    if row:
        empresa_id = row[0]
    else:
        cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (EMPRESA_PADRAO, agora))
        empresa_id = cur.lastrowid
    for usuario, nome, senha, perfil in USUARIOS_PADRAO:
        cur.execute("SELECT id FROM usuarios WHERE empresa_id=? AND lower(usuario)=lower(?)", (empresa_id, usuario))
        if not cur.fetchone():
            cur.execute("""INSERT INTO usuarios
                (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em)
                VALUES (?,?,?,?,?,'Ativo','Código de recuperação',?,?)""",
                (empresa_id, usuario, nome, senha_hash(senha), perfil, senha_hash(senha), agora))
    conn.commit()
    conn.close()


def brl(v):
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def empresas_ativas():
    conn = conectar()
    df = pd.read_sql_query("SELECT id,nome FROM empresas WHERE status='Ativa' ORDER BY nome", conn)
    conn.close()
    return df


def autenticar(empresa, usuario, senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.id,u.usuario,COALESCE(u.nome,u.usuario),u.perfil,e.id,e.nome,u.senha_hash
                   FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?) AND u.status='Ativo' AND e.status='Ativa'""",
                (empresa.strip(), usuario.strip()))
    row = cur.fetchone()
    conn.close()
    if not row or not check_senha(senha, row[6]):
        return None
    return {"user_id": row[0], "usuario": row[1], "nome": row[2], "perfil": row[3], "empresa_id": row[4], "empresa": row[5]}


def criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta):
    empresa, usuario = empresa.strip(), usuario.strip().lower()
    if not empresa or not usuario or not senha:
        return False, "Preencha empresa, usuário e senha."
    if len(senha) < 4:
        return False, "Senha precisa ter pelo menos 4 caracteres."
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (empresa,))
        row = cur.fetchone()
        if row:
            empresa_id, perfil = row[0], "Usuario"
        else:
            cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (empresa, agora))
            empresa_id, perfil = cur.lastrowid, "Admin"
        cur.execute("""INSERT INTO usuarios
            (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em)
            VALUES (?,?,?,?,?,'Ativo',?,?,?)""",
            (empresa_id, usuario, nome.strip() or usuario, senha_hash(senha), perfil,
             pergunta.strip() or "Código de recuperação", senha_hash(resposta.strip().lower()), agora))
        conn.commit()
        return True, f"Conta criada. Perfil: {perfil}."
    except sqlite3.IntegrityError:
        return False, "Usuário já existe nessa empresa."
    finally:
        conn.close()


def pergunta_recuperacao(empresa, usuario):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.pergunta FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""", (empresa.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def resetar_senha(empresa, usuario, resposta, nova):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""SELECT u.id,u.resposta_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
                   WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)""", (empresa.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Usuário não encontrado."
    if senha_hash(resposta.strip().lower()) != row[1]:
        conn.close()
        return False, "Resposta incorreta."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova), row[0]))
    conn.commit()
    conn.close()
    return True, "Senha alterada."


def carregar_lancamentos(empresa_id):
    colunas = ["id","empresa_id","tipo","descricao","categoria","valor","forma_pagamento","status","data_lancamento","data_vencimento","data_pagamento","observacao","criado_por","criado_em","atualizado_em"]
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC", conn, params=(empresa_id,))
    conn.close()
    for c in colunas:
        if c not in df.columns:
            df[c] = pd.Series(dtype="object")
    if df.empty:
        return df[colunas].copy()
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    for c in ["data_lancamento","data_vencimento","data_pagamento"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df[colunas].copy()


def filtrar_mes(df, mes, ano):
    if df is None or df.empty or "data_lancamento" not in df.columns:
        return df.copy() if df is not None else pd.DataFrame()
    d = df.copy()
    d["data_lancamento"] = pd.to_datetime(d["data_lancamento"], errors="coerce")
    return d[(d["data_lancamento"].dt.month == mes) & (d["data_lancamento"].dt.year == ano)].copy()


def salvar_lancamento(auth, dados, lancamento_id=None):
    conn = conectar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if lancamento_id:
        conn.execute("""UPDATE lancamentos SET tipo=?,descricao=?,categoria=?,valor=?,forma_pagamento=?,status=?,data_lancamento=?,data_vencimento=?,data_pagamento=?,observacao=?,atualizado_em=?
                        WHERE id=? AND empresa_id=?""",
                     (dados["tipo"],dados["descricao"],dados["categoria"],float(dados["valor"]),dados["forma_pagamento"],dados["status"],dados["data_lancamento"],dados["data_vencimento"],dados["data_pagamento"],dados["observacao"],agora,lancamento_id,auth["empresa_id"]))
    else:
        conn.execute("""INSERT INTO lancamentos (empresa_id,tipo,descricao,categoria,valor,forma_pagamento,status,data_lancamento,data_vencimento,data_pagamento,observacao,criado_por,criado_em,atualizado_em)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (auth["empresa_id"],dados["tipo"],dados["descricao"],dados["categoria"],float(dados["valor"]),dados["forma_pagamento"],dados["status"],dados["data_lancamento"],dados["data_vencimento"],dados["data_pagamento"],dados["observacao"],auth["usuario"],agora,agora))
    conn.commit()
    conn.close()


def excluir_lancamento(auth, lancamento_id):
    conn = conectar()
    conn.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?", (lancamento_id, auth["empresa_id"]))
    conn.commit()
    conn.close()


def filtro_mes_ano(prefixo):
    hoje = date.today()
    c1, c2 = st.columns(2)
    with c1:
        mes = st.selectbox("Mês", range(1,13), index=hoje.month-1, format_func=lambda x: f"{x:02d}", key=f"mes_{prefixo}")
    with c2:
        ano = st.number_input("Ano", 2020, 2100, hoje.year, key=f"ano_{prefixo}")
    return int(mes), int(ano)


def cards(df):
    if df is None or df.empty:
        receitas = despesas = saldo = 0
        qtd = 0
    else:
        receitas = df[(df["tipo"]=="Receita") & (df["status"]!="Cancelado")]["valor"].sum()
        despesas = df[(df["tipo"]=="Despesa") & (df["status"]!="Cancelado")]["valor"].sum()
        saldo = receitas - despesas
        qtd = len(df)
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">Receitas</div><div class="kpi-value green">{brl(receitas)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Despesas</div><div class="kpi-value red">{brl(despesas)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Saldo do mês</div><div class="kpi-value blue">{brl(saldo)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Lançamentos</div><div class="kpi-value">{qtd}</div></div>
    </div>
    """, unsafe_allow_html=True)


def tela_login():
    st.markdown('<div class="login-hero"><div class="app-logo">📈</div><h1 class="login-title">Casa Marques</h1><div class="login-sub">Controle Financeiro</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Entrar", "Criar conta", "Esqueci senha"])
    with tab1:
        empresas = empresas_ativas()
        with st.form("login"):
            lista = empresas["nome"].tolist()
            empresa = st.selectbox("Empresa", lista, index=lista.index(EMPRESA_PADRAO) if EMPRESA_PADRAO in lista else 0)
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")
        if entrar:
            auth = autenticar(empresa, usuario, senha)
            if auth:
                st.session_state["auth"] = auth
                st.session_state["page"] = "Resumo"
                st.rerun()
            else:
                st.error("Empresa, usuário ou senha inválidos.")
        st.caption("Acesso: Casa Marques | paulo ou mara | 031730")
    with tab2:
        with st.form("cadastro"):
            empresa = st.text_input("Empresa")
            nome = st.text_input("Seu nome")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?")
            resposta = st.text_input("Resposta recuperação", type="password")
            criar = st.form_submit_button("Criar acesso")
        if criar:
            ok, msg = criar_conta_publica(empresa, nome, usuario, senha, pergunta, resposta)
            st.success(msg) if ok else st.error(msg)
    with tab3:
        with st.form("rec"):
            empresa = st.text_input("Empresa", value=EMPRESA_PADRAO)
            usuario = st.text_input("Usuário")
            buscar = st.form_submit_button("Buscar pergunta")
        if buscar:
            p = pergunta_recuperacao(empresa, usuario)
            if p:
                st.session_state["rec"] = {"empresa": empresa, "usuario": usuario, "pergunta": p}
            else:
                st.error("Usuário não encontrado.")
        if "rec" in st.session_state:
            st.info(st.session_state["rec"]["pergunta"])
            with st.form("reset"):
                resposta = st.text_input("Resposta", type="password")
                nova = st.text_input("Nova senha", type="password")
                alterar = st.form_submit_button("Alterar senha")
            if alterar:
                ok, msg = resetar_senha(st.session_state["rec"]["empresa"], st.session_state["rec"]["usuario"], resposta, nova)
                st.success(msg) if ok else st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)


def form_lancamento(default=None, key="novo"):
    default = default or {}
    with st.form(key):
        tipo = st.radio("Tipo", ["Receita","Despesa"], horizontal=True, index=0 if default.get("tipo")=="Receita" else 1)
        cats = CATEGORIAS[tipo]
        data = st.date_input("Data", value=pd.to_datetime(default.get("data_lancamento")).date() if default.get("data_lancamento") is not None and pd.notna(default.get("data_lancamento")) else date.today())
        descricao = st.text_input("Descrição", value=default.get("descricao","") or "")
        cat_default = default.get("categoria", cats[0])
        categoria = st.selectbox("Categoria", cats, index=cats.index(cat_default) if cat_default in cats else 0)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f", value=float(default.get("valor",0) or 0))
        c1, c2 = st.columns(2)
        with c1:
            fp = default.get("forma_pagamento", FORMAS[0])
            forma = st.selectbox("Forma", FORMAS, index=FORMAS.index(fp) if fp in FORMAS else 0)
        with c2:
            stt = default.get("status", "Em aberto")
            status = st.selectbox("Status", STATUS, index=STATUS.index(stt) if stt in STATUS else 0)
        venc = st.date_input("Vencimento", value=pd.to_datetime(default.get("data_vencimento")).date() if default.get("data_vencimento") is not None and pd.notna(default.get("data_vencimento")) else date.today())
        pag = None
        if status == "Pago":
            pag = st.date_input("Data pagamento", value=pd.to_datetime(default.get("data_pagamento")).date() if default.get("data_pagamento") is not None and pd.notna(default.get("data_pagamento")) else date.today())
        obs = st.text_area("Observação", value=default.get("observacao","") or "")
        salvar = st.form_submit_button("Salvar lançamento", type="primary")
    return salvar, {"tipo":tipo,"descricao":descricao.strip(),"categoria":categoria,"valor":valor,"forma_pagamento":forma,"status":status,"data_lancamento":str(data),"data_vencimento":str(venc),"data_pagamento":str(pag) if pag else None,"observacao":obs}


def tx_icon(tipo, categoria):
    if tipo == "Receita":
        return "💼", "#DCFCE7"
    if categoria in ["Alimentação","Mercado"]:
        return "🛒", "#FEE2E2"
    if categoria == "Moradia":
        return "🏠", "#DBEAFE"
    if categoria == "Cartão":
        return "💳", "#EDE9FE"
    return "💸", "#F3F4F6"


def lista_cards(df):
    if df.empty:
        st.info("Nenhum lançamento no mês selecionado.")
        return
    for _, r in df.head(40).iterrows():
        ic, bg = tx_icon(r["tipo"], r["categoria"])
        cor = "green" if r["tipo"]=="Receita" else "red"
        data = r["data_lancamento"].strftime("%d/%m/%Y") if pd.notna(r["data_lancamento"]) else "-"
        st.markdown(f'<div class="tx-card"><div class="tx-icon" style="background:{bg};">{ic}</div><div class="tx-main"><div class="tx-title">{r["descricao"]}</div><div class="tx-sub">{r["categoria"]} · {data} · {r["status"]}</div></div><div class="tx-value {cor}">{brl(r["valor"])}</div></div>', unsafe_allow_html=True)


def selecionar_lancamento(df, label, key):
    if df.empty:
        st.info("Nenhum lançamento no mês.")
        return None
    op = {f'#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {brl(r.valor)}': int(r.id) for r in df.itertuples()}
    escolha = st.selectbox(label, list(op.keys()), key=key)
    return op[escolha]


def admin_page(auth):
    st.markdown('<div class="topbar"><div><div class="top-title">Mais</div><div class="top-sub">Administração e configurações</div></div></div>', unsafe_allow_html=True)
    if st.button("Sair da conta"):
        st.session_state.clear()
        st.rerun()
    if auth["perfil"] != "Admin":
        st.info("Seu perfil não possui acesso administrativo.")
        return
    conn = conectar()
    users = pd.read_sql_query("""SELECT u.id,e.nome empresa,u.usuario,u.nome,u.perfil,u.status FROM usuarios u JOIN empresas e ON e.id=u.empresa_id ORDER BY e.nome,u.usuario""", conn)
    conn.close()
    st.dataframe(users, use_container_width=True, hide_index=True)
    tab1, tab2, tab3 = st.tabs(["Criar usuário","Gerenciar","Criar empresa"])
    with tab1:
        empresas = empresas_ativas()
        with st.form("novo_user"):
            emp = st.selectbox("Empresa", empresas["nome"].tolist())
            nome = st.text_input("Nome")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["Usuario","Admin"])
            pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?")
            resposta = st.text_input("Resposta recuperação", type="password")
            criar = st.form_submit_button("Criar usuário")
        if criar:
            emp_id = int(empresas.loc[empresas["nome"]==emp, "id"].iloc[0])
            try:
                conn = conectar()
                conn.execute("""INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo',?,?,?)""",
                             (emp_id,usuario.strip().lower(),nome.strip() or usuario,senha_hash(senha),perfil,pergunta,senha_hash(resposta.strip().lower()),datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); conn.close()
                st.success("Usuário criado."); st.rerun()
            except sqlite3.IntegrityError:
                st.error("Usuário já existe.")
    with tab2:
        if not users.empty:
            op = {f"{r.empresa} | {r.usuario} | {r.perfil} | {r.status}": int(r.id) for r in users.itertuples()}
            uid = op[st.selectbox("Usuário", list(op.keys()), key="adm_sel")]
            nova = st.text_input("Nova senha", type="password")
            if st.button("Trocar senha"):
                if len(nova) < 4: st.error("Senha curta.")
                else:
                    conn=conectar(); conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova), uid)); conn.commit(); conn.close(); st.success("Senha alterada.")
            status = st.selectbox("Status", ["Ativo","Inativo"])
            if st.button("Atualizar status"):
                conn=conectar(); conn.execute("UPDATE usuarios SET status=? WHERE id=?", (status, uid)); conn.commit(); conn.close(); st.success("Status atualizado."); st.rerun()
            conf = st.checkbox("Confirmo excluir usuário")
            if st.button("Excluir usuário"):
                if not conf: st.warning("Confirme.")
                elif uid == auth["user_id"]: st.error("Não pode excluir o usuário logado.")
                else:
                    conn=conectar(); conn.execute("DELETE FROM usuarios WHERE id=?", (uid,)); conn.commit(); conn.close(); st.success("Usuário excluído."); st.rerun()
    with tab3:
        with st.form("empresa"):
            nome = st.text_input("Nome da empresa")
            criar = st.form_submit_button("Criar empresa")
        if criar and nome.strip():
            try:
                conn=conectar(); conn.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (nome.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close(); st.success("Empresa criada."); st.rerun()
            except sqlite3.IntegrityError:
                st.error("Empresa já existe.")


def app_logado():
    auth = st.session_state["auth"]
    page = st.session_state.get("page", "Resumo")

    menu_opcoes = ["Resumo", "Lançamentos", "Novo", "Relatórios", "Mais"]
    page_selected = st.radio(
        "Menu",
        menu_opcoes,
        horizontal=True,
        index=menu_opcoes.index(page) if page in menu_opcoes else 0,
        key="menu_superior",
        label_visibility="collapsed"
    )
    if page_selected != page:
        st.session_state["page"] = page_selected
        st.rerun()
    page = page_selected
    if page == "Resumo":
        st.markdown(f'<div class="topbar"><div><div class="top-title">Olá, {auth["nome"].split()[0]} 👋</div><div class="top-sub">{auth["empresa"]} - resumo financeiro</div></div><div class="avatar">{auth["nome"][0].upper()}</div></div>', unsafe_allow_html=True)
        mes, ano = filtro_mes_ano("resumo")
        df = carregar_lancamentos(auth["empresa_id"])
        df_mes = filtrar_mes(df, mes, ano)
        cards(df_mes)
        st.markdown('<div class="section-title">Últimos lançamentos</div>', unsafe_allow_html=True)
        lista_cards(df_mes)
    elif page == "Lançamentos":
        st.markdown('<div class="topbar"><div><div class="top-title">Lançamentos</div><div class="top-sub">Consulte seus registros</div></div></div>', unsafe_allow_html=True)
        mes, ano = filtro_mes_ano("lanc")
        df_mes = filtrar_mes(carregar_lancamentos(auth["empresa_id"]), mes, ano)
        lista_cards(df_mes)
        if not df_mes.empty:
            show = df_mes.copy()
            show["valor"] = show["valor"].apply(brl)
            for c in ["data_lancamento","data_vencimento","data_pagamento"]:
                show[c] = show[c].dt.strftime("%d/%m/%Y").fillna("")
            st.dataframe(show[["id","tipo","descricao","categoria","valor","forma_pagamento","status","data_lancamento","data_vencimento","data_pagamento"]], use_container_width=True, hide_index=True)
    elif page == "Novo":
        st.markdown('<div class="topbar"><div><div class="top-title">Novo Lançamento</div><div class="top-sub">Cadastre receita ou despesa</div></div></div>', unsafe_allow_html=True)
        salvar, dados = form_lancamento(key="novo")
        if salvar:
            if not dados["descricao"] or dados["valor"] <= 0: st.warning("Preencha descrição e valor.")
            else:
                salvar_lancamento(auth, dados); st.success("Salvo."); st.session_state["page"]="Resumo"; st.rerun()
    elif page == "Relatórios":
        st.markdown('<div class="topbar"><div><div class="top-title">Relatórios</div><div class="top-sub">Resumo do período</div></div></div>', unsafe_allow_html=True)
        mes, ano = filtro_mes_ano("rel")
        df_mes = filtrar_mes(carregar_lancamentos(auth["empresa_id"]), mes, ano)
        cards(df_mes)
        if not df_mes.empty:
            cat = df_mes.groupby(["tipo","categoria"], as_index=False)["valor"].sum()
            cat["valor"] = cat["valor"].apply(brl)
            st.dataframe(cat, use_container_width=True, hide_index=True)
    elif page == "Mais":
        admin_page(auth)

    with st.expander("Ações rápidas: editar, status ou excluir lançamento"):
        mes, ano = filtro_mes_ano("acoes")
        df = carregar_lancamentos(auth["empresa_id"])
        df_mes = filtrar_mes(df, mes, ano)
        t1,t2,t3 = st.tabs(["Editar","Status","Excluir"])
        with t1:
            lid = selecionar_lancamento(df_mes, "Escolha para editar", "sel_edit")
            if lid:
                row = df[df["id"]==lid].iloc[0].to_dict()
                salvar,dados = form_lancamento(row, "edit")
                if salvar:
                    salvar_lancamento(auth, dados, lid); st.success("Alterado."); st.rerun()
        with t2:
            lid = selecionar_lancamento(df_mes, "Escolha para status", "sel_status")
            if lid:
                novo = st.selectbox("Novo status", STATUS, key="novo_status")
                pag = st.date_input("Data pagamento", value=date.today(), key="pag_status") if novo=="Pago" else None
                if st.button("Atualizar status"):
                    conn=conectar(); conn.execute("UPDATE lancamentos SET status=?,data_pagamento=?,atualizado_em=? WHERE id=? AND empresa_id=?", (novo, str(pag) if pag else None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lid, auth["empresa_id"])); conn.commit(); conn.close(); st.success("Status atualizado."); st.rerun()
        with t3:
            lid = selecionar_lancamento(df_mes, "Escolha para excluir", "sel_del")
            if lid:
                conf = st.checkbox("Confirmo exclusão definitiva")
                if st.button("Excluir lançamento"):
                    if conf: excluir_lancamento(auth, lid); st.success("Excluído."); st.rerun()
                    else: st.warning("Confirme.")

    st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
    nav_items = [
        ("Resumo", "🏠", "Resumo"),
        ("Lançamentos", "📋", "Lanç."),
        ("Novo", "➕", "Novo"),
        ("Relatórios", "📊", "Relat."),
        ("Mais", "⚙️", "Mais"),
    ]
    cols = st.columns(5)
    for col, (page_name, icon, label) in zip(cols, nav_items):
        with col:
            if st.button(icon, key=f"nav_{page_name}", help=page_name):
                st.session_state["page"] = page_name
                st.rerun()
            active_class = "nav-label nav-label-active" if page == page_name else "nav-label"
            st.markdown(f'<div class="{active_class}">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    init_db()
    if "auth" not in st.session_state:
        tela_login()
    else:
        app_logado()


if __name__ == "__main__":
    main()
