# backend/app/transformers/fhir_transformer.py
from fhir.resources.patient import Patient
from fhir.resources.identifier import Identifier
from fhir.resources.humanname import HumanName
from fhir.resources.address import Address
from fhir.resources.extension import Extension
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from datetime import date
from typing import Dict, Any


class FHIRTransformer:
    """Transforma datos de HC colombiana a recursos FHIR R4"""
    
    @staticmethod
    def to_fhir_patient(data: Dict[str, Any]) -> Patient:
        """
        Transforma datos de identificación a recurso FHIR Patient
        
        Args:
            data: Diccionario con los 15 campos de identificación
            
        Returns:
            Patient: Recurso FHIR Patient
        """
        
        # Crear identificador principal (documento de identidad)
        identifier = Identifier(
            system="http://www.minsalud.gov.co/identificacion",
            value=data["numeroDocumento"],
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code=FHIRTransformer._map_document_type(data["tipoDocumento"]),
                    display=data["tipoDocumento"]
                )]
            )
        )
        
        # Crear nombre
        name = HumanName(
            text=data["nombreCompleto"],
            use="official"
        )
        
        # Crear dirección
        address = Address(
            use="home",
            country=data["paisResidencia"],
            city=FHIRTransformer._get_city_name(data["municipioResidencia"]),
            extension=[
                Extension(
                    url="http://hl7.org/fhir/StructureDefinition/iso21090-SC-coding",
                    valueCoding=Coding(
                        system="https://www.dane.gov.co/divipola",
                        code=data["municipioResidencia"]
                    )
                )
            ]
        )
        
        # Crear paciente
        patient = Patient(
            identifier=[identifier],
            name=[name],
            gender=data["sexo"],
            birthDate=str(data["fechaNacimiento"]),
            address=[address]
        )
        
        # Agregar extensiones opcionales
        extensions = []
        
        # Nacionalidad
        if data.get("paisNacionalidad"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-nationality",
                extension=[
                    Extension(
                        url="code",
                        valueCodeableConcept=CodeableConcept(
                            coding=[Coding(
                                system="urn:iso:std:iso:3166",
                                code=data["paisNacionalidad"]
                            )]
                        )
                    )
                ]
            ))
        
        # Ocupación
        if data.get("ocupacion"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-occupation",
                valueString=data["ocupacion"]
            ))
        
        # Etnia
        if data.get("etnia") and data["etnia"] != "Ninguna":
            extensions.append(Extension(
                url="http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                valueCodeableConcept=CodeableConcept(
                    text=data["etnia"]
                )
            ))
        
        # Discapacidad
        if data.get("categoriaDiscapacidad"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-disability",
                valueCodeableConcept=CodeableConcept(
                    text=data["categoriaDiscapacidad"]
                )
            ))
        
        # Género (diferente de sexo)
        if data.get("genero"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-genderIdentity",
                valueCodeableConcept=CodeableConcept(
                    text=data["genero"]
                )
            ))
        
        if extensions:
            patient.extension = extensions
        
        return patient
    
    @staticmethod
    def _map_document_type(tipo: str) -> str:
        """Mapea tipos de documento colombianos a códigos FHIR"""
        mapping = {
            "CC": "DL",  # Driver's License (usado para cédula)
            "TI": "PPN", # Passport Number (usado para TI)
            "CE": "PPN", # Passport Number
            "PA": "PPN", # Passport
            "RC": "MR",  # Medical Record Number
            "MS": "AN",  # Account Number
            "AS": "AN"   # Account Number
        }
        return mapping.get(tipo, "DL")
    
    @staticmethod
    def _get_city_name(codigo_dane: str) -> str:
        """Obtiene el nombre de la ciudad desde el código DANE"""
        cities = {
            "11001": "Bogotá D.C.",
            "05001": "Medellín",
            "76001": "Cali",
            "08001": "Barranquilla",
            "13001": "Cartagena",
            "68001": "Bucaramanga",
            "66001": "Pereira",
            "17001": "Manizales",
            "50001": "Villavicencio"
        }
        return cities.get(codigo_dane, "Desconocida")
