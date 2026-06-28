import os, sqlite3, hashlib, hmac
from datetime import date, datetime
import pandas as pd
import streamlit as st

EMPRESA = "Casa Marques"
DB_PATH = os.path.join(os.path.dirname(__file__), "dados", "financeiro.db")
USUARIOS = [("paulo","Paulo","031730","Admin"), ("mara","Mara","031730","Usuario")]
CATEGORIAS = {
    "Receita": ["Salário","Venda","Serviço","Freelance","Transferência","Investimento","Reembolso","Outros"],
    "Despesa": ["Supermercado","Alimentação","Casa","Conta de Luz","Água","Internet","Transporte","Combustível","Saúde","Cartão","Empréstimo","Lazer","Outros"],
}
FORMAS = ["Pix","Dinheiro","Cartão Crédito","Cartão Débito","Boleto","Transferência","Outro"]
STATUS = ["Em aberto","Pago","Cancelado"]

st.set_page_config(page_title="Casa Marques Financeiro", page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown('''
<style>
html, body, [data-testid="stAppViewContainer"]{background:#F8FAFF;}
.main .block-container{padding-top:.6rem;padding-bottom:6.2rem;max-width:470px;}
[data-testid="stSidebar"],#MainMenu,footer,header{display:none;visibility:hidden;}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.top-title{font-size:25px;font-weight:900;color:#10172A;letter-spacing:-.04em;}
.top-sub{font-size:13px;color:#64748B;margin-top:4px;font-weight:600;}
.avatar{width:50px;height:50px;border-radius:50%;background:linear-gradient(145deg,#5B42FF,#8257FF);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;box-shadow:0 12px 25px rgba(91,66,255,.28);}
.login-wrap{min-height:92vh;padding:30px 22px;border-radius:0 0 34px 34px;background:radial-gradient(circle at 30% 0%,#5742ff 0%,#1B124D 42%,#060B1B 100%);color:white;}
.logo{width:92px;height:92px;border-radius:28px;background:linear-gradient(145deg,#6D5CFF,#1DD3FF);display:flex;align-items:center;justify-content:center;font-size:48px;margin:32px auto 16px;box-shadow:0 22px 48px rgba(99,91,255,.42);}
.login-title{text-align:center;font-size:31px;font-weight:900;margin:0;letter-spacing:-.03em;}
.login-sub{text-align:center;color:#CBD5E1;margin:8px 0 26px;font-weight:600;}
.card-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 16px;}
.big-card{min-height:142px;border-radius:24px;padding:18px;border:1px solid rgba(226,232,240,.9);box-shadow:0 14px 32px rgba(15,23,42,.08);position:relative;overflow:hidden;}
.card-green{background:linear-gradient(145deg,#E9FFF1,#FFFFFF);}.card-red{background:linear-gradient(145deg,#FFF0F1,#FFFFFF);}.card-blue{background:linear-gradient(145deg,#EEF2FF,#FFFFFF);}.card-soft{background:linear-gradient(145deg,#F4F7FF,#FFFFFF);}
.icon-round{width:50px;height:50px;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:26px;margin-bottom:14px;}
.icon-green{background:#CFFAD9}.icon-red{background:#FFE0E2}.icon-blue{background:#DDD8FF}.icon-soft{background:#E8EEFF}
.card-label{font-size:13px;font-weight:850;color:#26324A;margin-bottom:8px;}.card-value{font-size:22px;font-weight:950;letter-spacing:-.03em;}
.green{color:#05A839}.red{color:#E11928}.blue{color:#183CE7}.purple{color:#5B42FF}
.arrow-dot{position:absolute;right:17px;bottom:17px;width:34px;height:34px;border-radius:50%;background:white;display:flex;align-items:center;justify-content:center;font-weight:900;box-shadow:0 8px 18px rgba(15,23,42,.12);}
.section{font-size:17px;font-weight:900;color:#10172A;margin:16px 0 10px;}
.tx{display:flex;align-items:center;gap:13px;background:#fff;border-radius:20px;padding:14px;margin-bottom:10px;border:1px solid #EEF1F6;box-shadow:0 8px 18px rgba(15,23,42,.045);}
.tx-ico{width:46px;height:46px;border-radius:17px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;}.tx-title{font-weight:900;color:#111827;font-size:14px;}.tx-sub{font-size:12px;color:#64748B;margin-top:3px;font-weight:600;}.tx-val{font-weight:950;text-align:right;font-size:14px;}
.badge{display:inline-block;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:850;margin-top:4px;}.badge-green{background:#DCFCE7;color:#138A36}.badge-red{background:#FFE3E5;color:#E11928}.badge-amber{background:#FEF3C7;color:#A16207}
.stButton>button{width:100%;border-radius:18px;min-height:50px;font-weight:900;border:1px solid #E6E9F2;background:#fff;color:#17203A;box-shadow:0 8px 18px rgba(15,23,42,.05);}
.stButton>button:hover{background:#F0EDFF;border-color:#6D5CFF;color:#5B42FF;}
div[data-baseweb="select"]>div,.stTextInput input,.stNumberInput input,.stDateInput input,textarea{border-radius:17px!important;font-size:16px!important;border-color:#E1E6F0!important;}
.receita-btn{background:#E8FBEF;border:1px solid #C7F3D5;border-radius:22px;padding:20px;text-align:center;font-size:18px;font-weight:950;color:#078A2D;}.despesa-btn{background:#FFF0F1;border:1px solid #FFD5D9;border-radius:22px;padding:20px;text-align:center;font-size:18px;font-weight:950;color:#D51020;}
.small-muted{font-size:12px;color:#64748B;font-weight:600;}.user-row{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #EEF1F6;border-radius:20px;padding:14px;margin-bottom:10px;}.user-ball{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:900;background:linear-gradient(145deg,#22C55E,#16A34A);}
.bottom-spacer{height:74px;}
@media(min-width:800px){.main .block-container{max-width:560px;}}
</style>
''', unsafe_allow_html=True)

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def senha_hash(s):
    return hashlib.pbkdf2_hmac("sha256", str(s).encode(), b"casa_marques_final", 140000).hex()

def senha_ok(s, h):
    return hmac.compare_digest(senha_hash(s), h or "")

def init_db():
    con=db(); cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, status TEXT, criado_em TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, usuario TEXT, nome TEXT, senha_hash TEXT, perfil TEXT, status TEXT, pergunta TEXT, resposta_hash TEXT, criado_em TEXT, UNIQUE(empresa_id, usuario))")
    cur.execute("CREATE TABLE IF NOT EXISTS lancamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL, forma_pagamento TEXT, status TEXT, data_lancamento TEXT, data_vencimento TEXT, data_pagamento TEXT, observacao TEXT, criado_por TEXT, criado_em TEXT, atualizado_em TEXT)")
    agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (EMPRESA,)); row=cur.fetchone()
    if row: emp_id=row[0]
    else:
        cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (EMPRESA,agora)); emp_id=cur.lastrowid
    for usuario,nome,senha,perfil in USUARIOS:
        cur.execute("SELECT id FROM usuarios WHERE empresa_id=? AND lower(usuario)=lower(?)", (emp_id,usuario))
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo','Código de recuperação',?,?)", (emp_id,usuario,nome,senha_hash(senha),perfil,senha_hash(senha),agora))
    con.commit(); con.close()

