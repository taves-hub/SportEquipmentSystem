--
-- PostgreSQL database dump
--

\restrict o3H6z8F5oCCxybW5z6gBHkhKgfzLqjmwc4WTsx834pqSfb2mumIZKebbRhWFtJb

-- Dumped from database version 17.5
-- Dumped by pg_dump version 18.0

-- Started on 2026-02-13 20:29:11

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 28038)
-- Name: admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admins (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(200) NOT NULL,
    email character varying(120) NOT NULL
);


ALTER TABLE public.admins OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 28037)
-- Name: admins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admins_id_seq OWNER TO postgres;

--
-- TOC entry 5026 (class 0 OID 0)
-- Dependencies: 217
-- Name: admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admins_id_seq OWNED BY public.admins.id;


--
-- TOC entry 237 (class 1259 OID 28206)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 28152)
-- Name: campus_distributions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.campus_distributions (
    id integer NOT NULL,
    campus_id integer NOT NULL,
    equipment_id integer NOT NULL,
    category_code character varying(10) NOT NULL,
    category_name character varying(100) NOT NULL,
    quantity integer NOT NULL,
    date_distributed timestamp without time zone,
    distributed_by character varying(120),
    notes text,
    document_path character varying(500)
);


ALTER TABLE public.campus_distributions OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 28151)
-- Name: campus_distributions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.campus_distributions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.campus_distributions_id_seq OWNER TO postgres;

--
-- TOC entry 5027 (class 0 OID 0)
-- Dependencies: 235
-- Name: campus_distributions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.campus_distributions_id_seq OWNED BY public.campus_distributions.id;


--
-- TOC entry 224 (class 1259 OID 28072)
-- Name: clearance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clearance (
    id integer NOT NULL,
    student_id character varying(20) NOT NULL,
    status character varying(20),
    last_updated timestamp without time zone
);


ALTER TABLE public.clearance OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 28071)
-- Name: clearance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.clearance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clearance_id_seq OWNER TO postgres;

--
-- TOC entry 5028 (class 0 OID 0)
-- Dependencies: 223
-- Name: clearance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.clearance_id_seq OWNED BY public.clearance.id;


--
-- TOC entry 222 (class 1259 OID 28063)
-- Name: equipment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    category_code character varying(10) NOT NULL,
    quantity integer NOT NULL,
    condition character varying(50),
    damaged_count integer NOT NULL,
    lost_count integer NOT NULL,
    date_received timestamp without time zone,
    is_active boolean NOT NULL,
    serial_number character varying(100) NOT NULL
);


ALTER TABLE public.equipment OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 28092)
-- Name: equipment_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment_categories (
    id integer NOT NULL,
    category_code character varying(10) NOT NULL,
    category_name character varying(100) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.equipment_categories OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 28091)
-- Name: equipment_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipment_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipment_categories_id_seq OWNER TO postgres;

--
-- TOC entry 5029 (class 0 OID 0)
-- Dependencies: 227
-- Name: equipment_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipment_categories_id_seq OWNED BY public.equipment_categories.id;


--
-- TOC entry 221 (class 1259 OID 28062)
-- Name: equipment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipment_id_seq OWNER TO postgres;

--
-- TOC entry 5030 (class 0 OID 0)
-- Dependencies: 221
-- Name: equipment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipment_id_seq OWNED BY public.equipment.id;


--
-- TOC entry 232 (class 1259 OID 28112)
-- Name: issued_equipment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issued_equipment (
    id integer NOT NULL,
    student_id character varying(20),
    staff_payroll character varying(20),
    equipment_id integer,
    quantity integer NOT NULL,
    date_issued timestamp without time zone,
    expected_return timestamp without time zone,
    status character varying(50),
    return_conditions text,
    date_returned timestamp without time zone,
    damage_clearance_status character varying(50),
    damage_clearance_notes text,
    damage_clearance_document character varying(500),
    issued_by character varying(120),
    serial_numbers text
);


ALTER TABLE public.issued_equipment OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 28111)
-- Name: issued_equipment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issued_equipment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.issued_equipment_id_seq OWNER TO postgres;

--
-- TOC entry 5031 (class 0 OID 0)
-- Dependencies: 231
-- Name: issued_equipment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issued_equipment_id_seq OWNED BY public.issued_equipment.id;


