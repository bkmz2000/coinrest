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
-- Name: actual_coingecko; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.actual_coingecko (
    id integer NOT NULL,
    cg_id text
);


ALTER TABLE public.actual_coingecko OWNER TO exchange;

--
-- Name: actual_coingecko_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.actual_coingecko_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.actual_coingecko_id_seq OWNER TO exchange;

--
-- Name: actual_coingecko_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.actual_coingecko_id_seq OWNED BY public.actual_coingecko.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO exchange;

--
-- Name: exchange; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.exchange (
    id integer NOT NULL,
    ccxt_name text,
    cg_identifier text,
    full_name text,
    trust_score smallint,
    centralized boolean,
    logo text
);


ALTER TABLE public.exchange OWNER TO exchange;

--
-- Name: exchange_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.exchange_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.exchange_id_seq OWNER TO exchange;

--
-- Name: exchange_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.exchange_id_seq OWNED BY public.exchange.id;


--
-- Name: exchange_tickers_mapper; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.exchange_tickers_mapper (
    id bigint NOT NULL,
    exchange_id smallint,
    symbol text,
    cg_id text,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.exchange_tickers_mapper OWNER TO exchange;

--
-- Name: exchange_tickers_mapper_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.exchange_tickers_mapper_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.exchange_tickers_mapper_id_seq OWNER TO exchange;

--
-- Name: exchange_tickers_mapper_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.exchange_tickers_mapper_id_seq OWNED BY public.exchange_tickers_mapper.id;


--
-- Name: historical; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.historical (
    id bigint NOT NULL,
    cg_id text,
    price_usd numeric,
    volume_usd numeric,
    price_btc numeric,
    volume_btc numeric,
    "timestamp" bigint
);


ALTER TABLE public.historical OWNER TO exchange;

--
-- Name: historical_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.historical_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.historical_id_seq OWNER TO exchange;

--
-- Name: historical_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.historical_id_seq OWNED BY public.historical.id;


--
-- Name: last; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.last (
    id integer NOT NULL,
    cg_id text,
    price_usd numeric,
    price_btc numeric,
    volume_usd numeric,
    volume_btc numeric,
    last_update timestamp without time zone DEFAULT now()
);


ALTER TABLE public.last OWNER TO exchange;

--
-- Name: last_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.last_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.last_id_seq OWNER TO exchange;

--
-- Name: last_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.last_id_seq OWNED BY public.last.id;


--
-- Name: quote_converter; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.quote_converter (
    id integer NOT NULL,
    currency text NOT NULL,
    rate numeric,
    update_at timestamp without time zone
);


ALTER TABLE public.quote_converter OWNER TO exchange;

--
-- Name: TABLE quote_converter; Type: COMMENT; Schema: public; Owner: exchange
--

COMMENT ON TABLE public.quote_converter IS 'Table for mapping quote currencies to USD';


--
-- Name: quote_converter_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.quote_converter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.quote_converter_id_seq OWNER TO exchange;

--
-- Name: quote_converter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.quote_converter_id_seq OWNED BY public.quote_converter.id;


--
-- Name: ticker; Type: TABLE; Schema: public; Owner: exchange
--

CREATE TABLE public.ticker (
    id bigint NOT NULL,
    exchange_id smallint,
    base text,
    base_cg text,
    quote text,
    quote_cg text,
    price numeric,
    price_usd numeric,
    base_volume numeric,
    quote_volume numeric,
    volume_usd numeric,
    last_update integer
);


ALTER TABLE public.ticker OWNER TO exchange;

--
-- Name: ticker_id_seq; Type: SEQUENCE; Schema: public; Owner: exchange
--

CREATE SEQUENCE public.ticker_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ticker_id_seq OWNER TO exchange;

--
-- Name: ticker_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: exchange
--

ALTER SEQUENCE public.ticker_id_seq OWNED BY public.ticker.id;


--
-- Name: actual_coingecko id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.actual_coingecko ALTER COLUMN id SET DEFAULT nextval('public.actual_coingecko_id_seq'::regclass);


--
-- Name: exchange id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange ALTER COLUMN id SET DEFAULT nextval('public.exchange_id_seq'::regclass);


--
-- Name: exchange_tickers_mapper id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange_tickers_mapper ALTER COLUMN id SET DEFAULT nextval('public.exchange_tickers_mapper_id_seq'::regclass);


--
-- Name: historical id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.historical ALTER COLUMN id SET DEFAULT nextval('public.historical_id_seq'::regclass);


--
-- Name: last id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.last ALTER COLUMN id SET DEFAULT nextval('public.last_id_seq'::regclass);


--
-- Name: quote_converter id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.quote_converter ALTER COLUMN id SET DEFAULT nextval('public.quote_converter_id_seq'::regclass);


--
-- Name: ticker id; Type: DEFAULT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.ticker ALTER COLUMN id SET DEFAULT nextval('public.ticker_id_seq'::regclass);


--
-- Name: actual_coingecko actual_coingecko_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.actual_coingecko
    ADD CONSTRAINT actual_coingecko_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: last cg_id_unique; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.last
    ADD CONSTRAINT cg_id_unique UNIQUE (cg_id);


--
-- Name: quote_converter currency; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.quote_converter
    ADD CONSTRAINT currency UNIQUE (currency);


--
-- Name: exchange_tickers_mapper exchange_symbol_unique; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange_tickers_mapper
    ADD CONSTRAINT exchange_symbol_unique UNIQUE (exchange_id, symbol);


--
-- Name: exchange_tickers_mapper exchange_tickers_mapper_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange_tickers_mapper
    ADD CONSTRAINT exchange_tickers_mapper_pkey PRIMARY KEY (id);


--
-- Name: exchange exchnages_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange
    ADD CONSTRAINT exchnages_pkey PRIMARY KEY (id);


--
-- Name: historical gecko_stamp_unique; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.historical
    ADD CONSTRAINT gecko_stamp_unique UNIQUE (cg_id, "timestamp");


--
-- Name: historical historical_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.historical
    ADD CONSTRAINT historical_pkey PRIMARY KEY (id);


--
-- Name: last last_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.last
    ADD CONSTRAINT last_pkey PRIMARY KEY (id);


--
-- Name: quote_converter quote_mapper_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.quote_converter
    ADD CONSTRAINT quote_mapper_pkey PRIMARY KEY (id, currency);


--
-- Name: ticker ticker_pkey; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.ticker
    ADD CONSTRAINT ticker_pkey PRIMARY KEY (id);


--
-- Name: exchange unique_exchnage_cg_id; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.exchange
    ADD CONSTRAINT unique_exchnage_cg_id UNIQUE (cg_identifier);


--
-- Name: ticker unique_ticker; Type: CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.ticker
    ADD CONSTRAINT unique_ticker UNIQUE (exchange_id, base, quote);


--
-- Name: ticker exchange_fk; Type: FK CONSTRAINT; Schema: public; Owner: exchange
--

ALTER TABLE ONLY public.ticker
    ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id) REFERENCES public.exchange(id);


--
-- PostgreSQL database dump complete
--

