from __future__ import annotations

import io
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CATEGORIAS = [
    "Alimentação",
    "Moradia",
    "Transporte",
    "Saúde",
    "Farmácia",
    "Mercado",
    "Lazer",
    "Educação",
    "Cartão",
    "Empréstimo",
    "Salário",
    "Venda",
    "Pix recebido",
    "Outros",
]
FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito", "Boleto", "Transferência", "Outro"]
STATUS = ["Em aberto", "Pago", "Cancelado"]
COLUNAS = [
    "id", "data_lancamento", "tipo", "descricao", "categoria", "valor",
    "forma_pagamento", "status", "data_vencimento", "data_pagamento", "observacao",
    "criado_em", "atualizado_em",
]
LOCAL_PATH = Path("dados/financeiro.csv")


def moeda(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def hoje_iso() -> str:
    return date.today().isoformat()


def agora_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def supabase_config() -> tuple[str, str]:
    return get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY")


def usar_supabase() -> bool:
    url, key = supabase_config()
    return bool(url and key)


def supabase_headers() -> dict[str, str]:
    _, key = supabase_config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def limpar_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUNAS)
    for c in COLUNAS:
        if c not in df.columns:
            df[c] = "" if c != "valor" else 0.0
    df = df[COLUNAS].copy()
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    for c in ["data_lancamento", "data_vencimento", "data_pagamento"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date.astype(str).replace("NaT", "")
    df = df[df["id"].astype(str).str.strip() != ""].copy()
    return df


def carregar_dados() -> pd.DataFrame:
    if usar_supabase():
        url, _ = supabase_config()
        endpoint = f"{url.rstrip('/')}/rest/v1/financeiro?select=*&order=data_lancamento.desc,criado_em.desc"
        try:
            r = requests.get(endpoint, headers=supabase_headers(), timeout=20)
            r.raise_for_status()
            return limpar_df(pd.DataFrame(r.json()))
        except Exception as e:
            st.warning(f"Não consegui carregar do Supabase. Usando arquivo local nesta sessão. Detalhe: {e}")
    if LOCAL_PATH.exists():
        return limpar_df(pd.read_csv(LOCAL_PATH, dtype=str))
    return pd.DataFrame(columns=COLUNAS)


def salvar_local(df: pd.DataFrame) -> None:
    LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    limpar_df(df).to_csv(LOCAL_PATH, index=False, encoding="utf-8-sig")


def inserir_registro(novo: dict[str, Any]) -> None:
    novo = {c: novo.get(c, "") for c in COLUNAS}
    if usar_supabase():
        url, _ = supabase_config()
        endpoint = f"{url.rstrip('/')}/rest/v1/financeiro"
        r = requests.post(endpoint, headers=supabase_headers(), json=novo, timeout=20)
        r.raise_for_status()
    else:
        df = carregar_dados()
        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
        salvar_local(df)


def atualizar_registro(id_reg: str, dados: dict[str, Any]) -> None:
    dados["atualizado_em"] = agora_iso()
    if usar_supabase():
        url, _ = supabase_config()
        endpoint = f"{url.rstrip('/')}/rest/v1/financeiro?id=eq.{id_reg}"
        r = requests.patch(endpoint, headers=supabase_headers(), json=dados, timeout=20)
        r.raise_for_status()
    else:
        df = carregar_dados()
        mask = df["id"].astype(str) == str(id_reg)
        for k, v in dados.items():
            if k in df.columns:
                df.loc[mask, k] = v
        salvar_local(df)


def excluir_registro(id_reg: str) -> None:
    if usar_supabase():
        url, _ = supabase_config()
        endpoint = f"{url.rstrip('/')}/rest/v1/financeiro?id=eq.{id_reg}"
        r = requests.delete(endpoint, headers=supabase_headers(), timeout=20)
        r.raise_for_status()
    else:
        df = carregar_dados()
        df = df[df["id"].astype(str) != str(id_reg)]
        salvar_local(df)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="financeiro")
    return output.getvalue()