--
-- TOC entry 230 (class 1259 OID 28103)
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    recipient_role character varying(20) NOT NULL,
    recipient_id integer,
    message text NOT NULL,
    url character varying(500),
    is_read boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 28102)
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- TOC entry 5032 (class 0 OID 0)
-- Dependencies: 229
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- TOC entry 226 (class 1259 OID 28081)
-- Name: satellite_campuses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.satellite_campuses (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    location character varying(200),
    code character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.satellite_campuses OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 28080)
-- Name: satellite_campuses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.satellite_campuses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.satellite_campuses_id_seq OWNER TO postgres;

--
-- TOC entry 5033 (class 0 OID 0)
-- Dependencies: 225
-- Name: satellite_campuses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.satellite_campuses_id_seq OWNED BY public.satellite_campuses.id;


--
-- TOC entry 220 (class 1259 OID 28055)
-- Name: staff; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.staff (
    payroll_number character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL
);


ALTER TABLE public.staff OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 28136)
-- Name: storekeepers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storekeepers (
    id integer NOT NULL,
    payroll_number character varying(20) NOT NULL,
    full_name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(200) NOT NULL,
    campus_id integer NOT NULL,
    is_approved boolean NOT NULL,
    approved_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.storekeepers OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 28135)
-- Name: storekeepers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.storekeepers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.storekeepers_id_seq OWNER TO postgres;

--
-- TOC entry 5034 (class 0 OID 0)
-- Dependencies: 233
-- Name: storekeepers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.storekeepers_id_seq OWNED BY public.storekeepers.id;


--
-- TOC entry 219 (class 1259 OID 28048)
-- Name: students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.students (
    id character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    phone character varying(15)
);


ALTER TABLE public.students OWNER TO postgres;

--
-- TOC entry 4794 (class 2604 OID 28041)
-- Name: admins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins ALTER COLUMN id SET DEFAULT nextval('public.admins_id_seq'::regclass);


--
-- TOC entry 4802 (class 2604 OID 28155)
-- Name: campus_distributions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campus_distributions ALTER COLUMN id SET DEFAULT nextval('public.campus_distributions_id_seq'::regclass);


--
-- TOC entry 4796 (class 2604 OID 28075)
-- Name: clearance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clearance ALTER COLUMN id SET DEFAULT nextval('public.clearance_id_seq'::regclass);


--
-- TOC entry 4795 (class 2604 OID 28066)
-- Name: equipment id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment ALTER COLUMN id SET DEFAULT nextval('public.equipment_id_seq'::regclass);


--
-- TOC entry 4798 (class 2604 OID 28095)
-- Name: equipment_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_categories ALTER COLUMN id SET DEFAULT nextval('public.equipment_categories_id_seq'::regclass);


--
-- TOC entry 4800 (class 2604 OID 28115)
-- Name: issued_equipment id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_equipment ALTER COLUMN id SET DEFAULT nextval('public.issued_equipment_id_seq'::regclass);


--
-- TOC entry 4799 (class 2604 OID 28106)
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- TOC entry 4797 (class 2604 OID 28084)
-- Name: satellite_campuses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.satellite_campuses ALTER COLUMN id SET DEFAULT nextval('public.satellite_campuses_id_seq'::regclass);


--
-- TOC entry 4801 (class 2604 OID 28139)
-- Name: storekeepers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storekeepers ALTER COLUMN id SET DEFAULT nextval('public.storekeepers_id_seq'::regclass);


--
-- TOC entry 5001 (class 0 OID 28038)
-- Dependencies: 218
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (id, username, password_hash, email) FROM stdin;
1	admin	scrypt:32768:8:1$LoIeVMYCpVGQva2D$6927ce131f275806e0e02e5d397ad37e4d036f12983c24a12ae8870acb57eb342bf60c6167af35f88076f4899d5397282e1afcfa865421c3240765f1d858ba01	admin@example.com
\.


--
-- TOC entry 5020 (class 0 OID 28206)
-- Dependencies: 237
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
285be9df0a73
\.


--
-- TOC entry 5019 (class 0 OID 28152)
-- Dependencies: 236
-- Data for Name: campus_distributions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.campus_distributions (id, campus_id, equipment_id, category_code, category_name, quantity, date_distributed, distributed_by, notes, document_path) FROM stdin;
\.


