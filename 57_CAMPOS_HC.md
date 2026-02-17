# 📋 Los 57 Campos de Historia Clínica Interoperable - Colombia

## Referencia: Resolución 866 de 2021 - MinSalud

---

## 1️⃣ DATOS DE IDENTIFICACIÓN DEL USUARIO (15 campos)

| # | Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|-------|------|-------------|-------------|---------|
| 1 | Tipo de documento de identidad | Select | ✅ Sí | CC, TI, CE, PA, RC, MS | "CC" |
| 2 | Número de documento de identidad | String | ✅ Sí | Identificador único | "1234567890" |
| 3 | País de nacionalidad | Select | ✅ Sí | Código ISO 3166 | "CO" (Colombia) |
| 4 | Nombre completo | String | ✅ Sí | Nombres y apellidos | "Juan Pérez García" |
| 5 | Fecha de nacimiento | Date | ✅ Sí | YYYY-MM-DD | "1985-03-15" |
| 6 | Edad | Integer | ✅ Sí | Calculada o ingresada | 39 |
| 7 | Unidad de medida de edad | Select | ✅ Sí | Años, Meses, Días | "Años" |
| 8 | Sexo | Select | ✅ Sí | M, F, I (Indeterminado) | "M" |
| 9 | Género | Select | ⚪ No | Masculino, Femenino, Otro | "Masculino" |
| 10 | Ocupación | String | ⚪ No | Profesión u oficio | "Ingeniero" |
| 11 | Voluntad anticipada | Boolean | ⚪ No | Sí/No | true |
| 12 | Categoría de discapacidad | Select | ⚪ No | Física, Mental, Sensorial, Múltiple | "Ninguna" |
| 13 | País de residencia | Select | ✅ Sí | Código ISO 3166 | "CO" |
| 14 | Municipio de residencia | Select | ✅ Sí | Código DANE | "11001" (Bogotá) |
| 15 | Etnia | Select | ⚪ No | Indígena, ROM, Raizal, Palenquero, Negro, Otro | "Otro" |

### Valores Permitidos

**Tipo de Documento**:
- `CC` - Cédula de Ciudadanía
- `TI` - Tarjeta de Identidad
- `CE` - Cédula de Extranjería
- `PA` - Pasaporte
- `RC` - Registro Civil
- `MS` - Menor sin identificación
- `AS` - Adulto sin identificación

**Sexo**:
- `M` - Masculino
- `F` - Femenino
- `I` - Indeterminado

**Unidad de Edad**:
- `1` - Años
- `2` - Meses
- `3` - Días

---

## 2️⃣ DATOS DE LA ATENCIÓN (9 campos)

| # | Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|-------|------|-------------|-------------|---------|
| 16 | Entidad de salud | String | ✅ Sí | EPS o entidad responsable | "EPS Sanitas" |
| 17 | Fecha y hora de ingreso | DateTime | ✅ Sí | Timestamp de llegada | "2026-02-14T10:30:00" |
| 18 | Modalidad de entrega del servicio | Select | ✅ Sí | Intramural, Extramural, Telemedicina | "Intramural" |
| 19 | Entorno de atención | Select | ✅ Sí | Urgencias, Consulta Externa, Hospitalización | "Urgencias" |
| 20 | Vía de ingreso | Select | ✅ Sí | Espontánea, Remitido, Contraremitido | "Espontánea" |
| 21 | Causa de la atención | Text | ✅ Sí | Motivo de consulta | "Dolor abdominal agudo" |
| 22 | Fecha y hora del triage | DateTime | ⚪ No | Solo para urgencias | "2026-02-14T10:35:00" |
| 23 | Clasificación del triage | Select | ⚪ No | I, II, III, IV, V | "III" |
| 24 | Comunidad étnica | String | ⚪ No | Especificación de etnia | "Wayúu" |

### Valores Permitidos

**Modalidad de Entrega**:
- `01` - Intramural
- `02` - Extramural
- `03` - Telemedicina Interactiva
- `04` - Telemedicina No Interactiva
- `05` - Telexperticia
- `06` - Telemonitoreo

**Entorno de Atención**:
- `01` - Urgencias
- `02` - Consulta Externa
- `03` - Hospitalización
- `04` - Cirugía
- `05` - Apoyo Diagnóstico
- `06` - Apoyo Terapéutico

