#!/usr/bin/python
# todo:
# uh redo ignore cuz globs weird
# make pandoc do the heavy lifting cause regex sux
# all that render_thingy stuff

import os
import glob
import re
import sys
import fnmatch
import shutil
import subprocess
import datetime

# i will SOLVE EVERYTHING with OOP!!!
# ackshually im too lazy to use oop rignt now, i'll do it another ay
#class entry:
#    def __init__(self, path):
#        self.path = path
#        # rendered contents
#        self.contents = None
#        # metadata
#        # self.metadata = None
#        self.date = None
#        self.title = None
#        # local path (add base_url, source_dir, dest_dir later)
#        self.source_path = os.path.join(source_dir, path)
#        self.dest_path = os.path.join(dest_dir, os.path.splitext(path)[0] + '.html')

USAGE = "ssg.py src dst title base_url"


def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('src',
            help='Source directory')
    parser.add_argument('dst',
            help='Destination directory')
    parser.add_argument('title',
            help='Website title')
    parser.add_argument('base_url',
            help='Base url of your website')
    parser.add_argument('author',
            help='Author of your website (for RSS and Atom feeds)',
            default='N/A',
            nargs='?')
    parser.add_argument('description',
            help='Description of your website (for RSS feed)',
            default='my website',
            nargs='?')
    args = parser.parse_args()
    return args

def readlink_file(input_file):
    try:
        # remove trailing slashes, then get the real path
        return os.path.realpath(os.path.normpath(input_file), strict=True)
    except:
        print("Could not resolve path: {}".format(input_file))
        raise SystemExit

def ignore_files():
    # add files to ignore
    # note: in original ssg6 script hidden files are ignored only if there is no .ssgignore
    # first ignore hidden files, header + footer files
    ignore_files = ['*/.*', '*/_*']
    try:
        # is there more to this?
        with open(os.path.join(source_dir, '.ssgignore')) as ssgignore:
            for line in ssgignore.readlines():
                ignore_files.append('*/{}*'.format(line))
    except:
        # fail quietly
        pass
    # convert ignore_files to tuple (or should I use a set?)
    # haha im so clever i use both
    return tuple(set(ignore_files))

def print_status(items, singular, plural):
    num_items = len(items)
    if num_items == 0:
        output = "no {}".format(plural)
    elif num_items == 1:
        output = "{} {}".format(num_items, singular)
    else:
        output = "{} {}".format(num_items, plural)
    print(output, file=sys.stderr)


def copy_dirs(source_dir, dest_dir):
    # ignore all files
    def _ignore_files(directory, files):
        ignored = []
        # ignore patterns that match IGNORE
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
        # also ignore files
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
        # remove duplicates
        return set(files + ignored)
    # copy subdirectories of src to dst, ignore stuff
    shutil.copytree(source_dir, dest_dir, ignore=_ignore_files, dirs_exist_ok=True)

def list_files(directory):
    file_list = []
    ignored = []
    # recursively search for files, ignore those in IGNORE and hidden files
    for root, directories, files in os.walk(directory, topdown=True):
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
        files[:] = [f for f in files if f not in ignored]
        # actually we need to match the pattern
        for filename in files:
            filepath = os.path.join(root, filename)
            file_list.append(filepath)
    return file_list

def list_affected_files(directory, dest_files):
    file_list = []
    has_partials = []
    last_modification = os.stat(dest_files).st_atime
    # recursively search for files, ignore those in IGNORE
    for root, directories, files in os.walk(directory, topdown=True):
        # create list of files to be ignored
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
            ignored.extend(fnmatch.filter(directories, pattern))
        directories[:] = [d for d in directories if d not in ignored]
        files[:] = [f for f in files if f not in ignored]
        for filename in files:
            info = filename.stat()
            if (info.st_mtime > last_modification):
                file_path = os.path.join()
                file_list.append(os)
            if filename.endswith(PARTIAL_EXTENSIONS):
               has_partials.append(filename)
    # return has_partials if has_partials is not empty
    # why tf does it matter if it's a js/css file? wtf?
    return has_partials if not has_partials else file_list

