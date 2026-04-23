-- Test kontrollib, et marketing-vaates puudub email veerg täielikult.
-- Tagastab 0 rida -> test läbib (korrektselt maskeeritud).
-- Tagastab 1+ rida -> test ebaõnnestub (email on vaatest nähtav).

SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'secured'
  AND table_name   = 'dim_users_marketing'
  AND column_name  = 'email'
