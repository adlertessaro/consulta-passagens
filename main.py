import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
ORIGEM = 'GRU'
DESTINO = 'CHI'
DATA_IDA = '2024-12-01'
ADULTOS = 8
PRECO_ALVO = 500.00

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def buscar_preco_atual():
    """Consulta o Google Flights via SerpApi."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": ORIGEM,
        "arrival_id": DESTINO,
        "outbound_date": DATA_IDA,
        "adults": ADULTOS,
        "currency": "BRL",
        "api_key": os.getenv("SERPAPI_KEY")
    }
    
    try:
        resposta = requests.get(url, params=params)
        dados = resposta.json()
        
        if "best_flights" not in dados:
            return None
            
        melhor_voo = dados["best_flights"][0]
        return {
            "origem": ORIGEM,
            "destino": DESTINO,
            "data_voo": DATA_IDA,
            "preco": float(melhor_voo["price"]),
            "companhia": melhor_voo["flights"][0]["airline"]
        }
    except Exception as e:
        print(f"Erro ao consultar a API: {e}")
        return None
    
def salvar_no_supabase(dados_voo):
    """Insere o novo registro de preço no banco de dados."""
    try:
        supabase.table("historico_precos").insert(dados_voo).execute()
        print("Dados salvos no Supabase com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar no Supabase: {e}")

def obter_ultimo_preco():
    """Obtém o último preço registrado para a mesma rota e data."""
    try:
        resposta = supabase.table("historico_precos")\
            .select("*")\
            .eq("origem", ORIGEM)\
            .eq("destino", DESTINO)\
            .eq("data_voo", DATA_IDA)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        
        if resposta.data:
            return resposta.data[0]
        return None
    except Exception as e:
        print(f"Erro ao obter último preço do Supabase: {e}")
        return None
    
def enviar_telegram(dados_voo):
    """Envia uma mensagem para o Telegram se o preço estiver abaixo do alvo."""
    if dados_voo["preco"] < PRECO_ALVO:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        mensagem = (f"Preço baixo encontrado!\n"
                    f"Origem: {dados_voo['origem']}\n"
                    f"Destino: {dados_voo['destino']}\n"
                    f"Data: {dados_voo['data_voo']}\n"
                    f"Preço: R${dados_voo['preco']:.2f}\n"
                    f"Companhia: {dados_voo['companhia']}")
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensagem
        }
        
        try:
            requests.post(url, data=payload)
            print("Mensagem enviada para o Telegram.")
        except Exception as e:
            print(f"Erro ao enviar mensagem para o Telegram: {e}")
                  
                  
def monitorar_preco():
    """Função principal para monitorar o preço do voo."""
    preco_atual = buscar_preco_atual()
    
    if not preco_atual:
        print("Não foi possível obter o preço atual.")
        return
    
    ultimo_preco = obter_ultimo_preco()
    
    if not ultimo_preco or preco_atual["preco"] != ultimo_preco["preco"]:
        salvar_no_supabase(preco_atual)
        enviar_telegram(preco_atual)
    else:
        print("O preço atual é igual ao último registrado. Nenhuma ação necessária.")

        
def monitorar():
    voo_atual = buscar_preco_atual()
    
    if not voo_atual:
        print("Não foi possível obter os dados do voo nesta rodada.")
        return

    print(f"Voo encontrado: R$ {voo_atual['preco']} pela {voo_atual['companhia']}.")

    ultimo_preco = obter_ultimo_preco()
    
    # Salva a busca atual no histórico do Supabase de qualquer forma
    salvar_no_supabase(voo_atual)

    # Lógica de Alerta Inteligente
    if voo_atual["preco"] <= PRECO_ALVO:
        # Só avisa se o preço caiu em relação à última checagem ou se for a primeira rodada
        if ultimo_preco is None or voo_atual["preco"] < ultimo_preco:
            msg = (
                f"🚨 QUEDA DE PREÇO DETECTADA!\n\n"
                f"Destino: {voo_atual['destino']}\n"
                f"Preço: R$ {voo_atual['preco']}\n"
                f"Companhia: {voo_atual['companhia']}\n"
                f"Data do Voo: {voo_atual['data_voo']}"
            )
            enviar_telegram(msg)
            print("Alerta enviado para o Telegram.")
        else:
            print("O preço está abaixo da meta, mas não mudou desde a última checagem. Sem spam.")
    else:
        print("Preço acima do alvo. Monitorando...")

if __name__ == "__main__":    
    monitorar()