**Vía de Ingreso**:
- `01` - Espontánea
- `02` - Remitido
- `03` - Contraremitido

**Clasificación Triage** (Manchester):
- `I` - Resucitación (Rojo) - Inmediato
- `II` - Emergencia (Naranja) - 15 minutos
- `III` - Urgente (Amarillo) - 30 minutos
- `IV` - Menos urgente (Verde) - 60 minutos
- `V` - No urgente (Azul) - 120 minutos

---

## 3️⃣ TECNOLOGÍAS EN SALUD (11 campos)

| # | Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|-------|------|-------------|-------------|---------|
| 25 | Descripción del medicamento | String | ⚪ No | Nombre genérico o comercial | "Acetaminofén 500mg" |
| 26 | Dosis | String | ⚪ No | Cantidad por toma | "500mg" |
| 27 | Vía de administración | Select | ⚪ No | Oral, IV, IM, SC, etc. | "Oral" |
| 28 | Frecuencia | String | ⚪ No | Cada cuánto se administra | "Cada 8 horas" |
| 29 | Días de tratamiento | Integer | ⚪ No | Duración del tratamiento | 5 |
| 30 | Unidades aplicadas | Integer | ⚪ No | Cantidad total | 15 |
| 31 | Identificación del personal de salud | String | ⚪ No | Cédula o código | "98765432" |
| 32 | Finalidad de la tecnología | Select | ⚪ No | Terapéutica, Diagnóstica, Paliativa | "Terapéutica" |
| 33 | Tipo de diagnóstico de ingreso | Select | ⚪ No | Principal, Relacionado | "Principal" |
| 34 | Diagnóstico de ingreso | String | ⚪ No | Código CIE-10 | "J00" |
| 35 | Tipo de diagnóstico de egreso | Select | ⚪ No | Principal, Relacionado | "Principal" |

### Valores Permitidos

**Vía de Administración**:
- `01` - Oral
- `02` - Intravenosa (IV)
- `03` - Intramuscular (IM)
- `04` - Subcutánea (SC)
- `05` - Tópica
- `06` - Inhalatoria
- `07` - Rectal
- `08` - Oftálmica
- `09` - Ótica
- `10` - Nasal

**Finalidad de la Tecnología**:
- `01` - Terapéutica
- `02` - Diagnóstica
- `03` - Paliativa
- `04` - Preventiva
- `05` - Rehabilitación

**Tipo de Diagnóstico**:
- `01` - Principal
- `02` - Relacionado
- `03` - Complicación

---

## 4️⃣ DIAGNÓSTICOS (4 campos)

| # | Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|-------|------|-------------|-------------|---------|
| 36 | Diagnóstico de egreso | String | ✅ Sí | Código CIE-10 | "J18.9" |
| 37 | Diagnóstico relacionado 1 | String | ⚪ No | Código CIE-10 | "I10" |
| 38 | Diagnóstico relacionado 2 | String | ⚪ No | Código CIE-10 | "E11.9" |
| 39 | Diagnóstico relacionado 3 | String | ⚪ No | Código CIE-10 | "" |

### Códigos CIE-10 Comunes

| Código | Descripción |
|--------|-------------|
| J00 | Rinofaringitis aguda (resfriado común) |
| J18.9 | Neumonía, no especificada |
| I10 | Hipertensión esencial (primaria) |
| E11.9 | Diabetes mellitus tipo 2 sin complicaciones |
| K29.7 | Gastritis, no especificada |
| M54.5 | Dolor lumbar |
| A09 | Diarrea y gastroenteritis de presunto origen infeccioso |

---

## 5️⃣ DATOS DE EGRESO (18 campos)

| # | Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|-------|------|-------------|-------------|---------|
| 40 | Fecha y hora de salida | DateTime | ✅ Sí | Timestamp de egreso | "2026-02-14T14:30:00" |
| 41 | Condición de salida | Select | ✅ Sí | Vivo, Muerto | "Vivo" |
| 42 | Diagnóstico de muerte | String | ⚪ No | Código CIE-10 si aplica | "" |
| 43 | Código del prestador | String | ✅ Sí | Código habilitación | "110010001234" |
| 44 | Tipo de incapacidad | Select | ⚪ No | Temporal, Permanente | "Temporal" |
| 45 | Días de incapacidad | Integer | ⚪ No | Duración en días | 3 |
| 46 | Días de licencia de maternidad | Integer | ⚪ No | Solo si aplica | 0 |
| 47 | Alergias | Text | ⚪ No | Lista de alergias conocidas | "Penicilina, Mariscos" |
| 48 | Antecedentes familiares | Text | ⚪ No | Historia familiar relevante | "Padre: HTA, Madre: DM2" |
| 49 | Riesgos ocupacionales | Text | ⚪ No | Exposiciones laborales | "Ruido, Polvo" |
| 50 | Responsable del egreso | String | ✅ Sí | Nombre del médico | "Dr. Carlos Rodríguez" |
| 51 | Zona de residencia | Select | ✅ Sí | Urbana, Rural | "Urbana" |
| 52 | Dirección de residencia | String | ✅ Sí | Dirección completa | "Calle 123 #45-67" |
| 53 | Teléfono | String | ⚪ No | Número de contacto | "3001234567" |
| 54 | Correo electrónico | Email | ⚪ No | Email del paciente | "juan@example.com" |
| 55 | Nombre del responsable | String | ⚪ No | Acudiente o familiar | "María Pérez" |
| 56 | Parentesco del responsable | Select | ⚪ No | Relación con el paciente | "Esposa" |
| 57 | Teléfono del responsable | String | ⚪ No | Contacto del acudiente | "3009876543" |

### Valores Permitidos

**Condición de Salida**:
- `01` - Vivo
- `02` - Muerto

**Tipo de Incapacidad**:
- `01` - Temporal
- `02` - Permanente Parcial
- `03` - Permanente Total

**Zona de Residencia**:
- `01` - Urbana
- `02` - Rural

**Parentesco**:
- `01` - Padre/Madre
- `02` - Hijo/Hija
- `03` - Esposo/Esposa
- `04` - Hermano/Hermana
- `05` - Abuelo/Abuela
- `06` - Tío/Tía
- `07` - Otro

---

## 📊 Resumen por Categoría

| Categoría | Campos Obligatorios | Campos Opcionales | Total |
|-----------|---------------------|-------------------|-------|
| Identificación | 8 | 7 | 15 |
| Atención | 6 | 3 | 9 |
| Tecnologías | 0 | 11 | 11 |
| Diagnósticos | 1 | 3 | 4 |
| Egreso | 7 | 11 | 18 |
| **TOTAL** | **22** | **35** | **57** |

---

## 🎯 Campos Mínimos para MVP

Para un MVP funcional, estos son los campos absolutamente esenciales:

### Identificación (8 campos obligatorios)
1. Tipo de documento
2. Número de documento
3. País de nacionalidad
4. Nombre completo
5. Fecha de nacimiento
6. Edad
7. Sexo
8. País de residencia

### Atención (6 campos obligatorios)
9. Entidad de salud
10. Fecha y hora de ingreso
11. Modalidad de entrega
12. Entorno de atención
13. Vía de ingreso
14. Causa de la atención

### Diagnóstico (1 campo obligatorio)
15. Diagnóstico de egreso

### Egreso (7 campos obligatorios)
16. Fecha y hora de salida
17. Condición de salida
18. Código del prestador
19. Responsable del egreso
20. Zona de residencia
21. Dirección de residencia
22. Municipio de residencia

**Total MVP: 22 campos obligatorios**

---

## 🔗 Mapeo a Recursos FHIR

| Campos | Recurso FHIR | Elementos FHIR |
|--------|--------------|----------------|
| 1-15 | Patient | identifier, name, birthDate, gender, address |
| 16-24 | Encounter | class, period, reasonCode, hospitalization |
| 25-32 | MedicationRequest | medicationCodeableConcept, dosageInstruction |
| 33-39 | Condition | code, clinicalStatus, verificationStatus |
| 40-57 | Encounter + Patient | period.end, hospitalization.dischargeDisposition |

---

## 📚 Referencias Normativas

- **Resolución 866 de 2021** - MinSalud Colombia
- **Resolución 3374 de 2000** - Historia Clínica
- **Ley 1438 de 2011** - Sistema General de Seguridad Social en Salud
- **FHIR R4** - HL7 International

---

**Última actualización**: 2026-02-14  
**Versión**: 1.0
