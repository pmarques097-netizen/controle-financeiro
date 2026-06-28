
import sqlite3
import hashlib
import hmac
import os
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_PATH = os.path.join("dados", "controle_financeiro.db")

CATEGORIAS_RECEITA = ["Salário", "Venda", "Serviço", "Investimento", "Reembolso", "Outras Receitas"]
CATEGORIAS_DESPESA = ["Alimentação", "Mercado", "Moradia", "Transporte", "Saúde", "Educação", "Lazer", "Cartão", "Empréstimo", "Impostos", "Outras Despesas"]
FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito", "Boleto", "Transferência", "Cheque", "Outro"]
STATUS_LISTA = ["Em aberto", "Pago", "Cancelado"]

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 980px;}
    div[data-testid="stMetric"] {background: #111827; padding: 14px; border-radius: 14px; border: 1px solid #263244;}
    .stButton>button {width: 100%; border-radius: 12px; height: 44px; font-weight: 700;}
    .small-card {background:#0f172a; padding:12px; border-radius:14px; border:1px solid #243247;}
    input, textarea, select {font-size: 16px !important;}
</style>
""", unsafe_allow_html=True)

def connect():
    os.makedirs("dados", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def check_senha(senha: str, senha_hash: str) -> bool:
    return hmac.compare_digest(hash_senha(senha), senha_hash or "")

def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Ativa',
        criado_em TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
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
        UNIQUE(empresa_id, usuario),
        FOREIGN KEY(empresa_id) REFERENCES empresas(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lancamentos (
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
        atualizado_em TEXT,
        FOREIGN KEY(empresa_id) REFERENCES empresas(id),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)
    # empresa/user inicial
    cur.execute("SELECT COUNT(*) FROM empresas")
    if cur.fetchone()[0] == 0:
        agora = datetime.now().isoformat(timespec="seconds")
        cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, ?, ?)", ("Pessoal", "Ativa", agora))
        empresa_id = cur.lastrowid
        cur.execute("""
            INSERT INTO usuarios (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (empresa_id, "admin", "Administrador", hash_senha("admin123"), "admin", "Ativo", "Código de recuperação", hash_senha("admin123"), agora))
    con.commit()
    con.close()

def get_empresas(ativas=True):
    con = connect()
    where = "WHERE status='Ativa'" if ativas else ""
    df = pd.read_sql_query(f"SELECT * FROM empresas {where} ORDER BY nome", con)
    con.close()
    return df

def get_empresa_id(nome):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM empresas WHERE nome = ?", (nome,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def autenticar(empresa_nome, usuario, senha):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT u.id, u.usuario, u.nome, u.senha_hash, u.perfil, u.status, e.id, e.nome, e.status
        FROM usuarios u
        JOIN empresas e ON e.id = u.empresa_id
        WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)
    """, (empresa_nome.strip(), usuario.strip()))
    row = cur.fetchone()
    con.close()
    if not row:
        return None, "Empresa ou usuário não encontrado."
    uid, user, nome, senha_hash, perfil, status_user, emp_id, emp_nome, status_emp = row
    if status_emp != "Ativa":
        return None, "Empresa inativa."
    if status_user != "Ativo":
        return None, "Usuário inativo."
    if not check_senha(senha, senha_hash):
        return None, "Senha inválida."
    return {
        "id": uid,
        "usuario": user,
        "nome": nome or user,
        "perfil": perfil,
        "empresa_id": emp_id,
        "empresa": emp_nome
    }, None

def criar_empresa_usuario(nome_empresa, nome, usuario, senha, pergunta, resposta):
    nome_empresa = nome_empresa.strip()
    usuario = usuario.strip().lower()
    if not nome_empresa or not usuario or not senha:
        return False, "Preencha empresa, usuário e senha."
    if len(senha) < 4:
        return False, "A senha precisa ter pelo menos 4 caracteres."
    con = connect()
    cur = con.cursor()
    agora = datetime.now().isoformat(timespec="seconds")
    try:
        cur.execute("SELECT id FROM empresas WHERE lower(nome)=lower(?)", (nome_empresa,))
        row = cur.fetchone()
        if row:
            empresa_id = row[0]
            perfil = "usuario"
        else:
            cur.execute("INSERT INTO empresas (nome, status, criado_em) VALUES (?, 'Ativa', ?)", (nome_empresa, agora))
            empresa_id = cur.lastrowid
            perfil = "admin"  # primeiro usuário da empresa vira admin
        cur.execute("""
            INSERT INTO usuarios (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?)
        """, (empresa_id, usuario, nome.strip() or usuario, hash_senha(senha), perfil, pergunta.strip(), hash_senha(resposta.strip().lower()), agora))
        con.commit()
        return True, f"Conta criada com sucesso. Perfil: {perfil}."
    except sqlite3.IntegrityError:
        return False, "Esse usuário já existe nessa empresa."
    finally:
        con.close()

def resetar_senha_publico(empresa_nome, usuario, resposta, nova_senha):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT u.id, u.resposta_hash
        FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
        WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)
    """, (empresa_nome.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    if not row:
        con.close()
        return False, "Empresa ou usuário não encontrado."
    uid, resposta_hash = row
    if not resposta_hash or not check_senha(resposta.strip().lower(), resposta_hash):
        con.close()
        return False, "Resposta de recuperação incorreta."
    if len(nova_senha) < 4:
        con.close()
        return False, "A nova senha precisa ter pelo menos 4 caracteres."
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (hash_senha(nova_senha), uid))
    con.commit()
    con.close()
    return True, "Senha alterada com sucesso."

def get_pergunta(empresa_nome, usuario):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT u.pergunta
        FROM usuarios u JOIN empresas e ON e.id=u.empresa_id
        WHERE lower(e.nome)=lower(?) AND lower(u.usuario)=lower(?)
    """, (empresa_nome.strip(), usuario.strip().lower()))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def get_lancamentos(empresa_id):
    con = connect()
    df = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY date(data_lancamento) DESC, id DESC", con, params=(empresa_id,))
    con.close()
    if df.empty:
        return df
    for col in ["data_lancamento", "vencimento", "data_pagamento"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def filtrar_mes(df, ano, mes):
    if df.empty:
        return df
    return df[(df["data_lancamento"].dt.year == ano) & (df["data_lancamento"].dt.month == mes)].copy()

def salvar_lancamento(empresa_id, usuario_id, dados, lancamento_id=None):
    con = connect()
    cur = con.cursor()
    agora = datetime.now().isoformat(timespec="seconds")
    if lancamento_id:
        cur.execute("""
            UPDATE lancamentos
            SET tipo=?, descricao=?, categoria=?, valor=?, data_lancamento=?, vencimento=?, data_pagamento=?,
                forma_pagamento=?, status=?, observacao=?, atualizado_em=?
            WHERE id=? AND empresa_id=?
        """, (
            dados["tipo"], dados["descricao"], dados["categoria"], dados["valor"], dados["data_lancamento"],
            dados["vencimento"], dados["data_pagamento"], dados["forma_pagamento"], dados["status"], dados["observacao"],
            agora, lancamento_id, empresa_id
        ))
    else:
        cur.execute("""
            INSERT INTO lancamentos
            (empresa_id, usuario_id, tipo, descricao, categoria, valor, data_lancamento, vencimento, data_pagamento,
             forma_pagamento, status, observacao, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            empresa_id, usuario_id, dados["tipo"], dados["descricao"], dados["categoria"], dados["valor"], dados["data_lancamento"],
            dados["vencimento"], dados["data_pagamento"], dados["forma_pagamento"], dados["status"], dados["observacao"],
            agora, agora
        ))
    con.commit()
    con.close()

