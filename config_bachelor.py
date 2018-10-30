import hookmeup

# TODO: - handle moodle folder names - what to put for moodle regexes?

def unidir(subdir):
    return "../" + subdir

config = [
    {
        "id": "dwt",
        "url": "http://wwwalbers.in.tum.de/lehre/2017SS/dwt/index.html.de",
        "targets": [
            (hookmeup.match_url("2017SS/dwt/.+\.pdf"), unidir("06_DWT/Skript"))
        ]
    },
    {
        "id": "dwt_ue",
        "url": "http://wwwalbers.in.tum.de/lehre/2017SS/dwt/uebung/index.html.de",
        "targets": [
            (hookmeup.match_url("2017SS/dwt/uebung/.+\.pdf"), unidir("06_DWT/Übung"))
        ],
        "user": "dwt17",
        "passwd": hookmeup.pwd_direct("markov")
    },
    
    {
        "id": "theo",
        "url": "https://www7.in.tum.de/um/courses/theo/ss2016/index.php?category=uebungen",
        "targets": [
            (hookmeup.match_url("/ss2016/.+\.pdf"), unidir("automation/local_playground/theo"))
        ]
    },
    
    {
        "id": "eidi2",
        "url": hookmeup.moodle_url(28866),
        "allow_duplicates": False,
        "targets": [
            (hookmeup.match_filename("blatt\d\d.*\.(pdf|zip)"),
                unidir("automation/local_playground/eidi2/übung")),
            (hookmeup.match_all(hookmeup.match_url("www.moodle\.tum\.de"), hookmeup.match_filename("$(?<!php)")),
                unidir("automation/local_playground/eidi2")),
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle")
    },
    {
        "id": "ki",
        "url": hookmeup.moodle_url(28827),
        "targets": [
            (hookmeup.match_filename("Practical"), unidir("automation/local_playground/ki/Practical")),
            (hookmeup.match_filename("ArtificialIntelligence_\d|exercise_\d"), unidir("automation/local_playground/ki/Skript")),
            (hookmeup.match_all(), unidir("automation/local_playground/ki"))
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle")
        
        # TODO not actually implemented, but would be cool
        # "postprocess": [
            # hookmeup.post_rename({
                # "main.pdf": "IsabelleTutorial.pdf"
            # })
        # ],
    },
    {
        "id": "physics",
        "url": hookmeup.moodle_url(28738),
        "targets": [
            (hookmeup.match_filename("lecture.+\.pdf"), unidir("automation/local_playground/physics/Skript")),
            (hookmeup.match_all(), unidir("automation/local_playground/physics"))
        ],
        "user": "ga65ciy",
        "passwd": hookmeup.pwd_from_console("Moodle")
    }
]

hookmeup.main(config)
