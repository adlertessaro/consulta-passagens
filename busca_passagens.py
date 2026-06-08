import os
import sys  # 🛠️ IMPORTANTE: Adicionado para rastrear o caminho do executável
import requests
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# 🛠️ CORREÇÃO DE CAMINHO ABSOLUTO PARA O PYINSTALLER
if getattr(sys, 'frozen', False):
    # Se estiver rodando como um arquivo .exe compilado
    pasta_principal = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como um script .py normal
    pasta_principal = os.path.dirname(os.path.abspath(__file__))

# Força o load_dotenv a ler o arquivo exatamente ao lado do executável
caminho_do_env = os.path.join(pasta_principal, '.env')
load_dotenv(caminho_do_env)

# Configurações do Voo
ORIGEM = "POA"  # Porto Alegre
DESTINO = "SCL"  # Santiago do Chile
DATA_IDA = "2026-10-07"
DATA_VOLTA = "2026-10-11"
ADULTOS_PARA_CALCULO = 8  # Quantidade de pessoas no grupo
PRECO_ALVO_POR_PESSOA = 1800.00  # Seu limite por passagem individual

# CONFIGURAÇÃO DE PREFERÊNCIAS (Opções: "direto", "conexao" ou "qualquer")
PRIORIZAR_IDA = "conexao"  
PRIORIZAR_VOLTA = "direto"  

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def buscar_preco_atual():
    """Consulta a Ida e a Volta de forma independente para garantir a aplicação dos filtros."""
    url = "https://serpapi.com/search"
    api_key = os.getenv("SERPAPI_KEY")
    
    params_ida = {
        "engine": "google_flights",
        "departure_id": ORIGEM,
        "arrival_id": DESTINO,
        "outbound_date": DATA_IDA,
        "type": "2",  
        "adults": 1, 
        "currency": "BRL",
        "api_key": api_key
    }
    
    params_volta = {
        "engine": "google_flights",
        "departure_id": DESTINO,
        "arrival_id": ORIGEM,
        "outbound_date": DATA_VOLTA,
        "type": "2",  
        "adults": 1, 
        "currency": "BRL",
        "api_key": api_key
    }
    
    try:
        res_ida = requests.get(url, params=params_ida).json()
        opcoes_ida = res_ida.get("best_flights", []) + res_ida.get("other_flights", [])
        
        res_volta = requests.get(url, params=params_volta).json()
        opcoes_volta = res_volta.get("best_flights", []) + res_volta.get("other_flights", [])
        
        if not opcoes_ida or not opcoes_volta:
            print("Não foi possível encontrar voos em um dos trechos.")
            return None

        melhor_ida = None
        for voo in opcoes_ida:
            segmentos = voo.get("flights", [])
            if not segmentos:
                continue
            eh_direto = len(segmentos) == 1
            if PRIORIZAR_IDA == "direto" and not eh_direto:
                continue
            if PRIORIZAR_IDA == "conexao" and eh_direto:
                continue
            melhor_ida = voo
            break

        melhor_volta = None
        for voo in opcoes_volta:
            segmentos = voo.get("flights", [])
            if not segmentos:
                continue
            eh_direto = len(segmentos) == 1
            if PRIORIZAR_VOLTA == "direto" and not eh_direto:
                continue
            if PRIORIZAR_VOLTA == "conexao" and eh_direto:
                continue
            melhor_volta = voo
            break

        if not melhor_ida or not melhor_volta:
            print(f"Filtros incompatíveis com as opções reais: Ida={PRIORIZAR_IDA} | Volta={PRIORIZAR_VOLTA}")
            return None

        segmentos_ida = melhor_ida["flights"]
        saida_ida = segmentos_ida[0]
        chegada_ida = segmentos_ida[-1]
        duracao_ida = sum(v.get("duration", 0) for v in segmentos_ida)
        escalas_ida = [v["arrival_airport"]["id"].upper() for v in segmentos_ida[:-1]]
        passa_por_buenos_aires = any(ap in escalas_ida for ap in ["AEP", "EZE", "BUE"])
        texto_conexoes_ida = ", ".join(escalas_ida) if escalas_ida else "Voo Direto"

        segmentos_volta = melhor_volta["flights"]
        saida_volta = segmentos_volta[0]
        chegada_volta = segmentos_volta[-1]
        duracao_volta = sum(v.get("duration", 0) for v in segmentos_volta)
        escalas_volta = [v["arrival_airport"]["id"].upper() for v in segmentos_volta[:-1]]
        texto_conexoes_volta = ", ".join(escalas_volta) if escalas_volta else "Voo Direto"

        preco_combinado = float(melhor_ida["price"]) + float(melhor_volta["price"])
        link_ida = res_ida.get("search_metadata", {}).get("google_flights_url", "http://google.com/travel/flights")

        return {
            "origem": ORIGEM,
            "destino": DESTINO,
            "data_voo": DATA_IDA,
            "preco": preco_combinado,
            "companhia": saida_ida["airline"],
            "link": link_ida,
            "conexoes_lista_ida": texto_conexoes_ida,
            "conexoes_lista_volta": texto_conexoes_volta,
            "passa_buenos_aires": passa_por_buenos_aires,
            
            # Ida 🛫
            "aeroporto_origem_ida": saida_ida["departure_airport"]["name"],
            "cidade_origem_ida": "Porto Alegre", 
            "pais_origem_ida": "Brasil",
            "horario_saida_ida": saida_ida["departure_airport"]["time"],
            "duracao_ida": f"{duracao_ida} minutos",
            "horario_chegada_ida": chegada_ida["arrival_airport"]["time"],
            "aeroporto_destino_ida":  chegada_ida["arrival_airport"]["name"],
            "cidade_destino_ida": "Santiago",
            "pais_destino_ida": "Chile",

            # Volta 🛬
            "aeroporto_origem_volta": saida_volta["departure_airport"]["name"],
            "cidade_origem_volta": "Santiago",
            "pais_origem_volta": "Chile",
            "horario_saida_volta": saida_volta["departure_airport"]["time"],
            "duracao_volta": f"{duracao_volta} minutos",
            "horario_chegada_volta": chegada_volta["arrival_airport"]["time"],
            "aeroporto_destino_volta":  chegada_volta["arrival_airport"]["name"],
            "cidade_destino_volta": "Porto Alegre",
            "pais_destino_volta": "Brasil"
        }
    except Exception as e:
        print(f"Erro ao consultar a API: {e}")
        return None
    
