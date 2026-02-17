# backend/app/models/patient_model.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class PatientIdentificationData(BaseModel):
    """Modelo para los 15 campos de identificación del paciente"""
    
    # Campo 1: Tipo de documento
    tipoDocumento: str = Field(..., description="Tipo de documento de identidad")
    
    # Campo 2: Número de documento
    numeroDocumento: str = Field(..., description="Número de documento de identidad")
    
    # Campo 3: País de nacionalidad
    paisNacionalidad: str = Field(..., description="Código ISO del país de nacionalidad")
    
    # Campo 4: Nombre completo
    nombreCompleto: str = Field(..., description="Nombre completo del paciente")
    
    # Campo 5: Fecha de nacimiento
    fechaNacimiento: date = Field(..., description="Fecha de nacimiento")
    
    # Campo 6: Edad
    edad: int = Field(..., ge=0, le=150, description="Edad del paciente")
    
    # Campo 7: Unidad de medida de edad
    unidadEdad: str = Field(default="1", description="1=Años, 2=Meses, 3=Días")
    
    # Campo 8: Sexo
    sexo: str = Field(..., description="Sexo: male, female, other, unknown")
    
    # Campo 9: Género (opcional)
    genero: Optional[str] = Field(None, description="Identidad de género")
    
    # Campo 10: Ocupación (opcional)
    ocupacion: Optional[str] = Field(None, description="Ocupación o profesión")
    
    # Campo 11: Voluntad anticipada (opcional)
    voluntadAnticipada: Optional[str] = Field(None, description="true/false")
    
    # Campo 12: Categoría de discapacidad (opcional)
    categoriaDiscapacidad: Optional[str] = Field(None, description="Tipo de discapacidad")
    
    # Campo 13: País de residencia
    paisResidencia: str = Field(..., description="Código ISO del país de residencia")
    
    # Campo 14: Municipio de residencia
    municipioResidencia: str = Field(..., description="Código DANE del municipio")
    
    # Campo 15: Etnia (opcional)
    etnia: Optional[str] = Field(None, description="Grupo étnico")

    class Config:
        json_schema_extra = {
            "example": {
                "tipoDocumento": "CC",
                "numeroDocumento": "1234567890",
                "paisNacionalidad": "CO",
                "nombreCompleto": "Juan Pérez García",
                "fechaNacimiento": "1985-03-15",
                "edad": 39,
                "unidadEdad": "1",
                "sexo": "male",
                "genero": "Masculino",
                "ocupacion": "Ingeniero",
                "voluntadAnticipada": "false",
                "categoriaDiscapacidad": "",
                "paisResidencia": "CO",
                "municipioResidencia": "11001",
                "etnia": "Ninguna"
            }
        }
