import re
import json
from html import unescape
from threading import Thread, active_count
from requests import Session, utils
from requests.exceptions import RequestException
from lxml import html
from os import makedirs
from os.path import exists, getmtime, dirname
from calendar import timegm
from time import strptime, sleep
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor
from traceback import print_exc

NUM_THREADS = 4  # max number of threads

def create_filepath(filepath):
    if not exists(filepath):
        # ignore errors, since there may be race conditions when creating the dirs
        try:
            makedirs(filepath)
        except FileExistsError:
            pass

def write_to_file(filename, response):
    create_filepath(dirname(filename))
    with open(filename, 'wb') as fd:
        for chunk in response.iter_content(1024):
            fd.write(chunk)

def download_file(session, url, filename, preview_only):
    try:
        try_download_file(session, url, filename, preview_only)
    except:
        print('[!] Download of', filename, 'failed with an exception!')
        print_exc()

def try_download_file(session, url, filename, preview_only):
    if not exists(filename):
        response = session.get(url, allow_redirects=True)
        if response.status_code == 200:
            if not preview_only:
                write_to_file(filename, response)
            print('[+] ' + filename)
        else:
            print('[!] Download of', filename, 'failed:', response.status_code)
    else:
        response = session.head(url, allow_redirects=True)
        if response.status_code == 200:
            last_mod_file = getmtime(filename)
            try:
                last_mod_www = timegm(strptime(response.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z'))
            except KeyError:
                print('Can\'t check {} for updates.'.format(url))
                last_mod_www = last_mod_file

            if last_mod_www > last_mod_file:
                response = session.get(url)
                if response.status_code == 200:
                    if not preview_only:
                        write_to_file(filename, response)
                    print('[M] ' + filename)
                else:
                    print('[!] Download of', filename, 'failed: ', response.status_code)
        else:
            print('[!] Download of', filename, 'failed: ', response.status_code)



def sanitize(str):
    str = str.strip()
    str = re.sub(' ', '_', str)
    str = re.sub('[^\w\-_.)(]', '', str)
    return str

# returns a list of tuples (download_link, target_path)
# target path is a relative subfolder for the link (ending with a / unless equal to '')
def collect_links(session, url, closed_set = set()):
    print("Collecting from", url, "...")
    
    response = session.get(url)
    html_root = html.fromstring(response.text)
    html_root.make_links_absolute(url)
    
    # for moodle links, only extract links from subsection of the page
    if 'moodle.tum.de' in url:
        if 'mod/assign/view.php' in url:
            link_elems = html_root.cssselect('#intro a')
        else:
            link_elems = html_root.cssselect('#region-main a')
            
        #link_elems = html_root.xpath('//div[@class="region-content"]//a')
        #hrefs = [elem.get('href') for elem in html_root.cssselect('.course-content a')]
    
    elif 'piazza.com' in url:
        # piazza page is completely rendered using js, so we have to parse that to get the files :(
        # find class id
        network_matches = re.findall(r'this\.network\s*=\s*({.*});$', response.text, re.MULTILINE)
        if len(network_matches) <= 0:
            print("Piazza: No class id found!")
            return []

        network = json.loads(network_matches[0])
        class_id = network['id']

        # collect readable section names
        section_matches = re.findall(r'this\.resource_sections\s*=\s*(\[.*\]);$', response.text, re.MULTILINE)
        section_names = {}
        if len(section_matches) > 0:
            sections = json.loads(section_matches[0])
            section_names = dict((s['name'], s['title']) for s in sections)

        # find files
        file_matches = re.findall(r'this\.resource_data\s*=\s*(\[.*\]);$', response.text, re.MULTILINE)
        if len(file_matches) <= 0:
            print("Piazza: No file descriptions found")
            return []

        file_descriptions = json.loads(file_matches[0])
        download_link_base = 'https://piazza.com/class_profile/get_resource/' + class_id + '/'

        def file_mapper(f):
            # TODO not sure if files without sections exist, not handled here
            section_name = f['config']['section']
            if section_name in section_names:
                section_name = section_names[section_name]

            return (download_link_base + f['id'], unescape(section_name) + "/")

        return list(map(file_mapper, file_descriptions))
        
    else:
        # extract all links
        link_elems = html_root.cssselect('a')
    
    
    recursed_links = []
    for l in link_elems:
        href = l.get("href")
        
        # remove hash from link
        if '#' in href:
            href = href[:href.index('#')]
        
        # don't process the same link twice
        if href in closed_set:
            continue;
        closed_set.add(href)
        
        #print(href, '"', l.xpath('string()'), '"')
        
        # link to a folder or assignment
        if 'mod/folder/view.php' in href or 'mod/assign/view.php' in href:
            recursed_links += ((tpl[0], sanitize(l.xpath('string()')) + '/' + tpl[1]) for tpl in collect_links(session, href, closed_set))
        # normal link -> only include http(s) links
        elif href.lower().startswith('http'):
            recursed_links.append((href, ''))
    
    return recursed_links


# follow redirects and extracts a filename from an url
# returns (url, filename)
def resolve_link(session, url):
    resp = session.head(url, allow_redirects=True)
    url = resp.url # set to redirected url
    
    filename = None
    # try to extract filename from header
    if 'Content-Disposition' in resp.headers:
        match = re.match('filename="?([^"]+)"?', resp.headers['Content-Disposition'])
        if match:
            filename = match[0]
    
    # otherwise get filename from url
    if not filename:
        filename = url[url.rindex('/')+1:]
        if '?' in filename:
            filename = filename[:filename.index('?')]
            
        filename = utils.unquote(filename)
    
    return (url, filename)
    
    
    
# returns [(resolved_url, download_pathname)],
# with 'download_pathname' containing the filename and a potential website-induced nesting (NOT subfolders from config)
def get_file_links(session, url):
    recursed_links = collect_links(session, url)
    
    print("Resolving", len(recursed_links), "links ...")
    def merge_tuples(tpl):
        url, filename = resolve_link(session, tpl[0])
        return (url, tpl[1] + filename)
    resolved_links = list(map(merge_tuples, recursed_links))
    
    return resolved_links

    
def establish_moodle_session(user, passwd):
    session = Session()

    response = session.get('https://www.moodle.tum.de')
    response = session.get('https://www.moodle.tum.de/Shibboleth.sso/Login?providerId=https://tumidp.lrz.de/idp/shibboleth&target=https://www.moodle.tum.de/auth/shibboleth/index.php')
    response = session.post('https://tumidp.lrz.de/idp/profile/SAML2/Redirect/SSO?execution=e1s1', data={'j_username': user, 'j_password': passwd, '_eventId_proceed':''})
 
    if "Login failed" in response.text:
        raise ValueError("Login failed!")
                            
    parsed = html.fromstring(response.text)

    session.post('https://www.moodle.tum.de/Shibboleth.sso/SAML2/POST',
                 data={'RelayState': parsed.forms[0].fields['RelayState'],
                       'SAMLResponse': parsed.forms[0].fields['SAMLResponse']})

    return session

def establish_piazza_session(user, passwd):
    session = Session()

    response = session.post('https://piazza.com/class', data={'email': user, 'password': passwd})
    
    return session

def main(url, targets, allow_multi_matches, preview_only, user='', passwd=''):
    # create session
    print("Creating session ...")
    if 'www.moodle.tum.de' in url:
        try: session = establish_moodle_session(user, passwd)
        except RequestException:
            print('Failed to establish Moodle session!')
            print_exc()
            return
    elif 'piazza.com' in url:
        try: session = establish_piazza_session(user, passwd)
        except RequestException:
            print('Failed to establish Piazza session!')
            print_exc()
            return
    else:
        session = Session()
        session.auth = (user, passwd)
        session.headers = {
            "Accept-Language": "en-US,en;"
        }

    # get file links
    print("Gathering links ...")
    try:
        links = get_file_links(session, url)
    except RequestException as e:
        print('Failed to gather links!')
        print('  Failed at link:', e.request.url)
        print_exc()
        return
        
    
    remaining_links = set(links)
    
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for i, t in enumerate(targets): # t : (filterFunc, localDir), filterFunc : (url, filename) -> bool
            current_links = list(filter(lambda link: (allow_multi_matches or link in remaining_links)
                                                 and t[0](link[0], link[1]),
                                        links))
            remaining_links -= set(current_links)
            
            local_dir = t[1]
            if(not local_dir.endswith('/')):
                local_dir += '/'
            
            if preview_only:
                print("{} - matched {} files".format(i, len(current_links)))
                print("\n".join("  * {} ({})".format(local_dir + l[1], l[0]) for l in current_links))
            
            # download files
            for l in current_links:
                executor.submit(download_file, session, l[0], local_dir + l[1], preview_only)
    
    if preview_only:
        print("ignored {} files".format(len(remaining_links)))
        print("\n".join("  * {} ({})".format(l[1], l[0]) for l in remaining_links))
    
    print('Done!')
    