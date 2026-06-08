# ✈️ Monitor Fantasma de Passagens (POA ➔ SCL)

Este projeto é um robô de monitoramento contínuo de preços de passagens aéreas entre Porto Alegre (POA) e Santiago do Chile (SCL). Ele foi desenvolvido inteiramente em **Python 3** e foi projetado especificamente para ser **empacotado como um executável oculto**, rodando silenciosamente em segundo plano no Windows sem abrir nenhuma janela de terminal.

---

## 🧠 Como o Robô Funciona por Dentro

O script quebra a limitação do Google Flights fazendo duas consultas independentes de "Somente Ida" na API da SerpApi. Ele aplica filtros diferentes para cada trecho:
1. **Ida:** Procura apenas voos com conexão (para economizar).
2. **Volta:** Filtra estritamente voos diretos da LATAM (para garantir o conforto no retorno).
O sistema soma as duas tarifas, valida o preço total para o grupo de **8 pessoas**, salva o histórico no **Supabase** e envia alertas formatados via **Telegram**.

---

## 🛠️ Tecnologias e Pré-requisitos

* **Linguagem:** Python 3.x instalado no sistema.
* **Banco de Dados:** Supabase (PostgreSQL).
* **Notificações:** API de Bots do Telegram.
* **Provedor de Dados:** SerpApi (Mecanismo do Google Flights).

---

## ⚙️ Configuração das Credenciais (`.env`)

Crie um arquivo de texto com o nome exato de `.env` na raiz da pasta do projeto e adicione as suas chaves:

```env
SERPAPI_KEY="sua_chave_da_serpapi_aqui"
SUPABASE_URL="sua_url_do_supabase_aqui"
SUPABASE_KEY="sua_chave_anon_do_supabase_aqui"
TELEGRAM_BOT_TOKEN="token_do_seu_bot_do_telegram"
TELEGRAM_CHAT_ID="id_do_seu_chat_ou_grupo"