--
-- TOC entry 5007 (class 0 OID 28072)
-- Dependencies: 224
-- Data for Name: clearance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clearance (id, student_id, status, last_updated) FROM stdin;
1	CT202/100784/19	Pending	2026-01-21 09:27:16
2	CT202/100783/19	Cleared	2026-01-20 11:03:14
3	STU_A01	Pending	2026-01-20 11:02:48
4	CT202/100782/19	Cleared	2026-01-20 11:23:47
5	STU_SK01	Cleared	2026-01-21 09:25:25
6	CT202/100781/19	Pending	2026-01-20 11:00:15
7	CT202/100780/19	Pending	2026-01-20 11:02:48
8	CT202/100790/19	Pending	2026-01-20 11:02:48
9	STU555	Pending	2026-01-20 11:02:48
10		Cleared	2026-01-21 07:58:28
11	CT202/100795/19	Cleared	2026-01-22 10:19:15
12	STU002	Pending	2026-01-23 05:36:02
13	CT202/10001/26	Pending	2026-01-23 07:14:24
14	CT202/10782/19	Pending	2026-01-23 09:10:12
15	CT202/10002/26	Pending	2026-01-27 12:46:19
\.


--
-- TOC entry 5005 (class 0 OID 28063)
-- Dependencies: 222
-- Data for Name: equipment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipment (id, name, category, category_code, quantity, condition, damaged_count, lost_count, date_received, is_active, serial_number) FROM stdin;
1	Footballs	Ball Sports Equipment	BSE-01	17	Good	0	0	2026-02-13 07:40:30.547426	t	EQ-BE9D65F6
2	Basketballs	Ball Sports Equipment	BSE-01	24	Good	0	0	2026-02-13 07:40:30.551458	t	EQ-B7703942
3	Volleyballs	Ball Sports Equipment	BSE-01	19	Good	0	0	2026-02-13 07:40:30.553142	t	EQ-42D8D62D
4	Rugby balls	Ball Sports Equipment	BSE-01	17	Good	0	0	2026-02-13 07:40:30.554777	t	EQ-AC35C0BE
5	Handballs	Ball Sports Equipment	BSE-01	16	Good	0	0	2026-02-13 07:40:30.557354	t	EQ-73DCB5C3
6	Netballs	Ball Sports Equipment	BSE-01	23	Good	0	0	2026-02-13 07:40:30.559064	t	EQ-39D4D88C
7	Volleyball nets	Net & Court Equipment	NCE-02	20	Good	0	0	2026-02-13 07:40:30.561587	t	EQ-DA1B6C6D
8	Tennis nets	Net & Court Equipment	NCE-02	25	Good	0	0	2026-02-13 07:40:30.563519	t	EQ-45662EBB
9	Badminton nets	Net & Court Equipment	NCE-02	16	Good	0	0	2026-02-13 07:40:30.565644	t	EQ-1D424ADA
10	Netball rings & nets	Net & Court Equipment	NCE-02	25	Good	0	0	2026-02-13 07:40:30.567826	t	EQ-8A635BD1
11	Court boundary lines	Net & Court Equipment	NCE-02	18	Good	0	0	2026-02-13 07:40:30.569999	t	EQ-44AA6E87
12	Relay batons	Athletics & Track Equipment	ATE-03	11	Good	0	0	2026-02-13 07:40:30.572323	t	EQ-3FE1033C
13	Hurdles	Athletics & Track Equipment	ATE-03	14	Good	0	0	2026-02-13 07:40:30.574156	t	EQ-6E2C3DF4
14	Starting blocks	Athletics & Track Equipment	ATE-03	19	Good	0	0	2026-02-13 07:40:30.576809	t	EQ-05D8D94C
15	Shot put	Athletics & Track Equipment	ATE-03	17	Good	0	0	2026-02-13 07:40:30.578601	t	EQ-8C1D7E1D
16	Discus	Athletics & Track Equipment	ATE-03	16	Good	0	0	2026-02-13 07:40:30.580215	t	EQ-EB1AE2AA
17	Javelin	Athletics & Track Equipment	ATE-03	22	Good	0	0	2026-02-13 07:40:30.582374	t	EQ-857473B7
18	Measuring tapes	Athletics & Track Equipment	ATE-03	13	Good	0	0	2026-02-13 07:40:30.58418	t	EQ-48327FC6
19	Table tennis bats	Indoor Sports Equipment	ISE-04	22	Good	0	0	2026-02-13 07:40:30.586277	t	EQ-B3B6AFBF
20	Table tennis balls	Indoor Sports Equipment	ISE-04	21	Good	0	0	2026-02-13 07:40:30.587884	t	EQ-3E0BEBBD
21	Chess boards & pieces	Indoor Sports Equipment	ISE-04	16	Good	0	0	2026-02-13 07:40:30.590088	t	EQ-FFDDBBA2
22	Scrabble sets	Indoor Sports Equipment	ISE-04	18	Good	0	0	2026-02-13 07:40:30.592633	t	EQ-E8D0BF23
23	Pool cues	Indoor Sports Equipment	ISE-04	13	Good	0	0	2026-02-13 07:40:30.595325	t	EQ-D68C46D4
24	Pool balls	Indoor Sports Equipment	ISE-04	16	Good	0	0	2026-02-13 07:40:30.598522	t	EQ-3E803EF5
25	Hockey sticks	Field & Team Sports Gear	FSE-05	16	Good	0	0	2026-02-13 07:40:30.601008	t	EQ-9A0AD693
26	Cricket bats	Field & Team Sports Gear	FSE-05	21	Good	0	0	2026-02-13 07:40:30.602814	t	EQ-2EE87E75
27	Cricket balls	Field & Team Sports Gear	FSE-05	22	Good	0	0	2026-02-13 07:40:30.604498	t	EQ-C5D9130E
28	Baseball bats	Field & Team Sports Gear	FSE-05	14	Good	0	0	2026-02-13 07:40:30.606572	t	EQ-2E1C45FE
29	Softballs	Field & Team Sports Gear	FSE-05	15	Good	0	0	2026-02-13 07:40:30.608553	t	EQ-3FEAAA01
30	Lacrosse sticks	Field & Team Sports Gear	FSE-05	17	Good	0	0	2026-02-13 07:40:30.610239	t	EQ-732BCEED
31	Skipping ropes	Fitness & Training Equipment	FTE-06	13	Good	0	0	2026-02-13 07:40:30.612591	t	EQ-AF7B6EF4
32	Agility cones	Fitness & Training Equipment	FTE-06	11	Good	0	0	2026-02-13 07:40:30.614817	t	EQ-ACB36685
33	Resistance bands	Fitness & Training Equipment	FTE-06	19	Good	0	0	2026-02-13 07:40:30.617312	t	EQ-133E866A
34	Medicine balls	Fitness & Training Equipment	FTE-06	17	Good	0	0	2026-02-13 07:40:30.619772	t	EQ-0AF05E32
35	Agility ladders	Fitness & Training Equipment	FTE-06	17	Good	0	0	2026-02-13 07:40:30.62227	t	EQ-E5938AC6
36	Speed hurdles	Fitness & Training Equipment	FTE-06	25	Good	0	0	2026-02-13 07:40:30.624531	t	EQ-AA38C6F6
37	Shin guards	Protective & Safety Gear	PSE-07	24	Good	0	0	2026-02-13 07:40:30.626874	t	EQ-9D76A50A
38	Helmets	Protective & Safety Gear	PSE-07	13	Good	0	0	2026-02-13 07:40:30.629076	t	EQ-944C1343
39	Mouth guards	Protective & Safety Gear	PSE-07	25	Good	0	0	2026-02-13 07:40:30.630913	t	EQ-6600B44D
40	Knee pads	Protective & Safety Gear	PSE-07	14	Good	0	0	2026-02-13 07:40:30.632692	t	EQ-752620FB
41	Elbow pads	Protective & Safety Gear	PSE-07	19	Good	0	0	2026-02-13 07:40:30.63451	t	EQ-03AECCB1
42	Goalkeeper gloves	Protective & Safety Gear	PSE-07	20	Good	0	0	2026-02-13 07:40:30.636676	t	EQ-EF9FACC8
43	Sports jerseys	Apparel & Wearables	AWE-08	23	Good	0	0	2026-02-13 07:40:30.640082	t	EQ-74EE35CF
44	Training bibs	Apparel & Wearables	AWE-08	25	Good	0	0	2026-02-13 07:40:30.642242	t	EQ-05C88878
45	Socks	Apparel & Wearables	AWE-08	11	Good	0	0	2026-02-13 07:40:30.644357	t	EQ-121A9039
46	Tracksuits	Apparel & Wearables	AWE-08	10	Good	0	0	2026-02-13 07:40:30.646127	t	EQ-857D264D
47	Training vests	Apparel & Wearables	AWE-08	24	Good	0	0	2026-02-13 07:40:30.647839	t	EQ-A17E915A
48	T-shirts	Apparel & Wearables	AWE-08	24	Good	0	0	2026-02-13 07:40:30.649565	t	EQ-88D8EFA7
\.


