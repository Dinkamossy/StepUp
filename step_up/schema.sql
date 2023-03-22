DROP TABLE IF EXISTS user;

CREATE TABLE user
(
    username       TEXT NOT NULL ,
    password       TEXT NOT NULL,
    email          TEXT NOT NULL,
    picture        BLOB,
    sex            TEXT NOT NULL,
    race           TEXT NOT NULL,
    age            TEXT NOT NULL,
    feet           INTEGER NOT NULL,
    inches         INTEGER NOT NULL,
    userid         INTEGER PRIMARY KEY UNIQUE,
    current_weight INTEGER NOT NULL,
    target_weight  INTEGER NOT NULL,
    weight_circum  INTEGER NOT NULL,
    neck_circum    INTEGER NOT NULL,
    body_comp      INTEGER NOT NULL
);
