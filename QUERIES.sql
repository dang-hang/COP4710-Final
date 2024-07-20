-- 1. User Authentication

SELECT password FROM user_ WHERE username = %s;

-- 1.1. User Registration
INSERT INTO user_ (user_id, username, email, password) VALUES (%s, %s, %s, %s);

-- 2. Search movie:
SELECT movie.*, STRING_AGG(DISTINCT actor.name, ', ') AS actors, 
	STRING_AGG(DISTINCT genre.genre_name, ', ') AS genres, language.language_name AS language,
	STRING_AGG(DISTINCT review.review, ' | ') AS reviews FROM movie LEFT JOIN casting ON movie.movie_id = casting.movie_id 
	LEFT JOIN actor ON casting.actor_id = actor.actor_id LEFT JOIN movie_genre ON movie.movie_id = movie_genre.movie_id 
	LEFT JOIN genre ON movie_genre.genre_id = genre.genre_id LEFT JOIN movie_language ON movie.movie_id = movie_language.movie_id 
	LEFT JOIN language ON movie_language.language_id = language.language_id LEFT JOIN review ON movie.movie_id = review.movie_id 
	WHERE LOWER(movie.title) LIKE %s GROUP BY movie.movie_id, language.language_name;

-- 3. Add movie
INSERT INTO movie (movie_id, title, description, release_year, rating, rank, language) VALUES (%s, %s, %s, %s, %s, %s, %s);

-- 4. Update movie
UPDATE movie SET {column} = %s WHERE movie_id = %s;

-- 5. Add review
INSERT INTO review (review_id, user_id, movie_id, rating, review) VALUES (%s, %s, %s, %s, %s);

-- 6. Change user's password
UPDATE user_ SET password = %s WHERE username = %s;

-- 7. Top 10 highest movie ratings
SELECT m.movie_id, m.title,.release_year,(r.rating) AS average_rating, STRING_AGG(DISTINCT g.genre_name, ', ') 
	AS genres FROM movie m LEFT JOIN review r ON m.movie_id = r.movie_id LEFT JOIN movie_genre mg 
	ON m.movie_id = mg.movie_id LEFT JOIN genre g ON mg.genre_id = g.genre_id 
	GROUP BY m.movie_id, m.title, m.release_year HAVING AVG(r.rating) IS NOT NULL 
	ORDER BY average_rating DESC LIMIT 10;

-- 8. User profile
SELECT username, email, password FROM user_ WHERE username = %s



-- UPDATING

-- Ensure release_year is within a reasonable range
ALTER TABLE Movie
ADD CONSTRAINT check_release_year 
CHECK (release_year BETWEEN 1888 AND EXTRACT(YEAR FROM CURRENT_DATE));

-- Ensure rating is between 0 and 10
ALTER TABLE Movie
ADD CONSTRAINT check_rating
CHECK (rating >= 0 AND rating <= 10);

-- Ensure email format is valid
ALTER TABLE User_
ADD CONSTRAINT check_email_format
CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$');


-- Trigger to update movie rating when a new review is added
CREATE OR REPLACE FUNCTION update_movie_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Movie
    SET rating = (
        SELECT AVG(rating)
        FROM Review
        WHERE movie_id = NEW.movie_id
    )
    WHERE movie_id = NEW.movie_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_review_insert
AFTER INSERT ON Review
FOR EACH ROW
EXECUTE FUNCTION update_movie_rating();

-- Trigger to prevent deleting a movie with reviews
CREATE OR REPLACE FUNCTION prevent_movie_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM Review WHERE movie_id = OLD.movie_id) THEN
        RAISE EXCEPTION 'Cannot delete movie with existing reviews';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_movie_delete
BEFORE DELETE ON Movie
FOR EACH ROW
EXECUTE FUNCTION prevent_movie_deletion();

-- Trigger to automatically set the rank based on rating
CREATE OR REPLACE FUNCTION update_movie_rank()
RETURNS TRIGGER AS $$
BEGIN
    NEW.rank = (
        SELECT COUNT(*) + 1
        FROM Movie
        WHERE rating > NEW.rating
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_movie_insert_update
BEFORE INSERT OR UPDATE OF rating ON Movie
FOR EACH ROW
EXECUTE FUNCTION update_movie_rank();


-- 9. Get all reviews for a movie
SELECT r.review_id, u.username, r.rating, r.review
FROM review r
JOIN user_ u ON r.user_id = u.user_id
WHERE r.movie_id = %s
ORDER BY r.review_id DESC;