st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 1rem; max-width: 980px;}
[data-testid="stMetricValue"] {font-size: 1.5rem;}
.stButton button {width: 100%; height: 3rem; border-radius: 12px; font-weight: 700;}
.stDownloadButton button {width: 100%; height: 3rem; border-radius: 12px; font-weight: 700;}
input, textarea, select {font-size: 16px !important;}
</style>
""", unsafe_allow_html=True)

st.title("💰 Controle Financeiro Pessoal")
st.caption("Versão simples para celular | Receitas, despesas, vencimentos e status de pagamento")

if usar_supabase():
    st.success("Banco online Supabase conectado.", icon="✅")
else:
    st.info("Modo local/temporário. Para usar no Streamlit Cloud com dados permanentes, configure o Supabase conforme o README.", icon="ℹ️")

aba = st.radio(
    "Menu",
    ["➕ Novo", "🔁 Alterar status", "📊 Painel", "📤 Exportar"],
    horizontal=True,
    label_visibility="collapsed",
)

df = carregar_dados()

if aba == "➕ Novo":
    st.subheader("Novo lançamento")
    with st.form("form_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            data_lanc = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            categoria = st.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index("Outros"))
        with c2:
            valor = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f")
            forma = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO)
            status = st.selectbox("Status", STATUS)
        descricao = st.text_input("Descrição", placeholder="Ex.: Almoço, aluguel, salário...")
        c3, c4 = st.columns(2)
        with c3:
            vencimento = st.date_input("Data de vencimento", value=date.today(), format="DD/MM/YYYY")
        with c4:
            data_pagamento = st.date_input("Data de pagamento", value=date.today(), format="DD/MM/YYYY") if status == "Pago" else None
        obs = st.text_area("Observação", height=80)
        salvar = st.form_submit_button("Salvar lançamento")
        if salvar:
            if not descricao.strip():
                st.error("Informe uma descrição.")
            elif valor <= 0:
                st.error("Informe um valor maior que zero.")
            else:
                novo = {
                    "id": str(uuid.uuid4()),
                    "data_lancamento": data_lanc.isoformat(),
                    "tipo": tipo,
                    "descricao": descricao.strip(),
                    "categoria": categoria,
                    "valor": float(valor),
                    "forma_pagamento": forma,
                    "status": status,
                    "data_vencimento": vencimento.isoformat(),
                    "data_pagamento": data_pagamento.isoformat() if data_pagamento else "",
                    "observacao": obs.strip(),
                    "criado_em": agora_iso(),
                    "atualizado_em": agora_iso(),
                }
                try:
                    inserir_registro(novo)
                    st.success("Lançamento salvo com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

elif aba == "🔁 Alterar status":
    st.subheader("Alterar status")
    if df.empty:
        st.warning("Nenhum lançamento cadastrado.")
    else:
        df_op = df.copy()
        df_op["rotulo"] = df_op.apply(
            lambda r: f"{r['data_lancamento']} | {r['status']} | {r['tipo']} | {r['descricao']} | {moeda(r['valor'])}",
            axis=1,
        )
        escolhido = st.selectbox("Selecione o lançamento", df_op["rotulo"].tolist())
        linha = df_op[df_op["rotulo"] == escolhido].iloc[0]
        st.write(f"**Descrição:** {linha['descricao']}")
        st.write(f"**Valor:** {moeda(linha['valor'])}")
        c1, c2 = st.columns(2)
        with c1:
            novo_status = st.selectbox("Novo status", STATUS, index=STATUS.index(linha["status"]) if linha["status"] in STATUS else 0)
        with c2:
            nova_data_pag = st.date_input("Data de pagamento", value=date.today(), format="DD/MM/YYYY")
        c3, c4 = st.columns(2)
        with c3:
            if st.button("Atualizar status"):
                try:
                    atualizar_registro(linha["id"], {
                        "status": novo_status,
                        "data_pagamento": nova_data_pag.isoformat() if novo_status == "Pago" else "",
                    })
                    st.success("Status atualizado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        with c4:
            if st.button("Excluir lançamento"):
                try:
                    excluir_registro(linha["id"])
                    st.success("Lançamento excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

elif aba == "📊 Painel":
    st.subheader("Painel")
    if df.empty:
        st.warning("Nenhum lançamento cadastrado.")
    else:
        dfp = df.copy()
        dfp["data_lancamento_dt"] = pd.to_datetime(dfp["data_lancamento"], errors="coerce")
        min_data = dfp["data_lancamento_dt"].min().date() if dfp["data_lancamento_dt"].notna().any() else date.today()
        max_data = dfp["data_lancamento_dt"].max().date() if dfp["data_lancamento_dt"].notna().any() else date.today()
        c1, c2 = st.columns(2)
        with c1:
            dt_ini = st.date_input("Data inicial", value=min_data, format="DD/MM/YYYY")
        with c2:
            dt_fim = st.date_input("Data final", value=max_data, format="DD/MM/YYYY")
        cats = st.multiselect("Categorias", CATEGORIAS, default=[])
        mask = (dfp["data_lancamento_dt"].dt.date >= dt_ini) & (dfp["data_lancamento_dt"].dt.date <= dt_fim)
        if cats:
            mask &= dfp["categoria"].isin(cats)
        dfp = dfp[mask].copy()
        receitas = dfp[(dfp["tipo"] == "Receita") & (dfp["status"] != "Cancelado")]["valor"].sum()
        despesas = dfp[(dfp["tipo"] == "Despesa") & (dfp["status"] != "Cancelado")]["valor"].sum()
        aberto = dfp[(dfp["status"] == "Em aberto") & (dfp["tipo"] == "Despesa")]["valor"].sum()
        saldo = receitas - despesas
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Receitas", moeda(receitas))
        k2.metric("Despesas", moeda(despesas))
        k3.metric("Saldo", moeda(saldo))
        k4.metric("Em aberto", moeda(aberto))
        if not dfp.empty:
            resumo_cat = dfp[dfp["tipo"] == "Despesa"].groupby("categoria", as_index=False)["valor"].sum().sort_values("valor", ascending=False)
            if not resumo_cat.empty:
                fig = px.bar(resumo_cat, x="categoria", y="valor", title="Despesas por categoria", text_auto=".2s")
                st.plotly_chart(fig, use_container_width=True)
            mostra = dfp[["data_lancamento", "tipo", "descricao", "categoria", "valor", "forma_pagamento", "status", "data_vencimento", "data_pagamento"]].copy()
            mostra["valor"] = mostra["valor"].apply(moeda)
            st.dataframe(mostra, use_container_width=True, hide_index=True)

elif aba == "📤 Exportar":
    st.subheader("Exportar / Backup")
    if df.empty:
        st.warning("Nenhum dado para exportar.")
    else:
        st.download_button("Baixar Excel", data=to_excel_bytes(df), file_name="controle_financeiro.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Baixar CSV", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name="controle_financeiro.csv", mime="text/csv")
    st.divider()
    st.caption("Para restaurar dados no modo local, suba um CSV exportado anteriormente.")
    arquivo = st.file_uploader("Restaurar CSV", type=["csv"])
    if arquivo is not None and not usar_supabase():
        try:
            novo_df = limpar_df(pd.read_csv(arquivo, dtype=str))
            salvar_local(novo_df)
            st.success("Backup restaurado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar: {e}")