def list_pages(directory):
    # oh god regex no no no
    pages = list_files(directory)
    pages = [page for page in pages if page.endswith(MARKUP_EXTENSIONS)]
    for i in range(len(pages)):
        # remove extra cruft at the beginning of the path
        pages[i] = pages[i].replace(source_dir + '/', '')
        # should i compile into regex object?
        if pages[i].endswith('/index.html'):
            pages[i] = re.sub("/index.html", "/", pages[i])
        if pages[i].endswith('.md'):
            pages[i] = re.sub(".md", ".html", pages[i])
        if pages[i].startswith("./"):
            pages[i] = re.sub("^./", "", pages[i])
        print(pages[i])
    return pages


def render_html_file(body, title):
    # if the body has an <html> starting or closing tag, just spit it back
    if re.search(r"<\/?[Hh][Tt][Mm][Ll]", body):
        return body
    # look for h1 tag
    has_h1 = re.search(r"<\s*[Hh]1(>|\s[^>]*>)", body)
    if has_h1:
        t = has_h1.string[has_h1.start():has_h1.end()]
        # remove h1 closing tag
        t = re.sub(r"<\s*\/\s*[Hh]1.*", "", t, count=1)
        # remove leading and trailing whitespace
        t = re.sub(r"^\s*|\s$", "", t)
        if t:
            title = t + " &mdash; " + title
    result = ''
    header = HEADER.split(sep='\n')
    n = len(header)
    for i in range(n):
        line = header[i]
        has_title = re.search(r"<title></title>", line.lower())
        if has_title:
            head = line[0:has_title.start()]
            tail = line[has_title.start():has_title.end()]
            result = '\n'.join((result, head, ' '.join(("<title>", title, "</title>")), tail))
        else:
            result = '\n'.join((result, line))
    result = '\n'.join((result, body, FOOTER))
    return result

def render_markup_files(files, src, dst, title):
    import json

    for f in files:
        output_path = (os.path.splitext(f)[0] + ".html").replace(src, dst, 1)
        try:
            rendered_html = subprocess.run(['pandoc', '--to=html', '--quiet', '--defaults=pandoc/defaults.yaml', f], capture_output=True).stdout.decode('utf-8')
            # skip index
            if os.path.basename(output_path) != "index.html":
                file_metadata = json.loads(subprocess.run(['pandoc', '--to=html', '--quiet', '--template=pandoc/templates/metadata.ext', f], capture_output=True).stdout.decode('utf-8'))
                # convert all dictionary keys to lowercase
                file_metadata = {k.lower(): v for k, v in file_metadata.items()}
                date = file_metadata['date']
                title = file_metadata['title']
                header = "{}\n<p class=\"date\" {} </p>".format(title, date)
                complete_file = '\n'.join((header, rendered_html))
                # don't make function to render_toc
                # use pandoc yaml metadata toc option in the md files instead
                output_html = render_html_file(complete_file, title)
            else:
                # don't need date, title and toc for index.html
                # output_html = rendered_html
                output_html = render_html_file(rendered_html, title)
            with open(output_path, 'w') as output:
                output.write(output_html)
        except RuntimeError:
            print("Could not render file: {}".format(f))
            raise SystemExit

def render_html_files(files, src, dst, title):
    for f in files:
        output_path = f.replace(src, dst, 1)
        with open(f) as html_file:
            contents = html_file.read()
        output_text = render_html_file(contents, title)
        with open(output_path, 'w') as output:
            output.write(output_text)


def render_sitemap(urls, base_url):
    today = str(datetime.date.today())
    output = """<?xml version="1.0" encoding="UTF-8"?>
	<urlset
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
	http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
	xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    """
    for url in urls:
        output = '\n'.join((output, "<url><loc>{}/{}</loc><lastmod>{}</lastmod><priority>1.0</priority></url>".format(base_url, url, today)))
    output = '\n'.join((output, "</urlset>"))
    with open(os.path.join(dest_dir, 'sitemap.xml'), 'w') as sitemap:
        sitemap.write(output)

