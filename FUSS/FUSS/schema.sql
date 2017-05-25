DROP TABLE IF EXISTS entries;
CREATE TABLE entries(
  id integer PRIMARY KEY AUTOINCREMENT,
  sensor_type integer NOT NULL,
  date datetime NOT NULL,
  reading text NOT NULL
);

DROP TABLE IF EXISTS sensors;
CREATE TABLE sensors(
  id integer PRIMARY KEY AUTOINCREMENT,
  name text NOT NULL,
  mac_address bigint NOT NULL,
  function_number integer NOT NULL,
  sensor_category integer NOT NULL
);

DROP TABLE IF EXISTS users;
CREATE TABLE users(
  id integer PRIMARY KEY AUTOINCREMENT,
  username text NOT NULL,
  password text NOT NULL
);

DROP TABLE IF EXISTS sensor_category;
CREATE TABLE sensor_category
(
  id integer PRIMARY KEY AUTOINCREMENT,
  name text NOT NULL
);

INSERT INTO sensor_category (name) VALUES ("MISC");
INSERT INTO sensor_category (name) VALUES ("TEMPERATURE");
INSERT INTO sensor_category (name) VALUES ("HUMIDYTY");
