import requests
import pandas as pd
import json


# The Client ID of the Happify Application
CLIENT_ID = '4d2ec298dfdd4a378de66ddef1a45d9a'

def authorize():
	""" Instructs user how to authorize Happify to access data 
	
	Args:
		None
	Returns:
		Whatever access token the user has pasted in the input field
	"""
	params = {
		'client_id' : CLIENT_ID,
        'response_type' : 'token',
        'redirect_uri' : 'http://localhost:8888/callback',
        'scope' : 'playlist-modify-private playlist-read-collaborative user-library-read playlist-read-private'
    }
	r = requests.get('https://accounts.spotify.com/authorize', params=params)
	print("Authorize access to your Spotify account by visiting:\n {}".format(r.request.url))
	print("Paste the accesstoken parameter from the callback url here:")
	return input()
	
	
def get_playlists(access_token):
	""" Fetches a users playlists
	https://beta.developer.spotify.com/documentation/web-api/reference/playlists/get-a-list-of-current-users-playlists/

	Args:
		access_token (string): The access token obtained by authorizing Happify
	Returns:
		A pandas DataFrame with the item attribute of the JSON response

	"""

	endpoint = 'https://api.spotify.com/v1/me/playlists'
	headers = {
		'Authorization': 'Bearer '+  access_token
	}
	r = requests.get(endpoint, headers=headers)
	r.raise_for_status()
	return pd.DataFrame(r.json()['items'])
   
def get_playlist_tracks(user_id, playlist_id, access_token):
	""" Fetches all tracks from a playlist
	https://beta.developer.spotify.com/documentation/web-api/reference/playlists/get-playlists-tracks/

	Args:
		user_id (string): The user id of the user who owns the playlist. 
		playlist_id: The playlists id
		access_token (string): The access token obtained by authorizing Happify.
	Returns:
		A list with the track field of all tracks returned.

	"""
	endpoint = 'https://api.spotify.com/v1/users/{}/playlists/{}/tracks'.format(user_id, playlist_id)
	headers = {
		'Authorization': 'Bearer '+  access_token
	}
	params = {
		'fields':'items(track(name,id,album(name),artists))'
	}
	r =  requests.get(endpoint, headers=headers, params=params)
	r.raise_for_status()
	tracks = [item['track'] for item in r.json()['items']]
	return tracks   
	
def get_track_features(track_ids, access_token):
	""" Fetches meta data for a list of track ids
	https://beta.developer.spotify.com/documentation/web-api/reference/tracks/get-audio-features/

	Args:
		track_ids (list of string): All track ids to fetch meta data for. 
		playlist_id: The playlists id
		access_token (string): The access token obtained by authorizing Happify.
	Returns:
		A list with the audio features returned.

	"""
	endpoint = 'https://api.spotify.com/v1/audio-features'
	headers = {
		'Authorization': 'Bearer '+  access_token
	}
	params = {
		'ids' : ",".join(track_ids)
	}
	r = requests.get(endpoint, headers=headers, params=params)
	r.raise_for_status()
	audio_features = r.json()['audio_features']
	return audio_features

def track_features(access_token, tracks):
	""" Combines basic track data with meta data bout the tracks

	Args:
		access_token (string): The access token obtained by authorizing Happify.
		tracks (list of string): All track ids to fetch meta data for. 
		
	Returns:
		A pandas DataFrame with the combined track and feature data.
	"""
	tracks_df = pd.DataFrame(tracks)
	feature_df = pd.DataFrame(get_track_features(list(tracks_df['id']), access_token))
	tracks_df = pd.merge(tracks_df, feature_df, on = 'id', suffixes = ['_track', '_feature'])
	return tracks_df
	
def get_user_id(access_token):
	""" Fetches the ID of the current user
	Args:
		access_token (string): The access token obtained by authorizing Happify.
		
	Returns:
		The user id of the current user.
	"""
	endpoint = 'https://api.spotify.com/v1/me'
	headers = {
		'Authorization': 'Bearer '+  access_token
	}
	return requests.get(endpoint, headers=headers).json()['id']
	
def create_playlist(access_token, user_id, playlist_name, description = "Playlist created by Happify"):
	""" Creates an empty playlist for the specied user
	
	Args:
		access_token (string): The access token obtained by authorizing Happify.
		user_id (string): The ID of the user for which the playlist is created.
		playlist_name (string): The name of the playlist.
		description (string): Description for the playlist.
		
	Returns:
		The id of the created playlist.
	"""
	endpoint = 'https://api.spotify.com/v1/users/{}/playlists'.format(user_id)
	headers = {
		'Authorization': 'Bearer '+  access_token,
		'Content-Type': 'application/json'
	}
	data = r'{"name":"'+playlist_name+r'", "public":false,"description":"' + description + r'"}'

	params = {
		'name' : playlist_name,
		'public' : 'false',
		'description' : description
	}
	r = requests.post(endpoint, headers=headers, data = data)
	r.raise_for_status()
	return r.json()['id']
    
def add_tracks_to_playlist(access_token, playlist_id, user_id, track_uris):
	""" Adds tracks to a playlist
	
	Args:
		access_token (string): The access token obtained by authorizing Happify.
		playlist_id (string): The ID of the playlist the tracks should be added to.
		user_id (string): The ID of the user who owns the playlist.
		track_uris (list of string): A lit with spotify uri's representing the tracks to be added to the playlist.
		
	Returns:
		The id of the created playlist.
	"""
	endpoint = 'https://api.spotify.com/v1/users/{}/playlists/{}/tracks'.format(user_id, playlist_id)
	headers = {
		'Authorization': 'Bearer '+  access_token,
		'Content-Type': 'application/json'
	}
	data = {
		"uris": track_uris
	}
	data = json.dumps(data)
	return requests.post(endpoint, headers=headers, data = data)
    
    
    
	