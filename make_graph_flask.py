from flask import Flask, jsonify, request, render_template
import requests
import networkx as nx
import json
import matplotlib.pyplot as plt

app = Flask(__name__)

LASTFM_API_KEY = "e72fe324cfc10f3f83e141295d682948"
LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
DEFAULT_COLOR = "#A9A9A9"
COLOR_MAP = {
    "Rock": "#DC143C",  # Crimson
    "Hip-Hop": "#FF4500",  # Orange Red
    "Hip Hop": "#FF4500",  # Orange Red
    "Rap": "#FF4500",  # Orange Red
    "Jazz": "#4B0082",  # Indigo
    "Classical": "#FFD700",  # Gold
    "Country": "#32CD32",  # Lime Green
    "Electronic": "#00FFFF",  # Cyan
    "Reggae": "#FF8C00",  # Dark Orange
    "Blues": "#0000FF",  # Blue
    "Metal": "#8B0000",  # Dark Red
    "Folk": "#228B22",  # Forest Green
    "R&B": "#8A2BE2",  # Blue Violet
    "RnB": "#8A2BE2",  # Blue Violet
    "Latin": "#FF6347",  # Tomato
    "Dance": "#7FFFD4",  # Aquamarine
    "Soul": "#DDA0DD",   # Plum
    "Indie": "#FFFF00",   # Yellow
    "Pop": "#FF69B4"  # Hot Pink
}

def get_similar_songs(track, artist, num_songs):
    params = {
        "method": "track.getsimilar",
        "track": track,
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": num_songs,  # Adjust how many recommendations you want
    }

    response = requests.get(LASTFM_API_URL, params=params)

    if response.status_code != 200:
        return {"error": "Failed to fetch data from Last.fm"}

    data = response.json()

    if "similartracks" not in data or "track" not in data["similartracks"]:
        return {"error": "No recommendations found"}

    recommendations = [
        {"title": song["name"], "artist": song["artist"]["name"]}
        for song in data["similartracks"]["track"]
    ]

    return recommendations

def get_song_info(track, artist):
    params = {
        "method": "track.getInfo",
        "track": track,
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    response = requests.get(LASTFM_API_URL, params=params)

    if response.status_code != 200:
        return {"error": "Failed to fetch data from Last.fm"}

    data = response.json()

    if "track" in data:
        return data["track"]

    return None

def make_graph(song, num_songs, num_layers):
    graph = nx.Graph()

    node_attributes = {song["name"] + " - " + song["artist"] : {"title" : song["name"], "artist" : song["artist"]}}
    draw_connections(graph, song["name"], song["artist"], num_songs, num_layers, node_attributes)

    for node in node_attributes:
        song_info = get_song_info(node_attributes[node]["title"], node_attributes[node]["artist"])
        node_attributes[node]["listeners"] = song_info["listeners"]
        tag_list = song_info["toptags"]["tag"]
        color = DEFAULT_COLOR
        tags = []
        for i in range(len(tag_list)):
            tags.append(tag_list[i]["name"])

        color_found = False
        for i in range(len(tags)):
            tag = tags[i]
            for key in COLOR_MAP.keys():
                if key.lower() in tag.lower():
                    # print(key + " in " + tag)
                    color = COLOR_MAP[key]
                    color_found = True
                    break
            if color_found:
                break
        node_attributes[node]["color"] = color

        # node_attributes[node]["tags"] = tags

    nx.set_node_attributes(graph, node_attributes)

    # nx.draw(graph, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=15)
    # plt.show()

    # Convert NetworkX graph to JSON for JavaScript usage
    data = nx.readwrite.json_graph.node_link_data(graph)
    graph_json = json.dumps(data)

    return graph_json

def draw_connections(graph, track, artist, num_songs, num_layers, node_attributes):
    if num_layers == 0:
        return

    recs = get_similar_songs(track, artist, num_songs)
    graph.add_node(track + " - " + artist)

    for i in range(len(recs)):
        node_id = recs[i]["title"] + " - " + recs[i]["artist"]
        graph.add_node(node_id)
        graph.add_edge(track + " - " + artist, node_id)
        node_attributes[node_id] = {"title" : recs[i]["title"], "artist" : recs[i]["artist"]}


    for i in range(len(recs)):
        draw_connections(graph, recs[i]["title"], recs[i]["artist"], num_songs, num_layers - 1, node_attributes)

def song_search(term):
    params = {
        "method": "track.search",
        "track": term,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(LASTFM_API_URL, params=params)
    data = response.json()

    if "results" in data and "trackmatches" in data["results"]:
        tracks = data["results"]["trackmatches"]["track"]
        if len(tracks) > 0:
            return tracks[0]
    return None

@app.route('/')
def render():
    return render_template('graph_UI.html')

@app.route("/search", methods=["POST"])
def search():
    song = song_search(request.json.get("input"))
    graph_json = make_graph(song, 4, 3)
    return graph_json

if __name__ == "__main__":
    app.run(debug=True)
