import json
import re
import pytz

import platform,socket,re,uuid,json,psutil,logging # type: ignore
from datetime import datetime
import geocoder, geopy      # type: ignore

from termcolor import cprint # type: ignore
    
    
def combine_string(list_of_string: list) -> str:
    """
    Concatenates a list of strings into a single string with newline separators.

    @param list_of_string: A list of strings to be concatenated.
    
    @return: A single string formed by joining the input strings with newline characters.
    """
    
    result = ""
    for s in list_of_string:
        result = result + s + "\n"
    return result
        

def iterate_through_location(location: json):
    """
    Iterates through a dictionary of locations to find the first valid URI or URL.

    The function checks each entry in the dictionary to see if it contains a 'uri' or 'url' key,
    returning the first non-None value found.

    @param location: A dictionary where each value may contain 'uri' or 'url' keys.

    @return: The first non-None URI or URL found in the dictionary, or None if neither is found.
    """
    
    for loc_data in location.values():
            
            if not isinstance(loc_data, dict):  # Check if the location data is a dictionary
                continue
            
            # Check if 'uri' or 'url' key exists in the dictionary
            uri = loc_data.get("uri")
            url = loc_data.get("url")
            
            # Return the first found uri or url
            if uri:
                return uri
            if url:
                return url
    return None


def sanitize_input(text: str) -> str:
    """
    Remove leading and trailing whitespace
    
    @param text: input text
    
    @return: sanitized text
    """
    
    text = text.strip()
    # Check if the text is not empty
    if not text:
        raise ValueError("Input text cannot be empty or only whitespace.")
    return text
        
        
def clean_tag(string: str) -> str:
    """
    Function to remove text between specified tag from a string
    """
    return re.sub(r"<(instructions|examples|context|documents)>.*?</\1>", "", string)


def system() -> str:
    try:
        info={}
        info['platform']=platform.system()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['architecture']=platform.machine()
        info['hostname']=socket.gethostname()
        info['ip-address']=socket.gethostbyname(socket.gethostname())
        info['mac-address']=':'.join(re.findall('..', '%012x' % uuid.getnode()))
        info['processor']=platform.processor()
        info['ram']=str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB"
        return str(info)
    except Exception as e:
        logging.exception(e)
        
    
def location():
    return geopy.geocoders.Nominatim(user_agent="GetLoc").reverse(geocoder.ip('me').latlng)


def real_time():
    return datetime.now(tz = pytz.timezone("Asia/Bangkok")).strftime('%Y-%m-%d %H:%M:%S %Z')
