CREATE TABLE User_ (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE Movie (
    movie_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    release_year INT,
    rating DECIMAL(3, 2),
    rank INT
);

CREATE TABLE Review (
    review_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES User_(user_id),
    movie_id INT REFERENCES Movie(movie_id),
    rating INT CHECK (rating >= 1 AND rating <= 10),
    review TEXT
);


CREATE TABLE Language (
    language_id SERIAL PRIMARY KEY,
    language_name VARCHAR(50) NOT NULL
);

CREATE TABLE Movie_Language (
    movie_id INT REFERENCES Movie(movie_id),
    language_id INT REFERENCES Language(language_id),
    PRIMARY KEY (movie_id, language_id)
);

CREATE TABLE Genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL
);

CREATE TABLE Movie_Genre (
    movie_id INT REFERENCES Movie(movie_id),
    genre_id INT REFERENCES Genre(genre_id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE Actor (
    actor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Casting (
    actor_id INT REFERENCES Actor(actor_id),
    movie_id INT REFERENCES Movie(movie_id),
    role VARCHAR(100),
    PRIMARY KEY (actor_id, movie_id)
);

ALTER TABLE user_ ALTER COLUMN password TYPE VARCHAR(60);