def brl(v): return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def empresas():
    con=db(); df=pd.read_sql_query("SELECT id,nome FROM empresas WHERE status='Ativa' ORDER BY nome", con); con.close(); return df

def autenticar(empresa,usuario,senha):
    con=db(); cur=con.cursor()
    cur.execute("SELECT u.id,u.usuario,u.nome,u.perfil,e.id,e.nome,u.senha_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?) AND u.status='Ativo' AND e.status='Ativa'", (empresa.strip(),usuario.strip()))
    row=cur.fetchone(); con.close()
    if not row or not senha_ok(senha,row[6]): return None
    return {"user_id":row[0],"usuario":row[1],"nome":row[2],"perfil":row[3],"empresa_id":row[4],"empresa":row[5]}

def criar_conta(empresa,nome,usuario,senha,pergunta,resposta):
    empresa=empresa.strip(); usuario=usuario.strip().lower()
    if not empresa or not usuario or not senha: return False,"Preencha empresa, usuário e senha."
    con=db(); cur=con.cursor(); agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)",(empresa,)); row=cur.fetchone()
        if row: emp_id,perfil=row[0],"Usuario"
        else:
            cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)",(empresa,agora)); emp_id,perfil=cur.lastrowid,"Admin"
        cur.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo',?,?,?)",(emp_id,usuario,nome.strip() or usuario,senha_hash(senha),perfil,pergunta,senha_hash(resposta.strip().lower()),agora))
        con.commit(); return True,f"Conta criada. Perfil: {perfil}."
    except sqlite3.IntegrityError: return False,"Usuário já existe nessa empresa."
    finally: con.close()

def pergunta_rec(empresa,usuario):
    con=db(); cur=con.cursor(); cur.execute("SELECT u.pergunta FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)",(empresa.strip(),usuario.strip().lower())); row=cur.fetchone(); con.close(); return row[0] if row else None