--
-- TOC entry 5011 (class 0 OID 28092)
-- Dependencies: 228
-- Data for Name: equipment_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipment_categories (id, category_code, category_name, description, is_active, created_at) FROM stdin;
1	BSE-01	Ball Sports Equipment	Equipment for ball sports equipment	t	2026-02-13 07:40:30.511996
2	NCE-02	Net & Court Equipment	Equipment for net & court equipment	t	2026-02-13 07:40:30.524844
3	ATE-03	Athletics & Track Equipment	Equipment for athletics & track equipment	t	2026-02-13 07:40:30.528269
4	ISE-04	Indoor Sports Equipment	Equipment for indoor sports equipment	t	2026-02-13 07:40:30.53153
5	FSE-05	Field & Team Sports Gear	Equipment for field & team sports gear	t	2026-02-13 07:40:30.534548
6	FTE-06	Fitness & Training Equipment	Equipment for fitness & training equipment	t	2026-02-13 07:40:30.536492
7	PSE-07	Protective & Safety Gear	Equipment for protective & safety gear	t	2026-02-13 07:40:30.538282
8	AWE-08	Apparel & Wearables	Equipment for apparel & wearables	t	2026-02-13 07:40:30.540008
\.


--
-- TOC entry 5015 (class 0 OID 28112)
-- Dependencies: 232
-- Data for Name: issued_equipment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issued_equipment (id, student_id, staff_payroll, equipment_id, quantity, date_issued, expected_return, status, return_conditions, date_returned, damage_clearance_status, damage_clearance_notes, damage_clearance_document, issued_by, serial_numbers) FROM stdin;
\.


