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
    {"usuario": "paulo", "nome": "Paulo Marques", "senha": "031730", "perfil": "Admin"},
    {"usuario": "mara", "nome": "Mara", "senha": "031730", "perfil": "Usuario"},
]
CATEGORIAS_RECEITA = ["Salário", "Venda", "Serviço", "Transferência", "Investimento", "Reembolso", "Outros"]
CATEGORIAS_DESPESA = ["Alimentação", "Moradia", "Transporte", "Saúde", "Educação", "Cartão", "Empréstimo", "Lazer", "Impostos", "Mercado", "Casa", "Outros"]
FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito", "Boleto", "Transferência", "Outro"]
STATUS_OPCOES = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(page_title=APP_TITLE, page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {background: linear-gradient(180deg,#FAFBFF 0%,#F5F7FB 100%);} 
.main .block-container {padding-top:.8rem; padding-bottom:5.5rem; max-width:760px;}
[data-testid="stSidebar"] {display:none;} #MainMenu, footer, header {visibility:hidden;}
.login-hero {min-height:92vh; border-radius:0 0 34px 34px; padding:28px 22px; background:radial-gradient(circle at 30% 10%,#4637ff 0%,#181043 42%,#030712 100%); color:white;}
.app-logo {width:84px;height:84px;border-radius:24px;background:linear-gradient(135deg,#7C3AED,#38BDF8);display:flex;align-items:center;justify-content:center;font-size:44px;margin:30px auto 18px auto;box-shadow:0 18px 40px rgba(99,91,255,.35)}
.login-title {text-align:center;font-size:29px;font-weight:850;margin:0}.login-sub{text-align:center;color:#CBD5E1;margin:8px 0 26px 0}
.topbar {display:flex;align-items:center;justify-content:space-between;padding:10px 2px 14px 2px}.top-title{font-size:23px;font-weight:850;color:#111827;letter-spacing:-.03em}.top-sub{font-size:13px;color:#6B7280;margin-top:2px}
.avatar {width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#635BFF,#38BDF8);color:white;display:flex;align-items:center;justify-content:center;font-weight:850}
.kpi-grid {display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0 14px 0}.kpi-card{background:#fff;border:1px solid #EEF0F5;border-radius:20px;padding:15px;box-shadow:0 8px 18px rgba(15,23,42,.05)}.kpi-label{font-size:12px;color:#6B7280;font-weight:700}.kpi-value{font-size:22px;font-weight:850;margin-top:8px}.green{color:#22C55E}.red{color:#EF4444}.blue{color:#2563EB}.amber{color:#F59E0B}
.tx-card{display:flex;gap:12px;align-items:center;padding:14px;border-radius:18px;background:#fff;border:1px solid #EEF0F5;margin-bottom:10px;box-shadow:0 7px 18px rgba(15,23,42,.045)}.tx-icon{width:42px;height:42px;border-radius:15px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}.tx-main{flex:1}.tx-title{font-weight:820;color:#111827}.tx-sub{font-size:12px;color:#6B7280;margin-top:2px}.tx-value{font-weight:850;text-align:right}
.bottom-nav{position:fixed;left:50%;bottom:12px;transform:translateX(-50%);width:calc(100% - 24px);max-width:740px;background:rgba(255,255,255,.94);border:1px solid #E5E7EB;box-shadow:0 16px 40px rgba(15,23,42,.16);border-radius:24px;padding:8px;z-index:9999}.nav-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}.nav-item{text-align:center;padding:8px 3px;border-radius:16px;color:#64748B;font-size:11px;font-weight:800}.nav-active{background:#EEF2FF;color:#4F46E5}.nav-plus{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#635BFF,#7C3AED);color:white;display:inline-flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 8px 20px rgba(99,91,255,.35)}
.section-title{font-size:18px;font-weight:850;margin:16px 0 10px}.stButton>button{width:100%;border-radius:16px;min-height:46px;font-weight:850}.stTextInput input,.stNumberInput input,.stDateInput input,textarea{border-radius:16px!important;font-size:16px!important}div[data-baseweb="select"]>div{border-radius:16px!important}
@media(max-width:600px){.main .block-container{padding-left:.7rem;padding-right:.7rem}.kpi-value{font-size:19px}.top-title{font-size:21px}}
</style>
""", unsafe_allow_html=True)

def conectar(): return sqlite3.connect(DB_PATH, check_same_thread=False)
def senha_hash(senha: str, salt: str = "casa_marques_final") -> str:
    return hashlib.pbkdf2_hmac("sha256", str(senha).encode(), salt.encode(), 140000).hex()
def check_senha(senha, shash): return hmac.compare_digest(senha_hash(senha), shash or "")

def init_db():
    conn=conectar(); cur=conn.cursor(); agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT UNIQUE NOT NULL,status TEXT NOT NULL DEFAULT 'Ativa',criado_em TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT,empresa_id INTEGER NOT NULL,usuario TEXT NOT NULL,nome TEXT,senha_hash TEXT NOT NULL,perfil TEXT NOT NULL DEFAULT 'Usuario',status TEXT NOT NULL DEFAULT 'Ativo',pergunta TEXT,resposta_hash TEXT,criado_em TEXT NOT NULL,UNIQUE(empresa_id, usuario))")
    cur.execute("CREATE TABLE IF NOT EXISTS lancamentos (id INTEGER PRIMARY KEY AUTOINCREMENT,empresa_id INTEGER NOT NULL,tipo TEXT NOT NULL,descricao TEXT NOT NULL,categoria TEXT NOT NULL,valor REAL NOT NULL,forma_pagamento TEXT,status TEXT NOT NULL,data_lancamento TEXT NOT NULL,data_vencimento TEXT,data_pagamento TEXT,observacao TEXT,criado_por TEXT,criado_em TEXT NOT NULL,atualizado_em TEXT)")
    cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (EMPRESA_PADRAO,)); row=cur.fetchone()
    if row: empresa_id=row[0]
    else:
        cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (EMPRESA_PADRAO, agora)); empresa_id=cur.lastrowid
    for u in USUARIOS_PADRAO:
        cur.execute("SELECT id FROM usuarios WHERE empresa_id=? AND lower(usuario)=lower(?)", (empresa_id,u['usuario']))
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo',?,?,?)", (empresa_id,u['usuario'],u['nome'],senha_hash(u['senha']),u['perfil'],"Código de recuperação",senha_hash(u['senha']),agora))
    conn.commit(); conn.close()

def brl(v):
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception: return "R$ 0,00"
def empresas_ativas():
    conn=conectar(); df=pd.read_sql_query("SELECT id,nome FROM empresas WHERE status='Ativa' ORDER BY nome", conn); conn.close(); return df

def autenticar(empresa_nome, usuario, senha):
    conn=conectar(); cur=conn.cursor(); cur.execute("SELECT u.id,u.usuario,COALESCE(u.nome,u.usuario),u.perfil,e.id,e.nome,u.senha_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?) AND u.status='Ativo' AND e.status='Ativa'", (empresa_nome.strip(),usuario.strip()))
    row=cur.fetchone(); conn.close()
    if not row or not check_senha(senha,row[6]): return None
    return {"user_id":row[0],"usuario":row[1],"nome":row[2],"perfil":row[3],"empresa_id":row[4],"empresa":row[5]}

def criar_conta_publica(empresa,nome,usuario,senha,pergunta,resposta):
    if not empresa.strip() or not usuario.strip() or not senha: return False,"Preencha empresa, usuário e senha."
    if len(senha)<4: return False,"A senha precisa ter pelo menos 4 caracteres."
    conn=conectar(); cur=conn.cursor(); agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (empresa.strip(),)); row=cur.fetchone()
        if row: eid=row[0]; perfil="Usuario"
        else: cur.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)", (empresa.strip(),agora)); eid=cur.lastrowid; perfil="Admin"
        cur.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo',?,?,?)", (eid,usuario.strip().lower(),nome.strip() or usuario.strip(),senha_hash(senha),perfil,pergunta.strip() or "Código de recuperação",senha_hash(resposta.strip().lower()),agora))
        conn.commit(); return True,f"Conta criada com sucesso. Perfil: {perfil}."
    except sqlite3.IntegrityError: return False,"Esse usuário já existe nessa empresa."
    finally: conn.close()

def pergunta_recuperacao(empresa,usuario):
    conn=conectar(); cur=conn.cursor(); cur.execute("SELECT u.pergunta FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)", (empresa.strip(),usuario.strip().lower())); row=cur.fetchone(); conn.close(); return row[0] if row else None

def resetar_senha(empresa,usuario,resposta,nova_senha):
    if len(nova_senha)<4: return False,"A nova senha precisa ter pelo menos 4 caracteres."
    conn=conectar(); cur=conn.cursor(); cur.execute("SELECT u.id,u.resposta_hash FROM usuarios u JOIN empresas e ON e.id=u.empresa_id WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)", (empresa.strip(),usuario.strip().lower())); row=cur.fetchone()
    if not row: conn.close(); return False,"Empresa ou usuário não encontrado."
    if senha_hash(resposta.strip().lower()) != row[1]: conn.close(); return False,"Resposta de recuperação incorreta."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (senha_hash(nova_senha),row[0])); conn.commit(); conn.close(); return True,"Senha alterada com sucesso."

def carregar_lancamentos(empresa_id):
    conn=conectar(); df=pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC", conn, params=(empresa_id,)); conn.close()
    if not df.empty:
        df['valor']=pd.to_numeric(df['valor'],errors='coerce').fillna(0)
        for c in ['data_lancamento','data_vencimento','data_pagamento']: df[c]=pd.to_datetime(df[c],errors='coerce')
    return df

def filtrar_mes(df,mes,ano):
    if df.empty: return df
    return df[(df['data_lancamento'].dt.month==mes)&(df['data_lancamento'].dt.year==ano)].copy()

def salvar_lancamento(auth,dados,lancamento_id=None):
    conn=conectar(); agora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params=(dados['tipo'],dados['descricao'],dados['categoria'],float(dados['valor']),dados['forma_pagamento'],dados['status'],dados['data_lancamento'],dados['data_vencimento'],dados['data_pagamento'],dados['observacao'])
    if lancamento_id:
        conn.execute("UPDATE lancamentos SET tipo=?,descricao=?,categoria=?,valor=?,forma_pagamento=?,status=?,data_lancamento=?,data_vencimento=?,data_pagamento=?,observacao=?,atualizado_em=? WHERE id=? AND empresa_id=?", params+(agora,lancamento_id,auth['empresa_id']))
    else:
        conn.execute("INSERT INTO lancamentos (empresa_id,tipo,descricao,categoria,valor,forma_pagamento,status,data_lancamento,data_vencimento,data_pagamento,observacao,criado_por,criado_em,atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (auth['empresa_id'],)+params+(auth['usuario'],agora,agora))
    conn.commit(); conn.close()
def excluir_lancamento(auth,lancamento_id): conn=conectar(); conn.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?", (lancamento_id,auth['empresa_id'])); conn.commit(); conn.close()

def tela_login():
    st.markdown('<div class="login-hero"><div class="app-logo">📈</div><h1 class="login-title">Casa Marques</h1><div class="login-sub">Controle Financeiro</div>', unsafe_allow_html=True)
    abas=st.tabs(["Entrar","Criar conta","Esqueci senha"])
    with abas[0]:
        empresas=empresas_ativas(); lista=empresas['nome'].tolist() if not empresas.empty else [EMPRESA_PADRAO]
        with st.form('login'):
            empresa=st.selectbox('Empresa',lista,index=lista.index(EMPRESA_PADRAO) if EMPRESA_PADRAO in lista else 0); usuario=st.text_input('Usuário'); senha=st.text_input('Senha',type='password'); entrar=st.form_submit_button('Entrar')
        if entrar:
            sess=autenticar(empresa,usuario,senha)
            if sess: st.session_state['auth']=sess; st.session_state['page']='Resumo'; st.rerun()
            else: st.error('Empresa, usuário ou senha inválidos.')
        st.caption('Acesso inicial: Casa Marques | paulo | 031730')
    with abas[1]:
        with st.form('cadastro'):
            empresa=st.text_input('Empresa'); nome=st.text_input('Seu nome'); usuario=st.text_input('Usuário'); senha=st.text_input('Senha',type='password'); pergunta=st.text_input('Pergunta de recuperação',value='Qual seu código de recuperação?'); resposta=st.text_input('Resposta de recuperação',type='password'); criar=st.form_submit_button('Criar acesso')
        if criar:
            ok,msg=criar_conta_publica(empresa,nome,usuario,senha,pergunta,resposta); st.success(msg) if ok else st.error(msg)
    with abas[2]:
        with st.form('buscar'):
            empresa=st.text_input('Empresa',value=EMPRESA_PADRAO,key='rec_empresa'); usuario=st.text_input('Usuário',key='rec_usuario'); buscar=st.form_submit_button('Buscar pergunta')
        if buscar:
            p=pergunta_recuperacao(empresa,usuario)
            if p: st.session_state['recuperacao']={'empresa':empresa,'usuario':usuario,'pergunta':p}
            else: st.error('Empresa ou usuário não encontrado.')
        if 'recuperacao' in st.session_state:
            st.info(st.session_state['recuperacao']['pergunta'])
            with st.form('reset'):
                resposta=st.text_input('Resposta',type='password'); nova=st.text_input('Nova senha',type='password'); alterar=st.form_submit_button('Alterar senha')
            if alterar:
                rec=st.session_state['recuperacao']; ok,msg=resetar_senha(rec['empresa'],rec['usuario'],resposta,nova); st.success(msg) if ok else st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)

def filtro_mes_ano():
    hoje=date.today(); c1,c2=st.columns(2)
    with c1: mes=st.selectbox('Mês',list(range(1,13)),index=hoje.month-1,format_func=lambda x:f'{x:02d}')
    with c2: ano=st.number_input('Ano',min_value=2020,max_value=2100,value=hoje.year,step=1)
    return int(mes),int(ano)

def cards(df):
    rec=df[(df['tipo']=='Receita')&(df['status']!='Cancelado')]['valor'].sum() if not df.empty else 0
    desp=df[(df['tipo']=='Despesa')&(df['status']!='Cancelado')]['valor'].sum() if not df.empty else 0
    saldo=rec-desp; qtd=len(df) if not df.empty else 0
    st.markdown(f'<div class="kpi-grid"><div class="kpi-card"><div class="kpi-label">Receitas</div><div class="kpi-value green">{brl(rec)}</div></div><div class="kpi-card"><div class="kpi-label">Despesas</div><div class="kpi-value red">{brl(desp)}</div></div><div class="kpi-card"><div class="kpi-label">Saldo do mês</div><div class="kpi-value blue">{brl(saldo)}</div></div><div class="kpi-card"><div class="kpi-label">Lançamentos</div><div class="kpi-value">{qtd}</div></div></div>', unsafe_allow_html=True)

def form_lancamento(default=None,form_key='form'):
    default=default or {}; tipo_default=default.get('tipo','Despesa')
    with st.form(form_key):
        tipo=st.radio('Tipo',['Receita','Despesa'],horizontal=True,index=0 if tipo_default=='Receita' else 1); cats=CATEGORIAS_RECEITA if tipo=='Receita' else CATEGORIAS_DESPESA
        dl=default.get('data_lancamento'); dv=default.get('data_vencimento'); dp=default.get('data_pagamento')
        data_lanc=st.date_input('Data',value=pd.to_datetime(dl).date() if dl is not None and pd.notna(dl) else date.today())
        descricao=st.text_input('Descrição',value=default.get('descricao',''))
        cat_default=default.get('categoria',cats[0]); categoria=st.selectbox('Categoria',cats,index=cats.index(cat_default) if cat_default in cats else 0)
        valor=st.number_input('Valor (R$)',min_value=0.0,step=1.0,format='%.2f',value=float(default.get('valor',0) or 0))
        c1,c2=st.columns(2)
        with c1: forma_default=default.get('forma_pagamento',FORMAS_PAGAMENTO[0]); forma=st.selectbox('Forma de pagamento',FORMAS_PAGAMENTO,index=FORMAS_PAGAMENTO.index(forma_default) if forma_default in FORMAS_PAGAMENTO else 0)
        with c2: status_default=default.get('status','Em aberto'); status=st.selectbox('Status',STATUS_OPCOES,index=STATUS_OPCOES.index(status_default) if status_default in STATUS_OPCOES else 0)
        venc=st.date_input('Vencimento',value=pd.to_datetime(dv).date() if dv is not None and pd.notna(dv) else date.today())
        data_pag=None
        if status=='Pago': data_pag=st.date_input('Data de pagamento',value=pd.to_datetime(dp).date() if dp is not None and pd.notna(dp) else date.today())
        obs=st.text_area('Observação',value=default.get('observacao','') or '',height=90); salvar=st.form_submit_button('Salvar lançamento',type='primary')
    return salvar, {'tipo':tipo,'descricao':descricao.strip(),'categoria':categoria,'valor':valor,'forma_pagamento':forma,'status':status,'data_lancamento':str(data_lanc),'data_vencimento':str(venc),'data_pagamento':str(data_pag) if data_pag else None,'observacao':obs}

def tx_icon(tipo,categoria):
    if tipo=='Receita': return '💼','#DCFCE7'
    if categoria in ['Alimentação','Mercado']: return '🛒','#FEE2E2'
    if categoria=='Transporte': return '⛽','#FEF3C7'
    if categoria=='Moradia': return '🏠','#DBEAFE'
    if categoria=='Saúde': return '💊','#FCE7F3'
    if categoria=='Cartão': return '💳','#EDE9FE'
    return '💸','#F3F4F6'

def lista_cards(df):
    if df.empty: st.info('Nenhum lançamento no mês selecionado.'); return
    for _,r in df.head(40).iterrows():
        icon,bg=tx_icon(r['tipo'],r['categoria']); cor='green' if r['tipo']=='Receita' else 'red'; data_txt=r['data_lancamento'].strftime('%d/%m/%Y') if pd.notna(r['data_lancamento']) else '-'
        st.markdown(f"""<div class="tx-card"><div class="tx-icon" style="background:{bg};">{icon}</div><div class="tx-main"><div class="tx-title">{r['descricao']}</div><div class="tx-sub">{r['categoria']} - {data_txt} - {r['status']}</div></div><div class="tx-value {cor}">{brl(r['valor'])}</div></div>""", unsafe_allow_html=True)

def selecionar_lancamento(df,label):
    if df.empty: st.info('Nenhum lançamento no mês selecionado.'); return None
    op={f"#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {brl(r.valor)}":int(r.id) for r in df.itertuples()}
    esc=st.selectbox(label,list(op.keys())); return op[esc]

def nav_bottom(page):
    pages=['Resumo','Lançamentos','Novo','Relatórios','Mais']; icons={'Resumo':'⌂','Lançamentos':'▣','Novo':'+','Relatórios':'▥','Mais':'•••'}
    html='<div class="bottom-nav"><div class="nav-grid">'
    for p in pages:
        cls='nav-item nav-active' if p==page else 'nav-item'; html += f'<div class="{cls}"><span class="nav-plus">+</span><br>Novo</div>' if p=='Novo' else f'<div class="{cls}">{icons[p]}<br>{p}</div>'
    html+='</div></div>'; st.markdown(html,unsafe_allow_html=True)
    cols=st.columns(5)
    for col,p in zip(cols,pages):
        with col:
            if st.button(p,key=f'nav_{p}'): st.session_state['page']=p; st.rerun()

def pagina_resumo(auth):
    st.markdown(f"""<div class="topbar"><div><div class="top-title">Olá, {auth['nome'].split()[0]} 👋</div><div class="top-sub">{auth['empresa']} - resumo financeiro</div></div><div class="avatar">{auth['nome'][0].upper()}</div></div>""", unsafe_allow_html=True)
    mes,ano=filtro_mes_ano(); df=carregar_lancamentos(auth['empresa_id']); df_mes=filtrar_mes(df,mes,ano); cards(df_mes); st.markdown('<div class="section-title">Últimos lançamentos</div>',unsafe_allow_html=True); lista_cards(df_mes); return df_mes

def pagina_lancamentos(auth,df_mes):
    st.markdown('<div class="topbar"><div><div class="top-title">Lançamentos</div><div class="top-sub">Consulte e filtre seus registros</div></div></div>',unsafe_allow_html=True)
    if df_mes.empty: st.info('Nenhum lançamento no mês selecionado.'); return
    c1,c2=st.columns(2)
    with c1: ft=st.selectbox('Tipo',['Todos','Receita','Despesa'])
    with c2: fs=st.selectbox('Status',['Todos']+STATUS_OPCOES)
    df=df_mes.copy()
    if ft!='Todos': df=df[df['tipo']==ft]
    if fs!='Todos': df=df[df['status']==fs]
    lista_cards(df); show=df.copy(); show['valor']=show['valor'].apply(brl)
    for c in ['data_lancamento','data_vencimento','data_pagamento']: show[c]=show[c].dt.strftime('%d/%m/%Y').fillna('')
    st.dataframe(show[['id','tipo','descricao','categoria','valor','forma_pagamento','status','data_lancamento','data_vencimento','data_pagamento']],use_container_width=True,hide_index=True)
    st.download_button('Exportar CSV',data=df.to_csv(index=False).encode('utf-8-sig'),file_name='casa_marques_financeiro.csv',mime='text/csv')

def pagina_relatorios(df_mes):
    st.markdown('<div class="topbar"><div><div class="top-title">Relatórios</div><div class="top-sub">Resumo do período selecionado</div></div></div>',unsafe_allow_html=True); cards(df_mes)
    if df_mes.empty: st.info('Sem dados para relatório.'); return
    cat=df_mes.groupby(['tipo','categoria'],as_index=False)['valor'].sum(); cat['valor_formatado']=cat['valor'].apply(brl); st.dataframe(cat[['tipo','categoria','valor_formatado']],hide_index=True,use_container_width=True)
    fp=df_mes.groupby(['forma_pagamento'],as_index=False)['valor'].sum(); fp['valor_formatado']=fp['valor'].apply(brl); st.dataframe(fp[['forma_pagamento','valor_formatado']],hide_index=True,use_container_width=True)

def administracao(auth):
    st.markdown('<div class="topbar"><div><div class="top-title">Mais</div><div class="top-sub">Administração e configurações</div></div></div>',unsafe_allow_html=True)
    if st.button('Sair da conta'): st.session_state.clear(); st.rerun()
    if auth['perfil']!='Admin': st.info('Seu perfil não possui acesso administrativo.'); return
    conn=conectar(); users=pd.read_sql_query("SELECT u.id,e.nome AS empresa,u.usuario,COALESCE(u.nome,u.usuario) AS nome,u.perfil,u.status FROM usuarios u JOIN empresas e ON e.id=u.empresa_id ORDER BY e.nome,u.usuario",conn); conn.close(); st.dataframe(users,use_container_width=True,hide_index=True)
    tabs=st.tabs(['Criar usuário','Gerenciar','Criar empresa'])
    with tabs[0]:
        empresas=empresas_ativas(); lista=empresas['nome'].tolist()
        with st.form('novo_usuario'):
            emp_nome=st.selectbox('Empresa',lista,index=lista.index(auth['empresa']) if auth['empresa'] in lista else 0); nome=st.text_input('Nome'); usuario=st.text_input('Usuário'); senha=st.text_input('Senha',type='password'); perfil=st.selectbox('Perfil',['Usuario','Admin']); pergunta=st.text_input('Pergunta recuperação',value='Qual seu código de recuperação?'); resposta=st.text_input('Resposta recuperação',type='password'); criar=st.form_submit_button('Criar usuário')
        if criar:
            try:
                emp_id=int(empresas.loc[empresas['nome']==emp_nome,'id'].iloc[0]); conn=conectar(); conn.execute("INSERT INTO usuarios (empresa_id,usuario,nome,senha_hash,perfil,status,pergunta,resposta_hash,criado_em) VALUES (?,?,?,?,?,'Ativo',?,?,?)",(emp_id,usuario.strip().lower(),nome.strip() or usuario.strip(),senha_hash(senha),perfil,pergunta.strip(),senha_hash(resposta.strip().lower()),datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); conn.commit(); conn.close(); st.success('Usuário criado.'); st.rerun()
            except sqlite3.IntegrityError: st.error('Usuário já existe nessa empresa.')
    with tabs[1]:
        if not users.empty:
            op={f"{r.empresa} | {r.usuario} | {r.perfil} | {r.status}":int(r.id) for r in users.itertuples()}; uid=op[st.selectbox('Usuário',list(op.keys()))]
            nova=st.text_input('Nova senha',type='password')
            if st.button('Trocar senha'):
                if len(nova)<4: st.error('Senha precisa ter pelo menos 4 caracteres.')
                else: conn=conectar(); conn.execute('UPDATE usuarios SET senha_hash=? WHERE id=?',(senha_hash(nova),uid)); conn.commit(); conn.close(); st.success('Senha alterada.')
            novo_status=st.selectbox('Status',['Ativo','Inativo'])
            if st.button('Atualizar status'): conn=conectar(); conn.execute('UPDATE usuarios SET status=? WHERE id=?',(novo_status,uid)); conn.commit(); conn.close(); st.success('Status atualizado.'); st.rerun()
            conf=st.checkbox('Confirmo excluir este usuário')
            if st.button('Excluir usuário'):
                if not conf: st.warning('Marque a confirmação.')
                elif uid==auth['user_id']: st.error('Você não pode excluir o usuário logado.')
                else: conn=conectar(); conn.execute('DELETE FROM usuarios WHERE id=?',(uid,)); conn.commit(); conn.close(); st.success('Usuário excluído.'); st.rerun()
    with tabs[2]:
        with st.form('nova_empresa'):
            nome=st.text_input('Nome da empresa'); criar=st.form_submit_button('Criar empresa')
        if criar and nome.strip():
            try: conn=conectar(); conn.execute("INSERT INTO empresas (nome,status,criado_em) VALUES (?,'Ativa',?)",(nome.strip(),datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); conn.commit(); conn.close(); st.success('Empresa criada.'); st.rerun()
            except sqlite3.IntegrityError: st.error('Empresa já existe.')

def app_logado():
    auth=st.session_state['auth']; page=st.session_state.get('page','Resumo')
    if page=='Resumo': pagina_resumo(auth)
    else:
        if page in ['Lançamentos','Relatórios']:
            mes,ano=filtro_mes_ano(); df_mes=filtrar_mes(carregar_lancamentos(auth['empresa_id']),mes,ano)
        else:
            h=date.today(); df_mes=filtrar_mes(carregar_lancamentos(auth['empresa_id']),h.month,h.year)
        if page=='Lançamentos': pagina_lancamentos(auth,df_mes)
        elif page=='Novo':
            st.markdown('<div class="topbar"><div><div class="top-title">Novo Lançamento</div><div class="top-sub">Cadastre receita ou despesa</div></div></div>',unsafe_allow_html=True); salvar,dados=form_lancamento(form_key='novo')
            if salvar:
                if not dados['descricao'] or dados['valor']<=0: st.warning('Preencha descrição e valor maior que zero.')
                else: salvar_lancamento(auth,dados); st.success('Lançamento salvo.'); st.session_state['page']='Resumo'; st.rerun()
        elif page=='Relatórios': pagina_relatorios(df_mes)
        elif page=='Mais': administracao(auth)
    with st.expander('Ações rápidas: editar, status ou excluir lançamento'):
        mes,ano=filtro_mes_ano(); df=carregar_lancamentos(auth['empresa_id']); df2=filtrar_mes(df,mes,ano); tab1,tab2,tab3=st.tabs(['Editar','Status','Excluir'])
        with tab1:
            lid=selecionar_lancamento(df2,'Escolha para editar')
            if lid:
                row=df[df['id']==lid].iloc[0].to_dict(); salvar,dados=form_lancamento(row,form_key='editar')
                if salvar:
                    if not dados['descricao'] or dados['valor']<=0: st.warning('Preencha descrição e valor maior que zero.')
                    else: salvar_lancamento(auth,dados,lid); st.success('Lançamento alterado.'); st.rerun()
        with tab2:
            lid=selecionar_lancamento(df2,'Escolha para alterar status')
            if lid:
                ns=st.selectbox('Novo status',STATUS_OPCOES); dp=None
                if ns=='Pago': dp=st.date_input('Data pagamento',value=date.today())
                if st.button('Atualizar status'): conn=conectar(); conn.execute('UPDATE lancamentos SET status=?,data_pagamento=?,atualizado_em=? WHERE id=? AND empresa_id=?',(ns,str(dp) if dp else None,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),lid,auth['empresa_id'])); conn.commit(); conn.close(); st.success('Status atualizado.'); st.rerun()
        with tab3:
            lid=selecionar_lancamento(df2,'Escolha para excluir')
            if lid:
                conf=st.checkbox('Confirmo exclusão definitiva')
                if st.button('Excluir lançamento'):
                    if conf: excluir_lancamento(auth,lid); st.success('Lançamento excluído.'); st.rerun()
                    else: st.warning('Confirme antes de excluir.')
    nav_bottom(page)

def main():
    init_db()
    if 'auth' not in st.session_state: tela_login()
    else: app_logado()
if __name__=='__main__': main()