def render_article_list(urls, base_url):
    # gaaah this is so inefficient, reads every file twice for date
    items = ""
    urls_sorted = []
    for i in urls:
        i = os.path.join(source_dir, i)
        if not i.endswith(("/index.html", "/contact.html")):
            markup_file_path = os.path.splitext(i)[0] + '.md'
            with open(markup_file_path) as f:
                    contents = f.read()
                    has_date = re.search(r'\b(Date|date)\b\s*:(.*)', contents)
                    page_date = has_date.string[has_date.start():has_date.end()]
                    page_date = re.sub(r'\b(Date|date)\b\s*:\s*', '', page_date)
                    url = [page_date, i.replace(source_dir + '/', '')]
                    urls_sorted.append(url)
    urls_sorted.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)
    urls_sorted = [q[1] for q in urls_sorted]
    for url in urls_sorted:
           # ughhh i already had the metadata, now i have to parse it AGAIN AAAAAAAAAAAAAAAAAAHHHHHHHH
        real_path = os.path.splitext(os.path.join(source_dir, url))[0] + '.md'
        print(real_path)
        with open(real_path) as f:
            contents = f.read()
            # geezus look at this. This sucks!
            # has_title = re.search(r'\s*\b(Title|title)\b:(.*)', contents)
            # has_date = re.search(r'\s*\b(Date|date)\b:(.*)', contents)
            has_title = re.search(r'\b(Title|title)\b\s*:(.*)', contents)
            has_date = re.search(r'\b(Date|date)\b\s*:(.*)', contents)
            page_title = has_title.string[has_title.start():has_title.end()]
            page_date = has_date.string[has_date.start():has_date.end()]
            # get rid of "title:" and "date:"
            page_title = re.sub(r'\b(Title|title)\b\s*:\s*', '', page_title)
            page_date = re.sub(r'\b(Date|date)\b\s*:\s*', '', page_date)
            # remove cruft at beginning of file
            url = os.path.join(base_url, url)
            item = "<li><a href=\"{}\">{}</a><p class=\"date\"{}</p></li>".format(url, page_title, page_date)
            # k this kinda sucks too
            items = items + item

    with open(os.path.join(dest_dir, 'index.html'), 'r+') as index:
        contents = index.read()
        # gotta do this extra stuff because i opened as r+
        index.seek(0)
        # don't touch article list if same otherwise replace
        if "<ul class=\"articles\">{}</ul>".format(items) not in contents:
            contents = re.sub(r"(.*)<ul class=\"articles\">(.*)", "<ul class=\"articles\">{}</ul>".format(items), contents)
        if "<ul class=\"articles\">" not in contents:
            contents = contents.replace("</article>", "<ul class=\"articles\">{}</ul></article>".format(items))
        index.write(contents)
        index.truncate()


