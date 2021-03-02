import math


def get_file_name_features(file_name: str) -> dict:
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    opera_title = file_name[0:3]
    label = file_name.split("-", 2)[0]
    aria_id = file_name.split("[")[-1].split("]")[0]
    aria_title = file_name.split("-", 2)[1]
    composer = file_name.split("-", -1)[-1].split("[", 2)[0]
    year = file_name.split("-", -2)[-2]
    decade = str(int(year) // 100) + str(math.floor(int(year) % 100 / 10) * 10) + "s"
    act = file_name.split("[", 1)[-1].split(".", 1)[0]
    scene = file_name.split(".", 1)[-1].split("]", 1)[0]

    return {
        "AriaOpera": opera_title,
        "AriaLabel": label,
        "AriaId": aria_id,
        "AriaTitle": aria_title,
        "Composer": composer,
        "Year": year,
        "Decade": decade,
        "Act": act,
        "Scene": scene,
        "ActAndScene": act + scene,
    }
