# backend/app/services/fhir_service.py
import httpx
from fhir.resources.patient import Patient
from typing import Dict, Any, Optional
import json


class FHIRService:
    """Servicio para comunicación con HAPI FHIR Server"""
    
    def __init__(self, base_url: str = "http://hapi-fhir:8080/fhir"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
    
    async def create_patient(self, patient: Patient) -> Dict[str, Any]:
        """
        Crea un paciente en HAPI FHIR Server
        
        Args:
            patient: Recurso FHIR Patient
            
        Returns:
            Dict con la respuesta del servidor FHIR
        """
        try:
            # Convertir recurso FHIR a JSON
            patient_json = patient.json()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Patient",
                    content=patient_json,
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise Exception(f"Error HTTP {e.response.status_code}: {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Error de conexión con HAPI FHIR: {str(e)}")
        except Exception as e:
            raise Exception(f"Error al crear paciente: {str(e)}")
    
    async def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un paciente por ID desde HAPI FHIR Server
        
        Args:
            patient_id: ID del paciente en FHIR
            
        Returns:
            Dict con el recurso Patient o None si no existe
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/Patient/{patient_id}",
                    headers=self.headers
                )
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"Error HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Error al obtener paciente: {str(e)}")
    
    async def search_patient_by_identifier(self, identifier: str) -> Dict[str, Any]:
        """
        Busca pacientes por número de documento
        
        Args:
            identifier: Número de documento
            
        Returns:
            Dict con Bundle de resultados
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/Patient",
                    params={"identifier": identifier},
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise Exception(f"Error al buscar paciente: {str(e)}")
    
    async def update_patient(self, patient_id: str, patient: Patient) -> Dict[str, Any]:
        """
        Actualiza un paciente existente
        
        Args:
            patient_id: ID del paciente en FHIR
            patient: Recurso Patient actualizado
            
        Returns:
            Dict con la respuesta del servidor
        """
        try:
            patient_json = patient.json()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}/Patient/{patient_id}",
                    content=patient_json,
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise Exception(f"Error al actualizar paciente: {str(e)}")
    
    async def delete_patient(self, patient_id: str) -> bool:
        """
        Elimina un paciente
        
        Args:
            patient_id: ID del paciente en FHIR
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/Patient/{patient_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return True
                
        except Exception as e:
            raise Exception(f"Error al eliminar paciente: {str(e)}")
    
    async def check_server_health(self) -> Dict[str, Any]:
        """
        Verifica el estado del servidor FHIR
        
        Returns:
            Dict con metadata del servidor
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/metadata",
                    headers={"Accept": "application/fhir+json"}
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise Exception(f"Error al verificar servidor FHIR: {str(e)}")