--
-- TOC entry 5013 (class 0 OID 28103)
-- Dependencies: 230
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, recipient_role, recipient_id, message, url, is_read, created_at) FROM stdin;
1	admin	\N	Issue 55 escalated by Kennedy Mwangi	/admin/escalated-damage	f	2026-02-06 10:09:00
2	storekeeper	2	Admin rejected clearance for issue 55.	/storekeeper/damage-clearance	f	2026-02-06 10:10:35
\.


--
-- TOC entry 5009 (class 0 OID 28081)
-- Dependencies: 226
-- Data for Name: satellite_campuses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.satellite_campuses (id, name, location, code, is_active, created_at) FROM stdin;
1	Main Campus	Main Campus, University of Nairobi	001	t	2026-02-13 07:46:36.470473
2	Lower Kabete Campus	Lower Kabete, Nairobi	002	t	2026-02-13 07:46:36.488723
3	Kikuyu Campus	Kikuyu, Kiambu County	003	t	2026-02-13 07:46:36.491391
4	Kenyatta National Campus	Kenyatta National Hospital, Nairobi	004	t	2026-02-13 07:46:36.493755
5	Parklands Campus	Parklands, Nairobi	005	t	2026-02-13 07:46:36.495935
6	Kenya Science Campus	Kenya Science Campus, Nairobi	006	t	2026-02-13 07:46:36.497697
\.


