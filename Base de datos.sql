--
-- PostgreSQL database dump
--

\restrict 5ZrAC0uiFsilZqP4AN4hZDrU3gCC4GDVHFoD2wsqIjdalEZHPcGlszatxZHPcZN

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

-- Started on 2026-02-17 11:55:41

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 24665)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 5137 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- TOC entry 2 (class 3079 OID 24666)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 5139 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 890 (class 1247 OID 24702)
-- Name: dia; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.dia AS ENUM (
    'Lunes',
    'Martes',
    'Miércoles',
    'Jueves',
    'Viernes'
);


ALTER TYPE public.dia OWNER TO postgres;

--
-- TOC entry 887 (class 1247 OID 24692)
-- Name: estado_estudiante; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estado_estudiante AS ENUM (
    'revision',
    'inscrito',
    'retirado',
    'graduado',
    'rechazado'
);


ALTER TYPE public.estado_estudiante OWNER TO postgres;

--
-- TOC entry 881 (class 1247 OID 24678)
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.rol_usuario AS ENUM (
    'representante',
    'docente',
    'administrador'
);


ALTER TYPE public.rol_usuario OWNER TO postgres;

--
-- TOC entry 884 (class 1247 OID 24686)
-- Name: sexo; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.sexo AS ENUM (
    'Masculino',
    'Femenino'
);


ALTER TYPE public.sexo OWNER TO postgres;

--
-- TOC entry 893 (class 1247 OID 24714)
-- Name: tipo_parentesco; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.tipo_parentesco AS ENUM (
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


ALTER TYPE public.tipo_parentesco OWNER TO postgres;

--
-- TOC entry 259 (class 1255 OID 25069)
-- Name: registrar_curso_estudiante(uuid, uuid); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.registrar_curso_estudiante(IN estudiante_id uuid, IN curso_id uuid)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER PROCEDURE public.registrar_curso_estudiante(IN estudiante_id uuid, IN curso_id uuid) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 24746)
-- Name: Asistencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Asistencia" (
    "AsistenciaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "EstudianteId" uuid NOT NULL,
    "ClaseId" uuid NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Asistencia" OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 24928)
-- Name: Auditoria; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Auditoria" (
    "AuditoriaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "UsuarioId" uuid NOT NULL,
    "Descripcion" character varying NOT NULL,
    "Accion" character varying NOT NULL,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Auditoria" OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 24781)
-- Name: BloqueHorario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."BloqueHorario" (
    "BloqueHorarioId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "HoraInicio" time without time zone NOT NULL,
    "HoraFin" time without time zone NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."BloqueHorario" OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 24733)
-- Name: Clase; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Clase" (
    "ClaseId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "DocenteId" uuid NOT NULL,
    "CursoId" uuid NOT NULL,
    "PeriodoEscolarId" uuid NOT NULL,
    "Seccion" integer NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Clase" OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 24894)
-- Name: Curso; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Curso" (
    "CursoId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Grado" integer NOT NULL,
    CONSTRAINT ck_curso_grado CHECK ((("Grado" >= 1) AND ("Grado" <= 5)))
);


ALTER TABLE public."Curso" OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 24836)
-- Name: CursoEstudiante; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."CursoEstudiante" (
    "EstudianteId" uuid NOT NULL,
    "CursoId" uuid NOT NULL,
    "Seccion" smallint NOT NULL,
    "PeriodoEscolarId" uuid NOT NULL,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."CursoEstudiante" OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 24804)
-- Name: DatosPersona; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."DatosPersona" (
    "DatosPersonaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Nombre" character varying NOT NULL,
    "Apellido" character varying NOT NULL,
    "Sexo" public.sexo NOT NULL,
    "Cedula" integer,
    "Telefono" character varying(12),
    "Direccion" character varying(100),
    "Ocupacion" character varying(50),
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."DatosPersona" OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 24869)
-- Name: Docente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Docente" (
    "DocenteId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "DatosPersonaId" uuid NOT NULL,
    "MateriaId" uuid NOT NULL,
    "HorasAcademicas" smallint DEFAULT 20 NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp(),
    CONSTRAINT docente_minimo_horas_academicas CHECK (("HorasAcademicas" >= 20))
);


ALTER TABLE public."Docente" OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 24846)
-- Name: EstadoEstudiante; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."EstadoEstudiante" (
    "EstadoEstudianteId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "EstudianteId" uuid NOT NULL,
    "Estado" public.estado_estudiante DEFAULT 'revision'::public.estado_estudiante,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."EstadoEstudiante" OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 24822)
-- Name: Estudiante; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Estudiante" (
    "EstudianteId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "FechaNacimiento" date NOT NULL,
    "Parentesco" public.tipo_parentesco DEFAULT 'Tutor Legal'::public.tipo_parentesco NOT NULL,
    "DatosPersonaId" uuid NOT NULL,
    "RepresentanteId" uuid NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Estudiante" OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 24769)
-- Name: Horario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Horario" (
    "HorarioId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "CursoId" uuid NOT NULL,
    "PeriodoEscolarId" uuid NOT NULL,
    "Seccion" smallint NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Horario" OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 24792)
-- Name: HorarioItem; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."HorarioItem" (
    "HorarioItemId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Dia" public.dia NOT NULL,
    "DocenteId" uuid,
    "Actividad" character varying(20),
    "Activo" boolean DEFAULT true,
    "HorarioId" uuid NOT NULL,
    "BloqueHorarioId" uuid NOT NULL,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."HorarioItem" OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 24941)
-- Name: Incidencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Incidencia" (
    "IncidenciaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "DatosPersonaId" uuid NOT NULL,
    "Descripcion" character varying NOT NULL,
    "Documento" character varying NOT NULL,
    "Fecha" date NOT NULL
);


ALTER TABLE public."Incidencia" OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 24757)
-- Name: Materia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Materia" (
    "MateriaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Nombre" character varying(50) NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Materia" OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 24856)
-- Name: Nota; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Nota" (
    "NotaId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Ponderacion" smallint NOT NULL,
    "Lapso" smallint NOT NULL,
    "MateriaId" uuid NOT NULL,
    "EstudianteId" uuid NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp(),
    CONSTRAINT ck_nota_lapso CHECK ((("Lapso" >= 1) AND ("Lapso" <= 3))),
    CONSTRAINT ck_nota_ponderacion CHECK ((("Ponderacion" >= 0) AND ("Ponderacion" <= 20)))
);


ALTER TABLE public."Nota" OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 24882)
-- Name: PeriodoEscolar; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."PeriodoEscolar" (
    "PeriodoEscolarId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "FechaInicio" date NOT NULL,
    "FechaFin" date NOT NULL,
    "CapacidadSecciones" integer NOT NULL,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp(),
    "Activo" boolean DEFAULT true
);


ALTER TABLE public."PeriodoEscolar" OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 24902)
-- Name: PeriodoInscripcion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."PeriodoInscripcion" (
    "PeriodoInscripcion" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Inicio" date NOT NULL,
    "Fin" date NOT NULL,
    "PeriodoEscolarId" uuid NOT NULL,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."PeriodoInscripcion" OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 24914)
