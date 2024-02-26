--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1
-- Dumped by pg_dump version 15.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: mapper; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.mapper (
    id integer NOT NULL,
    cg_id text,
    exchange text,
    symbol text,
    update timestamp without time zone DEFAULT now()
);


ALTER TABLE public.mapper OWNER TO exchange;

--
-- Name: mapper_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.mapper_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.mapper_id_seq OWNER TO exchange;

--
-- Name: mapper_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.mapper_id_seq OWNED BY public.mapper.id;


--
-- Name: mapper id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.mapper ALTER COLUMN id SET DEFAULT nextval('public.mapper_id_seq'::regclass);


--
-- Name: mapper mapper_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.mapper
    ADD CONSTRAINT mapper_pkey PRIMARY KEY (id);


--
-- Name: mapper market; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.mapper
    ADD CONSTRAINT market UNIQUE (cg_id, exchange) INCLUDE (cg_id, exchange);


--
-- Name: CONSTRAINT market ON mapper; Type: COMMENT; Schema: public; Owner: exchange
--

COMMENT ON CONSTRAINT market ON public.mapper IS 'Unique together, only one coingecko_id for exchange market''s symbol';


--
-- PostgreSQL database dump complete
--

