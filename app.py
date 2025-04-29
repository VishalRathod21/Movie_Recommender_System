import streamlit as st
import pickle
import pandas as pd
import requests
import json
from datetime import datetime

# Initialize session state for user data
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'user_reviews' not in st.session_state:
    st.session_state.user_reviews = {}
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {'name': 'Guest', 'preferences': {}}

# Custom CSS for styling the app
st.markdown("""
    <style>
    body {
        background: #000000; /* Updated background to full black */
        color: #ffffff; /* White text color for contrast */
        font-family: 'Arial', sans-serif;
    }
    .title {
        color: #FFD700;
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        margin-top: 20px;
        text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
    }
    .subtitle {
        color: #eee;
        text-align: center;
        font-size: 18px;
        margin-bottom: 40px;
    }
    .featured-section {
        padding: 20px;
        background: rgba(0, 0, 0, 0.8); /* Slightly transparent black for contrast */
        border-radius: 10px;
        margin-bottom: 40px;
    }
    .featured-title {
        color: #FFD700;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 20px;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }
    .featured-movie {
        margin-bottom: 20px;
    }
    .featured-movie img {
        border-radius: 15px;
        transition: transform 0.3s ease;
        width: 100%;
        height: auto;
    }
    .featured-movie img:hover {
        transform: scale(1.05);
    }
    .stButton>button {
        background: #FFD700;
        color: black;
        border: none;
        padding: 12px 30px;
        font-size: 16px;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: #FFA500;
        transform: translateY(-3px);
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
    }
    footer {visibility: hidden;}
    .carousel {
        display: flex;
        overflow-x: auto;
        scroll-behavior: smooth;
        padding: 20px 0;
        gap: 20px;
    }
    .carousel-item {
        flex: 0 0 auto;
        width: 200px;
    }
    .review-section {
        background: rgba(0, 0, 0, 0.5);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .user-profile {
        background: rgba(0, 0, 0, 0.5);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# TMDB API key
TMDB_API_KEY = 'b86a89b1952c1b69a380fca68fe2d524'

# Fetch trending movies
def fetch_trending_movies():
    url = f'https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:10]

# Fetch movies by genre
def fetch_movies_by_genre(genre_id):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&sort_by=vote_average.desc'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:10]

# Fetch movie trailer
def fetch_movie_trailer(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    data = response.json()
    videos = data.get('results', [])
    for video in videos:
        if video['type'] == 'Trailer' and video['site'] == 'YouTube':
            return f"https://www.youtube.com/embed/{video['key']}"
    return None

# Enhanced movie details function
def fetch_movie_details(movie_id):
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US'
        response = requests.get(url)
        data = response.json()

        poster_path = data.get('poster_path', '')
        full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image+Available"
        movie_url = f"https://www.themoviedb.org/movie/{movie_id}"
        
        # Get additional details
        overview = data.get('overview', 'No overview available')
        release_date = data.get('release_date', '')
        genres = [genre['name'] for genre in data.get('genres', [])]
        rating = data.get('vote_average', 0)
        
        return {
            'poster': full_path,
            'url': movie_url,
            'overview': overview,
            'release_date': release_date,
            'genres': genres,
            'rating': rating
        }
    except Exception as e:
        st.error(f"Error fetching movie details: {e}")
        return None

# Function to recommend movies with enhanced features
def recommend(movie, num_recommendations=10):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = similarity[index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num_recommendations+1]

        recommended_movies = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            details = fetch_movie_details(movie_id)
            if details:
                details['title'] = movies.iloc[i[0]].title
                recommended_movies.append(details)

        return recommended_movies
    except Exception as e:
        st.error(f"Error in recommendation function: {e}")
        return []

# Load the movie data and similarity matrix
movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Main app layout
st.markdown('<h1 class="title">🎬 Movie Recommender System</h1>', unsafe_allow_html=True)

# User Profile Section
with st.sidebar:
    st.markdown('<div class="user-profile">', unsafe_allow_html=True)
    st.subheader("👤 User Profile")
    user_name = st.text_input("Your Name", value=st.session_state.user_profile['name'])
    st.session_state.user_profile['name'] = user_name
    st.markdown('</div>', unsafe_allow_html=True)

# Navigation
page = st.sidebar.radio("Navigation", ["Home", "Trending", "By Genre", "Watchlist", "Reviews"])

if page == "Home":
    # Featured movies section
    st.markdown('<div class="featured-section"><h2 class="featured-title">Featured Movies</h2>', unsafe_allow_html=True)
    
    # Fetch trending movies for the featured section
    featured_movies = fetch_trending_movies()[:5]  # Get top 5 trending movies
    
    # Display featured movies
    cols = st.columns(len(featured_movies))
    for i, movie in enumerate(featured_movies):
        with cols[i]:
            details = fetch_movie_details(movie['id'])
            if details:
                st.markdown(f"<a href='{details['url']}' target='_blank'><div class='featured-movie'><img src='{details['poster']}' /></div></a>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #FFD700;'>🎬 {movie['title']}</p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Movie selection dropdown
    selected_movie_name = st.selectbox(
        'Choose a movie to get recommendations:',
        movies['title'].values,
        index=0
    )

    # Display recommendations on button click with loading animation
    if st.button('Get Recommendations 🎥'):
        with st.spinner("Fetching your recommendations..."):
            recommended_movies = recommend(selected_movie_name, num_recommendations=10)

        if recommended_movies:
            st.markdown("<h3 style='text-align: center;'>Here are movies we recommend for you:</h3>", unsafe_allow_html=True)
            
            # Create a horizontal scrolling container
            st.markdown('<div class="carousel">', unsafe_allow_html=True)
            
            for movie in recommended_movies:
                st.markdown(f"""
                    <div class="carousel-item">
                        <a href='{movie["url"]}' target='_blank'>
                            <img src='{movie["poster"]}' style='width: 100%; border-radius: 15px;' />
                        </a>
                        <p style='text-align: center;'>🎬 {movie['title']}</p>
                        <p style='text-align: center;'>⭐ {movie['rating']}/10</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Add to watchlist button
                if st.button(f"Add to Watchlist", key=f"watch_{movie['title']}"):
                    if not any(m['title'] == movie['title'] for m in st.session_state.watchlist):
                        st.session_state.watchlist.append({
                            'id': movie['url'].split('/')[-1],
                            'title': movie['title']
                        })
                        st.success(f"Added {movie['title']} to your watchlist!")
                
                # Show trailer if available
                trailer_url = fetch_movie_trailer(movie['url'].split('/')[-1])
                if trailer_url:
                    st.video(trailer_url)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Sorry, we couldn't find any recommendations for this movie.")

elif page == "Trending":
    st.subheader("🔥 Trending Movies This Week")
    trending_movies = fetch_trending_movies()
    cols = st.columns(5)
    for i, movie in enumerate(trending_movies):
        with cols[i % 5]:
            details = fetch_movie_details(movie['id'])
            if details:
                st.image(details['poster'], use_container_width=True)
                st.markdown(f"**{movie['title']}**")
                st.markdown(f"⭐ {movie['vote_average']}/10")

elif page == "By Genre":
    st.subheader("🎭 Top Rated Movies by Genre")
    genres = {
        "Action": 28,
        "Comedy": 35,
        "Drama": 18,
        "Horror": 27,
        "Romance": 10749,
        "Sci-Fi": 878,
        "Thriller": 53
    }
    selected_genre = st.selectbox("Select Genre", list(genres.keys()))
    genre_movies = fetch_movies_by_genre(genres[selected_genre])
    
    cols = st.columns(5)
    for i, movie in enumerate(genre_movies):
        with cols[i % 5]:
            details = fetch_movie_details(movie['id'])
            if details:
                st.image(details['poster'], use_container_width=True)
                st.markdown(f"**{movie['title']}**")
                st.markdown(f"⭐ {movie['vote_average']}/10")

elif page == "Watchlist":
    st.subheader("📝 Your Watchlist")
    if st.session_state.watchlist:
        cols = st.columns(5)
        for i, movie in enumerate(st.session_state.watchlist):
            with cols[i % 5]:
                details = fetch_movie_details(movie['id'])
                if details:
                    st.image(details['poster'], use_container_width=True)
                    st.markdown(f"**{movie['title']}**")
                    if st.button(f"Remove from Watchlist", key=f"remove_{i}"):
                        st.session_state.watchlist.pop(i)
                        st.experimental_rerun()
    else:
        st.info("Your watchlist is empty. Add movies from the Home page!")

elif page == "Reviews":
    st.subheader("📝 Movie Reviews")
    selected_movie = st.selectbox("Select a movie to review", movies['title'].values)
    
    if selected_movie:
        movie_id = movies[movies['title'] == selected_movie].iloc[0].movie_id
        details = fetch_movie_details(movie_id)
        
        if details:
            st.image(details['poster'], width=200)
            st.markdown(f"**{selected_movie}**")
            
            # Display existing reviews
            if selected_movie in st.session_state.user_reviews:
                st.subheader("Previous Reviews")
                for review in st.session_state.user_reviews[selected_movie]:
                    st.markdown(f"""
                        <div class="review-section">
                            <p><strong>{review['user']}</strong> - {review['date']}</p>
                            <p>Rating: {'⭐' * review['rating']}</p>
                            <p>{review['comment']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Add new review
            st.subheader("Write a Review")
            rating = st.slider("Rating", 1, 5, 3)
            comment = st.text_area("Your Review")
            if st.button("Submit Review"):
                if selected_movie not in st.session_state.user_reviews:
                    st.session_state.user_reviews[selected_movie] = []
                st.session_state.user_reviews[selected_movie].append({
                    'user': st.session_state.user_profile['name'],
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'rating': rating,
                    'comment': comment
                })
                st.success("Review submitted successfully!")

# Footer section
st.markdown("---")
st.markdown("<p style='text-align: center;'>🎥 Enjoy watching your recommendations! ✨</p>", unsafe_allow_html=True)
