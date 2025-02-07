import time
import streamlit as st
from streamlit_cookies_controller import CookieController
import pandas as pd
from wordcloud import WordCloud
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import re
import seaborn as sns

######################################################################################
# Claude Sonnet helped build general structure of these functions to extend search capabilities
def parse_search_terms(search_input):
    """Parse search input to separate column-specific searches and exact phrases"""
    terms = []
    column_searches = {}
    
    # Split by space but preserve quoted phrases
    current_term = []
    in_quotes = False
    
    for i in range(len(search_input)):
        if search_input[i] == '"':
            in_quotes = not in_quotes
            if not in_quotes and current_term:
                terms.append(''.join(current_term))
                current_term = []
        elif search_input[i] == ' ' and not in_quotes:
            if current_term:
                terms.append(''.join(current_term))
                current_term = []
        else:
            current_term.append(search_input[i])
    
    if current_term:
        terms.append(''.join(current_term))

    # Process terms for column-specific searches
    final_terms = []
    
    for i in range(len(terms)):
        term = terms[i]
        if ':' in term:
            col = term.split(':', 1)[0].strip().lower()
            # If the value is empty after the colon, look at the next term
            value = term.split(':', 1)[1]
            if not value.strip():
                # Check if there are more terms to consume
                if i + 1 < len(terms):
                    value = terms[i + 1]
                    i += 1  # Skip the next term as we've used it
            column_searches[col] = value.strip()
        else:
            final_terms.append(term)
    
    return final_terms, column_searches

def apply_search_filters(data, search_input, data_filters):
    """Apply both general and column-specific searches to the dataframe"""
    if not search_input.strip():
        return data
    
    terms, column_searches = parse_search_terms(search_input)
    filtered_data = data.copy()
    
    # Apply column-specific searches
    for col, value in column_searches.items():
        matching_cols = [c for c in filtered_data.columns if c.lower() == col.lower()]
        if matching_cols:
            filtered_data = filtered_data[
                filtered_data[matching_cols[0]].astype(str).str.contains(value, case=False)
            ]
                
    for term in terms:
        if term:  # Skip empty terms
            term_filter = filtered_data.astype(str).apply(
                lambda x: x.str.contains(term, case=False)
            ).any(axis=1)
            filtered_data = filtered_data[term_filter]
    
    return filtered_data

def data_page(data):
    # Header
    st.header("Netflix TV Shows and Movies")
    st.markdown("""This Netflix dataset below represents 8000+ TV shows and movies. It shows trends in content overtime that Netflix has decided to procure.  
                Click each tab on the header bar, in order, to explore what this may mean for future productions.
                """)

    # Sidebar
    st.sidebar.title('Data Filters')
    columns = data.columns.tolist()
    data_filters = []

    for col in columns:
        if st.sidebar.checkbox(col, value=True):
            data_filters.append(col)
    
    st.markdown("")
    st.markdown("")
    # Search
    search_input = st.text_input(
        'Search for specific titles, filter movies by rating, display only what you want, or just explore the data!',
        placeholder='Add a specific tag to search by column -> Director: Tarantino. And/or surround the search in "quotes" to search specific phrases. (e.g. Director: "Quentin Tarantino")'
    )

    if search_input:
        data = apply_search_filters(data, search_input, data_filters)
    # Only keep selected
    data = data[data_filters]
        
    # Table
    if not data.empty:
        st.dataframe(data, hide_index=True, height=550)
        st.write(f"Found {len(data)} matches")
    else:
        st.warning("No matches found")
        
######################################################################################

def word_cloud_page(data):
    text = ' '.join(data['title'].astype(str))
    
    # Clean the text by removing special characters
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove common word clutter (could add bool to keep this)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of'}
    text = ' '.join([word for word in text.lower().split() if word not in common_words])
    
    progress_bar = st.progress(0)
    wordcloud = WordCloud()
    for percent in range(3):
        wordcloud = WordCloud(width=800, height=400, mode="RGBA", background_color="rgb(14,17,23)").generate(text)
        time.sleep(0.4)
        progress_bar.progress((percent+1)*33+1)
    
    progress_bar.empty()
    
    fig = plt.figure()
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.subplots_adjust(left=0, right=5, top=5, bottom=0)
    fig.patch.set_facecolor((0.055,0.066,0.09,1))
    st.pyplot(fig)
    st.caption("Most common words in titles for Netflix movies and TV shows.")
    
