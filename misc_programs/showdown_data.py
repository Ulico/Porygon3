import requests
import json
import json5
from enum import Enum


def get_dict(data_type):
    if data_type not in ["pokedex", "abilities", "moves", "items"]:
        print("invalid data type")
        return None
    url = f"https://play.pokemonshowdown.com/data/{data_type}.js"
    # print(url)

    response = requests.get(url)

    if response.status_code == 200:
        js_object_start = response.text.find("{")
        js_object_end = response.text.rfind("}") + 1
        js_object = response.text[js_object_start:js_object_end]

        return json5.loads(js_object)
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        return None


# def get_move_dict():

#
