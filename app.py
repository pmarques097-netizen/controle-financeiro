import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ARQUIVO = "dados/lancamentos.csv"
COLUNAS = [
    "ID", "Data", "Tipo", "Descricao", "Categoria", "Valor",
    "Forma_Pagamento", "Status", "Vencimento", "Data_Pagamento", "Observacao"
]

CATEGORIAS = [
    "Alimentação", "Moradia", "Transporte", "Saúde", "Farmácia",
    "Educação", "Lazer", "Cartão", "Empréstimo", "Salário",
    "Pix recebido", "Venda", "Outros"
]

FORMAS = ["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito", "Boleto", "Transferência", "Outros"]
STATUS = ["Em aberto", "Pago"]
TIPOS = ["Receita", "Despesa"]


def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def garantir_arquivo():
    os.makedirs("dados", exist_ok=True)
    if not os.path.exists(ARQUIVO):
        pd.DataFrame(columns=COLUNAS).to_csv(ARQUIVO, index=False)


def carregar():
    garantir_arquivo()
    try:
        df = pd.read_csv(ARQUIVO, dtype=str).fillna("")
    except Exception:
        df = pd.DataFrame(columns=COLUNAS)

    for c in COLUNAS:
        if c not in df.columns:
            df[c] = ""

    df = df[COLUNAS].copy()
    df = df[df["ID"].astype(str).str.strip() != ""].copy()

    if not df.empty:
        df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
        df = df[df["ID"].notna()].copy()
        df["ID"] = df["ID"].astype(int)
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    else:
        df["ID"] = pd.Series(dtype="int")
        df["Valor"] = pd.Series(dtype="float")

    return df


def salvar(df):
    garantir_arquivo()
    df = df.copy()
    for c in COLUNAS:
        if c not in df.columns:
            df[c] = ""
    df[COLUNAS].to_csv(ARQUIVO, index=False)


def proximo_id(df):
    if df.empty:
        return 1
    return int(pd.to_numeric(df["ID"], errors="coerce").max()) + 1


def formatar_tabela(df):
    if df.empty:
        return df
    out = df.copy()
    out["Valor"] = out["Valor"].apply(moeda)
    return out.rename(columns={
        "Forma_Pagamento": "Forma de Pagamento",
        "Data_Pagamento": "Data de Pagamento"
    })


