TRUNCATE TABLE staging.order_events RESTART IDENTITY CASCADE;
TRUNCATE TABLE monitoring.microbatch_run_log RESTART IDENTITY CASCADE;
DELETE FROM control.pipeline_state WHERE state_key = 'sales_stream';