-- Name: Usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Usuario" (
    "UsuarioId" uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "Email" character varying NOT NULL,
    "Clave" character varying NOT NULL,
    "Rol" public.rol_usuario NOT NULL,
    "DatosPersona" uuid,
    "Activo" boolean DEFAULT true,
    "FechaCreacion" timestamp without time zone DEFAULT clock_timestamp()
);


ALTER TABLE public."Usuario" OWNER TO postgres;

--
-- TOC entry 5115 (class 0 OID 24746)
-- Dependencies: 221
-- Data for Name: Asistencia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Asistencia" ("AsistenciaId", "EstudianteId", "ClaseId", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5130 (class 0 OID 24928)
-- Dependencies: 236
-- Data for Name: Auditoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Auditoria" ("AuditoriaId", "UsuarioId", "Descripcion", "Accion", "FechaCreacion") FROM stdin;
766f01fe-5157-4632-8291-c045e993cd10	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 18:14:30.023705
b797b073-685e-419a-a6a5-3ed3eaa0106c	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Usuario representante creado	Registro	2026-02-12 18:16:09.442972
fbb9ae9b-6084-467e-b314-df009fa8bd6a	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 18:16:38.47421
984fad4a-f276-47eb-9aec-a8c557ebd847	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 18:17:29.996979
46b449f2-5a39-422b-b72c-d55bb3a13e5f	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 18:17:41.486906
1e892fc9-e5d7-4803-8fbc-5aa742f75e23	f31e41bb-359c-442e-9bc3-a048629348ba	Establecido período escolar 2026-2027	Registro	2026-02-12 18:18:18.637024
4c3bd89c-14ba-4d69-9adc-7bdd546dc13d	f31e41bb-359c-442e-9bc3-a048629348ba	Período de inscripción creado	Registro	2026-02-12 18:18:49.627214
85d7f8a5-4926-4ea8-990a-8fba7bcf6f12	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 18:19:02.086385
707da748-6e26-4a0b-9423-c3aae0f93d61	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Se registro un nuevo estudiante	Registro	2026-02-12 18:19:40.954791
4aadee82-b862-40b2-8c6d-e01af5e7d4f5	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 18:20:22.845878
9e8edd2c-9159-4b1e-b3ea-20490be83992	75cef52a-673c-4cac-88d8-610e6991eb24	Usuario representante creado	Registro	2026-02-12 18:21:19.016552
6a80c825-d5d9-48d8-9a0b-9567b7cc2c30	75cef52a-673c-4cac-88d8-610e6991eb24	Inicio de sesión realizado	Sesión	2026-02-12 18:25:37.207208
95312aca-cce8-4dec-8ea7-b6c6ff0abe85	75cef52a-673c-4cac-88d8-610e6991eb24	Se registro un nuevo estudiante	Registro	2026-02-12 18:27:37.532944
c695fb69-8663-459a-ab42-0f9c3b26a319	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 18:27:46.2898
f09397a2-0420-4436-9b96-b6a24d87a989	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 18:48:00.948773
f43ddc77-7aa6-4030-9040-be4bb9471ae3	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 18:51:20.21554
4df41d48-8014-47d0-8fc0-72b23ba57d8f	f31e41bb-359c-442e-9bc3-a048629348ba	Período de inscripción creado	Registro	2026-02-12 18:53:33.911649
af04bccb-b8b4-4859-8144-5f2621ce2d41	75cef52a-673c-4cac-88d8-610e6991eb24	Inicio de sesión realizado	Sesión	2026-02-12 19:07:53.384587
3c79c5cb-3d75-4962-ba81-b0706b54c4a5	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 19:48:15.344651
d4d4a970-1d5f-4695-a4f7-4f25af8063bb	5b4bd651-a848-4bfb-b6f4-67a3ab2935af	Usuario representante creado	Registro	2026-02-12 19:49:07.964188
bfa68230-429c-4cd9-bac3-9c1d5d59764b	5b4bd651-a848-4bfb-b6f4-67a3ab2935af	Inicio de sesión realizado	Sesión	2026-02-12 19:49:27.530314
1c4a9157-d88e-430b-be12-2b5c8c6160a7	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:03:52.185394
4d5515ba-04a3-4ab9-af90-a50815583b1d	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 20:15:14.369602
c4816a58-4aee-4e73-8384-fd581d7dd61c	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:16:33.024546
84db6345-2dcd-4d54-8433-9a93fde6e01d	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:21:51.657077
07906af1-440d-45a2-aaac-5a67398e1068	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 20:22:01.528406
c45c0f12-2a1b-40fc-9087-e3e93ba41d05	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:23:13.223832
b62bc9d7-d3ec-4f2c-9e8c-7ae0fe4378ee	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 20:39:30.654955
1dd4d2a8-0937-4f73-be2d-420c144708cb	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:40:24.12587
bc9ea742-36c7-4f72-abe6-f189a9702759	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 20:52:28.315949
0f04af4d-13aa-4cf2-9263-f4c54f7cb291	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:00:44.175806
f364e9ea-e46d-4c2b-bda9-e3f38e05f571	bfd01c4a-61a4-4ffd-a11b-8800ce02e98b	Usuario representante creado	Registro	2026-02-12 21:09:46.33909
ddc5ca74-dede-423f-b94b-baf266e70965	bfd01c4a-61a4-4ffd-a11b-8800ce02e98b	Inicio de sesión realizado	Sesión	2026-02-12 21:10:04.701863
654c5869-ab28-46d0-8188-478925be5c23	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:21:37.974965
2951f895-1648-4665-8372-d89c68968bbf	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 21:22:16.642251
9be4f7ee-e038-4db5-b734-ea5ce16fc32d	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:30:12.293482
2ae0d9ba-6e9b-44a9-921e-e088962eba10	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:30:47.322482
c70a27f4-b666-40c2-aee7-82f6ca91b08b	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:50:01.949898
55b766be-adc5-4402-ad84-774366c7e0df	6dfdc9d5-4dcb-414c-9037-9ba0a1059972	Usuario representante creado	Registro	2026-02-12 21:50:57.904415
c4f0c0f2-1559-4104-b180-dac017c1fd12	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:52:41.577984
88e3337c-9113-4365-9a97-a1a0ffbecdbb	6dfdc9d5-4dcb-414c-9037-9ba0a1059972	Inicio de sesión realizado	Sesión	2026-02-12 21:53:48.648899
4330b27f-a3f7-4713-a7aa-3970dc7afc82	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 21:58:07.124972
72ee810c-ccfb-41f6-b9f2-394e4bdbabe9	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 22:00:19.753815
4060f102-dbf8-4955-a5ec-1fc84b6e062d	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-12 22:32:08.53248
99987332-52ef-40f0-90af-b670f0dd860c	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-12 22:32:20.453716
4f5403d1-0aaa-4642-81e6-2e682fc8112c	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 01:22:42.871074
1f652f17-ee25-4e49-b608-23170e349f24	2d99ceda-e6e9-47d4-9eea-44a20be0a447	Usuario representante creado	Registro	2026-02-13 01:39:35.314106
2181c7e6-8c9c-4852-a6e0-0d3c7291a50b	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 01:40:36.442404
c3278d1c-a8cd-4461-970e-9687b38cfb94	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 01:43:58.706355
e1725c33-16b9-454f-ac55-49ddc02d5b09	f31e41bb-359c-442e-9bc3-a048629348ba	Período de inscripción creado	Registro	2026-02-13 01:44:59.013556
473e9d93-4603-4109-b2c0-9fce7ef397bc	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 01:45:24.190085
141a8608-1721-469d-9fb9-5992f2905e73	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 01:45:40.532897
03e0091a-6603-46be-b4fa-c96aa9b7317e	f31e41bb-359c-442e-9bc3-a048629348ba	Período de inscripción creado	Registro	2026-02-13 01:51:05.362975
0fd5783e-4cfb-486a-a52a-81174ca31038	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 01:51:16.444432
3049acc7-b6ea-43f7-9eb5-bc58cf99d67a	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 01:52:14.400813
28952e99-1792-4c17-a7dd-c5c928e73c4d	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 01:56:11.299902
314d0d12-d320-487c-a30d-613d807b3109	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 01:56:22.076727
96da0451-7c16-41e2-bd39-045fd13130b1	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 02:05:47.101184
4e05f5b0-05ba-4e1f-9cb8-ea9b75c4c6a7	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 02:14:25.342995
af50a5dc-b5e7-4b91-a6ce-b1d5a32decb5	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 02:14:54.147255
545797e4-4986-4d3d-bdd4-e95a026802a9	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 02:24:33.496815
1f846874-d906-4a78-8da2-f3cd3e7cf30b	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 02:25:34.719101
20c6f96e-3fc2-412d-8b5a-8be0391e2dcf	c7ffb961-ca74-4869-aa15-ac85036186be	Usuario representante creado	Registro	2026-02-13 02:46:05.802413
4bbff93e-7c03-4bbe-8e7a-a4f4699fe5a3	c7ffb961-ca74-4869-aa15-ac85036186be	Inicio de sesión realizado	Sesión	2026-02-13 02:46:43.067107
61fbf2f4-6366-47ab-ac53-7777cf0d46ec	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 02:49:50.779036
3b1cc698-3ed4-4f11-bf04-cc0e38b4079b	c7ffb961-ca74-4869-aa15-ac85036186be	Inicio de sesión realizado	Sesión	2026-02-13 02:50:50.842536
99448ec1-c74b-4f6a-8101-f835af09b27b	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 03:04:17.713569
3d789e50-9e96-4f5d-ac59-f1e1f47833cf	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 03:51:43.278377
f04f0cc3-48c4-4a08-a155-79c5cc371145	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 08:21:46.618577
02ba9dc7-c7ee-40a4-ba71-22b0af2117ff	e9c5cdee-b94b-45d7-ad6d-5f172423dcda	Usuario representante creado	Registro	2026-02-13 08:23:55.550572
5ed779a8-ad23-4088-8f1f-5deec07d31bf	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 08:24:30.037413
ecc58dd1-b4fd-4bd1-9f80-7870a3ef53d4	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 08:24:46.887994
c8ea2189-a1fb-46e1-8d04-2411aa2ba19d	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 08:25:21.269503
347d2c80-6265-4643-b079-971460c6fe13	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 08:26:09.903896
a531372e-3aee-4be4-ba98-2a6d640e920b	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 08:34:31.010703
061bb341-2361-4096-b18b-68dbd9c69cfc	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 08:59:00.72998
3d2c6960-07a0-4bac-8566-a4a82ea952b1	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 09:00:53.759754
2515d540-0bc5-4eb4-b9da-6eeddb72d59c	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 09:00:57.573001
f20b7239-d174-44f6-a66e-41fcc85ce37a	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 09:01:06.468531
062f505b-c9a5-498f-9318-a13a807c8c15	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-13 09:02:24.228312
823800ed-627c-46f5-80c1-d53e6be51712	f481eed0-22ee-473e-8128-cd0550053210	Usuario representante creado	Registro	2026-02-13 09:22:08.450476
fcced219-4299-4159-ac70-d7f09bba4200	54b70f95-d576-40fa-88f5-17d45b8f5ec0	Inicio de sesión realizado	Sesión	2026-02-13 09:22:31.789617
95d16f84-fd07-4ffb-977e-0ebc9746f54a	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-17 11:14:45.73024
c6355853-0d1a-462b-a934-32f61db16922	f31e41bb-359c-442e-9bc3-a048629348ba	Inicio de sesión realizado	Sesión	2026-02-17 11:29:42.442271
\.