st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 760px;}
.stButton button {width: 100%; height: 3rem; border-radius: 12px; font-weight: 700;}
.stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div {border-radius: 10px;}
[data-testid="stMetricValue"] {font-size: 1.5rem;}
.card {padding: 14px; border: 1px solid #30363d; border-radius: 14px; background: #161b22; margin-bottom: 10px;}
.small {color: #9ca3af; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("💰 Controle Financeiro")
st.caption("Versão V7 simples para celular — receitas, despesas, vencimentos e status.")

df = carregar()

aba = st.radio("Menu", ["➕ Novo", "🔄 Status", "📊 Painel", "📋 Lista"], horizontal=True, label_visibility="collapsed")

if aba == "➕ Novo":
    st.subheader("Novo lançamento")
    with st.form("form_novo", clear_on_submit=True):
        data_lanc = st.date_input("Data", value=date.today(), format="DD/MM/YYYY", key="novo_data")
        tipo = st.selectbox("Tipo", TIPOS, key="novo_tipo")
        valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f", key="novo_valor")
        descricao = st.text_input("Descrição", placeholder="Ex.: Almoço, salário, aluguel", key="novo_desc")
        categoria = st.selectbox("Categoria", CATEGORIAS, key="novo_cat")
        forma = st.selectbox("Forma de pagamento", FORMAS, key="novo_forma")
        status = st.selectbox("Status", STATUS, key="novo_status")
        venc = st.date_input("Data de vencimento / regularização", value=date.today(), format="DD/MM/YYYY", key="novo_venc")
        data_pag = ""
        if status == "Pago":
            data_pag = st.date_input("Data de pagamento", value=date.today(), format="DD/MM/YYYY", key="novo_pag")
        obs = st.text_area("Observação", key="novo_obs")
        enviar = st.form_submit_button("Salvar lançamento")

    if enviar:
        if not descricao.strip():
            st.error("Informe a descrição.")
        elif valor <= 0:
            st.error("Informe um valor maior que zero.")
        else:
            novo = {
                "ID": proximo_id(df),
                "Data": data_lanc.strftime("%Y-%m-%d"),
                "Tipo": tipo,
                "Descricao": descricao.strip(),
                "Categoria": categoria,
                "Valor": float(valor),
                "Forma_Pagamento": forma,
                "Status": status,
                "Vencimento": venc.strftime("%Y-%m-%d"),
                "Data_Pagamento": data_pag.strftime("%Y-%m-%d") if data_pag else "",
                "Observacao": obs.strip(),
            }
            df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            salvar(df)
            st.success("Lançamento salvo com sucesso.")

elif aba == "🔄 Status":
    st.subheader("Alterar status")
    if df.empty:
        st.info("Nenhum lançamento cadastrado.")
    else:
        df_ord = df.sort_values("ID", ascending=False).copy()
        opcoes = []
        mapa = {}
        for _, r in df_ord.iterrows():
            item = f"#{int(r['ID'])} | {r['Status']} | {r['Tipo']} | {r['Descricao']} | {moeda(r['Valor'])} | Venc.: {r.get('Vencimento','-')}"
            opcoes.append(item)
            mapa[item] = int(r["ID"])

        escolhido = st.selectbox("Selecione o lançamento", opcoes, key="status_item")
        novo_status = st.selectbox("Novo status", STATUS, key="status_novo")
        data_pag = st.date_input("Data de pagamento", value=date.today(), format="DD/MM/YYYY", key="status_data_pag")

        if st.button("Atualizar status"):
            id_sel = mapa[escolhido]
            df.loc[df["ID"] == id_sel, "Status"] = novo_status
            if novo_status == "Pago":
                df.loc[df["ID"] == id_sel, "Data_Pagamento"] = data_pag.strftime("%Y-%m-%d")
            else:
                df.loc[df["ID"] == id_sel, "Data_Pagamento"] = ""
            salvar(df)
            st.success("Status atualizado.")

elif aba == "📊 Painel":
    st.subheader("Painel")
    if df.empty:
        st.info("Cadastre seu primeiro lançamento.")
    else:
        receita = df.loc[df["Tipo"] == "Receita", "Valor"].sum()
        despesa = df.loc[df["Tipo"] == "Despesa", "Valor"].sum()
        aberto = df.loc[df["Status"] == "Em aberto", "Valor"].sum()
        saldo = receita - despesa

        c1, c2 = st.columns(2)
        c1.metric("Receitas", moeda(receita))
        c2.metric("Despesas", moeda(despesa))
        c1.metric("Saldo", moeda(saldo))
        c2.metric("Em aberto", moeda(aberto))

        resumo_tipo = df.groupby("Tipo", as_index=False)["Valor"].sum()
        st.write("Resumo por tipo")
        st.bar_chart(resumo_tipo.set_index("Tipo"))

        resumo_cat = df.groupby("Categoria", as_index=False)["Valor"].sum().sort_values("Valor", ascending=False)
        st.write("Resumo por categoria")
        st.bar_chart(resumo_cat.set_index("Categoria"))

        abertos = df[df["Status"] == "Em aberto"].sort_values("Vencimento")
        st.write("Próximos vencimentos")
        st.dataframe(formatar_tabela(abertos.head(10)), use_container_width=True, hide_index=True)

elif aba == "📋 Lista":
    st.subheader("Lançamentos")
    if df.empty:
        st.info("Nenhum lançamento cadastrado.")
    else:
        col1, col2 = st.columns(2)
        filtro_tipo = col1.selectbox("Tipo", ["Todos"] + TIPOS, key="filtro_tipo")
        filtro_status = col2.selectbox("Status", ["Todos"] + STATUS, key="filtro_status")
        busca = st.text_input("Buscar descrição", key="busca")

        vis = df.copy()
        if filtro_tipo != "Todos":
            vis = vis[vis["Tipo"] == filtro_tipo]
        if filtro_status != "Todos":
            vis = vis[vis["Status"] == filtro_status]
        if busca.strip():
            vis = vis[vis["Descricao"].str.contains(busca.strip(), case=False, na=False)]

        vis = vis.sort_values("ID", ascending=False)
        st.dataframe(formatar_tabela(vis), use_container_width=True, hide_index=True)

        csv = vis.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Baixar CSV", csv, "controle_financeiro.csv", "text/csv")

st.caption("Obs.: no Streamlit Cloud gratuito, arquivos locais podem ser reiniciados. Para uso definitivo com histórico permanente, o ideal é ligar em Supabase/Google Sheets.")