######################################################################################
    
def rating_dist_bars(data):
    progress_bar = st.progress(0)
    for percent in range(3):
        time.sleep(0.25)
        progress_bar.progress((percent+1)*33+1)
    
    progress_bar.empty()
    
    # Remove random non-rating values from the data
    valid_data = data[~data['rating'].isin(['66 min', '74 min', '84 min'])]
    rating_counts = valid_data['rating'].value_counts().sort_values()
    
    fig, ax = plt.subplots(figsize=(9, 4))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    colors = ['goldenrod' if 'tv' in rating.lower() else 'cornflowerblue' for rating in rating_counts.index]
    sns.barplot(x=rating_counts.values, y=rating_counts.index, palette=colors)
    
    plt.title('Distribution of Content Ratings', fontsize=20, color='white')
    plt.xticks(color='white')
    plt.yticks(fontsize=12, color='white')
    plt.ylabel('')
    plt.tight_layout()
    plt.annotate(
        "Adult rated content dominates",
        xy=(60, 10),
        xytext=(800, 9),
        color='white',
        fontsize=16
    )
    
    movie_patch = mpatches.Patch(color='cornflowerblue', label='Movie Ratings')
    tv_patch = mpatches.Patch(color='goldenrod', label='TV Ratings')
    plt.legend(handles=[movie_patch, tv_patch], loc='upper right', facecolor=(0.055, 0.066, 0.09, 1), edgecolor='white', labelcolor='white')
    
    fig.patch.set_facecolor((0.055, 0.066, 0.09, 1))
    ax.set_facecolor((0.055, 0.066, 0.09, 1))
    st.pyplot(fig)

def content_type_trends(data):
    max_year = data['release_year'].max()
    data_filtered = data[data['release_year'] < max_year]
    
    yearly_content = data_filtered.groupby(['release_year', 'type']).size().unstack(fill_value=0)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    for content_type in yearly_content.columns:
        ax.plot(yearly_content.index, yearly_content[content_type], label=content_type)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    
    ax.set_title('Content Releases Over Time', fontsize=20, color='white')
    ax.set_xlabel('Release Year', fontsize=14, color='white')
    ax.set_ylabel('Number of Titles Added', fontsize=14, color='white')
    ax.legend(facecolor=(0.055, 0.066, 0.09, 1), edgecolor='white', labelcolor='white')
    
    plt.xticks(color='white')
    plt.yticks(color='white')
    plt.tight_layout()
    plt.annotate(
        "Movies seem to be getting less popular to \n make and/or to acquire for Netflix",
        xy=(1950, 250),
        xytext=(1950, 250),
        color='white',
        fontsize=16
    )
    
    fig.patch.set_facecolor((0.055, 0.066, 0.09, 1))
    ax.set_facecolor((0.055, 0.066, 0.09, 1))
    
    st.pyplot(fig)
    
def conclusion(data):
    st.header("In Summary")
    st.markdown("")
    st.markdown("") # spacers
    st.markdown("")
    st.markdown("")
    st.code("""
                There are a few key takeaways after visualizing the Netflix Data.  
                
                First is that love must sell. It is by far the most common title in all of the movies and tv shows analyzed. Stories involving a girl and love appear to be most prominent.  
                Second, movies are getting less and less releases over time. This also correlates with Netflix not acquiring as many movies. There are a few possible reasons for this. It
                could be that the newly more popular extended story tv shows (like Mandalorian or Breaking Bad) are succesful. It could be that tv shows work better with Netflix's subscription 
                model, as more viewers will be on the site for longer if they need to come back to finish they show. Or it could be a combination of reasons.  
                And the last takeaway I will point out, adult rated tv shows and movies tend to be most common. This could fall under similar reasoning as the second point, in that 
                more of Netflix's user base may be older or this type of content has seen surges in popularity lately.  
                
                Ultimately, Netflix certainly knows what they are doing and analyzes their data much closer than this. So we can surely follow their trends and expect that we will do well.
                """)
    
######################################################################################
#    MAIN (the lazy way)
######################################################################################

data = pd.read_csv("netflix_titles.csv")

