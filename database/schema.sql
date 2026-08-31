-- =============================================
-- ESQUEMA DE LA BASE DE DATOS
-- Sistema de Asistencia Escolar
-- =============================================

-- =============================================
-- CICLO LECTIVO
-- =============================================
CREATE TABLE ciclo_lectivo (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    anio         INTEGER NOT NULL UNIQUE,
    fecha_inicio DATE    NOT NULL,
    fecha_fin    DATE    NOT NULL
);

-- =============================================
-- CURSO
-- =============================================
CREATE TABLE curso (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo_id INTEGER NOT NULL,
    anio     INTEGER NOT NULL,
    division TEXT    NOT NULL,
    turno    TEXT    NOT NULL,
    UNIQUE(ciclo_id, anio, division, turno),
    FOREIGN KEY (ciclo_id) REFERENCES ciclo_lectivo(id)
);

-- =============================================
-- ALUMNO
-- =============================================
CREATE TABLE alumno (
    numero   INTEGER PRIMARY KEY,
    nombre   TEXT    NOT NULL,
    apellido TEXT    NOT NULL,
    dni      TEXT    UNIQUE,
    curso_id INTEGER NOT NULL,
    activo   BOOLEAN DEFAULT 1,
    FOREIGN KEY (curso_id) REFERENCES curso(id)
);

-- =============================================
-- MATERIA
-- =============================================
CREATE TABLE materia (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre   TEXT    NOT NULL,
    curso_id INTEGER NOT NULL,
    FOREIGN KEY (curso_id) REFERENCES curso(id)
);

-- =============================================
-- USUARIO
-- =============================================
CREATE TABLE usuario (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre   TEXT    NOT NULL,
    apellido TEXT    NOT NULL,
    username TEXT    UNIQUE NOT NULL,
    password TEXT    NOT NULL,
    rol      TEXT    NOT NULL
        CHECK (rol IN ('profesor','preceptor','directivo','admin')),
    activo   BOOLEAN DEFAULT 1
);

-- =============================================
-- HORARIO (la grilla semanal)
-- =============================================
CREATE TABLE horario (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id      INTEGER NOT NULL,
    dia_semana    INTEGER NOT NULL,
    numero_bloque INTEGER NOT NULL,
    hora_inicio   TIME    NOT NULL,
    hora_fin      TIME    NOT NULL,
    es_recreo     BOOLEAN DEFAULT 0,
    materia_id    INTEGER,
    usuario_id    INTEGER,
    FOREIGN KEY (curso_id)   REFERENCES curso(id),
    FOREIGN KEY (materia_id) REFERENCES materia(id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    CHECK (
        (es_recreo = 1  AND materia_id IS NULL AND usuario_id IS NULL) OR
        (es_recreo = 0  AND materia_id IS NOT NULL AND usuario_id IS NOT NULL)
    )
);

-- =============================================
-- LISTA_DIARIA (la de la preceptora)
-- =============================================
CREATE TABLE lista_diaria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_numero   INTEGER NOT NULL,
    fecha           DATE    NOT NULL,
    estado          TEXT    NOT NULL
        CHECK (estado IN ('presente','ausente','tarde','retirado')),
    hora_llegada    TIME,
    hora_retiro     TIME,
    motivo_retiro   TEXT,
    registrado_por  INTEGER NOT NULL,
    FOREIGN KEY (alumno_numero)  REFERENCES alumno(numero),
    FOREIGN KEY (registrado_por) REFERENCES usuario(id),
    UNIQUE(alumno_numero, fecha)
);

-- =============================================
-- ASISTENCIA (la del profesor, por materia por dia)
-- =============================================
CREATE TABLE asistencia (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_numero  INTEGER NOT NULL,
    materia_id     INTEGER NOT NULL,
    fecha          DATE    NOT NULL,
    estado         TEXT    NOT NULL
        CHECK (estado IN ('presente','ausente')),
    observaciones  TEXT,
    registrado_por INTEGER NOT NULL,
    FOREIGN KEY (alumno_numero)  REFERENCES alumno(numero),
    FOREIGN KEY (materia_id)     REFERENCES materia(id),
    FOREIGN KEY (registrado_por) REFERENCES usuario(id),
    UNIQUE(alumno_numero, materia_id, fecha)
);

-- =============================================
-- JUSTIFICACION
-- =============================================
CREATE TABLE justificacion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lista_diaria_id INTEGER,
    asistencia_id   INTEGER,
    motivo          TEXT    NOT NULL,
    fecha_carga     DATE    NOT NULL,
    archivo_adjunto TEXT,
    cargado_por     INTEGER NOT NULL,
    FOREIGN KEY (lista_diaria_id) REFERENCES lista_diaria(id),
    FOREIGN KEY (asistencia_id)   REFERENCES asistencia(id),
    FOREIGN KEY (cargado_por)     REFERENCES usuario(id),
    CHECK (
        (lista_diaria_id IS NOT NULL AND asistencia_id IS NULL) OR
        (lista_diaria_id IS NULL     AND asistencia_id IS NOT NULL)
    )
);

-- =============================================
-- DIA_HABIL
-- =============================================
CREATE TABLE dia_habil (
    fecha     DATE    PRIMARY KEY,
    es_habil  BOOLEAN NOT NULL,
    motivo    TEXT
);
