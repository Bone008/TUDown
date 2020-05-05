import tudown
import getpass
import re

# called by main when the operation has been read from sys args
def internal_main(config, arg, preview_only):
    if arg == "list":
        for item in config:
            print(item["id"], "-", item["url"])
        return 0
    if arg == 'all':
        # run all password functions once to handle all prompts
        # immediately and make the rest of the execution passive
        for item in config:
            if 'passwd' in item:
                item['passwd']()
        for item in config:
            print('---- Running item', item["id"], '----')
            run_item(item, preview_only)
            print()
        return 0
    
    item = next((item for item in config if item["id"] == arg), None)
    if item:
        run_item(item, preview_only)
        return 0
    else:
        print("config not found, \'list\' to list all")
        return -1

def run_item(item, preview_only):
    allow_multi_matches = item.get("allow_multi_matches", False)
    do_resolve = item.get("resolve", True)
    do_flatten = item.get("flatten", False)
    user = item.get("user", '')
    passwdFunc = item.get("passwd", lambda: '')
    headers = item.get("headers", {})
    
    tudown.main(item["url"], item["targets"], allow_multi_matches, do_resolve, do_flatten, preview_only, user, passwdFunc(), headers)


# to be called by config script
def main(config):
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("   {} list           list all configs".format(sys.argv[0]))
        print("   {} <id>           execute config <id>".format(sys.argv[0]))
        print("   {} <id> preview   preview config <id>".format(sys.argv[0]))
        print("   {} all            execute all configs".format(sys.argv[0]))
        print("   {} all preview    preview all configs".format(sys.argv[0]))
        sys.exit(-1)
    else:
        preview_only = (len(sys.argv) == 3 and sys.argv[2] == 'preview')
        exitcode = internal_main(config, sys.argv[1], preview_only)
        sys.exit(exitcode)




# == helper functions ==

# create a config filter function that matches a url by regex
def match_url(regex_str):
    r = re.compile(regex_str, re.IGNORECASE)
    return lambda url, filename: bool(r.search(url))

# create a config filter function that matches a filename by regex
def match_filename(regex_str):
    r = re.compile(regex_str, re.IGNORECASE)
    return lambda url, filename: bool(r.search(filename))

# used to logically combine multiple config filters
def match_all(*args):
    return lambda url, filename: all(map(lambda f: f(url, filename), args))
def match_any(*args):
    return lambda url, filename: any(map(lambda f: f(url, filename), args))

# get a course URL by id
def moodle_url(course_id):
    return "https://www.moodle.tum.de/course/view.php?id=" + str(course_id)

pwd_cache = {}
# create a password provider that reads from console,
# multiple reads with the same description will result in only one prompt
def pwd_from_console(desc):
    def executor():
        if not desc in pwd_cache:
            pwd_cache[desc] = getpass.getpass("Password (" + desc + "): ")
        return pwd_cache[desc]
    
    return executor

# create a password provider that directly returns a fixed password
def pwd_direct(pwd):
    return lambda: pwd