def render_feeds(urls, author):
    def _create_id(url, page_date):
        result = url.split(sep='://',maxsplit=1)[1]
        parts = result.split(sep='/',maxsplit=1)
        result = parts[0]+','+page_date+':'+parts[1]
        return result
    def _get_article(url):
        rendered_output_path = os.path.join(dest_dir, url)
        with open(rendered_output_path) as rendered_output:
            contents = rendered_output.read()
            # why tf is it making the string hang
            has_article = re.search(r'\s*(<article>)[\s\S]*(</article>)', contents)
            article = has_article.string[has_article.start():has_article.end()]
            article = re.sub(r'(<article>|</article>)', '', article)
            article = re.sub(r'(^\s*|\s*$)', '', article)
            return article
    try:
        from feedgen.feed import FeedGenerator
        fg = FeedGenerator()
        fg.id(_create_id(base_url,str(datetime.date.today())))
        fg.title(title)
        fg.author({'name':author,  'email':' '})
        fg.link(href=base_url, rel='self')
        fg.description(website_description)
        for url in urls:
            if not url.endswith(("index.html", "contact.html")):
                local_path = os.path.splitext(os.path.join(source_dir, url))[0] + '.md'
                with open(local_path) as f:
                    contents = f.read()
                    has_title = re.search(r'\b(Title|title)\b\s*:(.*)', contents)
                    has_date = re.search(r'\b(Date|date)\b\s*:(.*)', contents)
                    page_title = has_title.string[has_title.start():has_title.end()]
                    page_date = has_date.string[has_date.start():has_date.end()]
                    # get rid of "title:" and "date:"
                    page_title = re.sub(r'\b(Title|title)\b\s*:\s*', '', page_title)
                    page_date = re.sub(r'\b(Date|date)\b\s*:\s*', '', page_date)

                website_url = os.path.join(base_url, url)
                fe = fg.add_entry()
                fe.id(_create_id(website_url, page_date))
                fe.link(href=website_url)
                fe.description(_get_article(url))
                fe.title(page_title)
                # fe.pubDate(datetime.datetime.strptime(page_date, '%Y-%m-%d'))
        fg.atom_file(os.path.join(dest_dir, 'atom.xml'))
        fg.rss_file(os.path.join(dest_dir, 'rss.xml'))

    except ModuleNotFoundError:
        print("Note: Feedgen module not found, cannot render RSS and Atom feeds!", file=sys.stderr)


def check_deps():
    if not shutil.which("pandoc"):
        print("could not find pandoc, do you have it installed?")
        raise SystemExit


def main():
    args = parse_arguments()
    global source_dir, dest_dir, base_url, author, website_description
    source_dir = readlink_file(args.src)
    dest_dir = readlink_file(args.dst)
    base_url = args.base_url
    author = args.author
    website_description = args.description
    # should this be before initialization of source_dir
    if (not os.path.isdir(source_dir)) or (not os.path.isdir(dest_dir)):
        print("No such directory")
        raise SystemExit
    global IGNORE, MARKUP_EXTENSIONS, PARTIAL_EXTENSIONS
    IGNORE = ignore_files()
    MARKUP_EXTENSIONS = ('.md', '.org')
    PARTIAL_EXTENSIONS = ('.html','.js', '.css')

    # files - wtf does this mean?
    global title, HEADER, FOOTER
    title = args.title
    HEADER = ''
    header_path = os.path.join(source_dir, '_header.html')
    try:
        with open(header_path) as header_file:
            HEADER = header_file.read()
    except:
        # fail quietly
        pass

    FOOTER = ''
    footer_path = os.path.join(source_dir, '_footer.html')
    try:
        with open(footer_path) as footer_file:
            FOOTER = footer_file.read()
    except:
        # fail quietly
        pass

    # check that pandoc is installed
    check_deps()

    copy_dirs(source_dir, dest_dir)
    # files to operate on
    files = []
    dest_file_list = os.path.join(dest_dir, '.files')
    try:
        files = list_affected_files(source_dir, dest_file_list)
    except:
        files = list_files(source_dir)

    # try:
    if files:
        with open(dest_file_list, 'w') as files_list:
            files_str = """{}""".format('\n'.join(files))
            files_list.write(files_str)
        # render all markup files
        markup_files = []
        html_files = []
        other_files = []
        for f in files:
            if f.endswith('.html'):
                html_files.append(f)
            elif f.endswith(MARKUP_EXTENSIONS):
                markup_files.append(f)
            else:
                other_files.append(f)

        render_markup_files(markup_files, source_dir, dest_dir, title)
        render_html_files(html_files, source_dir, dest_dir, title)
        # copy other files
        for f in other_files:
            shutil.copy2(f, f.replace(source_dir, dest_dir))

        print("[ssg.py]", file=sys.stderr)
        print_status(files, 'file ', 'files ')
    # add more exceptions later
    # except:
    #     print("Could not write to {}!".format(dest_file_list))

    urls = list_pages(source_dir)
    if urls:
        render_sitemap(urls, base_url)
        render_article_list(urls, base_url)
        render_feeds(urls,author)

main()
