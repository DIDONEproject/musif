def get_gender(character: str) -> str:
    """
    Returns gender of a character depending on it's name.
    """

    if character in ["Didone", "Selene", "Dircea", "Creusa", "Semira", "Mandane"]:
        return "female"
    else:
        return "male"


def get_role(character: str) -> str:
    """
    Returns general role type for specific operatic characters
    """

    if character in ["Demofoonte", "Licomede", "Tito", "Catone", "Fenicio"]:
        return "Senior ruler"
    elif character in [
        "Didone",
        "Dircea",
        "Cleofide",
        "Mandane",
        "Deidamia",
        "Sabina",
        "Vitellia",
        "Marzia",
        "Cleonice",
    ]:
        return "Female lover 1"
    elif character in [
        "Enea",
        "Poro",
        "Arbace",
        "Timante",
        "Achille",
        "Adriano",
        "Sesto",
        "Cesare",
        "Alceste",
        "Demetrio",
    ]:
        return "Male lover 1"
    elif character in [
        "Selene",
        "Creusa",
        "Erissena",
        "Semira",
        "Emirena",
        "Servila",
        "Emilia",
        "Barsene",
    ]:
        return "Female lover 2"
    elif character in [
        "Iarba",
        "Alessandro",
        "Artaserse",
        "Cherinto",
        "Teagene",
        "Farnaspe",
        "Annio",
        "Olinte",
    ]:
        return "Male lover 2"
    elif character in ["Gandarte", "Aquilio", "Fulvio"]:
        return "Male lover 3"
    elif character in ["Araspe", "Megabise", "Adrasto", "Arcade", "Publio", "Mitrano"]:
        return "Confidant"
    elif character in ["Osmida", "Timagene", "Artabano", "Matusio", "Ulisse", "Osroa"]:
        return "Antagonist"