def excluir_lancamento(empresa_id, lancamento_id):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM lancamentos WHERE id=? AND empresa_id=?", (lancamento_id, empresa_id))
    con.commit()
    con.close()

def get_usuarios(empresa_id):
    con = connect()
    df = pd.read_sql_query("SELECT id, usuario, nome, perfil, status, pergunta, criado_em FROM usuarios WHERE empresa_id=? ORDER BY perfil, usuario", con, params=(empresa_id,))
    con.close()
    return df

def admin_criar_usuario(empresa_id, nome, usuario, senha, perfil, pergunta, resposta):
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (empresa_id, usuario, nome, senha_hash, perfil, status, pergunta, resposta_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?)
        """, (empresa_id, usuario.strip().lower(), nome.strip(), hash_senha(senha), perfil, pergunta.strip(), hash_senha(resposta.strip().lower()), datetime.now().isoformat(timespec="seconds")))
        con.commit()
        return True, "Usuário criado."
    except sqlite3.IntegrityError:
        return False, "Usuário já existe nessa empresa."
    finally:
        con.close()

def admin_alterar_senha(usuario_id, nova_senha):
    con = connect()
    con.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (hash_senha(nova_senha), usuario_id))
    con.commit()
    con.close()

def admin_status_usuario(usuario_id, status):
    con = connect()
    con.execute("UPDATE usuarios SET status=? WHERE id=?", (status, usuario_id))
    con.commit()
    con.close()

def admin_excluir_usuario(usuario_id, empresa_id, admin_id):
    if usuario_id == admin_id:
        return False, "Você não pode excluir seu próprio usuário logado."
    con = connect()
    con.execute("DELETE FROM usuarios WHERE id=? AND empresa_id=?", (usuario_id, empresa_id))
    con.commit()
    con.close()
    return True, "Usuário excluído."

def sidebar_logout():
    with st.sidebar:
        st.write(f"**Empresa:** {st.session_state.user['empresa']}")
        st.write(f"**Usuário:** {st.session_state.user['usuario']}")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

def tela_login():
    st.title("💰 Controle Financeiro")
    st.caption("Login, cadastro por empresa e recuperação de senha.")

    aba_login, aba_cadastro, aba_senha = st.tabs(["Entrar", "Criar conta / empresa", "Esqueci minha senha"])

    with aba_login:
        empresas = get_empresas()
        opcoes_emp = empresas["nome"].tolist() if not empresas.empty else ["Pessoal"]
        empresa = st.selectbox("Empresa", opcoes_emp)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary"):
            user, erro = autenticar(empresa, usuario, senha)
            if erro:
                st.error(erro)
            else:
                st.session_state.user = user
                st.rerun()
        st.info("Acesso inicial: Empresa **Pessoal**, usuário **admin**, senha **admin123**.")

    with aba_cadastro:
        st.subheader("Criar acesso")
        st.caption("Se a empresa ainda não existir, ela será criada e o primeiro usuário será Admin. Se já existir, o usuário será criado como comum.")
        empresa_nova = st.text_input("Empresa", key="cad_empresa")
        nome = st.text_input("Nome", key="cad_nome")
        usuario_novo = st.text_input("Usuário", key="cad_user")
        senha_nova = st.text_input("Senha", type="password", key="cad_senha")
        pergunta = st.text_input("Pergunta de recuperação", value="Qual seu código de recuperação?", key="cad_pergunta")
        resposta = st.text_input("Resposta de recuperação", type="password", key="cad_resposta")
        if st.button("Criar minha conta"):
            ok, msg = criar_empresa_usuario(empresa_nova, nome, usuario_novo, senha_nova, pergunta, resposta)
            st.success(msg) if ok else st.error(msg)

    with aba_senha:
        st.subheader("Recuperar senha")
        empresa_rec = st.text_input("Empresa", key="rec_empresa")
        usuario_rec = st.text_input("Usuário", key="rec_user")
        if st.button("Buscar pergunta"):
            pergunta = get_pergunta(empresa_rec, usuario_rec)
            if pergunta:
                st.session_state.pergunta_rec = pergunta
                st.session_state.rec_empresa = empresa_rec
                st.session_state.rec_user = usuario_rec
            else:
                st.error("Usuário não encontrado.")
        if st.session_state.get("pergunta_rec"):
            st.info(st.session_state.pergunta_rec)
            resposta_rec = st.text_input("Resposta", type="password")
            nova_senha = st.text_input("Nova senha", type="password")
            if st.button("Alterar senha"):
                ok, msg = resetar_senha_publico(st.session_state.rec_empresa, st.session_state.rec_user, resposta_rec, nova_senha)
                st.success(msg) if ok else st.error(msg)

def form_lancamento(defaults=None):
    defaults = defaults or {}
    tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, index=0 if defaults.get("tipo", "Despesa") == "Despesa" else 1)
    categorias = CATEGORIAS_DESPESA if tipo == "Despesa" else CATEGORIAS_RECEITA
    c1, c2 = st.columns(2)
    with c1:
        descricao = st.text_input("Descrição", value=defaults.get("descricao", ""))
        categoria_default = defaults.get("categoria", categorias[0])
        categoria_idx = categorias.index(categoria_default) if categoria_default in categorias else 0
        categoria = st.selectbox("Categoria", categorias, index=categoria_idx)
        valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f", value=float(defaults.get("valor", 0) or 0))
    with c2:
        data_lancamento = st.date_input("Data do lançamento", value=pd.to_datetime(defaults.get("data_lancamento")).date() if defaults.get("data_lancamento") else date.today())
        vencimento = st.date_input("Data de vencimento", value=pd.to_datetime(defaults.get("vencimento")).date() if defaults.get("vencimento") else date.today())
        status_default = defaults.get("status", "Em aberto")
        status = st.selectbox("Status", STATUS_LISTA, index=STATUS_LISTA.index(status_default) if status_default in STATUS_LISTA else 0)
    c3, c4 = st.columns(2)
    with c3:
        fp_default = defaults.get("forma_pagamento", FORMAS_PAGAMENTO[0])
        forma_pagamento = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO, index=FORMAS_PAGAMENTO.index(fp_default) if fp_default in FORMAS_PAGAMENTO else 0)
    with c4:
        data_pagamento = None
        if status == "Pago":
            data_pagamento = st.date_input("Data de pagamento", value=pd.to_datetime(defaults.get("data_pagamento")).date() if defaults.get("data_pagamento") else date.today())
    observacao = st.text_area("Observação", value=defaults.get("observacao", ""))
    return {
        "tipo": tipo,
        "descricao": descricao,
        "categoria": categoria,
        "valor": valor,
        "data_lancamento": str(data_lancamento),
        "vencimento": str(vencimento),
        "data_pagamento": str(data_pagamento) if data_pagamento else None,
        "forma_pagamento": forma_pagamento,
        "status": status,
        "observacao": observacao
    }

def tela_app():
    sidebar_logout()
    user = st.session_state.user
    empresa_id = user["empresa_id"]

    st.title("💰 Controle Financeiro")
    st.caption(f"Empresa: **{user['empresa']}** | Usuário: **{user['usuario']}** | Perfil: **{user['perfil']}**")

    hoje = date.today()
    cmes, cano = st.columns(2)
    with cmes:
        mes = st.selectbox("Mês", list(range(1, 13)), index=hoje.month-1, format_func=lambda x: f"{x:02d}")
    with cano:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=hoje.year, step=1)

    df = get_lancamentos(empresa_id)
    df_mes = filtrar_mes(df, int(ano), int(mes))

    abas = ["Painel", "Novo lançamento", "Alterar lançamento", "Alterar status", "Excluir lançamento", "Lançamentos"]
    if user["perfil"] == "admin":
        abas.append("Admin")
    tabs = st.tabs(abas)

    with tabs[0]:
        receitas = df_mes[(df_mes["tipo"]=="Receita") & (df_mes["status"]!="Cancelado")]["valor"].sum() if not df_mes.empty else 0
        despesas = df_mes[(df_mes["tipo"]=="Despesa") & (df_mes["status"]!="Cancelado")]["valor"].sum() if not df_mes.empty else 0
        saldo = receitas - despesas
        aberto = df_mes[df_mes["status"]=="Em aberto"]["valor"].sum() if not df_mes.empty else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Receitas", moeda(receitas))
        c2.metric("Despesas", moeda(despesas))
        c3.metric("Saldo", moeda(saldo))
        c4.metric("Em aberto", moeda(aberto))

        if not df_mes.empty:
            resumo = df_mes.groupby(["tipo", "categoria"], as_index=False)["valor"].sum()
            st.subheader("Resumo por categoria")
            st.dataframe(resumo, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento no mês selecionado.")

    with tabs[1]:
        st.subheader("Novo lançamento")
        dados = form_lancamento()
        if st.button("Salvar lançamento", type="primary"):
            if not dados["descricao"] or dados["valor"] <= 0:
                st.error("Preencha descrição e valor.")
            else:
                salvar_lancamento(empresa_id, user["id"], dados)
                st.success("Lançamento salvo.")
                st.rerun()

    with tabs[2]:
        st.subheader("Alterar lançamento")
        if df_mes.empty:
            st.info("Nenhum lançamento para alterar neste mês.")
        else:
            opcoes = {f"#{int(r.id)} | {r.tipo} | {r.descricao} | {moeda(r.valor)} | {r.status}": int(r.id) for r in df_mes.itertuples()}
            escolha = st.selectbox("Selecione", list(opcoes.keys()))
            lid = opcoes[escolha]
            row = df[df["id"] == lid].iloc[0].to_dict()
            dados_edit = form_lancamento(row)
            if st.button("Salvar alteração", type="primary"):
                salvar_lancamento(empresa_id, user["id"], dados_edit, lancamento_id=lid)
                st.success("Lançamento alterado.")
                st.rerun()

    with tabs[3]:
        st.subheader("Alterar status")
        if df_mes.empty:
            st.info("Nenhum lançamento neste mês.")
        else:
            opcoes = {f"#{int(r.id)} | {r.status} | {r.tipo} | {r.descricao} | {moeda(r.valor)}": int(r.id) for r in df_mes.itertuples()}
            escolha = st.selectbox("Lançamento", list(opcoes.keys()), key="status_select")
            novo_status = st.selectbox("Novo status", STATUS_LISTA)
            data_pag = None
            if novo_status == "Pago":
                data_pag = st.date_input("Data de pagamento", value=date.today(), key="status_pag")
            if st.button("Atualizar status"):
                lid = opcoes[escolha]
                row = df[df["id"] == lid].iloc[0].to_dict()
                row["status"] = novo_status
                row["data_pagamento"] = str(data_pag) if data_pag else None
                salvar_lancamento(empresa_id, user["id"], row, lancamento_id=lid)
                st.success("Status atualizado.")
                st.rerun()

    with tabs[4]:
        st.subheader("Excluir lançamento")
        if df_mes.empty:
            st.info("Nenhum lançamento para excluir neste mês.")
        else:
            opcoes = {f"#{int(r.id)} | {r.tipo} | {r.descricao} | {moeda(r.valor)} | {r.status}": int(r.id) for r in df_mes.itertuples()}
            escolha = st.selectbox("Selecione para excluir", list(opcoes.keys()), key="del_select")
            confirmar = st.checkbox("Confirmo que desejo excluir este lançamento.")
            if st.button("Excluir definitivamente"):
                if confirmar:
                    excluir_lancamento(empresa_id, opcoes[escolha])
                    st.success("Lançamento excluído.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de excluir.")

    with tabs[5]:
        st.subheader("Lançamentos")
        if df_mes.empty:
            st.info("Nenhum lançamento no mês selecionado.")
        else:
            show = df_mes.copy()
            show["valor"] = show["valor"].apply(moeda)
            for col in ["data_lancamento","vencimento","data_pagamento"]:
                show[col] = show[col].dt.strftime("%d/%m/%Y").fillna("")
            st.dataframe(show[["id","tipo","descricao","categoria","valor","data_lancamento","vencimento","data_pagamento","forma_pagamento","status","observacao"]], use_container_width=True, hide_index=True)
            csv = df_mes.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Baixar CSV", csv, file_name=f"lancamentos_{ano}_{mes:02d}.csv", mime="text/csv")

    if user["perfil"] == "admin":
        with tabs[6]:
            st.subheader("Administração")
            st.caption("Admin pode criar usuários, excluir usuários, ativar/inativar e trocar senha.")

            st.markdown("### Usuários da empresa")
            usuarios = get_usuarios(empresa_id)
            st.dataframe(usuarios, use_container_width=True, hide_index=True)

            a1, a2 = st.columns(2)
            with a1:
                st.markdown("#### Criar usuário")
                nome = st.text_input("Nome", key="adm_nome")
                usuario = st.text_input("Usuário", key="adm_user")
                senha = st.text_input("Senha", type="password", key="adm_senha")
                perfil = st.selectbox("Perfil", ["usuario", "admin"], key="adm_perfil")
                pergunta = st.text_input("Pergunta recuperação", value="Qual seu código de recuperação?", key="adm_pergunta")
                resposta = st.text_input("Resposta recuperação", type="password", key="adm_resposta")
                if st.button("Criar usuário", key="btn_adm_criar"):
                    ok, msg = admin_criar_usuario(empresa_id, nome, usuario, senha, perfil, pergunta, resposta)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()

            with a2:
                st.markdown("#### Gerenciar usuário")
                if not usuarios.empty:
                    mapa = {f"{r.usuario} | {r.nome} | {r.perfil} | {r.status}": int(r.id) for r in usuarios.itertuples()}
                    esc = st.selectbox("Usuário", list(mapa.keys()))
                    uid = mapa[esc]
                    nova = st.text_input("Nova senha", type="password", key="adm_nova_senha")
                    if st.button("Trocar senha"):
                        if len(nova) < 4:
                            st.error("Senha precisa ter pelo menos 4 caracteres.")
                        else:
                            admin_alterar_senha(uid, nova)
                            st.success("Senha alterada.")
                    status = st.selectbox("Status", ["Ativo", "Inativo"], key="adm_status")
                    if st.button("Alterar status do usuário"):
                        admin_status_usuario(uid, status)
                        st.success("Status alterado.")
                        st.rerun()
                    conf = st.checkbox("Confirmo excluir usuário", key="adm_conf_del")
                    if st.button("Excluir usuário"):
                        if conf:
                            ok, msg = admin_excluir_usuario(uid, empresa_id, user["id"])
                            st.success(msg) if ok else st.error(msg)
                            if ok: st.rerun()
                        else:
                            st.warning("Marque a confirmação.")

init_db()
if "user" not in st.session_state:
    tela_login()
else:
    tela_app()
