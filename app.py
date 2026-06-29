
import os
import sqlite3
import hashlib
import hmac
from datetime import date, datetime
import pandas as pd
import streamlit as st

EMPRESA_PADRAO = "Casa Marques"
DB_PATH = os.path.join(os.path.dirname(__file__), "dados", "financeiro.db")
USUARIOS_INICIAIS = [
    ("paulo", "Paulo", "031730", "Admin"),
    ("mara", "Mara", "031730", "Usuario"),
]
CATEGORIAS = {
    "Receita": ["Salário", "Venda de produtos", "Serviço prestado", "Freelance", "Transferência", "Investimento", "Reembolso", "Outros"],
    "Despesa": ["Supermercado", "Compra de mercadorias", "Conta de Luz", "Alimentação", "Casa", "Internet", "Transporte", "Combustível", "Saúde", "Cartão", "Empréstimo", "Lazer", "Outros"],
}
FORMAS = ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito", "Boleto", "Transferência", "Outro"]
STATUS = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(page_title="Casa Marques Financeiro", page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {background:#eef3fb;}
.main .block-container {padding:0 0 116px 0; max-width:520px;}
[data-testid="stSidebar"], #MainMenu, footer, header {display:none; visibility:hidden;}

.app-shell{background:#f6f8ff;min-height:100vh;border-radius:0;overflow:hidden;}
.hero{
    background:
      radial-gradient(circle at 86% 20%, rgba(124,58,237,.38) 0, rgba(124,58,237,0) 26%),
      radial-gradient(circle at 40% 10%, rgba(37,99,235,.35) 0, rgba(37,99,235,0) 28%),
      linear-gradient(145deg,#06091f 0%,#0b1034 58%,#130a3d 100%);
    color:white;padding:34px 22px 86px;border-radius:0 0 36px 36px;position:relative;
}
.hero-row{display:flex;align-items:center;gap:18px;}
.avatar-big{width:66px;height:66px;border-radius:50%;background:linear-gradient(145deg,#7c3aed,#5b42ff);display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:950;box-shadow:0 18px 36px rgba(91,66,255,.45);}
.hero-title{font-size:28px;font-weight:950;letter-spacing:-.04em;line-height:1.0;}
.hero-sub{font-size:14px;color:#cbd5e1;font-weight:700;margin-top:8px;}
.hero-actions{margin-left:auto;display:flex;gap:14px;font-size:30px;align-items:center;}
.content{padding:0 18px;margin-top:-64px;position:relative;z-index:2;}
.kpi-scroll{display:grid;grid-template-columns:repeat(4, minmax(155px,1fr));gap:10px;overflow-x:auto;padding-bottom:4px;}
.kpi{background:rgba(255,255,255,.92);backdrop-filter:blur(12px);border:1px solid rgba(226,232,240,.9);border-radius:26px;padding:17px;min-height:142px;box-shadow:0 16px 34px rgba(15,23,42,.12);}
.kpi-icon{width:46px;height:46px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:14px;color:white;box-shadow:inset 0 2px 8px rgba(255,255,255,.35),0 10px 18px rgba(15,23,42,.15);}
.kpi-label{font-size:12px;font-weight:900;color:#26324a;margin-bottom:8px;}
.kpi-value{font-size:19px;font-weight:950;letter-spacing:-.04em;}
.kpi-foot{height:5px;border-radius:999px;background:#e2e8f0;margin-top:18px;overflow:hidden;}
.kpi-bar{height:100%;border-radius:999px;width:42%;}
.green{color:#05A839}.red{color:#E11928}.blue{color:#1D4ED8}.purple{color:#6D28D9}
.bg-green{background:linear-gradient(145deg,#22C55E,#049A39)}.bg-red{background:linear-gradient(145deg,#FF4D5E,#D51020)}.bg-blue{background:linear-gradient(145deg,#3B82F6,#1D4ED8)}.bg-purple{background:linear-gradient(145deg,#7C3AED,#4F46E5)}

.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0;}
.quick-card{height:158px;border-radius:30px;color:white;padding:24px 20px;position:relative;overflow:hidden;box-shadow:0 20px 40px rgba(15,23,42,.22), inset 0 3px 12px rgba(255,255,255,.25);border:1px solid rgba(255,255,255,.26);}
.quick-card:before{content:"";position:absolute;right:-28px;top:-35px;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.18);}
.quick-icon{width:64px;height:64px;border-radius:22px;background:rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center;font-size:42px;box-shadow:inset 0 2px 10px rgba(255,255,255,.28),0 14px 24px rgba(0,0,0,.2);margin-bottom:24px;}
.quick-title{font-size:25px;font-weight:950;letter-spacing:-.04em;}
.quick-sub{font-size:14px;font-weight:800;opacity:.95;margin-top:4px;}
.quick-arrow{position:absolute;right:18px;bottom:18px;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.20);font-size:28px;font-weight:950;}
.q-green{background:linear-gradient(145deg,#22d367,#008c35)}.q-red{background:linear-gradient(145deg,#ff4158,#d80a22)}.q-blue{background:linear-gradient(145deg,#3b82f6,#0f55cf)}.q-purple{background:linear-gradient(145deg,#8b5cf6,#4c1d95)}
.hidden-btn button{margin-top:-8px;margin-bottom:8px;border-radius:18px!important;background:#fff!important;color:#111827!important;min-height:44px!important;font-weight:900!important;border:1px solid #e5e7eb!important;box-shadow:0 10px 20px rgba(15,23,42,.08)!important;}

.panel{background:white;border-radius:24px;border:1px solid #e8edf5;box-shadow:0 16px 32px rgba(15,23,42,.08);overflow:hidden;margin:18px 0;}
.panel-head{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid #eef2f7;font-size:16px;font-weight:950;color:#111827;}
.panel-link{color:#6d28d9;font-size:13px;font-weight:900;}
.tx{display:flex;align-items:center;gap:13px;padding:14px 18px;border-bottom:1px solid #f1f5f9;}
.tx:last-child{border-bottom:none;}
.tx-ico{width:46px;height:46px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:24px;}
.tx-main{flex:1}.tx-title{font-size:14px;font-weight:950;color:#10172a}.tx-sub{font-size:12px;color:#64748b;font-weight:700;margin-top:3px}
.tx-val{text-align:right;font-weight:950;font-size:14px}.tx-date{font-size:12px;color:#64748b;font-weight:700;margin-top:2px}
.section-title{font-size:22px;font-weight:950;letter-spacing:-.04em;color:#111827;margin:18px 0 12px;}

.bottom-nav{position:fixed;left:50%;bottom:10px;transform:translateX(-50%);width:calc(100% - 18px);max-width:520px;background:#080b22;border:1px solid rgba(255,255,255,.12);border-radius:30px;padding:10px 8px;box-shadow:0 22px 46px rgba(15,23,42,.35);z-index:9999;}
.nav-cols{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;}
.nav-cell{text-align:center;color:#cbd5e1;font-size:11px;font-weight:900;}
.nav-icon{font-size:24px;line-height:1.1;margin-bottom:3px;}
.nav-active{background:linear-gradient(145deg,#7c3aed,#4f46e5);border-radius:24px;color:#fff;padding:8px 2px;margin-top:-2px;box-shadow:0 14px 24px rgba(91,66,255,.4);}
.nav-plus{width:56px;height:56px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#7c3aed,#5b42ff);color:white;font-size:36px;margin-top:-26px;box-shadow:0 16px 28px rgba(91,66,255,.45);}

/* BOTÕES FUNCIONAIS - sem camada invisível por cima */
.quick-actions .stButton>button{
    min-height:154px!important;
    border-radius:30px!important;
    color:#ffffff!important;
    font-size:20px!important;
    line-height:1.25!important;
    white-space:pre-line!important;
    font-weight:950!important;
    border:1px solid rgba(255,255,255,.35)!important;
    box-shadow:0 20px 40px rgba(15,23,42,.18), inset 0 3px 12px rgba(255,255,255,.25)!important;
}
.quick-actions .stButton>button[kind="secondary"]:hover{transform:translateY(-1px);filter:brightness(1.02);} 
.quick-actions div[data-testid="column"]:nth-child(1) .stButton>button{background:linear-gradient(145deg,#22d367,#008c35)!important;}
.quick-actions div[data-testid="column"]:nth-child(2) .stButton>button{background:linear-gradient(145deg,#ff4158,#d80a22)!important;}
.quick-actions-2 div[data-testid="column"]:nth-child(1) .stButton>button{background:linear-gradient(145deg,#3b82f6,#0f55cf)!important;}
.quick-actions-2 div[data-testid="column"]:nth-child(2) .stButton>button{background:linear-gradient(145deg,#8b5cf6,#4c1d95)!important;}
.bottom-nav .stButton>button{
    min-height:58px!important;
    border-radius:22px!important;
    background:transparent!important;
    color:#cbd5e1!important;
    border:0!important;
    box-shadow:none!important;
    white-space:pre-line!important;
    font-size:13px!important;
    line-height:1.15!important;
    font-weight:900!important;
}
.bottom-nav .stButton>button:hover{background:rgba(124,58,237,.22)!important;color:#fff!important;}
.bottom-nav .nav-new .stButton>button{
    min-height:64px!important;
    border-radius:26px!important;
    background:linear-gradient(145deg,#7c3aed,#5b42ff)!important;
    color:#fff!important;
    font-size:15px!important;
    box-shadow:0 14px 24px rgba(91,66,255,.42)!important;
}


.login-wrap{min-height:92vh;padding:30px 22px;border-radius:0 0 34px 34px;background:radial-gradient(circle at 30% 0%,#5742ff 0%,#1B124D 42%,#060B1B 100%);color:white;}
.logo{width:92px;height:92px;border-radius:28px;background:linear-gradient(145deg,#6D5CFF,#1DD3FF);display:flex;align-items:center;justify-content:center;font-size:48px;margin:32px auto 16px;box-shadow:0 22px 48px rgba(99,91,255,.42);}
.stButton>button{width:100%;border-radius:18px;min-height:50px;font-weight:900;border:1px solid #E6E9F2;background:#fff;color:#17203A;box-shadow:0 8px 18px rgba(15,23,42,.05);}
div[data-baseweb="select"]>div,.stTextInput input,.stNumberInput input,.stDateInput input,textarea{border-radius:17px!important;font-size:16px!important;border-color:#E1E6F0!important;}
.form-card{background:white;border-radius:24px;border:1px solid #e8edf5;box-shadow:0 16px 32px rgba(15,23,42,.08);padding:18px;margin:14px 0;}
.type-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:10px;}
.type-card{border-radius:24px;padding:22px;text-align:center;font-size:18px;font-weight:950;}
.type-rec{background:#e8fbef;color:#078a2d}.type-desp{background:#fff0f1;color:#d51020}
.user-row{display:flex;align-items:center;gap:12px;background:white;border:1px solid #e8edf5;border-radius:20px;padding:14px;margin-bottom:10px;}
.user-ball{width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:950;background:linear-gradient(145deg,#22c55e,#16a34a);}
@media(max-width:420px){.quick-card{height:145px}.quick-title{font-size:22px}.kpi-scroll{grid-template-columns:repeat(4, minmax(145px,1fr));}.hero{padding-bottom:80px}}
</style>
""", unsafe_allow_html=True)

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def senha_hash(s):
    return hashlib.pbkdf2_hmac("sha256", str(s).encode(), b"casa_marques_visual_final", 140000).hex()

def senha_ok(s, h):
    return hmac.compare_digest(senha_hash(s), h or "")

def init_db():
    con = db(); cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, status TEXT, criado_em TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, usuario TEXT, nome TEXT, senha_hash TEXT, perfil TEXT, status TEXT, pergunta TEXT, resposta_hash TEXT, criado_em TEXT, UNIQUE(empresa_id, usuario))")
    cur.execute("CREATE TABLE IF NOT EXISTS lancamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL, forma_pagamento TEXT, status TEXT, data_lancamento TEXT, data_vencimento TEXT, data_pagamento TEXT, observacao TEXT, criado_por TEXT, criado_em TEXT, atualizado_em TEXT)")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (EMPRESA_PADRAO,))
    row = cur.fetchone()
    if row: emp_id = row[0]
    else:
        cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (EMPRESA_PADRAO, agora))
        emp_id = cur.lastrowid
    for usuario,nome,senha,perfil in USUARIOS_INICIAIS:
        cur.execute("SELECT id FROM usuarios WHERE empresa_id=? AND lower(usuario)=lower(?)", (emp_id, usuario))
        rowu = cur.fetchone()
        if rowu:
            cur.execute("UPDATE usuarios SET nome=?, senha_hash=?, perfil=?, status='Ativo', pergunta='Código de recuperação', resposta_hash=? WHERE id=?", (nome, senha_hash(senha), perfil, senha_hash(senha), rowu[0]))
        else:
            cur.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo','Código de recuperação',?,?)", (emp_id,usuario,nome,senha_hash(senha),perfil,senha_hash(senha),agora))
    con.commit(); con.close()

def brl(v):
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def empresas():
    con=db(); df=pd.read_sql_query("SELECT id,nome FROM empresas WHERE status='Ativa' ORDER BY nome", con); con.close(); return df

def autenticar(empresa, usuario, senha):
    con=db(); cur=con.cursor()
    cur.execute("SELECT u.id,u.usuario,u.nome,u.perfil,e.id,e.nome,u.senha_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?) AND u.status='Ativo' AND e.status='Ativa'", (empresa.strip(),usuario.strip()))
    row=cur.fetchone(); con.close()
    if not row or not senha_ok(senha,row[6]): return None
    return {"user_id":row[0],"usuario":row[1],"nome":row[2],"perfil":row[3],"empresa_id":row[4],"empresa":row[5]}

def carregar(emp_id):
    cols=["id","empresa_id","tipo","descricao","categoria","valor","forma_pagamento","status","data_lancamento","data_vencimento","data_pagamento","observacao","criado_por","criado_em","atualizado_em"]
    con=db(); df=pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC",con,params=(emp_id,)); con.close()
    for c in cols:
        if c not in df.columns: df[c]=pd.Series(dtype="object")
    if df.empty: return df[cols].copy()
    df["valor"]=pd.to_numeric(df["valor"],errors="coerce").fillna(0)
    for c in ["data_lancamento","data_vencimento","data_pagamento"]: df[c]=pd.to_datetime(df[c],errors="coerce")
    return df[cols].copy()

def filtrar(df,mes,ano):
    if df.empty: return df.copy()
    return df[(df["data_lancamento"].dt.month==mes)&(df["data_lancamento"].dt.year==ano)].copy()

def salvar(auth,d,lanc_id=None):
    con=db(); agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if lanc_id:
        con.execute("UPDATE lancamentos SET tipo=?,descricao=?,categoria=?,valor=?,forma_pagamento=?,status=?,data_lancamento=?,data_vencimento=?,data_pagamento=?,observacao=?,atualizado_em=? WHERE id=? AND empresa_id=?",(d["tipo"],d["descricao"],d["categoria"],float(d["valor"]),d["forma_pagamento"],d["status"],d["data_lancamento"],d["data_vencimento"],d["data_pagamento"],d["observacao"],agora,lanc_id,auth["empresa_id"]))
    else:
        con.execute("INSERT INTO lancamentos (empresa_id,tipo,descricao,categoria,valor,forma_pagamento,status,data_lancamento,data_vencimento,data_pagamento,observacao,criado_por,criado_em,atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(auth["empresa_id"],d["tipo"],d["descricao"],d["categoria"],float(d["valor"]),d["forma_pagamento"],d["status"],d["data_lancamento"],d["data_vencimento"],d["data_pagamento"],d["observacao"],auth["usuario"],agora,agora))
    con.commit(); con.close()

def excluir(auth,lanc_id):
    con=db(); con.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?",(lanc_id,auth["empresa_id"])); con.commit(); con.close()

def login():
    st.markdown('<div class="login-wrap"><div class="logo">📈</div><h1 style="text-align:center;font-size:31px;font-weight:900;margin:0;">Casa Marques</h1><div style="text-align:center;color:#CBD5E1;margin:8px 0 26px;font-weight:600;">Controle Financeiro</div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["Entrar","Criar conta"])
    with t1:
        emp=empresas(); lista=emp["nome"].tolist()
        with st.form("login"):
            empresa=st.selectbox("Empresa",lista,index=lista.index(EMPRESA_PADRAO) if EMPRESA_PADRAO in lista else 0)
            usuario=st.text_input("Usuário"); senha=st.text_input("Senha",type="password"); entrar=st.form_submit_button("Entrar")
        if entrar:
            auth=autenticar(empresa,usuario,senha)
            if auth: st.session_state["auth"]=auth; st.session_state["page"]="Resumo"; st.rerun()
            else: st.error("Empresa, usuário ou senha inválidos.")
        st.caption("Casa Marques | paulo ou mara | 031730")
    with t2:
        st.info("Cadastro público mantido desativado nessa versão visual. O Admin pode criar usuários em Mais.")
    st.markdown("</div>", unsafe_allow_html=True)

def filtro_mes(key):
    hoje=date.today(); c1,c2=st.columns([1.1,1])
    with c1: mes=st.selectbox("Mês",range(1,13),index=hoje.month-1,format_func=lambda x:f"{x:02d}",key=f"mes_{key}")
    with c2: ano=st.number_input("Ano",2020,2100,hoje.year,key=f"ano_{key}")
    return int(mes),int(ano)

def resumo_vals(df):
    rec=df[(df["tipo"]=="Receita")&(df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    desp=df[(df["tipo"]=="Despesa")&(df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    return rec, desp, rec-desp, len(df)

def kpis(df):
    rec,desp,saldo,qtd=resumo_vals(df)
    html=f"""
    <div class="kpi-scroll">
      <div class="kpi"><div class="kpi-icon bg-green">⬆</div><div class="kpi-label">Receitas do mês</div><div class="kpi-value green">{brl(rec)}</div><div class="kpi-foot"><div class="kpi-bar bg-green"></div></div></div>
      <div class="kpi"><div class="kpi-icon bg-red">⬇</div><div class="kpi-label">Despesas do mês</div><div class="kpi-value red">{brl(desp)}</div><div class="kpi-foot"><div class="kpi-bar bg-red"></div></div></div>
      <div class="kpi"><div class="kpi-icon bg-blue">💼</div><div class="kpi-label">Saldo do mês</div><div class="kpi-value blue">{brl(saldo)}</div><div class="kpi-foot"><div class="kpi-bar bg-blue"></div></div></div>
      <div class="kpi"><div class="kpi-icon bg-purple">📊</div><div class="kpi-label">Lançamentos</div><div class="kpi-value purple">{qtd}</div><div class="kpi-foot"><div class="kpi-bar bg-purple"></div></div></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def quick_buttons():
    # Botões reais do Streamlit: a área visual é a mesma área clicável.
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        if st.button("⬆\nRECEITAS\nCadastrar entrada", key="q_receita", use_container_width=True):
            st.session_state["page"] = "Novo"
            st.session_state["tipo_rapido"] = "Receita"
            st.rerun()
    with c2:
        if st.button("⬇\nDESPESAS\nCadastrar saída", key="q_despesa", use_container_width=True):
            st.session_state["page"] = "Novo"
            st.session_state["tipo_rapido"] = "Despesa"
            st.rerun()
    st.markdown('</div><div style="height:14px"></div><div class="quick-actions quick-actions-2">', unsafe_allow_html=True)
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        if st.button("📊\nRELATÓRIOS\nAnálise e gráficos", key="q_rel", use_container_width=True):
            st.session_state["page"] = "Relatórios"
            st.rerun()
    with c4:
        if st.button("⚙\nADMIN\nConfigurações", key="q_admin", use_container_width=True):
            st.session_state["page"] = "Mais"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def tx_icon(tipo,categoria):
    if tipo=="Receita": return "⬆","#dcfce7"
    return "⬇","#fee2e2"

def lista(df):
    st.markdown('<div class="panel"><div class="panel-head"><span>Lançamentos recentes</span><span class="panel-link">Ver todos</span></div>', unsafe_allow_html=True)
    if df.empty:
        st.markdown('<div style="padding:18px;color:#64748b;font-weight:700;">Nenhum lançamento no mês selecionado.</div>', unsafe_allow_html=True)
    else:
        for _,r in df.head(6).iterrows():
            ic,bg=tx_icon(r["tipo"],r["categoria"]); cor="green" if r["tipo"]=="Receita" else "red"
            data=r["data_lancamento"].strftime("%d/%m/%Y") if pd.notna(r["data_lancamento"]) else "-"
            st.markdown(f'<div class="tx"><div class="tx-ico" style="background:{bg};">{ic}</div><div class="tx-main"><div class="tx-title">{r["descricao"]}</div><div class="tx-sub">{r["tipo"]}</div></div><div><div class="tx-val {cor}">{brl(r["valor"])}</div><div class="tx-date">{data}</div></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def form_lanc(default=None,key="novo"):
    default=default or {}
    tipo_pre=st.session_state.pop("tipo_rapido", None) if key=="novo" else None
    tipo_padrao=tipo_pre or default.get("tipo")
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    with st.form(key):
        st.markdown('<div class="type-row"><div class="type-card type-rec">⬆<br>Receita</div><div class="type-card type-desp">⬇<br>Despesa</div></div>', unsafe_allow_html=True)
        tipo=st.radio("Tipo",["Receita","Despesa"],horizontal=True,index=0 if tipo_padrao=="Receita" else 1)
        cats=CATEGORIAS[tipo]
        data=st.date_input("Data",value=pd.to_datetime(default.get("data_lancamento")).date() if default.get("data_lancamento") is not None and pd.notna(default.get("data_lancamento")) else date.today())
        descricao=st.text_input("Descrição",value=default.get("descricao","") or "")
        categoria=st.selectbox("Categoria",cats,index=0)
        valor=st.number_input("Valor (R$)",min_value=0.0,step=1.0,format="%.2f",value=float(default.get("valor",0) or 0))
        forma=st.selectbox("Forma de pagamento",FORMAS,index=0)
        status=st.selectbox("Status",STATUS,index=0)
        venc=st.date_input("Vencimento",value=date.today())
        pag=st.date_input("Data pagamento",value=date.today()) if status=="Pago" else None
        obs=st.text_area("Observação")
        ok=st.form_submit_button("Salvar Lançamento",type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
    return ok,{"tipo":tipo,"descricao":descricao,"categoria":categoria,"valor":valor,"forma_pagamento":forma,"status":status,"data_lancamento":str(data),"data_vencimento":str(venc),"data_pagamento":str(pag) if pag else None,"observacao":obs}

def admin(auth):
    st.markdown('<div class="section-title">Administração</div>', unsafe_allow_html=True)
    if st.button("Sair"): st.session_state.clear(); st.rerun()
    if auth["perfil"]!="Admin": st.info("Sem permissão administrativa."); return
    con=db(); users=pd.read_sql_query("SELECT id,usuario,nome,perfil,status FROM usuarios WHERE empresa_id=? ORDER BY usuario",con,params=(auth["empresa_id"],)); con.close()
    for _,u in users.iterrows():
        st.markdown(f'<div class="user-row"><div class="user-ball">{u["usuario"][0].upper()}</div><div style="flex:1"><b>{u["nome"]}</b><br><span style="font-size:12px;color:#64748b;font-weight:700;">{u["perfil"]}</span></div><span>{u["status"]}</span></div>', unsafe_allow_html=True)
    with st.expander("Criar usuário"):
        with st.form("u"):
            nome=st.text_input("Nome"); usuario=st.text_input("Usuário"); senha=st.text_input("Senha",type="password"); perfil=st.selectbox("Perfil",["Usuario","Admin"]); criar=st.form_submit_button("Criar")
        if criar:
            try:
                con=db(); con.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo','Código de recuperação',?,?)",(auth["empresa_id"],usuario.lower(),nome,senha_hash(senha),perfil,senha_hash(senha),datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); con.commit(); con.close(); st.success("Criado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Usuário já existe.")

def nav(page):
    # Navegação inferior funcional: sem botão invisível e sem HTML sobreposto.
    items = [
        ("Resumo", "🏠\nResumo"),
        ("Lançamentos", "📋\nLanç."),
        ("Novo", "+\nNovo"),
        ("Relatórios", "📊\nRelat."),
        ("Mais", "☰\nMais"),
    ]
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    cols = st.columns(5, gap="small")
    for col, (p, label) in zip(cols, items):
        with col:
            if p == "Novo":
                st.markdown('<div class="nav-new">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{p}", use_container_width=True):
                st.session_state["page"] = p
                st.rerun()
            if p == "Novo":
                st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def app():
    auth=st.session_state["auth"]; page=st.session_state.get("page","Resumo")
    if page=="Resumo":
        st.markdown('<div class="app-shell">', unsafe_allow_html=True)
        st.markdown(f'<div class="hero"><div class="hero-row"><div class="avatar-big">{auth["nome"][0].upper()}</div><div><div class="hero-title">Olá, {auth["nome"].split()[0]} 👋</div><div class="hero-sub">{auth["empresa"]} • Resumo financeiro</div></div><div class="hero-actions">🔔 ⎋</div></div></div><div class="content">', unsafe_allow_html=True)
        mes,ano=filtro_mes("resumo"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano)
        kpis(dfm); quick_buttons(); lista(dfm)
        st.markdown('</div></div>', unsafe_allow_html=True)
    elif page=="Lançamentos":
        st.markdown('<div class="content" style="margin-top:0;padding-top:18px;"><div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
        mes,ano=filtro_mes("lanc"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano); busca=st.text_input("Buscar lançamento...")
        if busca and not dfm.empty: dfm=dfm[dfm["descricao"].str.contains(busca,case=False,na=False)]
        lista(dfm); st.markdown('</div>', unsafe_allow_html=True)
    elif page=="Novo":
        st.markdown('<div class="content" style="margin-top:0;padding-top:18px;"><div class="section-title">Novo Lançamento</div>', unsafe_allow_html=True)
        ok,d=form_lanc(key="novo")
        if ok:
            if not d["descricao"] or d["valor"]<=0: st.warning("Preencha descrição e valor.")
            else: salvar(auth,d); st.success("Salvo."); st.session_state["page"]="Resumo"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    elif page=="Relatórios":
        st.markdown('<div class="content" style="margin-top:0;padding-top:18px;"><div class="section-title">Relatórios</div>', unsafe_allow_html=True)
        mes,ano=filtro_mes("rel"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano); kpis(dfm)
        if not dfm.empty:
            cat=dfm.groupby(["tipo","categoria"],as_index=False)["valor"].sum(); cat["valor"]=cat["valor"].apply(brl); st.dataframe(cat,use_container_width=True,hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="content" style="margin-top:0;padding-top:18px;">', unsafe_allow_html=True); admin(auth); st.markdown('</div>', unsafe_allow_html=True)
    nav(page)

def main():
    init_db()
    if "auth" not in st.session_state: login()
    else: app()

if __name__=="__main__":
    main()