--
-- TOC entry 5003 (class 0 OID 28055)
-- Dependencies: 220
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.staff (payroll_number, name, email) FROM stdin;
100300	Cathy Johnson	jcathy@uonbi.ac.ke
100505	Susan Njeri	nsusan@uonbi.ac.ke
162420	Ian John	jian@uonbi.ac.ke
168940	jack johnson	jjack@uonbi.ac.ke
200100	Alex Mckennedy	malex@uonbi.ac.ke
205030	AnnJohn	jann@uonbi.ac.ke
215020	Kennedy Mwangi	kmwangi@uonbi.ac.ke
215030	Samuel Mbai	smbai@uonbi.ac.ke
218710	Kelvin Kimondi	kkimondi@uonbi.ac.ke
\.


--
-- TOC entry 5017 (class 0 OID 28136)
-- Dependencies: 234
-- Data for Name: storekeepers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.storekeepers (id, payroll_number, full_name, email, password_hash, campus_id, is_approved, approved_at, created_at) FROM stdin;
37	100200	Paul Oduya	poduya@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	1	t	2026-02-13 08:03:30.919994	2026-02-13 08:03:30.920188
38	100201	James Githinji	jgithinji@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	1	t	2026-02-13 08:03:31.057625	2026-02-13 08:03:31.057634
39	100202	Rachel Achieng	rachieng@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	1	t	2026-02-13 08:03:31.183524	2026-02-13 08:03:31.183532
40	100203	Samuel Langat	slangat@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	1	t	2026-02-13 08:03:31.30809	2026-02-13 08:03:31.308099
41	100204	Charles Kiptanui	ckiptanui@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	2	t	2026-02-13 08:03:31.433977	2026-02-13 08:03:31.433986
42	100205	Beatrice Mburu	bmburu@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	2	t	2026-02-13 08:03:31.563189	2026-02-13 08:03:31.563198
43	100206	Gladys Mitei	gmitei@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	2	t	2026-02-13 08:03:31.68884	2026-02-13 08:03:31.688848
44	100207	Robert Mumbi	rmumbi@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	2	t	2026-02-13 08:03:31.813726	2026-02-13 08:03:31.813734
45	100208	Mercy Wanjohi	mwanjohi@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	3	t	2026-02-13 08:03:31.940677	2026-02-13 08:03:31.940686
46	100209	Priscilla Jeptoo	pjeptoo@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	3	t	2026-02-13 08:03:32.064961	2026-02-13 08:03:32.064965
47	100210	Martin Nyambura	mnyambura@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	4	t	2026-02-13 08:03:32.19159	2026-02-13 08:03:32.191599
48	100211	Charles Wambui	cwambui@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	4	t	2026-02-13 08:03:32.314734	2026-02-13 08:03:32.314742
49	100212	Henry Oduya	hoduya@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	5	t	2026-02-13 08:03:32.441054	2026-02-13 08:03:32.441062
50	100213	Susan Kiplagat	skiplagat@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	5	t	2026-02-13 08:03:32.566388	2026-02-13 08:03:32.566397
51	100214	Helen Kiptoo	hkiptoo@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	5	t	2026-02-13 08:03:32.691971	2026-02-13 08:03:32.691981
52	100215	Mary Mwangi	mmwangi@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	6	t	2026-02-13 08:03:32.816051	2026-02-13 08:03:32.81606
53	100216	Alice Wambui	awambui@uonbi.ac.ke	scrypt:32768:8:1$dinbLi8D9OnDmgE0$51e3924d7d056ad825ab0ae97d45c528261b7d88cb05df0b8a7440b20548b25d6654493970c9f828acbb3b5757e78a6e8e9bb2326b971b951630f1973657a6b8	6	t	2026-02-13 08:03:32.942096	2026-02-13 08:03:32.942111
54	361393	Kennedy Mwangi	kennedynduthamw@gmail.com	scrypt:32768:8:1$dY91DMOfhhrA4Qv7$5efe78e5f3a9860531b46352856bcdcd6d913ef31ef7b6abba506c0465e1f67401c98e5c7429338208171298d2337bcadc34eee36ae9f84548e56acc5ada2df7	1	f	\N	2026-02-13 17:28:24.969395
\.


