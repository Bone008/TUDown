import hookmeup

# TODO: - handle moodle folder names - what to put for moodle regexes?

def unidir(subdir):
    return "../../" + subdir

config = [
    {
        "id": "robotics",
        "url": "http://robvis01.informatik.tu-muenchen.de/courses/robotics/slides/",
        "targets": [
            (hookmeup.match_url("robotics/slides/.+\.pdf"), unidir("Master/01_Robotics/Skript")),
        ],
        "user": "robotics",
        "passwd": hookmeup.pwd_direct("slides")
    },
    {
        "id": "proglang",
        "url": "http://www.in.tum.de/i02/lehre/wintersemester-1819/vorlesungen/programming-languages/",
        "targets": [
            (hookmeup.match_url("i02/ProgLang_Slides/.+\.pdf"), unidir("Master/01_Progamming_Languages/Skript")),
            (hookmeup.match_url("i02/ProgLang_Exc/.+\.pdf"), unidir("Master/01_Progamming_Languages/Übungen")),
        ]
    },
    {
        "id": "advanced",
        "url": "http://www14.in.tum.de/lehre/2018WS/ada/index.html.de",
        "targets": [
            (hookmeup.match_url("lehre/2018WS/ada/.+\.pdf"), unidir("Master/01_Advanced_Algorithms/Skript")),
        ]
    },
    {
        "id": "advanced_ue",
        "url": "http://www14.in.tum.de/lehre/2018WS/ada/uebung/index.html.en",
        "targets": [
            (hookmeup.match_url("ada/uebung/.+\.pdf"), unidir("Master/01_Advanced_Algorithms/Excercises")),
        ]
    },
    {
        "id": "deep",
        "url": "https://www.moodle.tum.de/course/view.php?id=41931",
        "allow_duplicates": False,
        "targets": [
            (hookmeup.match_filename(".+\.pdf"),
                unidir("Master/01_Deep_Learning/Skript")),
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle"),
    },
    {
        "id": "mocap",
        "url": "https://www.moodle.tum.de/course/view.php?id=41752",
        "allow_duplicates": False,
        "targets": [
            (hookmeup.match_filename("\d+.+\.(pdf|zip)"),
                unidir("Master/01_3D_Scanning/Skript")),
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle"),
    },
    { # TODO: Gastschlüssel!
        "id": "japanese",
        "url": "https://www.moodle.tum.de/course/view.php?id=45136",
        "allow_duplicates": False,
        "targets": [
            (hookmeup.match_filename(".+\.pdf"),
                unidir("Master/01_Japanisch")),
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle"),
    },
    {
        "id": "ml",
        "url": "https://piazza.com/tum.de/fall2018/in2064/resources",
        "targets": [
            (hookmeup.match_all(), unidir("Master/01_Machine_Learning"))
        ],
        "user": "lukas.bonauer@yahoo.de",
        "passwd": hookmeup.pwd_from_console("Piazza")
    },
]

hookmeup.main(config)
