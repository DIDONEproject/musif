from musif.scoreinfo import ScoreInfo


def get_operatic_features(score_info: ScoreInfo) -> dict:
    return {
        'Opera': score_info.opera,
        'Aria': score_info.aria,
        'Act': score_info.act,
        'Scene': score_info.scene,
        'Act&Scene': score_info.act_and_scene,
        'City': score_info.city,
        'Country': score_info.country,
        'Form': score_info.form,
    }


def get_role_features(score_info: ScoreInfo) -> dict:
    return {
        'RoleType': score_info.role_type,
        'Gender': score_info.gender,
        'Role': score_info.role,
    }