st.set_page_config(
    page_title="Netflix Data",
    page_icon="🎬",
    layout="wide"
)

cookie_pages = [
    "Raw Data", 
    "Word Cloud", 
    "Content Over Time", 
    "Ratings Distribution", 
    "Summary"
]
cookies = CookieController()
if not cookies.get('visited_tabs'):
    cookies.set('visited_tabs', False)
     
if cookies.get('visited_tabs') == False:
    cookies.set('visited_tabs', True)
    for page in cookie_pages:
        cookies.set(page, False)

if 'visited_pages' not in st.session_state:
    st.session_state.visited_tabs = cookies.getAll()

# Use query parameters to determine the current page
query_params = st.query_params
if "page" in query_params:
    current_page = query_params["page"]
else:
    current_page = "Raw Data"
st.session_state.current_page = current_page

if not st.session_state.visited_tabs[current_page]:
    cookies.set(current_page, True)

# Thank you dataprofessor, https://github.com/dataprofessor/streamlit_navbar/blob/main/app_navbar.py
# for the navbar inspiration below. And thanks Claude for making it really easy to do CSS... especially inline string css.

# Add Bootstrap CSS
st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)

# Custom CSS for the nav bar
st.markdown("""
    <style>
        [data-testid="stSidebarCollapsedControl"] {
            z-index: 0;
        }
        [data-testid="stHeader"] {
            height: 0;
        }
        .custom-navbar {
            position: fixed;
            top: 1px;
            left: 0;
            right: 0;
            z-index: 50;
            background-color: #7F1F00;
        }
        .container-fluid {
            height: 80px;
            display: flex;
        }
        .nav-link {
            color: white !important;
            margin-right: 1rem;
            transition: opacity 0.3s;
            z-index: 50;
            text-decoration: none !important;
            font-size: 30px;
            border-right-style: solid;
            border-right-color: #601600;
            padding-right: 32px;
            padding-top: 17px;
        }
        .nav-link.visited {
            color: gray !important;
            margin-right: 1rem;
            transition: opacity 0.3s;
            z-index: 50;
            text-decoration: none !important;
            font-size: 30px;
            border-right-style: solid;
            border-right-color: #601600;
            padding-right: 32px;
            padding-top: 17px;
        }
        a.navbar-brand {
            color: white !important;
            margin-right: 1rem;
            z-index: 50;
            font-size: 40px;
            padding-top: 8px;
        }
        .nav-link:hover {
            opacity: 0.8;
            text-decoration: none !important;
        }
        .nav-link.active {
            border-bottom: 2px solid white;
        }
        .st-emotion-cache-6qob1r e1c29vlm8 {  /* Streamlit's sidebar class */
            position: fixed;
            z-index: 999;
            padding-top: 3rem;
        }
        [data-testid="stToolbar"] {
            position: fixed;
            top: 12px !important;
            right: 0 !important;
            z-index: 21 !important;
        }
        [data-testid="stSidebar"] {
            z-index: 10 !important;
        }
        [data-testid="stVerticalBlock"] {
            gap: 5px;
        }
    </style>
""", unsafe_allow_html=True)

def create_navbar(pages):
    nav_html = '<nav class="custom-navbar"><div class="container-fluid">'
    nav_html += '<a class="navbar-brand nav-link" href="?page=Raw Data" target="_self">Netflix Data Explorer</a>'
    for page in pages:
        visited_class = "visited" if st.session_state.visited_tabs[page] == True else ""
        nav_html += f'<a class="navbar-brand nav-link {visited_class}" href="?page={page}" target="_self">{page}</a>'
    nav_html += '</div></nav>'
    st.markdown(nav_html, unsafe_allow_html=True)

pages_names = [
    "Word Cloud", 
    "Content Over Time", 
    "Ratings Distribution", 
    "Summary"
]
create_navbar(pages_names)

# Wrap main content in a div for proper spacing
st.markdown('<div class="main">', unsafe_allow_html=True)

pages = {
    "Raw Data": data_page,
    "Word Cloud": word_cloud_page,
    "Content Over Time": content_type_trends,
    "Ratings Distribution": rating_dist_bars,
    "Summary": conclusion
}
pages[st.session_state.current_page](data)

st.markdown('</div>', unsafe_allow_html=True)
