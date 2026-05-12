-- Abiskript arendajale või juhendajale.
-- Põhijuhendis kasutab õppija tavaliselt `docker compose down -v` käsku.
-- See fail tühjendab ainult praktikumi andmed ja töövoo järjehoidja.

TRUNCATE TABLE staging.order_events RESTART IDENTITY CASCADE;
TRUNCATE TABLE monitoring.microbatch_run_log RESTART IDENTITY CASCADE;
DELETE FROM control.pipeline_state WHERE state_key = 'sales_stream';