def resetar(empresa,usuario,resposta,nova):
    con=db(); cur=con.cursor(); cur.execute("SELECT u.id,u.resposta_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)",(empresa.strip(),usuario.strip().lower())); row=cur.fetchone()
    if not row: con.close(); return False,"Usuário não encontrado."
    if senha_hash(resposta.strip().lower()) != row[1]: con.close(); return False,"Resposta incorreta."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",(senha_hash(nova),row[0])); con.commit(); con.close(); return True,"Senha alterada."

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

def filtro_mes(key):
    hoje=date.today(); c1,c2=st.columns([1.2,1])
    with c1: mes=st.selectbox("Mês",range(1,13),index=hoje.month-1,format_func=lambda x:f"{x:02d}",key=f"mes_{key}")
    with c2: ano=st.number_input("Ano",2020,2100,hoje.year,key=f"ano_{key}")
    return int(mes),int(ano)

def login():
    st.markdown('<div class="login-wrap"><div class="logo">📈</div><h1 class="login-title">Casa Marques</h1><div class="login-sub">Controle Financeiro</div>', unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["Entrar","Criar conta","Esqueci senha"])
    with t1:
        emp=empresas(); lista=emp["nome"].tolist()
        with st.form("login"):
            empresa=st.selectbox("Empresa",lista,index=lista.index(EMPRESA) if EMPRESA in lista else 0)
            usuario=st.text_input("Usuário"); senha=st.text_input("Senha",type="password"); entrar=st.form_submit_button("Entrar")
        if entrar:
            auth=autenticar(empresa,usuario,senha)
            if auth: st.session_state["auth"]=auth; st.session_state["page"]="Resumo"; st.rerun()
            else: st.error("Empresa, usuário ou senha inválidos.")
        st.caption("Casa Marques | paulo ou mara | 031730")
    with t2:
        with st.form("cad"):
            empresa=st.text_input("Empresa"); nome=st.text_input("Nome"); usuario=st.text_input("Usuário"); senha=st.text_input("Senha",type="password"); pergunta=st.text_input("Pergunta recuperação",value="Qual seu código de recuperação?"); resposta=st.text_input("Resposta",type="password"); criar=st.form_submit_button("Criar acesso")
        if criar:
            ok,msg=criar_conta(empresa,nome,usuario,senha,pergunta,resposta); st.success(msg) if ok else st.error(msg)
    with t3:
        with st.form("buscar"):
            empresa=st.text_input("Empresa",value=EMPRESA); usuario=st.text_input("Usuário"); buscar=st.form_submit_button("Buscar pergunta")
        if buscar:
            p=pergunta_rec(empresa,usuario)
            if p: st.session_state["rec"]={"empresa":empresa,"usuario":usuario,"pergunta":p}
            else: st.error("Usuário não encontrado.")
        if "rec" in st.session_state:
            st.info(st.session_state["rec"]["pergunta"])
            with st.form("reset"):
                resposta=st.text_input("Resposta",type="password"); nova=st.text_input("Nova senha",type="password"); alt=st.form_submit_button("Alterar senha")
            if alt:
                ok,msg=resetar(st.session_state["rec"]["empresa"],st.session_state["rec"]["usuario"],resposta,nova); st.success(msg) if ok else st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)

