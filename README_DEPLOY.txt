CONTROLE FINANCEIRO PESSOAL - STREAMLIT CLOUD

1) Subir no GitHub
- Crie um repositório no GitHub.
- Envie estes arquivos:
  app.py
  requirements.txt
  pasta .streamlit
  pasta dados

2) Publicar no Streamlit Cloud
- Acesse https://share.streamlit.io
- Clique em New app
- Escolha o repositório
- Branch: main
- Main file path: app.py
- Clique em Deploy

3) IMPORTANTE SOBRE SALVAR DADOS
Sem banco online, o Streamlit Cloud pode perder dados quando reiniciar.
Para uso diário real, recomendo configurar Supabase.

4) Configurar Supabase para dados permanentes
- Crie uma conta em https://supabase.com
- Crie um projeto
- Vá em SQL Editor e rode o script abaixo:

create table if not exists financeiro (
  id text primary key,
  data_lancamento date,
  tipo text,
  descricao text,
  categoria text,
  valor numeric,
  forma_pagamento text,
  status text,
  data_vencimento date,
  data_pagamento date,
  observacao text,
  criado_em timestamp,
  atualizado_em timestamp
);

alter table financeiro enable row level security;

create policy "allow anon all financeiro"
on financeiro
for all
using (true)
with check (true);

5) Colocar secrets no Streamlit Cloud
No app publicado:
- Settings
- Secrets
- Cole:

SUPABASE_URL="https://SEU-PROJETO.supabase.co"
SUPABASE_KEY="SUA_ANON_KEY"

Depois clique em Save e reinicie o app.

6) Usar no celular
Abra o link do Streamlit Cloud no navegador do celular.
Você pode adicionar à tela inicial pelo Chrome/Safari.
