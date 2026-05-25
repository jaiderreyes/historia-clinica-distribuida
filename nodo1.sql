-- Nodo 1: Fragmento documento_id < 4000000000

CREATE TABLE usuario (
    documento_id            BIGINT PRIMARY KEY,
    tipo_documento          VARCHAR(10),
    pais_nacionalidad       VARCHAR(100),
    nombre_completo         VARCHAR(255) NOT NULL,
    fecha_nacimiento        DATE,
    edad                    INT,
    unidad_edad             VARCHAR(5)   DEFAULT '1',
    sexo                    VARCHAR(10),
    genero                  VARCHAR(50),
    ocupacion               VARCHAR(100),
    voluntad_anticipada     BOOLEAN      DEFAULT FALSE,
    categoria_discapacidad  VARCHAR(50),
    pais_residencia         VARCHAR(100),
    municipio_residencia    VARCHAR(100),
    etnia                   VARCHAR(50),
    comunidad_etnica        VARCHAR(100),
    zona_residencia         VARCHAR(50),
    fhir_patient_id         VARCHAR(64),
    created_at              TIMESTAMP    DEFAULT NOW(),
    updated_at              TIMESTAMP    DEFAULT NOW()
);



CREATE TABLE atencion (
    atencion_id SERIAL PRIMARY KEY,
    documento_id BIGINT,
    entidad_salud VARCHAR(255),
    fecha_ingreso TIMESTAMP,
    modalidad_entrega VARCHAR(50),
    entorno_atencion VARCHAR(50),
    via_ingreso VARCHAR(50),
    causa_atencion TEXT,
    fecha_triage TIMESTAMP,
    clasificacion_triage VARCHAR(10),
    FOREIGN KEY (documento_id) REFERENCES usuario(documento_id)
);



CREATE TABLE tecnologia_salud (
    tecnologia_id UUID PRIMARY KEY,
    atencion_id INT,
    descripcion_medicamento VARCHAR(255),
    dosis VARCHAR(50),
    via_administracion VARCHAR(50),
    frecuencia VARCHAR(50),
    dias_tratamiento INT,
    unidades_aplicadas INT,
    id_personal_salud UUID,
    finalidad_tecnologia VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);



CREATE TABLE diagnostico (
    diagnostico_id SERIAL PRIMARY KEY,
    atencion_id INT,
    tipo_diagnostico_ingreso VARCHAR(50),
    diagnostico_ingreso VARCHAR(255),
    tipo_diagnostico_egreso VARCHAR(50),
    diagnostico_egreso VARCHAR(255),
    diagnostico_rel1 VARCHAR(255),
    diagnostico_rel2 VARCHAR(255),
    diagnostico_rel3 VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);



CREATE TABLE egreso (
    egreso_id SERIAL PRIMARY KEY,
    atencion_id INT,
    fecha_salida TIMESTAMP,
    condicion_salida VARCHAR(100),
    diagnostico_muerte VARCHAR(255),
    codigo_prestador VARCHAR(20),
    tipo_incapacidad VARCHAR(100),
    dias_incapacidad INT,
    dias_lic_maternidad INT,
    alergias TEXT,
    antecedente_familiar TEXT,
    riesgos_ocupacionales TEXT,
    responsable_egreso VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);



CREATE TABLE profesional_salud (
    id_personal_salud UUID PRIMARY KEY,
    nombre VARCHAR(255),
    especialidad VARCHAR(100)
);