--
-- TOC entry 5002 (class 0 OID 28048)
-- Dependencies: 219
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students (id, name, email, phone) FROM stdin;
CT202/10001/26	John Doe	djohn@student.uonbi.ac.ke	\N
CT202/10002/26	Jane Smith	sjane@student.uonbi.ac.ke	\N
CT202/10003/26	Alice Johnson	jalice@student.uonbi.ac.ke	\N
CT202/10004/26	Bob Williams	wbob@student.uonbi.ac.ke	\N
CT202/10005/26	Charlie Brown	bcharlie@student.uonbi.ac.ke	\N
CT202/10006/26	Diana Davis	ddiana@student.uonbi.ac.ke	\N
CT202/100400/26	Mudola Brian 	brianm@student.uonbi.ac.ke	0721242373
CT202/100780/19	Victor mburu	vmburu@students.uonbi.ac.ke	0721242346
CT202/100781/19	Ian Kamu	iank@students.uonbi.ac.ke	0721242345
CT202/100782/26	McKennedy	mcken@uonbi.ac.ke	0723671345
CT202/100783/19	Moris Kamore	kamorem@uonbi.ac.ke	0713672681
CT202/100784/19	Joy kavulunze	kavulunzej@uonbi.ac.ke	0723671784
CT202/100790/19	Mark Mark	mmark@uonbi.ac.ke	0712345678
CT202/100790/26	Ian Kamu	kian@uonbi.ac.ke	0723671756
CT202/100795/19	Brian mudola	mbrian@student.uonbi.ac.ke	0712345610
CT202/10782/19	joseph clinton	clinton@students.uonbi.ac.ke	0721242356
CT202003	Charlie Brown	charlie.brown@example.com	345-678-9012
CT202004	Diana Prince	diana.prince@example.com	456-789-0123
CT202005	Eve Wilson	eve.wilson@example.com	567-890-1234
STU001	Test Student	student@test.com	1234567890
STU002	Jane Smith	jane@test.com	0987654321
STU555	Storekeeper Test	sktest@example.com	0755555555
STU_A01	Admin Student 1	admin_stu@test.com	0712121212
STU_SK01	Storekeeper Student 1	sk_stu@test.com	0713131313
\.


--
-- TOC entry 5035 (class 0 OID 0)
-- Dependencies: 217
-- Name: admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admins_id_seq', 1, false);


--
-- TOC entry 5036 (class 0 OID 0)
-- Dependencies: 235
-- Name: campus_distributions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.campus_distributions_id_seq', 1, false);


--
-- TOC entry 5037 (class 0 OID 0)
-- Dependencies: 223
-- Name: clearance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clearance_id_seq', 1, false);


--
-- TOC entry 5038 (class 0 OID 0)
-- Dependencies: 227
-- Name: equipment_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipment_categories_id_seq', 8, true);


--
-- TOC entry 5039 (class 0 OID 0)
-- Dependencies: 221
-- Name: equipment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipment_id_seq', 48, true);


--
-- TOC entry 5040 (class 0 OID 0)
-- Dependencies: 231
-- Name: issued_equipment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issued_equipment_id_seq', 1, false);


--
-- TOC entry 5041 (class 0 OID 0)
-- Dependencies: 229
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- TOC entry 5042 (class 0 OID 0)
-- Dependencies: 225
-- Name: satellite_campuses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.satellite_campuses_id_seq', 6, true);


--
-- TOC entry 5043 (class 0 OID 0)
-- Dependencies: 233
-- Name: storekeepers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.storekeepers_id_seq', 54, true);


--
-- TOC entry 4804 (class 2606 OID 28047)
-- Name: admins admins_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_email_key UNIQUE (email);


--
-- TOC entry 4806 (class 2606 OID 28043)
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (id);


--
-- TOC entry 4808 (class 2606 OID 28045)
-- Name: admins admins_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_username_key UNIQUE (username);


--
-- TOC entry 4848 (class 2606 OID 28210)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4846 (class 2606 OID 28159)
-- Name: campus_distributions campus_distributions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campus_distributions
    ADD CONSTRAINT campus_distributions_pkey PRIMARY KEY (id);


--
-- TOC entry 4822 (class 2606 OID 28077)
-- Name: clearance clearance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clearance
    ADD CONSTRAINT clearance_pkey PRIMARY KEY (id);


--
-- TOC entry 4824 (class 2606 OID 28079)
-- Name: clearance clearance_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clearance
    ADD CONSTRAINT clearance_student_id_key UNIQUE (student_id);


--
-- TOC entry 4832 (class 2606 OID 28101)
-- Name: equipment_categories equipment_categories_category_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_categories
    ADD CONSTRAINT equipment_categories_category_code_key UNIQUE (category_code);


