TRUNCATE TABLE source_muuk_laiem;

<<<<<<< HEAD
copy source_muuk_laiem (
=======
COPY source_muuk_laiem (
>>>>>>> bbba71bb3de89519a3d39fcf41a2af446c9e281d
    tellimuse_nr,
    kuupaev,
    kliendi_id,
    kliendi_nimi,
    kliendi_linn,
    kliendityyp,
    toote_nimi,
    kategooria,
    tootemark,
    kampaania_nimi,
    kampaania_tyyp,
    liiklusallikas,
    makseviis,
    kogus,
    uhikuhind,
    muugisumma
)
FROM '/data/veebipoe_muuk_lisaulesanne.csv'
WITH (FORMAT csv, HEADER true);