def cards(df):
    rec=df[(df["tipo"]=="Receita")&(df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    desp=df[(df["tipo"]=="Despesa")&(df["status"]!="Cancelado")]["valor"].sum() if not df.empty else 0
    saldo=rec-desp; qtd=len(df)
    st.markdown(f'''<div class="card-grid"><div class="big-card card-green"><div class="icon-round icon-green">💼</div><div class="card-label">Receitas do mês</div><div class="card-value green">{brl(rec)}</div><div class="arrow-dot green">➜</div></div><div class="big-card card-red"><div class="icon-round icon-red">💳</div><div class="card-label">Despesas do mês</div><div class="card-value red">{brl(desp)}</div><div class="arrow-dot red">➜</div></div><div class="big-card card-blue"><div class="icon-round icon-blue">📈</div><div class="card-label">Saldo do mês</div><div class="card-value blue">{brl(saldo)}</div><div class="arrow-dot blue">➜</div></div><div class="big-card card-soft"><div class="icon-round icon-soft">📄</div><div class="card-label">Lançamentos</div><div class="card-value purple">{qtd}</div><div class="small-muted">este mês</div><div class="arrow-dot purple">➜</div></div></div>''', unsafe_allow_html=True)

def tx_icon(tipo,categoria):
    if tipo=="Receita": return "💼","#DDFBE8"
    if categoria in ["Supermercado","Alimentação","Mercado"]: return "🛒","#FFE3E5"
    if categoria=="Conta de Luz": return "⚡","#FFE3E5"
    if categoria in ["Combustível","Transporte"]: return "⛽","#FFE3E5"
    return "💸","#F0EDFF"

def lista(df):
    if df.empty: st.info("Nenhum lançamento no mês selecionado."); return
    for _,r in df.iterrows():
        ic,bg=tx_icon(r["tipo"],r["categoria"]); cor="green" if r["tipo"]=="Receita" else "red"; data=r["data_lancamento"].strftime("%d/%m/%Y") if pd.notna(r["data_lancamento"]) else "-"; badge="badge-green" if r["tipo"]=="Receita" else "badge-red"
        st.markdown(f'''<div class="tx"><div class="tx-ico" style="background:{bg};">{ic}</div><div style="flex:1"><div class="tx-title">{r["descricao"]}</div><div class="tx-sub">{r["categoria"]} · {data}</div></div><div><div class="tx-val {cor}">{brl(r["valor"])}</div><span class="badge {badge}">{r["tipo"]}</span></div></div>''', unsafe_allow_html=True)

def form_lanc(default=None,key="novo"):
    default=default or {}
    with st.form(key):
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="receita-btn">⬆<br>Receita</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="despesa-btn">⬇<br>Despesa</div>', unsafe_allow_html=True)
        tipo=st.radio("Tipo",["Receita","Despesa"],horizontal=True,index=0 if default.get("tipo")=="Receita" else 1)
        cats=CATEGORIAS[tipo]
        data=st.date_input("Data",value=pd.to_datetime(default.get("data_lancamento")).date() if default.get("data_lancamento") is not None and pd.notna(default.get("data_lancamento")) else date.today())
        descricao=st.text_input("Descrição",value=default.get("descricao","") or "")
        cat_default=default.get("categoria",cats[0]); categoria=st.selectbox("Categoria",cats,index=cats.index(cat_default) if cat_default in cats else 0)
        valor=st.number_input("Valor (R$)",min_value=0.0,step=1.0,format="%.2f",value=float(default.get("valor",0) or 0))
        forma=st.selectbox("Forma de pagamento",FORMAS,index=0); status=st.selectbox("Status",STATUS,index=0)
        venc=st.date_input("Vencimento",value=date.today()); pag=st.date_input("Data pagamento",value=date.today()) if status=="Pago" else None
        obs=st.text_area("Observação"); ok=st.form_submit_button("Salvar Lançamento",type="primary")
    return ok,{"tipo":tipo,"descricao":descricao,"categoria":categoria,"valor":valor,"forma_pagamento":forma,"status":status,"data_lancamento":str(data),"data_vencimento":str(venc),"data_pagamento":str(pag) if pag else None,"observacao":obs}

def selecionar(df,label,key):
    if df.empty: st.info("Nenhum lançamento no mês."); return None
    op={f'#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {brl(r.valor)}':int(r.id) for r in df.itertuples()}
    return op[st.selectbox(label,list(op.keys()),key=key)]

def admin(auth):
    st.markdown('<div class="topbar"><div><div class="top-title">Mais</div><div class="top-sub">Administração</div></div></div>', unsafe_allow_html=True)
    if st.button("Sair"): st.session_state.clear(); st.rerun()
    if auth["perfil"]!="Admin": st.info("Usuário sem permissão administrativa."); return
    con=db(); users=pd.read_sql_query("SELECT id,usuario,nome,perfil,status FROM usuarios WHERE empresa_id=? ORDER BY usuario",con,params=(auth["empresa_id"],)); con.close()
    for _,u in users.iterrows():
        b="badge-green" if u["status"]=="Ativo" else "badge-red"; st.markdown(f'<div class="user-row"><div class="user-ball">{u["usuario"][0].upper()}</div><div style="flex:1"><b>{u["nome"]}</b><br><span class="small-muted">{u["perfil"]}</span></div><span class="badge {b}">{u["status"]}</span></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["Criar usuário","Gerenciar"])
    with t1:
        with st.form("u"):
            nome=st.text_input("Nome"); usuario=st.text_input("Usuário"); senha=st.text_input("Senha",type="password"); perfil=st.selectbox("Perfil",["Usuario","Admin"]); criar=st.form_submit_button("Criar usuário")
        if criar:
            try:
                con=db(); con.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo','Código de recuperação',?,?)",(auth["empresa_id"],usuario.lower(),nome,senha_hash(senha),perfil,senha_hash(senha),datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); con.commit(); con.close(); st.success("Criado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Usuário já existe.")
    with t2:
        if not users.empty:
            op={f'{r.usuario} | {r.perfil} | {r.status}':int(r.id) for r in users.itertuples()}; uid=op[st.selectbox("Usuário",list(op.keys()))]; nova=st.text_input("Nova senha",type="password")
            if st.button("Trocar senha") and nova:
                con=db(); con.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",(senha_hash(nova),uid)); con.commit(); con.close(); st.success("Senha alterada.")
            status=st.selectbox("Status",["Ativo","Inativo"])
            if st.button("Atualizar status"):
                con=db(); con.execute("UPDATE usuarios SET status=? WHERE id=?",(status,uid)); con.commit(); con.close(); st.success("Atualizado."); st.rerun()

def nav(page):
    items=[("Resumo","🏠","Resumo"),("Lançamentos","💬","Lanç."),("Novo","＋","Novo"),("Relatórios","📊","Relat."),("Mais","☰","Mais")]
    st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True); cols=st.columns(5)
    for col,(p,ico,label) in zip(cols,items):
        with col:
            if st.button(f"{ico}\n{label}",key=f"nav_{p}",help=p): st.session_state["page"]=p; st.rerun()

def app():
    auth=st.session_state["auth"]; page=st.session_state.get("page","Resumo")
    if page=="Resumo":
        st.markdown(f'<div class="topbar"><div><div class="top-title">Olá, {auth["nome"].split()[0]} 👋</div><div class="top-sub">{auth["empresa"]} · Resumo financeiro</div></div><div class="avatar">{auth["nome"][0].upper()}</div></div>', unsafe_allow_html=True)
        mes,ano=filtro_mes("resumo"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano); cards(dfm); st.markdown('<div class="section">Últimos lançamentos</div>', unsafe_allow_html=True); lista(dfm)
    elif page=="Lançamentos":
        st.markdown('<div class="topbar"><div><div class="top-title">Lançamentos</div></div></div>', unsafe_allow_html=True); mes,ano=filtro_mes("lanc"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano); busca=st.text_input("Buscar lançamento...")
        if busca and not dfm.empty: dfm=dfm[dfm["descricao"].str.contains(busca,case=False,na=False)]
        lista(dfm)
    elif page=="Novo":
        st.markdown('<div class="topbar"><div><div class="top-title">Novo Lançamento</div></div></div>', unsafe_allow_html=True); ok,d=form_lanc(key="novo")
        if ok:
            if not d["descricao"] or d["valor"]<=0: st.warning("Preencha descrição e valor.")
            else: salvar(auth,d); st.success("Salvo."); st.session_state["page"]="Resumo"; st.rerun()
    elif page=="Relatórios":
        st.markdown('<div class="topbar"><div><div class="top-title">Relatórios</div></div></div>', unsafe_allow_html=True); mes,ano=filtro_mes("rel"); dfm=filtrar(carregar(auth["empresa_id"]),mes,ano); cards(dfm)
        if not dfm.empty:
            cat=dfm.groupby(["tipo","categoria"],as_index=False)["valor"].sum(); cat["valor"]=cat["valor"].apply(brl); st.dataframe(cat,use_container_width=True,hide_index=True)
    else: admin(auth)
    with st.expander("Editar, status ou excluir lançamento"):
        mes,ano=filtro_mes("acao"); df=carregar(auth["empresa_id"]); dfm=filtrar(df,mes,ano); t1,t2,t3=st.tabs(["Editar","Status","Excluir"])
        with t1:
            lid=selecionar(dfm,"Editar lançamento","sel_edit")
            if lid:
                row=df[df["id"]==lid].iloc[0].to_dict(); ok,d=form_lanc(row,"edit")
                if ok: salvar(auth,d,lid); st.success("Alterado."); st.rerun()
        with t2:
            lid=selecionar(dfm,"Alterar status","sel_status")
            if lid:
                ns=st.selectbox("Novo status",STATUS,key="stat")
                if st.button("Atualizar"):
                    con=db(); con.execute("UPDATE lancamentos SET status=?, atualizado_em=? WHERE id=? AND empresa_id=?",(ns,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),lid,auth["empresa_id"])); con.commit(); con.close(); st.success("Atualizado."); st.rerun()
        with t3:
            lid=selecionar(dfm,"Excluir lançamento","sel_del")
            if lid:
                conf=st.checkbox("Confirmo exclusão")
                if st.button("Excluir"):
                    if conf: excluir(auth,lid); st.success("Excluído."); st.rerun()
                    else: st.warning("Confirme.")
    nav(page)

def main():
    init_db()
    if "auth" not in st.session_state: login()
    else: app()
if __name__ == "__main__": main()