--
-- TOC entry 4834 (class 2606 OID 28099)
-- Name: equipment_categories equipment_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_categories
    ADD CONSTRAINT equipment_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 4818 (class 2606 OID 28068)
-- Name: equipment equipment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_pkey PRIMARY KEY (id);


--
-- TOC entry 4820 (class 2606 OID 28070)
-- Name: equipment equipment_serial_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_serial_number_key UNIQUE (serial_number);


--
-- TOC entry 4838 (class 2606 OID 28119)
-- Name: issued_equipment issued_equipment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_equipment
    ADD CONSTRAINT issued_equipment_pkey PRIMARY KEY (id);


--
-- TOC entry 4836 (class 2606 OID 28110)
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- TOC entry 4826 (class 2606 OID 28090)
-- Name: satellite_campuses satellite_campuses_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.satellite_campuses
    ADD CONSTRAINT satellite_campuses_code_key UNIQUE (code);


--
-- TOC entry 4828 (class 2606 OID 28088)
-- Name: satellite_campuses satellite_campuses_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.satellite_campuses
    ADD CONSTRAINT satellite_campuses_name_key UNIQUE (name);


--
-- TOC entry 4830 (class 2606 OID 28086)
-- Name: satellite_campuses satellite_campuses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.satellite_campuses
    ADD CONSTRAINT satellite_campuses_pkey PRIMARY KEY (id);


--
-- TOC entry 4814 (class 2606 OID 28061)
-- Name: staff staff_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_email_key UNIQUE (email);


--
-- TOC entry 4816 (class 2606 OID 28059)
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (payroll_number);


--
-- TOC entry 4840 (class 2606 OID 28145)
-- Name: storekeepers storekeepers_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storekeepers
    ADD CONSTRAINT storekeepers_email_key UNIQUE (email);


--
-- TOC entry 4842 (class 2606 OID 28143)
-- Name: storekeepers storekeepers_payroll_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storekeepers
    ADD CONSTRAINT storekeepers_payroll_number_key UNIQUE (payroll_number);


--
-- TOC entry 4844 (class 2606 OID 28141)
-- Name: storekeepers storekeepers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storekeepers
    ADD CONSTRAINT storekeepers_pkey PRIMARY KEY (id);


--
-- TOC entry 4810 (class 2606 OID 28054)
-- Name: students students_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_email_key UNIQUE (email);


--
-- TOC entry 4812 (class 2606 OID 28052)
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- TOC entry 4853 (class 2606 OID 28160)
-- Name: campus_distributions campus_distributions_campus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campus_distributions
    ADD CONSTRAINT campus_distributions_campus_id_fkey FOREIGN KEY (campus_id) REFERENCES public.satellite_campuses(id);


--
-- TOC entry 4854 (class 2606 OID 28165)
-- Name: campus_distributions campus_distributions_equipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campus_distributions
    ADD CONSTRAINT campus_distributions_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES public.equipment(id);


--
-- TOC entry 4849 (class 2606 OID 28130)
-- Name: issued_equipment issued_equipment_equipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_equipment
    ADD CONSTRAINT issued_equipment_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES public.equipment(id);


--
-- TOC entry 4850 (class 2606 OID 28125)
-- Name: issued_equipment issued_equipment_staff_payroll_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_equipment
    ADD CONSTRAINT issued_equipment_staff_payroll_fkey FOREIGN KEY (staff_payroll) REFERENCES public.staff(payroll_number);


--
-- TOC entry 4851 (class 2606 OID 28120)
-- Name: issued_equipment issued_equipment_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_equipment
    ADD CONSTRAINT issued_equipment_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- TOC entry 4852 (class 2606 OID 28146)
-- Name: storekeepers storekeepers_campus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storekeepers
    ADD CONSTRAINT storekeepers_campus_id_fkey FOREIGN KEY (campus_id) REFERENCES public.satellite_campuses(id);


-- Completed on 2026-02-13 20:29:11

--
-- PostgreSQL database dump complete
--

\unrestrict o3H6z8F5oCCxybW5z6gBHkhKgfzLqjmwc4WTsx834pqSfb2mumIZKebbRhWFtJb

