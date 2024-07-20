import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2
import random
import re
import bcrypt

class MovieDatabaseApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Movie Database Search Engine")
        self.master.geometry("600x400")
        
        self.conn = psycopg2.connect(
            dbname='cop_final_prj',
            user='postgres',
            password='Tricuong091104@@',
            host='localhost',
            port=5432
        )
        
        self.current_user = None
        self.create_login_screen()

    def create_login_screen(self):
        self.clear_window()
        
        tk.Label(self.master, text="Welcome to Movie Database Search Engine", font=("Helvetica", 24)).pack(pady=20)
        
        tk.Button(self.master, text="Login", command=self.show_login, width=20).pack(pady=10)
        tk.Button(self.master, text="Register", command=self.show_register, width=20).pack(pady=10)
        tk.Button(self.master, text="Exit", command=self.master.quit, width=20).pack(pady=10)

    def show_login(self):
        self.clear_window()
        
        tk.Label(self.master, text="Login", font=("Helvetica", 18)).pack(pady=20)
        
        tk.Label(self.master, text="Username:").pack()
        self.username_entry = tk.Entry(self.master)
        self.username_entry.pack()
        
        tk.Label(self.master, text="Password:").pack()
        self.password_entry = tk.Entry(self.master, show="*")
        self.password_entry.pack()
        
        tk.Button(self.master, text="Login", command=self.login).pack(pady=20)
        tk.Button(self.master, text="Back", command=self.create_login_screen).pack()

    def login(self):
        username = self.username_entry.get().lower()
        password = self.password_entry.get()
        
        cur = self.conn.cursor()
        cur.execute('SELECT password FROM user_ WHERE username = %s', (username,))
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
            self.current_user = username
            messagebox.showinfo("Success", "Please close this window to explore our app")
            self.show_main_menu()
        else:
            messagebox.showerror("Error found", "Invalid username or password")

    def show_register(self):
        self.clear_window()
        
        tk.Label(self.master, text="Register", font=("Helvetica", 18)).pack(pady=20)
        
        tk.Label(self.master, text="Username:").pack()
        self.reg_username_entry = tk.Entry(self.master)
        self.reg_username_entry.pack()
        
        tk.Label(self.master, text="Password:").pack()
        self.reg_password_entry = tk.Entry(self.master, show="*")
        self.reg_password_entry.pack()
        
        tk.Label(self.master, text="Email:").pack()
        self.reg_email_entry = tk.Entry(self.master)
        self.reg_email_entry.pack()
        
        tk.Button(self.master, text="Register", command=self.register).pack(pady=20)
        tk.Button(self.master, text="Back", command=self.create_login_screen).pack()

    def register(self):
        username = self.reg_username_entry.get().lower()
        password = self.reg_password_entry.get()
        email = self.reg_email_entry.get().lower()
        
        if not re.match(r'^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$', email):
            messagebox.showerror("Error", "Invalid email format.")
            return
        
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM user_ WHERE username = %s', (username,))
        if cur.fetchone():
            messagebox.showerror("Error", "Username found in database.")
        else:
            user_id = self.generate_unique_id(cur, 'user_', 'user_id', 1000000, 9999999)
            try:
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                cur.execute('INSERT INTO user_ (user_id, username, email, password) VALUES (%s, %s, %s, %s)', 
                            (user_id, username, email, hashed_password.decode('utf-8')))
                self.conn.commit()
                messagebox.showinfo("Success", "Registration completed.")
                self.create_login_screen()
            except psycopg2.Error as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Registration failed: {e}")

    def show_main_menu(self):
        self.clear_window()
        
        tk.Label(self.master, text=f"Welcome, {self.current_user}!", font=("Helvetica", 18)).pack(pady=20)
        
        buttons = [
            ("Search a movie", self.search_movie),
            ("Add a movie", self.add_movie),
            ("Update a movie", self.update_movie),
            ("Add a review", self.add_review),
            ("Top rated movie", self.top_rated),
            ("View all movies", self.view_all_movies),
            ("My profile", self.my_profile),
            ("Logout", self.logout)
        ]
        
        for text, command in buttons:
            tk.Button(self.master, text=text, command=command, width=20).pack(pady=10)

    def search_movie(self):
        movie_name = simpledialog.askstring("Search Movie", "What is the movie you are looking for?: ")
        if movie_name:
            cur = self.conn.cursor()
            query = '''
                SELECT 
                    movie.movie_id, 
                    movie.title, 
                    movie.description, 
                    movie.release_year, 
                    movie.rating, 
                    movie.rank, 
                    STRING_AGG(DISTINCT actor.name, ', ') AS actors, 
                    STRING_AGG(DISTINCT genre.genre_name, ', ') AS genres, 
                    language.language_name AS language, 

                FROM 
                    movie 
                LEFT JOIN 
                    casting ON movie.movie_id = casting.movie_id 
                LEFT JOIN 
                    actor ON casting.actor_id = actor.actor_id 
                LEFT JOIN 
                    movie_genre ON movie.movie_id = movie_genre.movie_id 
                LEFT JOIN 
                    genre ON movie_genre.genre_id = genre.genre_id 
                LEFT JOIN 
                    movie_language ON movie.movie_id = movie_language.movie_id 
                LEFT JOIN 
                    language ON movie_language.language_id = language.language_id 
                LEFT JOIN 
                    review ON movie.movie_id = review.movie_id 
                WHERE 
                    LOWER(movie.title) LIKE %s
                GROUP BY 
                    movie.movie_id, language.language_name
            '''
            cur.execute(query, (f"%{movie_name.lower()}%",))
            results = cur.fetchall()
            
            if results:
                self.show_search_results(results)
            else:
                messagebox.showinfo("No Results", "No movies found matching that name.")

    def show_search_results(self, results):
        result_window = tk.Toplevel(self.master)
        result_window.title("Search Results")
        result_window.geometry("800x400")
        
        tree = ttk.Treeview(result_window, columns=("ID", "Title", "Description", "Release Year", "Rating", "Rank", "Actors", "Genres", "Language"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Title", text="Title")
        tree.heading("Description", text="Description")
        tree.heading("Release Year", text="Release Year")
        tree.heading("Rating", text="Rating")
        tree.heading("Rank", text="Rank")
        tree.heading("Actors", text="Actors")
        tree.heading("Genres", text="Genres")
        tree.heading("Language", text="Language")
        tree.pack(fill=tk.BOTH, expand=1)
        
        for result in results:
            tree.insert("", tk.END, values=(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8]))
        
        tree.bind("<Double-1>", lambda event: self.show_movie_details(event, results))

    def show_movie_details(self, event, results):
        try:
            item = event.widget.selection()[0]
            movie_id = event.widget.item(item, "values")[0]
            
            for result in results:
                if result[0] == movie_id:  # Match by movie_id
                    detail_window = tk.Toplevel(self.master)
                    detail_window.title(result[1])
                    detail_window.geometry("400x300")
                    
                    details = f"""
                    Title: {result[1]}
                    Description: {result[2]}
                    Release Year: {result[3]}
                    Rating: {result[4]}
                    Rank: {result[5]}
                    Actors: {result[6]}
                    Genres: {result[7]}
                    Language: {result[8]}
                    Reviews: {result[9]}
                    """

                    tk.Label(detail_window, text=details, justify=tk.LEFT).pack(padx=10, pady=10)
                    
                    # Add a button to show reviews
                    tk.Button(detail_window, text="Show Reviews", command=lambda: self.show_reviews(movie_id)).pack(pady=10)
                    break
        except IndexError:
            messagebox.showerror("Error Found", "No movie details available.")
        except Exception as e:
            messagebox.showerror("Error Found", f"An unexpected error occurred: {e}")

    def show_reviews(self, movie_id):
        review_window = tk.Toplevel(self.master)
        review_window.title("Movie Reviews")
        review_window.geometry("600x400")

        # Create a treeview to display reviews
        columns = ("Username", "Rating", "Review")
        tree = ttk.Treeview(review_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill=tk.BOTH, expand=1)

        scrollbar = ttk.Scrollbar(review_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Fetch and display reviews
        cur = self.conn.cursor()
        cur.execute("""
            SELECT u.username, r.rating, r.review
            FROM review r
            JOIN user_ u ON r.user_id = u.user_id
            WHERE r.movie_id = %s
            ORDER BY r.review_id DESC
        """, (movie_id,))
        
        reviews = cur.fetchall()
        
        if reviews:
            for review in reviews:
                tree.insert("", tk.END, values=review)
        else:
            tree.insert("", tk.END, values=("No reviews yet", "", ""))


    def add_movie(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("Add Movie")
        add_window.geometry("300x350")
        
        tk.Label(add_window, text="Title:").pack()
        title_entry = tk.Entry(add_window)
        title_entry.pack()
        
        tk.Label(add_window, text="Description:").pack()
        desc_entry = tk.Entry(add_window)
        desc_entry.pack()
        
        tk.Label(add_window, text="Release Year:").pack()
        year_entry = tk.Entry(add_window)
        year_entry.pack()
        
        tk.Label(add_window, text="Rating (0-10):").pack()
        rating_entry = tk.Entry(add_window)
        rating_entry.pack()
        
        tk.Label(add_window, text="Language:").pack()
        lang_entry = tk.Entry(add_window)
        lang_entry.pack()
        
        def submit_movie():
            try:
                release_year = int(year_entry.get())
                rating = float(rating_entry.get())
                
                if release_year < 1888 or release_year > 2024:  # Assuming current year is 2024
                    raise ValueError("Invalid release year. Must be between 1888 and current year.")
                
                if rating < 0 or rating > 10:
                    raise ValueError("Invalid rating. Must be between 0 and 10.")
                
                cur = self.conn.cursor()
                movie_id = self.generate_unique_id(cur, 'movie', 'movie_id', 100000, 999999)
                
                cur.execute("INSERT INTO movie (movie_id, title, description, release_year, rating) VALUES (%s, %s, %s, %s, %s)", 
                            (movie_id, title_entry.get(), desc_entry.get(), release_year, rating))
                
                # Insert language
                cur.execute("INSERT INTO language (language_name) VALUES (%s) ON CONFLICT (language_name) DO NOTHING", (lang_entry.get(),))
                cur.execute("SELECT language_id FROM language WHERE language_name = %s", (lang_entry.get(),))
                language_id = cur.fetchone()[0]
                cur.execute("INSERT INTO movie_language (movie_id, language_id) VALUES (%s, %s)", (movie_id, language_id))
                
                self.conn.commit()
                messagebox.showinfo("Success", "Movie added successfully!")
                add_window.destroy()
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
            except psycopg2.Error as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Failed to add movie: {e}")
        
        tk.Button(add_window, text="Submit", command=submit_movie).pack(pady=10)


    def update_movie(self):
        movie_name = simpledialog.askstring("Update Movie", "Enter movie name:")
        if movie_name:
            cur = self.conn.cursor()
            cur.execute("SELECT movie_id FROM movie WHERE LOWER(title) = %s", (movie_name.lower(),))
            movie_id = cur.fetchone()
            
            if movie_id:
                movie_id = movie_id[0]
                update_window = tk.Toplevel(self.master)
                update_window.title("Update Movie")
                update_window.geometry("300x200")
                
                options = ["Title", "Description", "Release Year", "Rating"]
                selected_option = tk.StringVar(update_window)
                selected_option.set(options[0])
                
                tk.OptionMenu(update_window, selected_option, *options).pack(pady=10)
                
                tk.Label(update_window, text="New Value:").pack()
                new_value_entry = tk.Entry(update_window)
                new_value_entry.pack()
                
                def submit_update():
                    try:
                        column = selected_option.get().lower().replace(" ", "_")
                        new_value = new_value_entry.get()
                        
                        if column == "release_year":
                            new_value = int(new_value)
                            if new_value < 1888 or new_value > 2024:  # Assuming current year is 2024
                                raise ValueError("Invalid release year. Must be between 1888 and current year.")
                        elif column == "rating":
                            new_value = float(new_value)
                            if new_value < 0 or new_value > 10:
                                raise ValueError("Invalid rating. Must be between 0 and 10.")
                        
                        cur = self.conn.cursor()
                        cur.execute(f"UPDATE movie SET {column} = %s WHERE movie_id = %s", (new_value, movie_id))
                        self.conn.commit()
                        messagebox.showinfo("Success", "Movie updated successfully!")
                        update_window.destroy()
                    except ValueError as ve:
                        messagebox.showerror("Error", str(ve))
                    except psycopg2.Error as e:
                        self.conn.rollback()
                        messagebox.showerror("Error", f"Failed to update movie: {e}")
                
                tk.Button(update_window, text="Submit", command=submit_update).pack(pady=10)
            else:
                messagebox.showinfo("Not Found", "No movie found with that name.")

    def add_review(self):
        movie_name = simpledialog.askstring("Add Review", "Enter your movie name:")
        if movie_name:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM movie WHERE LOWER(title) = %s", (movie_name.lower(),))
            result = cur.fetchone()
            if result:
                review_window = tk.Toplevel(self.master)
                review_window.title("Add Review")
                review_window.geometry("300x200")
                
                tk.Label(review_window, text="Review:").pack()
                review_entry = tk.Entry(review_window)
                review_entry.pack()
                
                tk.Label(review_window, text="Rating (1-10):").pack()
                rating_entry = tk.Entry(review_window)
                rating_entry.pack()
                
                def submit_review():
                    try:
                        rating = int(rating_entry.get())
                        if rating < 1 or rating > 10:
                            raise ValueError("Rating must be between 1 and 10.")
                        
                        movie_id = result[0]
                        review_id = self.generate_unique_id(cur, 'review', 'review_id', 100, 999)
                        user_id = self.get_user_id(self.current_user)
                        cur.execute('INSERT INTO review (review_id, user_id, movie_id, rating, review) VALUES (%s, %s, %s, %s, %s)', 
                                    (review_id, user_id, movie_id, rating, review_entry.get()))
                        self.conn.commit()
                        messagebox.showinfo("Success", "Your review has been added to our system!")
                        review_window.destroy()
                    except ValueError as ve:
                        messagebox.showerror("Error", str(ve))
                    except psycopg2.Error as e:
                        self.conn.rollback()
                        messagebox.showerror("Error", f"Failed to add review: {e}")
                
                tk.Button(review_window, text="Submit", command=submit_review).pack(pady=10)
            else:
                messagebox.showerror("Error", "Movie not found")


    def top_rated(self):
        top_movies_window = tk.Toplevel(self.master)
        top_movies_window.title("Top Rated Movies")
        top_movies_window.geometry("800x400")

        columns = ("Title", "Year", "Rating", "Genres")
        tree = ttk.Treeview(top_movies_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill=tk.BOTH, expand=1)

        scrollbar = ttk.Scrollbar(top_movies_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                m.title,
                m.release_year,
                AVG(r.rating) AS average_rating,
                STRING_AGG(DISTINCT g.genre_name, ', ') AS genres
            FROM 
                movie m
            LEFT JOIN 
                review r ON m.movie_id = r.movie_id
            LEFT JOIN 
                movie_genre mg ON m.movie_id = mg.movie_id
            LEFT JOIN 
                genre g ON mg.genre_id = g.genre_id
            GROUP BY 
                m.movie_id, m.title, m.release_year
            HAVING 
                AVG(r.rating) IS NOT NULL
            ORDER BY 
                average_rating DESC
            LIMIT 10;
        """)
        
        for movie in cur.fetchall():
            tree.insert("", tk.END, values=(movie[0], movie[1], f"{movie[2]:.2f}", movie[3]))
    
    def view_all_movies(self):
        cur = self.conn.cursor()
        cur.execute("SELECT movie_id, title, release_year, rating FROM movie")
        movies = cur.fetchall()
        
        movie_window = tk.Toplevel(self.master)
        movie_window.title("All Movies")
        movie_window.geometry("600x400")
        
        tree = ttk.Treeview(movie_window, columns=("ID", "Title", "Year", "Rating"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Title", text="Title")
        tree.heading("Year", text="Year")
        tree.heading("Rating", text="Rating")
        tree.pack(fill=tk.BOTH, expand=1)
        
        for movie in movies:
            tree.insert("", tk.END, values=movie)

    def my_profile(self):
        cur = self.conn.cursor()
        cur.execute('SELECT username, email, password FROM user_ WHERE username = %s', (self.current_user,))
        user_info = cur.fetchone()
        
        profile_window = tk.Toplevel(self.master)
        profile_window.title("My Profile")
        profile_window.geometry("300x200")
        
        tk.Label(profile_window, text=f"Username: {user_info[0]}").pack(pady=5)
        tk.Label(profile_window, text=f"Email: {user_info[1]}").pack(pady=5)
        tk.Label(profile_window, text=f"Password: {'*' * len(user_info[2])}").pack(pady=5)
        
        tk.Button(profile_window, text="Change Password", command=self.change_password).pack(pady=10)

    def change_password(self):
        new_password = simpledialog.askstring("Change Password", "Enter new password:", show='*')
        if new_password:
            cur = self.conn.cursor()
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cur.execute('UPDATE user_ SET password = %s WHERE username = %s', (hashed_password.decode('utf-8'), self.current_user))
            self.conn.commit()
            messagebox.showinfo("Success", "New password submitted!")

    def logout(self):
        self.current_user = None
        messagebox.showinfo("Logout", "You have been logged out successfully!")
        self.create_login_screen()

    def generate_unique_id(self, cur, table, id_column, start, end):
        while True:
            unique_id = random.randint(start, end)
            cur.execute(f'SELECT * FROM {table} WHERE {id_column} = %s', (unique_id,))
            if not cur.fetchone():
                return unique_id

    def get_user_id(self, username):
        cur = self.conn.cursor()
        cur.execute('SELECT user_id FROM user_ WHERE username = %s', (username,))
        return cur.fetchone()[0]

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MovieDatabaseApp(root)
    root.mainloop()
