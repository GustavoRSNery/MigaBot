import json
import os
from dotenv import load_dotenv
import vertexai
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool
from google import genai
from google.genai import types

# --- Configuração Inicial ---

# Carrega variáveis do arquivo .env
load_dotenv()

# Constantes para as variáveis de ambiente
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAG_CORPUS_NAME = os.getenv("RAG_CORPUS_NAME")
SYSTEM_PROMPT_FILE = "system_prompt_migo.txt"
SYSTEM_PROMPT_RESUME_FILE = "system_prompt_summarizer.txt"

class MigoAssessorIA:
    """
    Classe para encapsular a lógica do assistente de IA "Migo",
    integrando o modelo Gemini com RAG e um prompt de sistema definido.
    """
    def __init__(self, model_name: str = 'gemini-2.5-flash-preview-05-20'):
        """
        Inicializa o Vertex AI, configura as ferramentas e o modelo.
        """
        self._validate_config()
        
        # Define a credencial da conta de serviço, se especificada
        if CREDENTIALS_PATH:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

        # Inicializa o Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Carrega o prompt do sistema de um arquivo externo
        try:
            with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            print(f"Erro: Arquivo de prompt '{SYSTEM_PROMPT_FILE}' não encontrado.")
            raise
        # Carrega o prompt do sistema de um arquivo externo
        try:
            with open(SYSTEM_PROMPT_RESUME_FILE, 'r', encoding='utf-8') as f:
                system_prompt_resume = f.read()
                self.prompt_para_resumo = system_prompt_resume
        except FileNotFoundError:
            print(f"Erro: Arquivo de prompt '{SYSTEM_PROMPT_RESUME_FILE}' não encontrado.")
            raise
            
        # # Configura a ferramenta de RAG (Retrieval-Augmented Generation)
        # retrieval_tool = Tool.from_retrieval(
        #     retrieval=rag.Retrieval(
        #         source=rag.VertexRagStore(
        #             rag_resources=[
        #                 rag.RagResource(rag_corpus=RAG_CORPUS_NAME)
        #             ],
        #         ),
        #         # Aumentei o top_k para ter um pouco mais de contexto, ajuste se necessário
        #         similarity_threshold=0.5, 
        #     )
        # )
        
        # Inicializa o modelo Generativo com o prompt do sistema e as ferramentas
        self.model = GenerativeModel(
            model_name=model_name,
            system_instruction=[system_prompt],
            # tools=[retrieval_tool]
        )

        # Inicializa
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # self.model_resume = GenerativeModel(
        #     model_name=model_name,
        #     system_instruction=[system_prompt_resume],
        #     # tools=[retrieval_tool]
        # )
        
        # Inicia uma sessão de chat para manter o histórico automaticamente
        self.chat = self.model.start_chat()
        print("MigoAssessorIA inicializado com sucesso. ✨")

    def _validate_config(self):
        """Valida se as variáveis de ambiente essenciais estão definidas."""
        if not all([PROJECT_ID, RAG_CORPUS_NAME]):
            raise ValueError("As variáveis de ambiente PROJECT_ID e RAG_CORPUS_NAME são obrigatórias.")

    def enviar_relato(self, relato_usuario: str) -> str:
        """
        Envia um relato para o modelo Gemini e retorna a resposta.
        O histórico da conversa é gerenciado pela sessão de chat.
        """
        try:
            print("\n👤 Usuário:", relato_usuario)
            # Envia a mensagem para o chat e obtém a resposta
            response = self.chat.send_message(relato_usuario, stream=True)
            
            full_response_text = ""
            print("🤖 Migo: ", end="", flush=True)
            for chunk in response:
                print(chunk.text, end="", flush=True)
                full_response_text += chunk.text
            print() # Adiciona uma nova linha no final da resposta
            
            return full_response_text.strip()



        except Exception as e:
            print(f"\n🚨 Erro ao se comunicar com o Gemini: {e}")
            return "Desculpe, algo deu errado e não consegui processar sua mensagem. Tente novamente mais tarde."
    
    def gerar_resumo_json(self):
        # return str(self.chat.history)
    #     json_schema = {
    #         "type": "object",
    #         "properties": {
    #             "overview": {"type": "string"},
    #             "victims_gender": {"type": "string"},
    #             "seriousness": {"type": "string"},
    #             "victims_dept": {"type": "string"},
    #             "aggressor_dept": {"type": "string"},
    #         },
    #         "required": ["overview"]
    #     }

    #     generation_config = {
    #     "response_mime_type": "application/json",
    #     "response_schema": json_schema,
    # }
        
        # # resume = self.model_resume.generate_content(contents=str(self.chat.history), generation_config=config)
        # response = self.chat.send_message(
        #     content=self.prompt_para_resumo,
        #     generation_config=generation_config,
        # )

        # response = self.client.models.generate_content(
        #         model= self.model._model_name,
        #         contents=self.prompt_para_resumo,
        #         config=self.prompt_para_resumo
                

        # )

        generate_content_config = types.GenerateContentConfig(
        max_output_tokens=2048,
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            properties = {
                "resumo_do_relato": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "nome_da_vitima": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "nome_do_agressor": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "endereco_da_vitima": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "endereco_do_agressor": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "grau_de_seriedade": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "tipos_de_violencia": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text=self.prompt_para_resumo)],
    )
        
        response = self.client.models.generate_content(
                model= 'gemini-2.5-flash-preview-05-20',
                contents=str(self.chat.history),
                config=generate_content_config)
        
        return str(response.text)
        
    # def gerar_resumo_json(self) -> str:
    #     """
    #     Faz uma chamada final à conversa para gerar um resumo anônimo em JSON.
    #     """
    #     print("\n📄 Gerando resumo JSON da conversa...")
    #     if len(self.chat.history) <= 1:
    #         return '{"error": "Histórico da conversa muito curto para resumir."}'

    #     # Define o schema do JSON que queremos como resposta
    #     json_schema = {
    #         "type": "object",
    #         "properties": {
    #             "overview": {"type": "string"},
    #             "victims_gender": {"type": "string"},
    #             "seriousness": {"type": "string"},
    #             "victims_dept": {"type": "string"},
    #             "aggressor_dept": {"type": "string"},
    #         },
    #         "required": ["overview"]
    #     }

    #     # Cria a instrução final para ser enviada ao modelo
    #     prompt_final_para_resumo = """
    #     Com base em toda a nossa conversa anterior, gere um resumo anônimo do relato em formato JSON.
    #     Não adicione nenhum outro texto ou explicação fora do JSON.
    #     Apenas o código JSON é esperado como resposta.
    #     """

    #     try:
    #         # Faz a última chamada na conversa, usando generation_config para forçar JSON
    #         response = self.chat.send_message(
    #             content=prompt_final_para_resumo,
    #             generation_config={
    #                 "response_mime_type": "application/json",
    #                 "response_schema": json_schema
    #             }
    #         )
            
    #         # Valida e formata o JSON recebido
    #         return json.dumps(json.loads(response.text), indent=2)

    #     except Exception as e:
    #         print(f"🚨 Erro ao gerar o resumo JSON: {e}")
    #         return f'{{"error": "Falha ao gerar o resumo", "details": "{str(e)}"}}'

        

# # --- Bloco de Execução Principal ---
# if __name__ == "__main__":
#     try:
#         # Cria uma instância do nosso assistente Migo
#         assessor_migo = MigoAssessorIA()
        
#         # O Migo se apresenta automaticamente com base no prompt de sistema
#         # Vamos iniciar a conversa com uma saudação
#         primeira_resposta = assessor_migo.enviar_relato("Olá")

#         # Inicia um loop para conversar com o Migo
#         while True:
#             pergunta = input("\n> ")
#             if pergunta.lower() in ['sair', 'exit', 'quit']:
#                 print("Até logo! Lembre-se, o Migo está aqui se precisar. 🤝")
#                 break
            
#             assessor_migo.enviar_relato(pergunta)
            
#     except ValueError as ve:
#         print(f"Erro de configuração: {ve}")
#     except Exception as e:
#         print(f"Ocorreu um erro inesperado: {e}")