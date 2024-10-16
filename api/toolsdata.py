browsing_web = {
    "name": "browsing_web",
    "description": "Function to retrieve, browsing links and topics from internet browser",
    "input_schema": {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "The keyword or term that you want to search for"
            }
        },
        "required": ["search_term"]
    }
}


browsing_map = {
    "name": "browsing_map",
    "description": """
        Function to get location or search for facilities around the areas.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "The keyword or term of type of the facility that you want to search for. For example: 'shop', 'gas', etc..."
            },
            "place": {
                "type": "string",
                "description": "The place, location that you want to search around it. If this parameter is set, the other parameters are not used. Defaults to None."
            },
            "street": {
                "type": "string",
                "description": "House number/street. Defaults to None."
            },
            "city": {
                "type": "string",
                "description": "City of search. Defaults to None."
            },
            "country": {
                "type": "string",
                "description": "country of search. Defaults to None."
            },
            "radius": {
                "type": "integer",
                "description": "Expand the search square by the distance in kilometers. Defaults to 5."
            }
        },
        "required": ["search_term"]
    }
}


scrape_webpage = {
    "name": "scrape_webpage",
    "description": "Function access into the webpage an scarpe all the available informations from the body of the webpage.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The url link of the webpage that you want to srape the information"
            }
        },
        "required": ["search_term"]
    }
}



def return_tool():
    return [
        browsing_web,
        browsing_map,
        scrape_webpage
    ]
