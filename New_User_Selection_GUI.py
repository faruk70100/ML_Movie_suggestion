import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QScrollArea, QComboBox,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

import Movie_suggestion

class MovieRecommenderGUI(QWidget):
    def __init__(self, df_movies):
        super().__init__()
        self.df_movies = df_movies
        self.filtered_df = df_movies.copy()
        self.new_user_list = pd.DataFrame(columns=['movieId'])

        self.setWindowTitle("Movie Recommender")
        self.resize(1200, 700)

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)

        # Left Panel
        left_panel = QVBoxLayout()

        # Filters
        filter_layout = QHBoxLayout()

        # Genre filter
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(False)
        self.genre_combo.setInsertPolicy(QComboBox.NoInsert)
        self.genre_combo.setMinimumWidth(150)
        self.genre_combo.setMaximumWidth(200)
        self.genre_combo.addItem("All Genres")
        all_genres = sorted(set(g for sublist in self.df_movies['genres'].str.split('|') for g in sublist))
        for genre in all_genres:
            self.genre_combo.addItem(genre)
        filter_layout.addWidget(QLabel("Genre:"))
        filter_layout.addWidget(self.genre_combo)

        # Year filter
        self.year_start_combo = QComboBox()
        self.year_end_combo = QComboBox()
        all_years = sorted(self.df_movies['year'].dropna().astype(int).unique())
        self.year_start_combo.addItem("Start")
        self.year_end_combo.addItem("End")
        for year in all_years:
            self.year_start_combo.addItem(str(year))
            self.year_end_combo.addItem(str(year))
        filter_layout.addWidget(QLabel("Year Range:"))
        filter_layout.addWidget(self.year_start_combo)
        filter_layout.addWidget(self.year_end_combo)

        filter_btn = QPushButton("Apply Filters")
        filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(filter_btn)

        left_panel.addLayout(filter_layout)

        # Movie selection table
        self.movie_table = QTableWidget()
        self.movie_table.setColumnCount(4)
        self.movie_table.setHorizontalHeaderLabels(["Select", "Name", "Year", "Genres"])
        self.movie_table.horizontalHeader().setStretchLastSection(True)
        self.movie_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.movie_table.verticalHeader().setVisible(False)
        self.movie_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.movie_table.setColumnWidth(1, 250)
        self.movie_table.setColumnWidth(2, 60)
        self.movie_table.setColumnWidth(3, 150)

        self.populate_movie_table(self.filtered_df)

        left_panel.addWidget(self.movie_table)

        layout.addLayout(left_panel, 2)

        # Center Recommend Button
        center_layout = QVBoxLayout()
        self.recommend_button = QPushButton("Recommend >>")
        self.recommend_button.setFixedWidth(150)
        self.recommend_button.clicked.connect(self.recommend_movies)
        center_layout.addStretch()
        center_layout.addWidget(self.recommend_button)
        center_layout.addStretch()
        layout.addLayout(center_layout)

        # Right Panel (Recommended movies)
        self.recommend_table = QTableWidget()
        self.recommend_table.setColumnCount(3)
        self.recommend_table.setHorizontalHeaderLabels(["Name", "Year", "Genres"])
        self.recommend_table.horizontalHeader().setStretchLastSection(True)
        self.recommend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recommend_table.verticalHeader().setVisible(False)
        self.recommend_table.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.recommend_table, 2)

    def populate_movie_table(self, df):
        self.movie_table.setRowCount(len(df))
        for row, (_, movie) in enumerate(df.iterrows()):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, movieId=movie['movieId']: self.update_user_list(state, movieId))
            self.movie_table.setCellWidget(row, 0, checkbox)

            # Name
            self.movie_table.setItem(row, 1, QTableWidgetItem(movie['title']))

            # Year
            year_item = QTableWidgetItem(str(movie['year']) if pd.notnull(movie['year']) else "")
            self.movie_table.setItem(row, 2, year_item)

            # Genres
            self.movie_table.setItem(row, 3, QTableWidgetItem(movie['genres']))

    def update_user_list(self, state, movieId):
        if state == Qt.Checked:
            if movieId not in self.new_user_list['movieId'].values:
                self.new_user_list.loc[len(self.new_user_list)] = [movieId]
        else:
            self.new_user_list = self.new_user_list[self.new_user_list['movieId'] != movieId]

    def apply_filters(self):
        genre = self.genre_combo.currentText()
        year_start = self.year_start_combo.currentText()
        year_end = self.year_end_combo.currentText()

        df = self.df_movies.copy()

        # Genre filtering
        if genre != "All Genres":
            df = df[df['genres'].str.contains(genre, na=False)]

        # Year filtering
        if year_start.isdigit():
            df = df[df['year'].astype(float) >= int(year_start)]
        if year_end.isdigit():
            df = df[df['year'].astype(float) <= int(year_end)]

        self.filtered_df = df
        self.populate_movie_table(self.filtered_df)

    def recommend_movies(self):
        df_new_list = self.new_user_list['movieId'].tolist()
        ratings = pd.read_csv("ratings.csv")
        recommended = Movie_suggestion.movie_sugges(self.df_movies , ratings, df_new_list)
        self.show_recommendations(recommended)

    def show_recommendations(self, df_recommended):
        self.recommend_table.setRowCount(len(df_recommended))
        for row, (_, movie) in enumerate(df_recommended.iterrows()):
            self.recommend_table.setItem(row, 0, QTableWidgetItem(movie['title']))
            self.recommend_table.setItem(row, 1, QTableWidgetItem(str(movie['year'])))
            self.recommend_table.setItem(row, 2, QTableWidgetItem(movie['genres']))

def add_year_col(df):
    df['year'] = df['title'].str.extract(r'\((\d{4})\)')
    df['title'] = df['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
    return df

# Example usage:
if __name__ == "__main__":
    df = pd.read_csv("movies.csv")  # Must include columns: movieId, name, genres, year
    df = add_year_col(df)
    app = QApplication(sys.argv)
    gui = MovieRecommenderGUI(df)
    gui.show()
    sys.exit(app.exec_())