--
-- TOC entry 5118 (class 0 OID 24781)
-- Dependencies: 224
-- Data for Name: BloqueHorario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."BloqueHorario" ("BloqueHorarioId", "HoraInicio", "HoraFin", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5114 (class 0 OID 24733)
-- Dependencies: 220
-- Data for Name: Clase; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Clase" ("ClaseId", "DocenteId", "CursoId", "PeriodoEscolarId", "Seccion", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5127 (class 0 OID 24894)
-- Dependencies: 233
-- Data for Name: Curso; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Curso" ("CursoId", "Grado") FROM stdin;
3f32a31d-7983-49a2-91dd-7f043d8ff961	1
c2cb75bd-5ba6-4a12-a422-0148e591e6dc	2
c4f3a499-d63c-4891-b90f-af3401af950f	3
ba7f6e5c-5129-4c06-8e4a-c9b89a2ed603	4
81261a5a-9f5f-4d0f-b046-39e078af993b	5
\.


--
-- TOC entry 5122 (class 0 OID 24836)
-- Dependencies: 228
-- Data for Name: CursoEstudiante; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId", "FechaCreacion") FROM stdin;
31571a64-0b47-4395-843f-6ae2909b7d83	c2cb75bd-5ba6-4a12-a422-0148e591e6dc	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 18:19:40.953588
79cc6094-65c9-49d6-a1fc-6bd713782dde	3f32a31d-7983-49a2-91dd-7f043d8ff961	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 18:27:37.532166
c35b41da-1bcf-4980-a693-ef508610f358	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 19:12:08.361681
857c5e0e-9835-4b6f-bde8-d5d4aca530c1	c2cb75bd-5ba6-4a12-a422-0148e591e6dc	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 19:13:22.419206
92cfbc91-6f59-43c9-8417-a323be41ddbd	c4f3a499-d63c-4891-b90f-af3401af950f	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:00:44.979142
4c3ec1b9-bc20-4833-bd1c-d963001a96f1	ba7f6e5c-5129-4c06-8e4a-c9b89a2ed603	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:02:19.523692
5fbb8ce3-ebe9-4fec-8b5d-0bae2d4bd13c	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:03:38.575169
3be4c6fc-bc01-4e97-8f09-7a82db4ccecd	c4f3a499-d63c-4891-b90f-af3401af950f	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:16:17.243634
e22beece-8a35-4f9b-afd3-994acc0d3902	c4f3a499-d63c-4891-b90f-af3401af950f	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:22:58.420596
5abccd71-d1ad-4a37-a789-8f23201ead18	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 20:40:11.853891
ece253aa-add8-47e8-9563-9ad462cbe585	c4f3a499-d63c-4891-b90f-af3401af950f	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 21:11:22.217953
3f1959f5-6236-484f-8d4d-055937a530f2	c4f3a499-d63c-4891-b90f-af3401af950f	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 21:21:05.135154
86c6f6f7-0b65-4ff7-a41f-09620998e24f	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-12 21:56:24.184911
ddd107d1-66e5-4907-9aba-f77481c07f21	c2cb75bd-5ba6-4a12-a422-0148e591e6dc	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 01:51:54.148805
0d27dd22-efa3-44bd-872d-848a45bc7fe9	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 02:48:30.621063
301a2cce-966f-4af0-9d72-b55719c935dd	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 03:01:57.933465
74d1eb61-2495-4c2e-946c-7482ec3b9933	3f32a31d-7983-49a2-91dd-7f043d8ff961	0	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 08:36:36.138072
bd04143b-b17a-44ed-9a52-1326c513a64d	c2cb75bd-5ba6-4a12-a422-0148e591e6dc	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 08:57:36.7346
9e18b0cb-7b9a-45c5-babc-c56c96c825e0	c4f3a499-d63c-4891-b90f-af3401af950f	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 09:02:03.14123
7d8ce0c3-11c8-4d02-98ce-f73c8c208e48	3f32a31d-7983-49a2-91dd-7f043d8ff961	1	6970427c-4d91-433e-b85a-0a5591f39b90	2026-02-13 09:23:19.482951
\.


--
-- TOC entry 5120 (class 0 OID 24804)
-- Dependencies: 226
-- Data for Name: DatosPersona; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."DatosPersona" ("DatosPersonaId", "Nombre", "Apellido", "Sexo", "Cedula", "Telefono", "Direccion", "Ocupacion", "Activo", "FechaCreacion") FROM stdin;
93d88d53-91fb-4a92-8f7d-c325d860288e	Natasha	Gainza	Femenino	35210415	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-12 18:19:40.949602
b417acee-d29a-4b88-8b96-1a62ab490d5b	Luis	Maracara	Masculino	14104198	0412-2415263	Calle 11, av 2, maracay estado aragua	Mecanico	t	2026-02-12 18:21:18.637672
97b03df6-fd75-445d-b47e-cb699d8e0c8f	Lucia Fernanda	Gainza	Femenino	36521415	\N	Calle 11, av 2, maracay estado aragua	\N	t	2026-02-12 18:27:37.530308
7a68b5f6-1b66-42c9-aa8e-bac5e453be2d	Natasha	Gainza	Masculino	0	\N	Calle 11, av 2, maracay estado aragua	\N	t	2026-02-12 19:12:08.357665
61456484-050f-4c80-b4b9-0594b5dcf0c5	Natasha	Gainza	Masculino	5222225	\N	Calle 11, av 2, maracay estado aragua	\N	t	2026-02-12 19:13:22.417098
aabdc5cf-ab69-4eb5-8f74-c6b1b14e79d1	Abelardo	Rodriguez	Masculino	9641039	0412-3217085	Calle principal del arsenal, sector B2, Maracay	Ingeniero	t	2026-02-12 19:49:07.602831
bd7bcb17-c9a4-4591-bc19-1686f9b776d8	Natasha	Gainza	Femenino	32140120	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 20:00:44.975682
859e710f-5b59-42cd-8a89-d268535ea418	Ruben	Vladimia	Masculino	21410152	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 20:02:19.521949
760b0460-03fe-4b4a-bd3d-ca3e3e689af7	sara	Gonzales	Femenino	1	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 20:03:38.568429
cd5dda31-63b4-4b69-8ed2-e009f0fbc6c5	Luisa	Gainza	Femenino	32141525	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-12 20:16:17.240495
44f90c2a-6c23-4323-aac7-411cf6f40765	Natasha	Gainza	Masculino	38525412	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-12 20:40:11.851941
2de2e3eb-3990-4134-8488-3fefd9af9f7e	Natasha	Gainza	Masculino	15533590	0412-3217015	Calle principal del arsenal, sector B2, Maracay	Profesora	t	2026-02-12 21:09:45.977793
a5b8f93a-bd84-4354-b67e-f98f8f0e7695	lEGARDA	JOSE	Femenino	32141404	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 21:11:22.216264
fb4ee63c-293a-4d35-b793-86cf69c5b287	Natasha	Gainza	Femenino	20102	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 21:21:05.133368
d397cbd5-fb9b-4549-ac58-0b72ef7ac019	Daniel Del Valle	Calles Rodriguez	Masculino	14104192	0424-3201452	Calle principal del arsenal, sector B2, Maracay	Profesor	t	2026-02-12 21:50:57.522774
f5686498-acb5-4da9-b10d-eef622d6273f	Natasha	Gainza	Femenino	40251325	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-12 21:56:24.182875
3e6e881f-de2e-4a0d-a178-aaf48b32810e	Natasha	Gainza	Femenino	14104195	\N	\N	\N	t	2026-02-13 01:39:34.946739
f33351f4-743e-437f-9041-49b646181034	Natasha	Gainza	Masculino	35212412	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-13 01:51:54.143576
ccbed922-5309-4225-9c93-8aa7155313a4	Natasha	Gainza	Femenino	26792705	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-12 20:22:58.418803
b635b488-8f4e-4c63-9067-2bbc25fc1c22	Natasha	Gainza	Femenino	25770181	0412-3217086	Calle principal del arsenal, sector B2, Maracay	Empresaria	t	2026-02-13 02:46:05.439649
3b877c7b-34a4-4698-9480-6e48ec726431	ANDRI	BAPTISTA	Masculino	31564681	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-13 02:48:30.616635
5a1ffb60-14b5-4c85-b531-d155b505b723	Natasha	Gainza	Femenino	25770182	\N	Calle principal del arsenal, sector B2, Maracay	\N	t	2026-02-13 03:01:57.93032
eb026e31-6a90-41d4-bfe9-d4c2d04df75f	Natasha	Gainza	Masculino	14104165	\N	\N	\N	t	2026-02-13 08:23:55.170665
464873e5-ebe0-41e9-8f0a-410fdf35e01b	Natasha	Gainza	Masculino	25415215	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-13 08:36:36.097696
ae51c3ee-f391-4baa-a091-af1f3baa2b83	daniel	mongresut	Masculino	315648212	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-13 08:57:36.731077
a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	Natasha	Gainza	Femenino	26792706	0424-3217086	Calle los chaguaramos, edificio 11, quinto piso	profesor	t	2026-02-12 18:16:09.06178
bd342650-1272-400d-bc1b-5f1fc8b9e384	jose	area	Masculino	23346843	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-13 09:02:03.139131
e6dd3fb7-bf77-44ed-ac7a-484b94a4d32c	Natasha	Gainza	Masculino	2541252	\N	\N	\N	t	2026-02-13 09:22:08.065209
92c72cfd-98d7-4c44-89dc-5ebf5c220467	ruben	Gainza	Masculino	141410402	\N	Calle los chaguaramos, edificio 11, quinto piso	\N	t	2026-02-13 09:23:19.480925
\.


--
-- TOC entry 5125 (class 0 OID 24869)
-- Dependencies: 231
-- Data for Name: Docente; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Docente" ("DocenteId", "DatosPersonaId", "MateriaId", "HorasAcademicas", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5123 (class 0 OID 24846)
-- Dependencies: 229
-- Data for Name: EstadoEstudiante; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."EstadoEstudiante" ("EstadoEstudianteId", "EstudianteId", "Estado", "FechaCreacion") FROM stdin;
19f80c2c-aea5-44fa-a12f-b77760db881a	31571a64-0b47-4395-843f-6ae2909b7d83	rechazado	2026-02-12 18:19:40.951344
98d10039-a1e6-4d11-9b2a-dc49be83a14e	3be4c6fc-bc01-4e97-8f09-7a82db4ccecd	inscrito	2026-02-12 20:16:17.242212
458fcaa9-8a6b-43dd-a278-9b9f84138127	ece253aa-add8-47e8-9563-9ad462cbe585	rechazado	2026-02-12 21:11:22.217636
a4f9ad9a-7791-456f-99d7-8b623f59fddb	c35b41da-1bcf-4980-a693-ef508610f358	rechazado	2026-02-12 19:12:08.359202
0d254ccc-6e65-4c7a-8698-863c9e165389	0d27dd22-efa3-44bd-872d-848a45bc7fe9	revision	2026-02-13 02:48:30.618013
f92a0ae2-4048-4223-a8b5-ba0a2e032bfb	301a2cce-966f-4af0-9d72-b55719c935dd	revision	2026-02-13 03:01:57.932968
cf9379a5-cee9-4990-8457-8f90f44729f8	5abccd71-d1ad-4a37-a789-8f23201ead18	retirado	2026-02-12 20:40:11.85347
92dfecd7-6c36-488e-a4ae-2646ba7b46ce	857c5e0e-9835-4b6f-bde8-d5d4aca530c1	retirado	2026-02-12 19:13:22.418867
17f3d0f1-9899-4e83-a318-5865f5b1133d	e22beece-8a35-4f9b-afd3-994acc0d3902	inscrito	2026-02-12 20:22:58.420231
6548bb0e-ba31-4239-8c2a-8da9a99f47aa	5fbb8ce3-ebe9-4fec-8b5d-0bae2d4bd13c	inscrito	2026-02-12 20:03:38.570144
a8f3ef55-8251-4a1e-a9f9-38297dba8cc0	4c3ec1b9-bc20-4833-bd1c-d963001a96f1	inscrito	2026-02-12 20:02:19.523344
fc968bed-b270-4428-8c39-a20d05a7565c	79cc6094-65c9-49d6-a1fc-6bd713782dde	retirado	2026-02-12 18:27:37.531827
9d4d8df5-37c4-45c5-8a49-934298b6e8e2	ddd107d1-66e5-4907-9aba-f77481c07f21	inscrito	2026-02-13 01:51:54.145424
b145a589-4467-4a73-95fe-1ef7cf9b7f34	92cfbc91-6f59-43c9-8417-a323be41ddbd	inscrito	2026-02-12 20:00:44.977238
69c98a46-d26c-47d6-a2e8-bb98713bfc3b	3f1959f5-6236-484f-8d4d-055937a530f2	rechazado	2026-02-12 21:21:05.134832
2c253081-f5ce-4215-8e6f-1fbae5fee04b	bd04143b-b17a-44ed-9a52-1326c513a64d	inscrito	2026-02-13 08:57:36.73321
92329e8a-54c9-453b-b72a-5cd48e66a2a3	9e18b0cb-7b9a-45c5-babc-c56c96c825e0	rechazado	2026-02-13 09:02:03.140604
c0aa4618-885c-409f-9f0e-fefe3fe0782f	7d8ce0c3-11c8-4d02-98ce-f73c8c208e48	revision	2026-02-13 09:23:19.482309
84e54697-46b1-4a6c-88f1-299d33be7562	74d1eb61-2495-4c2e-946c-7482ec3b9933	rechazado	2026-02-13 08:36:36.099391
8cae5139-54de-4801-82bb-8c93fd5d179a	86c6f6f7-0b65-4ff7-a41f-09620998e24f	inscrito	2026-02-12 21:56:24.184518
\.


--
-- TOC entry 5121 (class 0 OID 24822)
-- Dependencies: 227
-- Data for Name: Estudiante; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Estudiante" ("EstudianteId", "FechaNacimiento", "Parentesco", "DatosPersonaId", "RepresentanteId", "Activo", "FechaCreacion") FROM stdin;
31571a64-0b47-4395-843f-6ae2909b7d83	2013-02-06	Tutor Legal	93d88d53-91fb-4a92-8f7d-c325d860288e	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	f	2026-02-12 18:19:40.950279
3be4c6fc-bc01-4e97-8f09-7a82db4ccecd	2011-07-31	Abuelo/a	cd5dda31-63b4-4b69-8ed2-e009f0fbc6c5	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-12 20:16:17.241319
ece253aa-add8-47e8-9563-9ad462cbe585	2012-02-01	Abuelo/a	a5b8f93a-bd84-4354-b67e-f98f8f0e7695	2de2e3eb-3990-4134-8488-3fefd9af9f7e	f	2026-02-12 21:11:22.216953
c35b41da-1bcf-4980-a693-ef508610f358	2011-02-02	Abuelo/a	7a68b5f6-1b66-42c9-aa8e-bac5e453be2d	b417acee-d29a-4b88-8b96-1a62ab490d5b	f	2026-02-12 19:12:08.358338
0d27dd22-efa3-44bd-872d-848a45bc7fe9	2011-02-20	Madre	3b877c7b-34a4-4698-9480-6e48ec726431	b635b488-8f4e-4c63-9067-2bbc25fc1c22	t	2026-02-13 02:48:30.617264
301a2cce-966f-4af0-9d72-b55719c935dd	2015-02-03	Madre	5a1ffb60-14b5-4c85-b531-d155b505b723	b635b488-8f4e-4c63-9067-2bbc25fc1c22	t	2026-02-13 03:01:57.931349
5abccd71-d1ad-4a37-a789-8f23201ead18	2011-02-01	Padre	44f90c2a-6c23-4323-aac7-411cf6f40765	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	f	2026-02-12 20:40:11.85269
857c5e0e-9835-4b6f-bde8-d5d4aca530c1	2010-03-31	Madre	61456484-050f-4c80-b4b9-0594b5dcf0c5	b417acee-d29a-4b88-8b96-1a62ab490d5b	f	2026-02-12 19:13:22.417956
e22beece-8a35-4f9b-afd3-994acc0d3902	2010-02-11	Madre	ccbed922-5309-4225-9c93-8aa7155313a4	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-12 20:22:58.419441
5fbb8ce3-ebe9-4fec-8b5d-0bae2d4bd13c	2011-05-06	Tío/a	760b0460-03fe-4b4a-bd3d-ca3e3e689af7	aabdc5cf-ab69-4eb5-8f74-c6b1b14e79d1	t	2026-02-12 20:03:38.569388
4c3ec1b9-bc20-4833-bd1c-d963001a96f1	2011-02-28	Madre	859e710f-5b59-42cd-8a89-d268535ea418	aabdc5cf-ab69-4eb5-8f74-c6b1b14e79d1	t	2026-02-12 20:02:19.522542
79cc6094-65c9-49d6-a1fc-6bd713782dde	2011-02-28	Madre	97b03df6-fd75-445d-b47e-cb699d8e0c8f	b417acee-d29a-4b88-8b96-1a62ab490d5b	f	2026-02-12 18:27:37.531058
ddd107d1-66e5-4907-9aba-f77481c07f21	2011-06-08	Madre	f33351f4-743e-437f-9041-49b646181034	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-13 01:51:54.144334
92cfbc91-6f59-43c9-8417-a323be41ddbd	2011-03-19	Madre	bd7bcb17-c9a4-4591-bc19-1686f9b776d8	aabdc5cf-ab69-4eb5-8f74-c6b1b14e79d1	t	2026-02-12 20:00:44.976364
3f1959f5-6236-484f-8d4d-055937a530f2	2011-02-02	Padre	fb4ee63c-293a-4d35-b793-86cf69c5b287	2de2e3eb-3990-4134-8488-3fefd9af9f7e	f	2026-02-12 21:21:05.134028
bd04143b-b17a-44ed-9a52-1326c513a64d	2012-07-20	Madre	ae51c3ee-f391-4baa-a091-af1f3baa2b83	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-13 08:57:36.731917
9e18b0cb-7b9a-45c5-babc-c56c96c825e0	2015-11-20	Madre	bd342650-1272-400d-bc1b-5f1fc8b9e384	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	f	2026-02-13 09:02:03.139909
7d8ce0c3-11c8-4d02-98ce-f73c8c208e48	2013-01-30	Madre	92c72cfd-98d7-4c44-89dc-5ebf5c220467	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-13 09:23:19.481602
74d1eb61-2495-4c2e-946c-7482ec3b9933	2011-02-20	Madre	464873e5-ebe0-41e9-8f0a-410fdf35e01b	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	f	2026-02-13 08:36:36.0986
86c6f6f7-0b65-4ff7-a41f-09620998e24f	2013-01-30	Madre	f5686498-acb5-4da9-b10d-eef622d6273f	d397cbd5-fb9b-4549-ac58-0b72ef7ac019	t	2026-02-12 21:56:24.183634
\.


--
-- TOC entry 5117 (class 0 OID 24769)
-- Dependencies: 223
-- Data for Name: Horario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Horario" ("HorarioId", "CursoId", "PeriodoEscolarId", "Seccion", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5119 (class 0 OID 24792)
-- Dependencies: 225
-- Data for Name: HorarioItem; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."HorarioItem" ("HorarioItemId", "Dia", "DocenteId", "Actividad", "Activo", "HorarioId", "BloqueHorarioId", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5131 (class 0 OID 24941)
-- Dependencies: 237
-- Data for Name: Incidencia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Incidencia" ("IncidenciaId", "DatosPersonaId", "Descripcion", "Documento", "Fecha") FROM stdin;
\.


--
-- TOC entry 5116 (class 0 OID 24757)
-- Dependencies: 222
-- Data for Name: Materia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Materia" ("MateriaId", "Nombre", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5124 (class 0 OID 24856)
-- Dependencies: 230
-- Data for Name: Nota; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Nota" ("NotaId", "Ponderacion", "Lapso", "MateriaId", "EstudianteId", "Activo", "FechaCreacion") FROM stdin;
\.


--
-- TOC entry 5126 (class 0 OID 24882)
-- Dependencies: 232
-- Data for Name: PeriodoEscolar; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."PeriodoEscolar" ("PeriodoEscolarId", "FechaInicio", "FechaFin", "CapacidadSecciones", "FechaCreacion", "Activo") FROM stdin;
6970427c-4d91-433e-b85a-0a5591f39b90	2026-01-02	2027-01-02	30	2026-02-12 18:18:18.635106	t
\.


--
-- TOC entry 5128 (class 0 OID 24902)
-- Dependencies: 234
-- Data for Name: PeriodoInscripcion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."PeriodoInscripcion" ("PeriodoInscripcion", "Inicio", "Fin", "PeriodoEscolarId", "Activo", "FechaCreacion") FROM stdin;
0a8686fd-5a82-4e0c-87bf-1c9e82513874	2026-02-22	2026-02-27	6970427c-4d91-433e-b85a-0a5591f39b90	t	2026-02-12 18:53:33.909336
6078ea3e-223a-494c-8dce-d2f5e2aa44f5	2026-02-13	2026-02-15	6970427c-4d91-433e-b85a-0a5591f39b90	t	2026-02-13 01:51:05.35741
\.


--
-- TOC entry 5129 (class 0 OID 24914)
-- Dependencies: 235
-- Data for Name: Usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Usuario" ("UsuarioId", "Email", "Clave", "Rol", "DatosPersona", "Activo", "FechaCreacion") FROM stdin;
f31e41bb-359c-442e-9bc3-a048629348ba	romulogallegosproyecto@gmail.com	$2b$10$w75IUe68HwWRQGXmLGVQmumMWLHcubkDLCEsBq1lmNrKvNgflcOuO	administrador	\N	t	2026-02-12 18:12:29.279688
54b70f95-d576-40fa-88f5-17d45b8f5ec0	bendecidaxsiempre9@gmail.com	$2b$10$8xbJsI/RbLB5YY5vuD6.3eJH1WICFtOCCNmG8ctC278SiT1oz.wH2	representante	a11b43ad-f05d-43b1-8a29-f3cfab3c7d49	t	2026-02-12 18:16:09.435622
75cef52a-673c-4cac-88d8-610e6991eb24	luis@gmail.com	$2b$10$TjEIxHdFi.AKy11qwmNzReVdhxE21T9ZH0AVc0cokJGs9uglQ52ly	representante	b417acee-d29a-4b88-8b96-1a62ab490d5b	t	2026-02-12 18:21:19.012354
5b4bd651-a848-4bfb-b6f4-67a3ab2935af	abe@gmail.com	$2b$10$meYPPN/FzV3KKQvGrmHcDeWgiq/gn4PGqe4AsIkc/uJLi30shSTWK	representante	aabdc5cf-ab69-4eb5-8f74-c6b1b14e79d1	t	2026-02-12 19:49:07.962202
bfd01c4a-61a4-4ffd-a11b-8800ce02e98b	natashagainza7@gmail.com	$2b$10$H9jNHkQLEDRiiYBZ5gdyJOYCh467DRzX7eNUHkh1ItjWOTbN1fI66	representante	2de2e3eb-3990-4134-8488-3fefd9af9f7e	t	2026-02-12 21:09:46.336649
6dfdc9d5-4dcb-414c-9037-9ba0a1059972	dani@gmail.com	$2b$10$thHuXSHIcJHavpzM9cl94uGc.5j7NiqKyctXiRwkCDKEcgj4AF/pC	representante	d397cbd5-fb9b-4549-ac58-0b72ef7ac019	t	2026-02-12 21:50:57.897591
2d99ceda-e6e9-47d4-9eea-44a20be0a447	natasha@ospreydetect.com	$2b$10$12BWB/zVDWSdY0hkTUR3xuK97ZrT4nNYHCqordEYqaP.mEQuparDi	representante	3e6e881f-de2e-4a0d-a178-aaf48b32810e	t	2026-02-13 01:39:35.308285
c7ffb961-ca74-4869-aa15-ac85036186be	bendecidaxsiempre8@gmail.com	$2b$10$jJfpno9uyuApcKs6FueGHe6bAXYrj.pwsIPJHAzOnORU41eonotmO	representante	b635b488-8f4e-4c63-9067-2bbc25fc1c22	t	2026-02-13 02:46:05.795377
e9c5cdee-b94b-45d7-ad6d-5f172423dcda	bendecidaxsiempre9@gmail.com	$2b$10$PmdmbFMi.2S1HxdHFcy/Iu.vbueoT.jDZ0PeOUONgYseq0Mcl6nIy	representante	eb026e31-6a90-41d4-bfe9-d4c2d04df75f	t	2026-02-13 08:23:55.541689
f481eed0-22ee-473e-8128-cd0550053210	bendecidaxsiempre9@gmail.com	$2b$10$/HdXQmpR1mIpq9gNTB.NnOdw2u3fqxkxm/Gq2P4MwOdEnhAYVaOfa	representante	e6dd3fb7-bf77-44ed-ac7a-484b94a4d32c	t	2026-02-13 09:22:08.443989
\.


--
-- TOC entry 4905 (class 2606 OID 24756)
-- Name: Asistencia Asistencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Asistencia"
    ADD CONSTRAINT "Asistencia_pkey" PRIMARY KEY ("AsistenciaId");


--
-- TOC entry 4942 (class 2606 OID 24940)
-- Name: Auditoria Auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Auditoria"
    ADD CONSTRAINT "Auditoria_pkey" PRIMARY KEY ("AuditoriaId");


--
-- TOC entry 4913 (class 2606 OID 24791)
-- Name: BloqueHorario BloqueHorario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."BloqueHorario"
    ADD CONSTRAINT "BloqueHorario_pkey" PRIMARY KEY ("BloqueHorarioId");


--
-- TOC entry 4903 (class 2606 OID 24745)
-- Name: Clase Clase_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clase"
    ADD CONSTRAINT "Clase_pkey" PRIMARY KEY ("ClaseId");


--
-- TOC entry 4926 (class 2606 OID 24845)
-- Name: CursoEstudiante CursoEstudiante_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."CursoEstudiante"
    ADD CONSTRAINT "CursoEstudiante_pkey" PRIMARY KEY ("EstudianteId", "CursoId");


--
-- TOC entry 4936 (class 2606 OID 24901)
-- Name: Curso Curso_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Curso"
    ADD CONSTRAINT "Curso_pkey" PRIMARY KEY ("CursoId");


--
-- TOC entry 4917 (class 2606 OID 24819)
-- Name: DatosPersona DatosPersona_Cedula_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."DatosPersona"
    ADD CONSTRAINT "DatosPersona_Cedula_key" UNIQUE ("Cedula");


--
-- TOC entry 4919 (class 2606 OID 24821)
-- Name: DatosPersona DatosPersona_Telefono_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."DatosPersona"
    ADD CONSTRAINT "DatosPersona_Telefono_key" UNIQUE ("Telefono");


--
-- TOC entry 4921 (class 2606 OID 24817)
-- Name: DatosPersona DatosPersona_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."DatosPersona"
    ADD CONSTRAINT "DatosPersona_pkey" PRIMARY KEY ("DatosPersonaId");


--
-- TOC entry 4932 (class 2606 OID 24881)
-- Name: Docente Docente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Docente"
    ADD CONSTRAINT "Docente_pkey" PRIMARY KEY ("DocenteId");


--
-- TOC entry 4928 (class 2606 OID 24855)
-- Name: EstadoEstudiante EstadoEstudiante_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."EstadoEstudiante"
    ADD CONSTRAINT "EstadoEstudiante_pkey" PRIMARY KEY ("EstadoEstudianteId");


--
-- TOC entry 4924 (class 2606 OID 24835)
-- Name: Estudiante Estudiante_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Estudiante"
    ADD CONSTRAINT "Estudiante_pkey" PRIMARY KEY ("EstudianteId");


--
-- TOC entry 4915 (class 2606 OID 24803)
-- Name: HorarioItem HorarioItem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."HorarioItem"
    ADD CONSTRAINT "HorarioItem_pkey" PRIMARY KEY ("HorarioItemId");


--
-- TOC entry 4911 (class 2606 OID 24780)
-- Name: Horario Horario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Horario"
    ADD CONSTRAINT "Horario_pkey" PRIMARY KEY ("HorarioId");


--
-- TOC entry 4944 (class 2606 OID 24953)
-- Name: Incidencia Incidencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Incidencia"
    ADD CONSTRAINT "Incidencia_pkey" PRIMARY KEY ("IncidenciaId");


--
-- TOC entry 4907 (class 2606 OID 24768)
-- Name: Materia Materia_Nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Materia"
    ADD CONSTRAINT "Materia_Nombre_key" UNIQUE ("Nombre");


--
-- TOC entry 4909 (class 2606 OID 24766)
-- Name: Materia Materia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Materia"
    ADD CONSTRAINT "Materia_pkey" PRIMARY KEY ("MateriaId");


--
-- TOC entry 4930 (class 2606 OID 24868)
-- Name: Nota Nota_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Nota"
    ADD CONSTRAINT "Nota_pkey" PRIMARY KEY ("NotaId");


--
-- TOC entry 4934 (class 2606 OID 24893)
-- Name: PeriodoEscolar PeriodoEscolar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."PeriodoEscolar"
    ADD CONSTRAINT "PeriodoEscolar_pkey" PRIMARY KEY ("PeriodoEscolarId");


--
-- TOC entry 4938 (class 2606 OID 24913)
-- Name: PeriodoInscripcion PeriodoInscripcion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."PeriodoInscripcion"
    ADD CONSTRAINT "PeriodoInscripcion_pkey" PRIMARY KEY ("PeriodoInscripcion");


--
-- TOC entry 4940 (class 2606 OID 24927)
-- Name: Usuario Usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Usuario"
    ADD CONSTRAINT "Usuario_pkey" PRIMARY KEY ("UsuarioId");


--
-- TOC entry 4922 (class 1259 OID 25068)
-- Name: cedula_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cedula_index ON public."DatosPersona" USING btree ("Cedula");


--
-- TOC entry 4948 (class 2606 OID 24975)
-- Name: Asistencia Asistencia_ClaseId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Asistencia"
    ADD CONSTRAINT "Asistencia_ClaseId_fkey" FOREIGN KEY ("ClaseId") REFERENCES public."Clase"("ClaseId");


--
-- TOC entry 4949 (class 2606 OID 24980)
-- Name: Asistencia Asistencia_EstudianteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Asistencia"
    ADD CONSTRAINT "Asistencia_EstudianteId_fkey" FOREIGN KEY ("EstudianteId") REFERENCES public."Estudiante"("EstudianteId");


--
-- TOC entry 4965 (class 2606 OID 25060)
-- Name: Auditoria Auditoria_UsuarioId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Auditoria"
    ADD CONSTRAINT "Auditoria_UsuarioId_fkey" FOREIGN KEY ("UsuarioId") REFERENCES public."Usuario"("UsuarioId");


--
-- TOC entry 4945 (class 2606 OID 24960)
-- Name: Clase Clase_CursoId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clase"
    ADD CONSTRAINT "Clase_CursoId_fkey" FOREIGN KEY ("CursoId") REFERENCES public."Curso"("CursoId");


--
-- TOC entry 4946 (class 2606 OID 24965)
-- Name: Clase Clase_DocenteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clase"
    ADD CONSTRAINT "Clase_DocenteId_fkey" FOREIGN KEY ("DocenteId") REFERENCES public."Docente"("DocenteId");


--
-- TOC entry 4947 (class 2606 OID 24970)
-- Name: Clase Clase_PeriodoEscolarId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clase"
    ADD CONSTRAINT "Clase_PeriodoEscolarId_fkey" FOREIGN KEY ("PeriodoEscolarId") REFERENCES public."PeriodoEscolar"("PeriodoEscolarId");


--
-- TOC entry 4956 (class 2606 OID 24990)
-- Name: CursoEstudiante CursoEstudiante_CursoId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."CursoEstudiante"
    ADD CONSTRAINT "CursoEstudiante_CursoId_fkey" FOREIGN KEY ("CursoId") REFERENCES public."Curso"("CursoId");


--
-- TOC entry 4957 (class 2606 OID 24985)
-- Name: CursoEstudiante CursoEstudiante_EstudianteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."CursoEstudiante"
    ADD CONSTRAINT "CursoEstudiante_EstudianteId_fkey" FOREIGN KEY ("EstudianteId") REFERENCES public."Estudiante"("EstudianteId");


--
-- TOC entry 4958 (class 2606 OID 24995)
-- Name: CursoEstudiante CursoEstudiante_PeriodoEscolarId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."CursoEstudiante"
    ADD CONSTRAINT "CursoEstudiante_PeriodoEscolarId_fkey" FOREIGN KEY ("PeriodoEscolarId") REFERENCES public."PeriodoEscolar"("PeriodoEscolarId");


--
-- TOC entry 4961 (class 2606 OID 25045)
-- Name: Docente Docente_DatosPersonaId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Docente"
    ADD CONSTRAINT "Docente_DatosPersonaId_fkey" FOREIGN KEY ("DatosPersonaId") REFERENCES public."DatosPersona"("DatosPersonaId");


--
-- TOC entry 4962 (class 2606 OID 25050)
-- Name: Docente Docente_MateriaId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Docente"
    ADD CONSTRAINT "Docente_MateriaId_fkey" FOREIGN KEY ("MateriaId") REFERENCES public."Materia"("MateriaId");


--
-- TOC entry 4954 (class 2606 OID 25035)
-- Name: Estudiante Estudiante_DatosPersonaId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Estudiante"
    ADD CONSTRAINT "Estudiante_DatosPersonaId_fkey" FOREIGN KEY ("DatosPersonaId") REFERENCES public."DatosPersona"("DatosPersonaId");


--
-- TOC entry 4955 (class 2606 OID 25040)
-- Name: Estudiante Estudiante_RepresentanteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Estudiante"
    ADD CONSTRAINT "Estudiante_RepresentanteId_fkey" FOREIGN KEY ("RepresentanteId") REFERENCES public."DatosPersona"("DatosPersonaId");


--
-- TOC entry 4952 (class 2606 OID 25020)
-- Name: HorarioItem HorarioItem_BloqueHorarioId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."HorarioItem"
    ADD CONSTRAINT "HorarioItem_BloqueHorarioId_fkey" FOREIGN KEY ("BloqueHorarioId") REFERENCES public."BloqueHorario"("BloqueHorarioId");


--
-- TOC entry 4953 (class 2606 OID 25015)
-- Name: HorarioItem HorarioItem_DocenteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."HorarioItem"
    ADD CONSTRAINT "HorarioItem_DocenteId_fkey" FOREIGN KEY ("DocenteId") REFERENCES public."Docente"("DocenteId");


--
-- TOC entry 4950 (class 2606 OID 25000)
-- Name: Horario Horario_CursoId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Horario"
    ADD CONSTRAINT "Horario_CursoId_fkey" FOREIGN KEY ("CursoId") REFERENCES public."Curso"("CursoId");


--
-- TOC entry 4951 (class 2606 OID 25005)
-- Name: Horario Horario_PeriodoEscolarId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Horario"
    ADD CONSTRAINT "Horario_PeriodoEscolarId_fkey" FOREIGN KEY ("PeriodoEscolarId") REFERENCES public."PeriodoEscolar"("PeriodoEscolarId");


--
-- TOC entry 4966 (class 2606 OID 24955)
-- Name: Incidencia Incidencia_DatosPersonaId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Incidencia"
    ADD CONSTRAINT "Incidencia_DatosPersonaId_fkey" FOREIGN KEY ("DatosPersonaId") REFERENCES public."DatosPersona"("DatosPersonaId");


--
-- TOC entry 4959 (class 2606 OID 25030)
-- Name: Nota Nota_EstudianteId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Nota"
    ADD CONSTRAINT "Nota_EstudianteId_fkey" FOREIGN KEY ("EstudianteId") REFERENCES public."Estudiante"("EstudianteId");


--
-- TOC entry 4960 (class 2606 OID 25025)
-- Name: Nota Nota_MateriaId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Nota"
    ADD CONSTRAINT "Nota_MateriaId_fkey" FOREIGN KEY ("MateriaId") REFERENCES public."Materia"("MateriaId");


--
-- TOC entry 4963 (class 2606 OID 25010)
-- Name: PeriodoInscripcion PeriodoInscripcion_PeriodoEscolarId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."PeriodoInscripcion"
    ADD CONSTRAINT "PeriodoInscripcion_PeriodoEscolarId_fkey" FOREIGN KEY ("PeriodoEscolarId") REFERENCES public."PeriodoEscolar"("PeriodoEscolarId");


--
-- TOC entry 4964 (class 2606 OID 25055)
-- Name: Usuario Usuario_DatosPersona_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Usuario"
    ADD CONSTRAINT "Usuario_DatosPersona_fkey" FOREIGN KEY ("DatosPersona") REFERENCES public."DatosPersona"("DatosPersonaId") ON DELETE CASCADE;


--
-- TOC entry 5138 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


-- Completed on 2026-02-17 11:55:41

--
-- PostgreSQL database dump complete
--

\unrestrict 5ZrAC0uiFsilZqP4AN4hZDrU3gCC4GDVHFoD2wsqIjdalEZHPcGlszatxZHPcZN

