import re
from typing import Any
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from datetime import datetime

_guardar_datos_tool_schema = {
    "type": "function",
    "name": "guardar_datos",
    "description": "Guarda los datos que brindó el paciente al llenar el formulario previo a la consulta en un " + \
                   "expediente médico. ",
    "parameters": {
        "type": "object",
        "properties": {
            "nombreCompleto": {
                "type": "string",
                "description": "El nombre del paciente"
            },
            "edad": {
                "type": "string",
                "description": "Edad del paciente"
            },
            "accidenteEnOjos": {
                "type": "string",
                "description": "Información sobre si el paciente ha sufrido un accidente de ojos o no"
            },
            "medicamentos": {
                "type": "string",
                "description": "Información sobre si el paciente se encuentra tomando algún medicamento"
            },
            "ultimaVisitaOftalmologica": {
                "type": "string",
                "description": "Información sobre cuando fue la última vez que el paciente visitó un oftalmólogo"
            },
            "motivoConsulta": {
                "type": "string",
                "description": "El motivo de la consulta del paciente"
            }
        },
        "required": ["nombreCompleto", "edad", "accidenteEnOjos", "medicamentos", "ultimaVisitaOftalmologica", "motivoConsulta"],
        "additionalProperties": False
    }
}


async def _guardar_datos_tool(container_client: ContainerClient, args: Any) -> None:
    content = f"""
# Formulario previo a consulta
## Nombre del paciente

{args["nombreCompleto"]}

## Edad del paciente

{args["edad"]}

## Comentarios sobre previos accidentes en los ojos del paciente

{args["accidenteEnOjos"]}

## Comentarios sobre medicamentos que utiliza el paciente

{args["medicamentos"]}

## Última vez que el paciente asistió a una clínica oftalmológica

{args["ultimaVisitaOftalmologica"]}

## Motivo de la consulta

{args["motivoConsulta"]}
    """
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d-%m-%Y")
    file_name = f"{args["nombreCompleto"].replace(" ","")}_formulario_{formatted_date}.md"
    blob_client = container_client.get_blob_client(file_name)
    blob_client.upload_blob(content)
    
    return ToolResult("Formulario guardado con éxito", ToolResultDirection.TO_CLIENT)


KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_=\-]+$')

# TODO: move from sending all chunks used for grounding eagerly to only sending links to 
# the original content in storage, it'll be more efficient overall

def attach_rag_tools(rtmt: RTMiddleTier, connection_string: str, container_name: str) -> None:
    #Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    #Create container client
    container_client = blob_service_client.get_container_client(container_name)
    rtmt.tools["guardar_datos"] = Tool(schema=_guardar_datos_tool_schema, target=lambda args: _guardar_datos_tool(container_client, args))
    