def salvar_no_supabase(dados_voo):
    """Insere o registro no banco de dados limpando os metadados virtuais do Telegram."""
    try:
        dados_banco = dados_voo.copy()
        campos_exclusivos_telegram = ["link", "conexoes_lista_ida", "conexoes_lista_volta", "passa_buenos_aires"]
        for campo in campos_exclusivos_telegram:
            dados_banco.pop(campo, None)
            
        supabase.table("historico_precos").insert(dados_banco).execute()
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
            .order("criado_em", desc=True)\
            .limit(1).execute()
        
        if resposta.data:
            return resposta.data[0]
        return None
    except Exception as e:
        print(f"Erro ao obter último preço do Supabase: {e}")
        return None
    
def enviar_telegram(mensagem):
    """Envia a mensagem formatada em Markdown para o Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
        print("Mensagem enviada para o Telegram.")
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

def monitorar():
    voo_atual = buscar_preco_atual()
    
    if not voo_atual:
        print("Não foi possível obter os dados do voo nesta rodada.")
        return

    print(f"Voo encontrado: R$ {voo_atual['preco']} (Soma de Ida + Volta).")
    ultimo_preco = obter_ultimo_preco()
    
    salvar_no_supabase(voo_atual)

    preco_total_grupo = voo_atual["preco"] * ADULTOS_PARA_CALCULO
    alerta_ba = "⚠️ **ATENÇÃO:** A Ida possui conexão em **Buenos Aires**! 🇦🇷\n" if voo_atual["passa_buenos_aires"] else ""

    bloco_itinerario = (
        f"🛫 **TRECHO DE IDA ({PRIORIZAR_IDA.upper()}):**\n"
        f"• Saída: {voo_atual['horario_saida_ida']} - {voo_atual['cidade_origem_ida']} ({voo_atual['aeroporto_origem_ida']})\n"
        f"• Chegada: {voo_atual['horario_chegada_ida']} - {voo_atual['cidade_destino_ida']} ({voo_atual['aeroporto_destino_ida']})\n"
        f"• Conexões na Ida: {voo_atual['conexoes_lista_ida']}\n"
        f"• Duração da Ida: {voo_atual['duracao_ida']}\n\n"
        
        f"🛬 **TRECHO DE VOLTA ({PRIORIZAR_VOLTA.upper()}):**\n"
        f"• Saída: {voo_atual['horario_saida_volta']} - {voo_atual['cidade_origem_volta']} ({voo_atual['aeroporto_origem_volta']})\n"
        f"• Chegada: {voo_atual['horario_chegada_volta']} - {voo_atual['cidade_destino_volta']} ({voo_atual['aeroporto_destino_volta']})\n"
        f"• Conexões na Volta: {voo_atual['conexoes_lista_volta']}\n"
        f"• Duração da Volta: {voo_atual['duracao_volta']}\n\n"
        
        f"{alerta_ba}"
        f"🛒 [CLIQUE AQUI PARA VER NO GOOGLE FLIGHTS]({voo_atual['link']})\n"
        f"*(O valor exibido reflete a combinação dos dois bilhetes individuais)*"
    )

    if voo_atual["preco"] <= PRECO_ALVO_POR_PESSOA:
        if ultimo_preco is not None and voo_atual["preco"] == ultimo_preco["preco"]:
            status = "ℹ️ O preço unificado continua igual ao da última checagem."
        elif ultimo_preco is not None and voo_atual["preco"] < ultimo_preco["preco"]:
            status = "🔥 URGENTE: O preço do combo baixou!"
        else:
            status = "✨ Primeira busca registrada dentro da meta!"

        msg = (
            f"🚨 META DE PREÇO ALCANÇADA!\n\n"
            f"{status}\n\n"
            f"Preço por pessoa (Ida+Volta): R$ {voo_atual['preco']:.2f}\n\n"
            f"💰 TOTAL GRUPO ({ADULTOS_PARA_CALCULO} paxs): R$ {preco_total_grupo:.2f}\n"
            f"Companhia principal: {voo_atual['companhia']}\n\n"
            f"{bloco_itinerario}"
        )
    else:
        msg = (
            f"📋 NOTIFICAÇÃO DE PASSAGENS\n\n"
            f"Nenhuma combinação atingiu a meta estipulada.\n"
            f"Preço atual por pessoa (Ida+Volta): R$ {voo_atual['preco']:.2f}\n\n"
            f"💰 Total estimado para o grupo: R$ {preco_total_grupo:.2f}\n"
            f"Companhia: {voo_atual['companhia']}\n\n"
            f"{bloco_itinerario}"
        )

    enviar_telegram(msg)
    print("Notificação enviada para o Telegram.")

if __name__ == "__main__":    
    print("🤖 Monitor de passagens iniciado com sucesso!")
    
    while True:
        try:
            monitorar()
        except Exception as e:
            print(f"Erro crítico no loop de monitoramento: {e}")
        
        time.sleep(14400)  # Dorme por 4 horas