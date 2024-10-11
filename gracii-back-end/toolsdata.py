functionB = {
    "name": "link_to_knowledgebase",
    "description": "A datasource that store every things about Chí Phèo story by Nam Cao. Use this to search more about the story,\
        the characters name Bá Kiến, Thị Nở, Tự Lãng, Chí Phèo, or other small characters in the story. \
            Use this to know more and to analysis when asking about the story and the characters.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The texts or keywords that you want to search for the reference  or for more information about it. \
                    This should be a pargraphs, a lot of string that you want to find more context,or a text that can help \
                        you understand more about the story, the characters ",
            }
        },
        "required": ["query"],
    },
}


functionC = {
    "name": "get_article",
    "description": "A tool to retrieve an up to date Wikipedia article. \
                    Use side by side with get_information tool for comparing and evaluation informations",
    "input_schema": {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "The search term to find a wikipedia article by title",
            },
        },
        "required": ["search_term"],
    },
}


def return_tool():
    return [
        functionB,
        functionC
    ]
