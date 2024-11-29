import os

from dotenv import load_dotenv
from aiohttp import web
from ragtools import attach_rag_tools
from rtmt import RTMiddleTier
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential


if __name__ == "__main__":
    load_dotenv()
    llm_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    llm_deployment = os.environ.get("AZURE_OPENAI_REALTIME_DEPLOYMENT")
    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    search_index = os.environ.get("AZURE_SEARCH_INDEX")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")
    connection_string = os.environ.get("AZURE_SA_CONNECTION_STRING")
    container_name = os.environ.get("AZURE_SA_CONTAINER_NAME")

    credentials = DefaultAzureCredential() if not llm_key or not search_key else None

    app = web.Application()

    rtmt = RTMiddleTier(llm_endpoint, llm_deployment, AzureKeyCredential(llm_key) if llm_key else credentials)
    rtmt.system_message = ("## Sobre ti\n" 
                          "Eres un asistente virtual de una clínica oftamológica.\n"
                          "Eres amigable y educado.\n" 
                          "El usuario escucha tus respuestas con audio así que contestas de manera corta y precisa.\n" 
                          "## Tu objetivo principal\n" 
                          "Tu tarea principal es realizar una serie de preguntas de diagnóstico cuando el usuario te comente que quiere llenar el formulario previo a su consulta. Una vez hayas terminado de hacer las preguntas, debes comentar que le enviarás la información a los doctores y que el paciente espere unos minutos para ser atendido. Al terminar con las preguntas siempre usa la herramienta 'guardar_datos_tool' para guardar la información del paciente.\n" 
                          "## Preguntas de diágnostico\n" 
                          "Debes de hacer las siguientes preguntas una por una y esperar a que el usuario te conteste completamente una pregunta para pasar a la siguiente, asegurate de que el usuario haya contestado todas las preguntas:\n" 
                          "1) ¿Cuál es tu nombre completo?\n"
                          "2) ¿Cuántos años tienes?\n" 
                          "3) ¿Has sufrido algún accidente en los ojos?\n" 
                          "4) ¿Tomas algún medicamento actualmente?\n" 
                          "5) ¿Cuándo fue la última vez que visitaste una clínica oftalmológica?\n" 
                          "6) Comentame cuál es tu motivo de la consulta el día de hoy.\n"
                          "## Responder a otros temas\n"
                          "No debes de responder a otros temas que no se relacionen con la consulta del paciente e informa que solo tienes permitido ayudar a llenar el formulario previo a la consulta.\n" )
    
    attach_rag_tools(rtmt, connection_string, container_name)

    rtmt.attach_to_app(app, "/realtime")

    app.add_routes([web.get('/', lambda _: web.FileResponse('./static/index.html'))])
    app.router.add_static('/', path='./static', name='static')
    web.run_app(app, host='localhost', port=8765)
