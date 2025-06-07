import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
import warnings
from scipy.sparse import csr_matrix

def create_matrix(df):
    N = len(df['userId'].unique())
    M = len(df['movieId'].unique())

    user_mapper = dict(zip(np.unique(df["userId"]), list(range(N))))
    movie_mapper = dict(zip(np.unique(df["movieId"]), list(range(M))))

    user_inv_mapper = dict(zip(list(range(N)), np.unique(df["userId"])))
    movie_inv_mapper = dict(zip(list(range(M)), np.unique(df["movieId"])))

    user_index = [user_mapper[i] for i in df['userId']]
    movie_index = [movie_mapper[i] for i in df['movieId']]

    X = csr_matrix((df["rating"], (movie_index, user_index)), shape=(M, N))

    return X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper


def find_similar_movies_for_list(
    movie_ids: list, # Changed to accept a list
    movie_mapper: dict,
    movie_inv_mapper: dict,
    X: np.ndarray,
    k: int = 10, # Number of *total* unique recommendations to return
    metric: str = 'cosine',
    show_distance: bool = False # This won't be used in the final return, but kept for consistency
) -> list:
    """
    Finds unique similar movies for a list of input movie IDs.

    Args:
        movie_ids (list): A list of movie IDs for which to find similar movies.
        movie_mapper (dict): Maps movie IDs to their internal matrix indices.
        movie_inv_mapper (dict): Maps internal matrix indices back to movie IDs.
        X (np.ndarray): The feature matrix (e.g., TF-IDF or vector embeddings of movies).
        k (int): The total number of unique similar movie IDs to return.
        metric (str): The distance metric to use for NearestNeighbors (e.g., 'cosine', 'euclidean').
        show_distance (bool): Whether to return distances (not used in final output list).

    Returns:
        list: A list of up to 'k' unique similar movie IDs.
    """
    all_suggested_ids = set()

    for movie_id in movie_ids:
        if movie_id not in movie_mapper:
            print(f"Warning: Movie ID {movie_id} not found in movie_mapper. Skipping.")
            continue # Skip to the next movie_id

        movie_ind = movie_mapper[movie_id]
        movie_vec = X[movie_ind]

        num_neighbors_per_movie = max(k + 5, 2)

        kNN = NearestNeighbors(n_neighbors=num_neighbors_per_movie, algorithm="brute", metric=metric)
        kNN.fit(X)
        movie_vec = movie_vec.reshape(1, -1)

        distances, indices = kNN.kneighbors(movie_vec, return_distance=True)

        for i in range(len(indices.flatten())):
            n_index = indices.flatten()[i]
            suggested_movie_id = movie_inv_mapper[n_index]

            if suggested_movie_id != movie_id:
                all_suggested_ids.add(suggested_movie_id)

    final_suggestions_list = list(all_suggested_ids)

    final_suggestions_list = [mid for mid in final_suggestions_list if mid not in movie_ids]

    return final_suggestions_list[:k]


def recommend_movies_for_user(df1, movies, ratings, X, user_mapper, movie_mapper, movie_inv_mapper, k=10):
    #df1 = ratings[ratings['userId'] == user_id]
    watched_movie_ids = df1

    #movie_title_lookup  = dict(zip(movies['movieId'], movies['title']))

    suggested_movie_ids = find_similar_movies_for_list(watched_movie_ids, movie_mapper, movie_inv_mapper, X, k)

    if not suggested_movie_ids:
        return pd.DataFrame(columns=movies.columns)
    else:
        # Filter the main 'movies' DataFrame to get details of suggested movies
        suggested_movies_df = movies[movies['movieId'].isin(suggested_movie_ids)].copy()

        return suggested_movies_df


def movie_sugges(movies, ratings, df_new_list):

    user_freq = ratings[['userId', 'movieId']].groupby('userId').count().reset_index()
    user_freq.columns = ['userId', 'n_ratings']

    #basic analyzes
    mean_rating = ratings.groupby('movieId')[['rating']].mean()
    lowest_rated = mean_rating['rating'].idxmin()
    movies.loc[movies['movieId'] == lowest_rated]
    highest_rated = mean_rating['rating'].idxmax()
    movies.loc[movies['movieId'] == highest_rated]
    ratings[ratings['movieId'] == lowest_rated]
    ratings[ratings['movieId'] == highest_rated]

    movie_stats = ratings.groupby('movieId')[['rating']].agg(['count', 'mean'])
    movie_stats.columns = movie_stats.columns.droplevel()

    # setting matrix for training
    X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper = create_matrix(ratings)

    #testing recommending for user_id 150
    #user_id = 150
    return recommend_movies_for_user(df_new_list, movies, ratings, X, user_mapper, movie_mapper, movie_inv_mapper, k=10)

