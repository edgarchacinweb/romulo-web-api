CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE "rol_usuario" AS ENUM (
'representante',
'docente',
'administrador'
);

CREATE TYPE "sexo" AS ENUM (
'Masculino',
'Femenino'
);

CREATE TYPE "estado_estudiante" AS ENUM (
'revision',
'inscrito',
'retirado',
'graduado'
);

CREATE TYPE "dia" AS ENUM (
'Lunes',
'Martes',
'Miércoles',
'Jueves',
'Viernes'
);

CREATE TYPE tipo_parentesco AS ENUM (
'Madre',
'Padre',
'Abuelo/a',
'Tío/a',
'Hermano/a',
'Padrastro',
'Madrastra',
'Tutor Legal',
'Otro'
);

CREATE TABLE "Clase" (
"ClaseId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"DocenteId" UUID NOT NULL,
"CursoId" UUID NOT NULL,
"PeriodoEscolarId" UUID NOT NULL,
"Seccion" INTEGER NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Asistencia" (
"AsistenciaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"EstudianteId" UUID NOT NULL,
"ClaseId" UUID NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Materia" (
"MateriaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Nombre" VARCHAR(50) NOT NULL UNIQUE,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "BloqueHorario" (
"BloqueHorarioId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"HoraInicio" TIME NOT NULL,
"HoraFin" TIME NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Horario" (
"HorarioId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Dia" DIA NOT NULL,
"DocenteId" UUID NULL,
"BloqueHorarioId" UUID NOT NULL,
"CursoId" UUID NOT NULL,
"PeriodoEscolarId" UUID NOT NULL,
"Seccion" INTEGER NOT NULL,
"Receso" BOOLEAN NOT NULL DEFAULT FALSE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "DatosPersona" (
"DatosPersonaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Nombre" VARCHAR NOT NULL,
"Apellido" VARCHAR NOT NULL,
"Sexo" SEXO NOT NULL,
"Cedula" INTEGER UNIQUE,
"Telefono" VARCHAR(12) NULL UNIQUE,
"Direccion" VARCHAR(100) NULL,
"Ocupacion" VARCHAR(50) NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Estudiante" (
"EstudianteId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"FechaNacimiento" DATE NOT NULL,
"Parentesco" tipo_parentesco DEFAULT 'Tutor Legal' NOT NULL,
"DatosPersonaId" UUID NOT NULL,
"RepresentanteId" UUID NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "CursoEstudiante" (
"EstudianteId" UUID NOT NULL,
"CursoId" UUID NOT NULL,
"Seccion" SMALLINT NOT NULL,
"PeriodoEscolarId" UUID NOT NULL,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp(),
PRIMARY KEY ("EstudianteId", "CursoId")
);

CREATE TABLE "EstadoEstudiante" (
"EstadoEstudianteId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"EstudianteId" UUID NOT NULL,
"Estado" ESTADO_ESTUDIANTE DEFAULT 'revision',
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Nota" (
"NotaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Ponderacion" SMALLINT NOT NULL,
"Lapso" SMALLINT NOT NULL,
"MateriaId" UUID NOT NULL,
"EstudianteId" UUID NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Docente" (
"DocenteId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"DatosPersonaId" UUID NOT NULL,
"HorasAcademicas" SMALLINT NOT NULL DEFAULT 20,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "DocenteMateria" (
"DocenteId" UUID NOT NULL,
"MateriaId" UUID NOT NULL,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp(),
PRIMARY KEY ("DocenteId", "MateriaId")
);

CREATE TABLE "PeriodoEscolar" (
"PeriodoEscolarId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"FechaInicio" DATE NOT NULL,
"FechaFin" DATE NOT NULL,
"CapacidadSecciones" INTEGER NOT NULL,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp(),
"Activo" BOOLEAN DEFAULT TRUE
);

CREATE TABLE "Curso" (
"CursoId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Grado" INTEGER NOT NULL
);

CREATE TABLE "PeriodoInscripcion" (
"PeriodoInscripcion" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Inicio" DATE NOT NULL,
"Fin" DATE NOT NULL,
"PeriodoEscolarId" UUID NOT NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Usuario" (
"UsuarioId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"Email" VARCHAR NOT NULL,
"Clave" VARCHAR NOT NULL,
"Rol" ROL_USUARIO NOT NULL,
"DatosPersona" UUID NULL,
"Activo" BOOLEAN DEFAULT TRUE,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Auditoria" (
"AuditoriaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"UsuarioId" UUID NOT NULL,
"Descripcion" VARCHAR NOT NULL,
"Accion" VARCHAR NOT NULL,
"FechaCreacion" TIMESTAMP DEFAULT clock_timestamp()
);

CREATE TABLE "Incidencia" (
"IncidenciaId" UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
"DatosPersonaId" UUID NOT NULL,
"Descripcion" VARCHAR NOT NULL,
"Documento" VARCHAR NOT NULL,
"Fecha" DATE NOT NULL
);

ALTER TABLE "Docente" ADD CONSTRAINT Docente_Minimo_Horas_Academicas CHECK ("Docente"."HorasAcademicas" >= 20);
ALTER TABLE "Incidencia" ADD FOREIGN KEY ("DatosPersonaId") REFERENCES "DatosPersona" ("DatosPersonaId");
ALTER TABLE "Clase" ADD FOREIGN KEY ("CursoId") REFERENCES "Curso" ("CursoId");
ALTER TABLE "Clase" ADD FOREIGN KEY ("DocenteId") REFERENCES "Docente" ("DocenteId");
ALTER TABLE "Clase" ADD FOREIGN KEY ("PeriodoEscolarId") REFERENCES "PeriodoEscolar" ("PeriodoEscolarId");
ALTER TABLE "Asistencia" ADD FOREIGN KEY ("ClaseId") REFERENCES "Clase" ("ClaseId");
ALTER TABLE "Asistencia" ADD FOREIGN KEY ("EstudianteId") REFERENCES "Estudiante" ("EstudianteId");
ALTER TABLE "CursoEstudiante" ADD FOREIGN KEY ("EstudianteId") REFERENCES "Estudiante" ("EstudianteId");
ALTER TABLE "CursoEstudiante" ADD FOREIGN KEY ("CursoId") REFERENCES "Curso" ("CursoId");
ALTER TABLE "CursoEstudiante" ADD FOREIGN KEY ("PeriodoEscolarId") REFERENCES "PeriodoEscolar" ("PeriodoEscolarId");
ALTER TABLE "PeriodoInscripcion" ADD FOREIGN KEY ("PeriodoEscolarId") REFERENCES "PeriodoEscolar" ("PeriodoEscolarId");
ALTER TABLE "Horario" ADD FOREIGN KEY ("DocenteId") REFERENCES "Docente" ("DocenteId");
ALTER TABLE "Horario" ADD FOREIGN KEY ("BloqueHorarioId") REFERENCES "BloqueHorario" ("BloqueHorarioId");
ALTER TABLE "Horario" ADD FOREIGN KEY ("CursoId") REFERENCES "Curso" ("CursoId");
ALTER TABLE "Horario" ADD FOREIGN KEY ("PeriodoEscolarId") REFERENCES "PeriodoEscolar" ("PeriodoEscolarId");
ALTER TABLE "Nota" ADD FOREIGN KEY ("MateriaId") REFERENCES "Materia" ("MateriaId");
ALTER TABLE "Nota" ADD FOREIGN KEY ("EstudianteId") REFERENCES "Estudiante" ("EstudianteId");
ALTER TABLE "Estudiante" ADD FOREIGN KEY ("DatosPersonaId") REFERENCES "DatosPersona" ("DatosPersonaId");
ALTER TABLE "Estudiante" ADD FOREIGN KEY ("RepresentanteId") REFERENCES "DatosPersona" ("DatosPersonaId");
ALTER TABLE "Docente" ADD FOREIGN KEY ("DatosPersonaId") REFERENCES "DatosPersona" ("DatosPersonaId");
ALTER TABLE "DocenteMateria" ADD FOREIGN KEY ("DocenteId") REFERENCES "Docente" ("DocenteId");
ALTER TABLE "DocenteMateria" ADD FOREIGN KEY ("MateriaId") REFERENCES "Materia" ("MateriaId");
ALTER TABLE "Usuario" ADD FOREIGN KEY ("DatosPersona") REFERENCES "DatosPersona" ("DatosPersonaId") ON DELETE CASCADE;
ALTER TABLE "Auditoria" ADD FOREIGN KEY ("UsuarioId") REFERENCES "Usuario" ("UsuarioId");
ALTER TABLE "Curso" ADD CONSTRAINT CK_Curso_Grado CHECK ("Curso"."Grado" >= 1 AND "Curso"."Grado" <= 5);
ALTER TABLE "Nota" ADD CONSTRAINT CK_Nota_Ponderacion CHECK ("Nota"."Ponderacion" >= 0 AND "Nota"."Ponderacion" <= 20);
ALTER TABLE "Nota" ADD CONSTRAINT CK_Nota_Lapso CHECK ("Nota"."Lapso" >= 1 AND "Nota"."Lapso" <= 3);
CREATE INDEX Cedula_index ON "DatosPersona" ("Cedula");

INSERT INTO "Curso" ("Grado") VALUES (1), (2), (3), (4), (5);
INSERT INTO "Usuario" ("Email", "Clave", "Rol") VALUES ('romulogallegosproyecto@gmail.com', '$2b$10$w75IUe68HwWRQGXmLGVQmumMWLHcubkDLCEsBq1lmNrKvNgflcOuO', 'administrador');

INSERT INTO "Materia" ("Nombre")
VALUES
('Matemáticas'),
('Castellano'),
('G.H.S'),
('Educación Física'),
('Inglés'),
('Biología'),
('Química'),
('Física');

INSERT INTO "BloqueHorario" ("HoraInicio", "HoraFin")
VALUES
('07:00', '07:40'),
('07:40', '08:20'),
('08:20', '08:25'),
('08:25', '09:05'),
('09:05', '09:45'),
('09:45', '10:00'),
('10:00', '10:40'),
('10:40', '11:20'),
('11:20', '11:25'),
('11:25', '12:05'),
('12:05', '12:45');

-- Procedimientos almacenados
CREATE PROCEDURE registrar_curso_estudiante(estudiante_id UUID, curso_id UUID) AS $$
DECLARE
	seccion SMALLINT;
	periodo_escolar_id UUID;
	estudiantes_por_seccion INTEGER;
	total_estudiantes INTEGER;
BEGIN
	-- Verificando que el curso exista
	PERFORM "CursoId" FROM "Curso" WHERE "CursoId"=curso_id;

	IF NOT FOUND THEN
		RAISE EXCEPTION 'El grado académico indicando no está registrado';
	END IF;

	-- Verificando que se registren duplicados
	PERFORM "EstudianteId" FROM "CursoEstudiante" WHERE "EstudianteId"=estudiante_id AND "CursoId"=curso_id;

	IF FOUND THEN
		RAISE EXCEPTION 'El estudiante ya se encuentra registrado en ese grado academico';
	END IF;

	-- Cargar año escolar actual
	SELECT "PeriodoEscolarId" INTO periodo_escolar_id FROM "PeriodoEscolar" ORDER BY "FechaInicio" DESC LIMIT 1;

	-- Obteniendo datos para calcular la sección correspondiente al estudiante
	SELECT COUNT("EstudianteId") INTO total_estudiantes FROM "CursoEstudiante" WHERE "CursoId"=curso_id AND "PeriodoEscolarId"=periodo_escolar_id;
	SELECT "CapacidadSecciones" INTO estudiantes_por_seccion FROM "PeriodoEscolar" WHERE "PeriodoEscolarId"=periodo_escolar_id;

	-- Calculando y asignando sección al estudiante
	IF total_estudiantes = 0 THEN
		seccion := 1;
	ELSE
		seccion := ceil(total_estudiantes/estudiantes_por_seccion);
	END IF;

	-- Creando registro
	INSERT INTO "CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId")
	VALUES
	(estudiante_id, curso_id, seccion, periodo_escolar_id);

	IF NOT FOUND THEN
		RAISE EXCEPTION 'Ocurrió un error al registrar el grado del estudiante';
	END IF;
END;
$$ LANGUAGE plpgsql;
